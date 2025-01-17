"""
    project     : Digital Editor

    type:       : Host
    file        : Business Logic

    description : Host Business Logic class
"""

from protocols.network          import *
from protocols.files_manager    import *
from protocols.registration     import *
from utilities.event            import c_event
from utilities.wrappers         import safe_call, standalone_execute

import threading
import base64
import queue
import time
import os

DEFAULT_FOLDER_NAME:    str     = "Digital Files"

TIMEOUT_CONNECTION:     float   = 0.5
TIMEOUT_MSG:            float   = 0.5
TIMEOUT_COMMAND:        float   = 0.1

ENUM_PROTOCOL_FILES:    int     = 1
ENUM_PROTOCOL_NETWORK:  int     = 2
ENUM_PROTOCOL_UNK:      int     = 0


class c_command:

    _client:    any     # c_client_handle

    _protocol:  int
    _command:   str
    _arguments: list

    def __init__( self, client: any,protocol: int, command: str, arguments: list ):
        """
            Default constructor for command object.
            
            Receive :
            - client    - Client handle object
            - protocol  - Related protocol command
            - command   - Command itself
            - arguments - Arguments for command

            Returns :   Command object
        """

        self._client    = client
        self._protocol  = protocol
        self._command   = command
        self._arguments = arguments

    
    def client( self ) -> any:
        """
            Access the client.

            Receive :   None

            Returns :   Client handle object
        """

        return self._client
    

    def protocol( self ) -> int:
        """
            Access the protocol index.

            Receive :   None

            Returns :   Int - Protocol enum
        """

        return self._protocol
    

    def command( self ) -> str:
        """
            Access the command itself.

            Receive :   None

            Returns :   Command string
        """

        return self._command
    

    def arguments( self ) -> list:
        """
            Access the arguments list.

            Receive :   None

            Returns :   List
        """

        return self._arguments


class c_client_handle:
    
    # region : Private Attributes

    _network:           c_network_protocol          # Clients handle network connection
    _files:             c_files_manager_protocol    # Clients handle files
    _registration:      c_registration_protocol     # Clients register process

    _information:       dict                        # Clients information
    _events:            dict                        # Each client events

    _selected_file:     c_virtual_file              # Selected file
    _selected_line:     int                         # Selected line

    _offsets:           list                        # Offsets for missed lines
    # We dont want modded client to spoof index change response.
    # As a result each change will be added to a list, and in general used as sum( ) for offset
    # And checks if one offset is responded, just remove from the list.

    _trust_factor:      int                         # Trust factor for the client
    _is_modded:         bool                        # Is the client modded
    _issues:            list                        # Issues that the client created that lowered the trust factor
    # This part will be used to keep track of the issues that the client created.
    # If the client created an issue, the trust factor will be lowered.
    # If the client didn't create any issue in a while, the trust factor will be increased.
    # The trust factor will be between 100 - 0. If the trust factor is 0, the client will be disconnected.

    _files_commands:    dict

    # endregion

    # region : Initialization client handle

    def __init__( self ):
        """
            Default constructor for client handle.

            Receive:    None

            Returns:    None
        """

        # Initialize client's events
        self.__initialize_events( )

        # Initialize client's information
        self.__initialize_information( )

    
    def __initialize_events( self ):
        """
            Initialize events for client handle.

            Receive:    None

            Returns:    None
        """

        self._events = {
            "on_client_connected":      c_event(),
            "on_client_disconnected":   c_event(),
            "on_client_command":        c_event()
        }

    
    def __initialize_information( self ):
        """
            Initialize information for client handle.

            Receive:    None

            Returns:    None
        """

        self._network       = None
        self._files         = c_files_manager_protocol( )
        self._registration  = c_registration_protocol( )

        self._information = {
            "last_error":   "",
            "username":     "unknown"
        }

        self._selected_file     = None
        self._selected_line     = 0
        self._trust_factor      = 50
        self._offsets           = [ ]

        self._files_commands = {
            FILES_COMMAND_REQ_FILES:        self.__share_files,

            FILES_COMMAND_GET_FILE:         None,

            FILES_COMMAND_PREPARE_UPDATE:   None,
            FILES_COMMAND_PREPARE_RESPONSE: None,
            FILES_COMMAND_UPDATE_LINE:      None,
            FILES_COMMAND_DELETE_LINE:      None,
            FILES_COMMAND_DISCARD_UPDATE:   None,
            FILES_COMMAND_APPLY_UPDATE:     None
        }

    # endregion

    # region : Connection

    def connect( self, socket_object: socket, address: tuple ) -> bool:
        """
            Connect the client to the server.

            Receive:    
            - socket_object     - Client socket object
            - address           - Client address

            Returns:    bool - Is the client connected successfully
        """
        print( f"Connected { address }" )

        # Attach connection
        self.__attach_connection( socket_object, address )

        # Register the connection
        self.__register_connection( )

        self.__event_client_connected( address )

        # Attach processes
        self.__attach_processes( )

        return True
    

    def __attach_connection( self, socket_object: socket, address: tuple ):
        """
            Create new connection object and attach it in the network protocol.

            Receive :
            - socket_object - Client socket
            - address       - Client address

            Returns :   None
        """

        # Create connection
        new_connection = c_connection( )

        # Unlike the default .connect. Here we just give the information. 
        new_connection.attach( address[0], address[1], socket_object )

        # Create and attach the connection to the protocol
        self._network = c_network_protocol( new_connection )

    
    def __register_connection( self ):
        """
            Register the connection to the server.

            Receive:    None

            Returns:    None
        """

        # Here will be the registration process
        # First the client will need to exchange encryption keys with the server
        # Afterwards it will register itself with a password and username

        raw_msg: str = self._network.receive( ).decode( )
        if not raw_msg.startswith( self._registration.get_header( ) ):
            self._information[ "last_error" ] = "Cannot receive normalized registration information about client"
            return self.disconnect( False )

        command, arguments = self._registration.parse_message( raw_msg )
        if not command or not arguments:
            self._information[ "last_error" ] = "Failed to parse message"
            return 

        self._information[ "username" ] = arguments[ 0 ]
        
        print( f"Client completed registration with { arguments }" )

    
    def __attach_processes( self ):
        """
            Attach processes for the client handle.

            Receive:    None

            Returns:    None
        """

        # Start the receive process
        self.__receive_process( )


    def disconnect( self, notify_the_client: bool = True ):
        """
            Disconnect the client from the server.

            Receive:    
            - notify_the_client  - Notify the client about the disconnection

            Returns:    None
        """

        # Potentially notify the client
        if notify_the_client:
            self._network.send( DISCONNECT_MSG )

        # End the connection
        self._network.end_connection( )

        # Call the event
        self.__event_client_disconnected( notify_the_client )

        print( f"Disconnected" )

    # endregion

    # region : Communication

    @standalone_execute
    def __receive_process( self ):
        """
            Process for receiving messages from the client.

            Receive:    None

            Returns:    None
        """

        # Run the process while the network is valid
        while self._network.is_valid( ):
            
            # Receive the message
            result = self._network.receive( TIMEOUT_MSG )

            # If there is no message, continue
            if result is None:
                continue
            
            # Decode the message
            result = result.decode( )
        
            self.__handle_message( result )


    def __handle_message( self, message: str ):
        """
            Handle message from client.

            Receive :
            - message - Client's message

            Returns :   None
        """

        print( message )

        if message == DISCONNECT_MSG:
            return self.disconnect( False )

        if message == PING_MSG:
            return print( "Client ping" )

        protocol, command, arguments = self.__parse_message( message )

        del message

        # Create a command object
        new_command = c_command( self, protocol, command, arguments )

        if not self.__verify( new_command ):
            del new_command
            return

        # Check if the client handle can handle the command by it self
        if protocol == ENUM_PROTOCOL_FILES:

            callback = self._files_commands[ command ]
            if callback is not None:
                return callback( command )

        # If it cannot, attach the command to the pool
        self.__event_client_command( new_command )

    
    def __parse_message( self, message: str ) -> tuple:
        """
            Parse message from the client.

            Receive :
            - message - Client's message

            Returns : Tuple ( Protocol, Command, Arguments )
        """

        if message.startswith( self._files.get_header( ) ):
            # Files protocol message
            command, arguments = self._files.parse_message( message )

            return ENUM_PROTOCOL_FILES, command, arguments
        
        # If failed
        return ENUM_PROTOCOL_UNK, message, None


    def __verify( self, command: c_command ) -> bool:
        """
            Verify if the command is valid.

            Receive :
            - command - Command object

            Returns :   Result 
        """

        protocol = command.protocol( )

        if protocol == ENUM_PROTOCOL_UNK:
            return False

        if protocol == ENUM_PROTOCOL_FILES:
            return command.command( ) in self._files_commands

        return True

    # endregion

    # region : Events

    def __event_client_connected( self, address: tuple ):
        """
            Event when the client connected to the server.

            Receive: 
            - address   - Client address

            Returns:    None
        """

        event: c_event = self._events[ "on_client_connected" ]
        event.attach( "ip",     address[ 0 ] )
        event.attach( "port",   address[ 1 ] )

        event.invoke( )


    def __event_client_disconnected( self, notify_the_client: bool ):
        """
            Event when the client disconnected from the server.

            Receive:    
            - notify_the_client  - Notify the client about the disconnection

            Returns:    None
        """

        event: c_event = self._events[ "on_client_disconnected" ]
        event.attach( "client", self )
        event.attach( "notify", notify_the_client and "1" or "0" )

        event.invoke( )

    
    def __event_client_command( self, command: c_command ):
        """
            Event when the client sent a command.

            Receive:    
            - command   - Command object

            Returns:    None
        """

        event: c_event = self._events[ "on_client_command" ]
        event.attach( "command", command )

        event.invoke( )
    

    def set_event( self, event_name: str, callback: any, index: str ):
        """
            Set an event for the client handle.

            Receive:    
            - event_name    - Event name
            - callback      - Callback function
            - index         - Index of the event

            Returns:    None
        """

        if not event_name in self._events:
            raise Exception( f"Event {event_name} is not valid." )
        
        event: c_event = self._events[ event_name ]
        event.set( callback, index, True )

    # endregion

    # region : File and line

    def load_files( self, files_protocol: c_files_manager_protocol ):
        """
            Initialize files for client.

            Receive :   
            - files - Files access

            Returns :   None
        """

        files: dict = files_protocol.get_files( )

        for index in files:
            file: c_virtual_file = files[ index ]

            self._files.copy( file )


    def __share_files( self, command: c_command ):
        """
            Share with client the allowed files.

            Receive :   
            - command - Original command

            Returns :   None
        """

        files_list: str = self._files.share_files( )

        self._network.send( files_list )


    # endregion

    # region : Offsets

    def get_offset( self ) -> int:
        """
            Get the offset for the client.

            Receive:    None

            Returns:    int - Offset
        """

        return sum( self._offsets )
    

    def add_offset( self, offset: int ):
        """
            Add an offset to the client.

            Receive:    
            - offset    - Offset

            Returns:    None
        """

        self._offsets.append( offset )

    
    def is_offset( self, offset: int ) -> bool:
        """
            Check if the client has an offset.

            Receive:    
            - offset    - Offset

            Returns:    bool - Is the offset in the client
        """

        for item in self._offsets:
            if offset == item:
                return True
            
        return False
    

    def remove_offset( self, offset: int ) -> bool:
        """
            Remove an offset from the client.

            Receive:    
            - offset    - Offset

            Returns:    bool - Is the offset removed
        """

        if not self.is_offset( offset ):
            return False
        
        self._offsets.remove( offset )
        return True

    # endregion

    # region : Utility

    def network( self ) -> c_network_protocol:
        """
            Get the network protocol.

            Receive :   None

            Returns :   c_network_protocol - Network protocol
        """

        return self._network
    

    def files( self ) -> c_files_manager_protocol:
        """
            Get the clients files protocol.

            Receive :   None

            Returns :   c_files_manager_protocol - Files protocol
        """

        return self._files
    

    def __call__( self, index: str ):
        """
            Index clients information.

            Receive:    
            - index - Index of the information

            Returns:    Any - Information
        """

        if index in self._information:
            return self._information[ index ]
        
        return None
    

    def __eq__( self, other ) -> bool:
        """
            Check if the client handle is equal to another client handle.

            Receive:    
            - other - Other client handle

            Returns:    bool - Is the client handle equal to the other
        """

        current_address = self._network.get_address( )
        other_address   = other._network.get_address( )

        if current_address[ 0 ] != other_address[ 0 ]:
            return False
        
        if current_address[ 1 ] != other_address[ 1 ]:
            return False
        
        return True

    # endregion




class c_host_business_logic:
    
    # region : Private Attributes

    _network:       c_network_protocol
    _files:         c_files_manager_protocol

    _information:   dict
    _events:        dict
    
    _command_pool:  queue.Queue

    _clients:       list

    # endregion 

    # region : Initialization host business logic

    def __init__( self ):
        """
            Default constructor for host business logic.

            Receive:    None

            Returns:    None
        """

        self.__initialize_protocols( )

        self.__initialize_events( )

        self.__initialize_information( )


    def __initialize_protocols( self ):
        """
            Initialize protocols for host business logic.

            Receive:    None

            Returns:    None
        """

        self._network = c_network_protocol()
        self._files   = c_files_manager_protocol()

    
    def __initialize_events( self ):
        """
            Initialize events for host business logic.

            Receive:    None

            Returns:    None
        """

        self._events = {
            "on_server_start":          c_event( ),
            "on_server_stop":           c_event( ),

            "on_client_connected":      c_event( ),
            "on_client_disconnected":   c_event( ),
            "on_client_command":        c_event( ),
        }


    def __initialize_information( self ):
        """
            Initialize information for host business logic.

            Receive:    None

            Returns:    None
        """

        self._information = {
            "success":          False,  # Is the setup process was successful
            "running":          False,  # Is server running
            "last_error":       ""      # Last error message
        }

        self._clients = [ ]

        self._command_pool = queue.Queue( )

    # endregion

    # region : Connection

    def setup( self, ip: str, port: int ):
        """
            Setup the server for host business logic.

            Receive:    
            - ip    - IP address      
            - port  - Port number

            Returns:    None
        """

        # I dont use @safe_call since I need to add debug options later on

        try:

            # Just save the information
            self._information[ "ip" ]       = ip
            self._information[ "port" ]     = port

            # Start connection using network protocol
            self._network.start_connection( CONNECTION_TYPE_SERVER, ip, port )

            # Set success setup flag to true
            self._information[ "success" ] = True

        except Exception as e:

            # In case of some error. Handle it
            self._information["last_error"] = f"Error occured on .setup() : {e}"
            self._information[ "success" ]  = False
            

    def start( self ) -> bool:
        """
            Start the server for host business logic.

            Receive:    None

            Returns:    bool - Is the server started successfully
        """

        if not self._information[ "success" ]:
            self._information[ "last_error" ]   = f"Cannot start the server execution if it hasn't been setupped."
            return False
        
        # Update is Running flag
        self._information[ "running" ] = True

        # Call event
        self.__event_host_start( )

        # Start to listen for new connections
        self._network.look_for_connections( )

        # Start the server process
        self.__attach_processes( )

        return True


    def terminate( self ):
        """
            Terminate the host.

            Receive:    None

            Returns:    None
        """

        # Update is Running flag
        self._information[ "running" ] = False

        # Call event
        self.__event_host_stop( )

        # Disconnect all the remaining clients
        for client in self._clients:
            client: c_client_handle = client

            client.disconnect( True )

        self._clients.clear( )

        # Close the network connection
        self._network.end_connection( )


    def generate_code( self ) -> str:
        """
            Generate a code for the client to connect to the server.

            Receive:    None

            Returns:    str - Generated code
        """

        local_ip, local_port = self._network.get_address( )

        result = f"{local_ip}:{local_port}"
        return base64.b64encode( result.encode( ) ).decode( )
    
    # endregion

    # region : Processes

    def __attach_processes( self ):
        """
            Attach processes for the host business logic.

            Receive:    None

            Returns:    None
        """

        # Start the process for handling connections
        self._information[ "connection_thread" ] = self.__process_handle_connections( )

        # Start the process for handling commands
        self._information[ "command_thread" ] = self.__process_handle_commands( )


    @standalone_execute
    def __process_handle_connections( self ):
        """
            Process for handling connections.

            Receive:    None
            
            Returns:    None
        """

        while self._information[ "running" ]:

            # Get the new client
            client_socket, client_addr = self._network.accept_connection( TIMEOUT_CONNECTION )

            # If there is no client, continue
            if client_socket is None or client_addr is None:
                continue

            self.__event_client_connected( client_socket, client_addr )


    @standalone_execute
    def __process_handle_commands( self ):
        """
            Process for handling commands.

            Receive:    None

            Returns:    None
        """

        while self._information[ "running" ]:

            if not self._command_pool.empty( ):

                # Get the command from the pool
                command: c_command = self._command_pool.get( block=False )

                # If there is no command, continue
                if command is None:
                    continue

                self.__handle_command( command )

            else:
                
                # If our command queue is empty, just sleep for 0.1 seconds.
                # Othersize this thread will run million times per second.
                time.sleep( TIMEOUT_COMMAND )

    # endregion

    # region : Commands

    def __handle_command( self, command: c_command ):
        """
            Handle command request.

            Receive :
            - command - Command object from client

            Returns :   None
        """

        protocol: int = command.protocol( )

        print( command.command( ) )
        print( command.arguments( ) )

    # endregion

    # region : Files

    def initialize_path( self, path: str, default_access_level: str ):
        """
            Create and setup the project files path.

            Receive :
            - path - Path string for files

            Returns :   None
        """

        self._information[ "original_path" ] = path
        self._information[ "default_access" ] = default_access_level

        self.__setup_default_access_level( )

        self.__setup_path( )

        self.__setup_files( )


    def __setup_default_access_level( self ):
        """
            Setup default access level for new users.

            Receive :   None

            Returns :   None
        """

        level: str = self._information[ "default_access" ]

        del self._information[ "default_access" ]

        level_number = {
            "Hidden":   FILE_ACCESS_LEVEL_HIDDEN,
            "Edit":     FILE_ACCESS_LEVEL_EDIT,
            "Limit":    FILE_ACCESS_LEVEL_LIMIT
        }

        if level not in level_number:
            raise Exception( "Invalid access level type" )
        
        self._information[ "default_access" ] = level_number[ level ]


    def __setup_path( self ):
        """
            Setup Folder for files.

            Receive :   None

            Returns :   None
        """

        original_path   = self._information[ "original_path" ]
        normal_path     = f"{ original_path }\\{ DEFAULT_FOLDER_NAME }"

        self._information[ "normal_path" ] = normal_path
        
        if not os.path.exists( normal_path ):
            os.mkdir( normal_path )


    def __setup_files( self ):
        """
            Setup files of the project.

            Receive :   None

            Returns :   None
        """

        # Here need to make a copy of each file to the new path.
        # Besides, create for each file another file that stores all the changes
        original_path   = self._information[ "original_path" ]

        self.__dump_path( original_path )


    def __dump_path( self, path: str ):
        """
            Dump specific path.

            Receive : 
            - path - Full path to a folder to dump

            Returns :   None
        """
        
        original_path   = self._information[ "original_path" ]
        normal_path     = self._information[ "normal_path" ]
        access_level    = self._information[ "default_access" ]

        with os.scandir( path ) as entries:
            
            for entry in entries:
                
                if entry.is_file( ):
                    # Is File

                    # TODO ! Check if the file already copied

                    fixed_name = f"{ path.replace( original_path, "" ) }\\{ entry.name }"
                    fixed_name = fixed_name.lstrip( "\\" )
                    
                    file = self._files.create_new_file( fixed_name, access_level, True )
                    r = file.copy( original_path, normal_path )

                    if r is not None:
                        print( r )
                    else:
                        print( file.name( ) )

                if entry.is_dir( ) and entry.name != DEFAULT_FOLDER_NAME and not entry.name.startswith( "." ):
                    # Is Folder
                    
                    self.__dump_path( f"{ path }\\{ entry.name }" )
            
    # endregion

    # region : Files operations

    def __operation_request_files( self, arguments: list, client: c_client_handle ):
        """
            Preform operation on request files.

            Receive :
            - arguments - Arguments from request
            - client    - Client handle

            Returns :   None
        """

        network: c_network_protocol = client.network( )

        files_list: str = client.files( ).share_files( )

        network.send( files_list )

    # endregion

    # region : Events

    def __event_host_start( self ):
        """
            Event when the host server started.

            Receive:    None

            Returns:    None
        """

        event: c_event = self._events[ "on_server_start" ]
        event.invoke( )

    
    def __event_host_stop( self ):
        """
            Event when the host server stopped.

            Receive:    None

            Returns:    None
        """

        event: c_event = self._events[ "on_server_stop" ]
        event.invoke( )

    
    def __event_client_connected( self, client_socket: socket, client_address: tuple ):
        """
            Event when a client connected to the server.

            Receive:    
            - client_socket     - Client socket
            - client_address    - Client address

            Returns:    None
        """

        # Create a new client handle
        new_client = c_client_handle( )

        # Save the client object
        self._clients.append( new_client )

        # Set the client events
        new_client.set_event( "on_client_disconnected", self.__event_client_disconnected,   "Host Client Disconnect" )
        new_client.set_event( "on_client_command",      self.__event_client_command,        "Host Client Command" )

        # Attach files for client
        new_client.load_files( self._files )

        # Connect the client
        new_client.connect( client_socket, client_address )

        # Call the event
        event: c_event = self._events[ "on_client_connected" ]
        event.invoke( )

    
    def __event_client_disconnected( self, event ):
        """
            Event when a client disconnected from the server.

            Receive:    
            - event - Event information

            Returns:    None
        """

        if event( "notify" ) == "0":
            client: c_client_handle = event( "client" )

            # Remove the client from the list
            self._clients.remove( client )

        # Call the event
        event: c_event = self._events[ "on_client_disconnected" ]
        event.invoke( )

    
    def __event_client_command( self, event ):
        """
            Event when a client sent a command.

            Receive:    
            - event - Event information

            Returns:    None
        """

        command: c_command = event( "command" )
        if command is None:
            return

        # Add the command to the pool
        self._command_pool.put( event( "command" ) )

        # Call the event
        event: c_event = self._events[ "on_client_command" ]
        event.invoke( )

    # endregion