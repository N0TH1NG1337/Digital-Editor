"""
    project     : Digital Editor

    type:       : Server
    file        : Business Logic

    description : Server Business Logic class
"""

from protocols.network          import *
from protocols.files_manager    import *
from utilities.event            import c_event
from utilities.base64           import base64
from utilities.wrappers         import safe_call, standalone_execute

import threading
import queue
import time
import os


DEFAULT_FOLDER_NAME = "Digital Files"


class c_cmd:
    
    _client:    any  
    _message:   str

    def __init__( self, client: any, message: str ):
        """
            Default constructor for command object.
            
            Receive :
            - client    - Client handle object
            - message   - The message it self

            Returns :   Command object
        """

        self._client    = client
        self._message   = message

    
    def client( self ) -> any:
        """
            Access the client.

            Receive :   None

            Returns :   Client handle object
        """

        return self._client
    

    def message( self ) -> str:
        """
            Access the message.

            Receive :   None

            Returns :   String value
        """

        return self._message

    


class c_client_handle:
    
    _network:       c_network_protocol  # Clients handle network connection

    _information:   dict                # Clients information
    _events:        dict                # Each client events

    # This is where the fun (cancer starts)
    _selected_file: c_virtual_file
    _selected_line: int
    _offset_index:  int

    # TODO ! ADD SELECTED LINE. OTHERWISE IT WILL BE POSSIBLE TO SPOOF LINE CHANGES

    # region : Initialize client handle

    def __init__( self ):
        """
            Default constructor for client handle.

            Receive :   None

            Returns :   Client handle object
        """

        self.__initialize_events( )

        self.__initialize_information( )

    
    def __initialize_events( self ):
        """
            Initialize each client handle events.

            Receive :   None

            Returns :   None
        """

        self._events = { }

        self._events[ "connect" ]       = c_event( )
        self._events[ "disconnect" ]    = c_event( )

        self._events[ "register_cmd" ]  = c_event( )
        self._events[ "log" ]           = c_event( )
    

    def __initialize_information( self ):
        """
            Initialize client handle information handle.

            Receive :   None

            Returns :   None
        """

        self._network       = None

        self._information   = { }

        # If this is None. It means that the client didnt choose any file.
        # WARNING ! CANNOT BE NONE IF ONCE CHECKED ANY FILE
        self._selected_file = None

        self._selected_line = 0
        self._offset_index  = -1

    # endregion

    # region : Connection

    def connect( self, socket_object: socket, address: tuple ):
        """
            Attach client connection details.

            Receive :
            - socket_object - Client socket
            - address       - Client address

            Returns :   None
        """

        self.__event_log( f"Client connected { address }" )

        # Attach connection
        self.__attach_connection( socket_object, address )

        # Register connection
        self.__register_connection( )

        self.__event_log( f"Client connected { address } registered as { self._information[ "username" ] }" )

        # Call the event
        self.__event_connect( address )

        # Complete the connection by running the receive process attachment
        self.__attach_receive_process( )


    def disconnect( self, notify_the_client: bool = True ):
        """
            Close connection from the server to client.

            Receive :   
            - notify_the_client [optional] - Send notification to client

            Returns :   None
        """

        # Potentially warn the client of closing connection
        if notify_the_client:
            self._network.send( DISCONNECT_MSG )

        # Close connection
        self._network.end_connection( )

        # Call the event
        self.__event_disconnect( notify_the_client )


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
    

    def __attach_receive_process( self ):
        """
            Receive process attachment.

            Receive :   None

            Returns :   None
        """

        self._information[ "receive_thread" ] = threading.Thread( target=self.__receive_process )
        self._information[ "receive_thread" ].start( )


    def __register_connection( self ):
        """
            Register the client with username.

            Receive :   None

            Returns :   None
        """

        raw_msg: str = self._network.receive( ).decode( )
        if not raw_msg.startswith( "username::" ):
            return
        
        parse_username = raw_msg.split( "::" )
        self._information[ "username" ] = parse_username[ 1 ]

    # endregion

    # region : Communication

    def __receive_process( self ):
        """
            Main receive function.

            Receive :   None

            Returns :   None
        """

        while self._network.is_valid():
            res = self._network.receive( 0.5 )

            if res is None:
                continue

            res = res.decode( )

            self.__event_log( f"Received from { self._information[ "username" ] } : { res }" )

            if res == DISCONNECT_MSG:
                self.disconnect( False )

                self.__event_log( f"Goodbye { self._information[ "username" ] }" )
                
                continue

            # Manuall checks

            # Create new command object
            new_cmd = c_cmd( self, res )

            # Pass it to the server command queue
            self.__event_register_cmd( new_cmd )

    # endregion

    # region : Events

    def __event_connect( self, address: tuple ):
        """
            Event client connect to server.

            Receive : 
            - address - Client address

            Returns :   None
        """

        event: c_event = self._events[ "connect" ]
        event.attach( "ip",     address[ 0 ] )
        event.attach( "port",   address[ 1 ] )

        event.invoke( )

    
    def __event_disconnect( self, notify_the_client: bool ):
        """
            Event client disconnect from the server.

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "disconnect" ]
        event.attach( "client", self )
        event.attach( "notify", notify_the_client and "1" or "0" )

        event.invoke( )


    def __event_register_cmd( self, command: c_cmd ):
        """
            Event register command to server

            Receive :   
            - command - Command to register to the server

            Returns :   None
        """

        event: c_event = self._events[ "register_cmd" ]
        event.attach( "command", command )

        event.invoke( )

    
    def __event_log( self, text: str ):
        """
            Event log. 

            Receive :
            - text - Log text to save

            Returns :   None
        """

        event: c_event = self._events[ "log" ]
        event.attach( "text", text )

        event.invoke( )


    def set_event( self, event_type: str, callback: any, index: str ):
        """
            Set specific event callback.

            Receive :
            - event_type    - Event index
            - callback      - Function to callback
            - index         - Function string index

            Returns :   None
        """

        if not event_type in self._events:
            raise Exception( "Invalid event type" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, True )

    # endregion

    # region : File

    def get_file_name( self ) -> str:
        """
            Get active client's file.

            Receive :   None

            Returns :   Virtual File object
        """

        if self._selected_file is None:
            return "Unknown"

        return self._selected_file.name( )
    

    def set_file( self, file: c_virtual_file ) -> None:
        """
            Set selected file for client.

            Receive : 
            - file - File object

            Returns :   None
        """

        self._selected_file = file

    # endregion

    # region : Utilities

    def network( self ) -> c_network_protocol:
        """
            Access clients network connection.

            Receive :   None

            Returns :   Network protocol object
        """

        return self._network


    def __call__( self, index: str ) -> any:
        """
            Index clients information.

            Receive :
            - index - Value index

            Returns :   Any type or None
        """

        if index in self._information:
            return self._information[ index ]
        
        return None


    def __eq__( self, value ):
        """
            Is this object is this client.

            Receive :
            - value - Other client object

            Returns :   Result
        """

        current_address = self._network.get_address( True )
        other_address = value.network( ).get_address( True )

        if current_address[ 0 ] != other_address[ 0 ]:
            return False
        
        if current_address[ 1 ] != other_address[ 1 ]:
            return False
        
        return True

    # endregion


class c_server_business_logic:

    _network:       c_network_protocol          # Network protocol class
    _files:         c_files_manager_protocol    # Files protocol class

    _information:   dict                        # Server logic information
    _events:        dict                        # Server events
    _logs:          list

    _command_pool:  queue.Queue                 # Server commands queue

    _clients:       list

    # region :  Initialize server logic

    def __init__( self ):
        """
            Default constructor for server logic object.

            Receive :   None

            Returns :   Server Logic object
        """

        # Initialize protocols
        self.__initialize_protocols( )

        # Initialize events
        self.__initialize_events( )

        # Initialize default values
        self.__initialize_information( )


    def __initialize_protocols( self ):
        """
            Initialize protocols objects.

            Receive :   None

            Returns :   None
        """

        self._network   = c_network_protocol( )

        self._files     = c_files_manager_protocol( )

    
    def __initialize_events( self ):
        """
            Initialize server logic events.

            Receive :   None

            Returns :   None
        """

        # Create dict for events
        self._events = { }

        # Default server events. Start and Stop.
        self._events[ "server_start" ]      = c_event( )
        self._events[ "server_stop" ]       = c_event( )

        # For each new / old clients these are used to connect the gui and the bl
        self._events[ "client_connect" ]    = c_event( )
        self._events[ "client_disconnect" ] = c_event( )


    def __initialize_information( self ):
        """
            Initialize server logic default values.

            Receive :   None

            Returns :   None
        """

        self._information = { }

        self._information[ "success" ]      = False     # Is the setup process was successful
        self._information[ "running" ]      = False     # Is server running

        self._information[ "last_error" ]   = ""        # Last error occured

        # Create clients list.
        self._clients   = [ ]

        self._logs      = [ ]

        # Create commands queue
        self._command_pool = queue.Queue( )

    # endregion

    # region : Connection

    def setup( self, ip: str, port: int ) -> None:
        """
            Setup server connection.

            Receive : 
            - ip    - Ip Value for server
            - port  - Port to connect

            Returns :   None
        """

        # I dont use @safe_call since I need to add debug options later on

        try:
            
            # Just save the information
            self._information[ "ip" ]   = ip  # Does it really matter ?
            self._information[ "port" ] = port

            # Start connection using network protocol
            self._network.start_connection( CONNECTION_TYPE_SERVER, ip, port )

            # Set success setup flag to true
            self._information[ "success" ] = True
        
        except Exception as e:
            
            # In case of some error. Handle it
            self._information[ "last_error" ]   = f"Error occured on .setup() : {e}"
            self._information[ "success" ]      = False


    def start( self ) -> bool:
        """
            Start the server.

            Receive :   None

            Returns :   None
        """

        # Check if we done .setup( ... )
        if not self._information[ "success" ]:
            self._information[ "last_error" ]   = f"Cannot start the server execution if it hasn't been setupped."
            return False
        
        # Update is Running flag
        self._information[ "running" ] = True

        # Call event
        self.__event_server_start( )

        # Start to listen for new connections
        self._network.look_for_connections( )

        # Start the server process
        self.__attach_processes( )

        return True
    

    def terminate( self ):
        """
            Stop server execution.

            Receive :   None

            Returns :   None
        """

        # Update is Running flag
        self._information[ "running" ] = False

        # Call event
        self.__event_server_stop( )

        # Disconnect all the remaining clients
        for client in self._clients:
            client: c_client_handle = client

            client.disconnect( True )

        self._clients.clear( )

        # Close connection
        self._network.end_connection( )

    
    def generate_code( self ) -> str:
        """
            Generate project code.

            Receive :   None

            Returns :   String value
        """

        local_ip, local_port = self._network.get_address( )

        result = f"{ local_ip }:{ local_port }"
        result = base64.encode( result )

        return result

    # endregion

    # region : Processes

    def __attach_processes( self ):
        """
            Attach processes callbacks to threads.

            Receive :   None

            Returns :   None
        """

        self._information[ "connection_thread" ]    = threading.Thread( target=self.__process_connections )
        self._information[ "commands_thread" ]      = threading.Thread( target=self.__process_commands )

        
        self._information[ "connection_thread" ].start( )
        self._information[ "commands_thread" ].start( )


    def __process_connections( self ):
        """
            New connections process.

            Receive :   None

            Returns :   None
        """

        while self._information[ "running" ]:

            client_socket, client_addr = self._network.accept_connection( 0.5 )

            if client_socket and client_addr:

                self.__event_client_connect( client_socket, client_addr )

    
    def __process_commands( self ):
        """
            Process commands from clients.

            Receive :   None

            Returns :   None
        """

        while self._information[ "running" ]:

            # Check if the command pool is not empty
            if not self._command_pool.empty( ):

                # Pull command
                command: c_cmd = self._command_pool.get( block=False )

                self.__handle_command( command )
            else:

                # If our command queue is empty, just sleep for 0.1 seconds.
                # Othersize this thread will run million times per second.
                time.sleep( 0.1 )

    # endregion

    # region : Commands

    def add_command( self, command: c_cmd ):
        """
            Callback to add command for server commands pool.

            Receive :
            - command - New command object

            Returns :   None
        """

        self._command_pool.put( command )


    def __handle_command( self, command: c_cmd ):
        """
            Handle command request.

            Receive :
            - command - Command object from client

            Returns :   None
        """

        client:         c_client_handle     = command.client( )
        message:        str                 = command.message( )

        if message.startswith( self._files.get_header( ) ):
            return self.__handle_files_message( client, message )
        
        return

    # endregion

    # region : Files

    def initialize_path( self, path: str ):
        """
            Create and setup the project files path.

            Receive :
            - path - Path string for files

            Returns :   None
        """

        self._information[ "original_path" ] = path

        self.__setup_path( )

        self.__setup_files( )
        

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
        
        normal_path = self._information[ "normal_path" ]

        with os.scandir( path ) as entries:
            
            for entry in entries:
                
                if entry.is_file( ):
                    # Is File

                    # Create the copy file it self
                    file = self._files.create_new_file( entry.name )
                    file.copy_from( path, normal_path )

                    # Get file fixed name without type
                    try:
                        file_name, file_type = file.parse_name( )
                    
                        # Create file that will contain all the changes
                        changes = self._files.create_new_file( f"{ file_name }_changes.txt" )
                        changes.create_new( normal_path )

                    except Exception:
                        pass
                
                elif entry.is_dir( ) and entry.name != DEFAULT_FOLDER_NAME and not entry.name.startswith( "." ):
                    # Is Folder

                    self.__dump_path( f"{ path }\\{ entry.name }" )
    

    def __handle_files_message( self, client: c_client_handle, message: str ):
        """
            Handle message from client related to files protocol.

            Receive :
            - message - Message from client

            Returns :   None
        """

        client_network: c_network_protocol  = client.network( )

        cmd, arguments = self._files.parse_message( message )

        if cmd == FILES_COMMAND_REQ_FILES:
            files_list = self._files.share_files( )
            
            client_network.send( files_list )

            self.log( "Sending client Files." )

        if cmd == FILES_COMMAND_GET_FILE:

            file: c_virtual_file = self._files.search_file( arguments[ 0 ] )
            if file is None:
                return
            
            client.set_file( file )
            
            file_size = file.get_file_size( )
            config: list = client_network.get_raw_details( file_size )

            prepare_client_msg = self._files.format_message( FILES_COMMAND_SET_FILE, [ file.name( ), str( file_size ) ] )
            client_network.send( prepare_client_msg )

            for chunk_info in config:
                start = chunk_info[ 0 ]
                end = chunk_info[ 1 ]
                has_next = chunk_info[ 2 ]

                file_chunk = file.read_from_file( start, end )
                client_network.send_raw( file_chunk, has_next )

            self.log( "Sent file." )

            # After the file have been sent.
            # We need to nofity the client what lines are being used.
            #lines: list = file.get_locked_lines( )
            #for line in lines:
            #    lock_line_msg = self._files.format_message( FILES_COMMAND_LOCK_LINE, [ file.name( ), str( line ) ] )
            #    client_network.send( lock_line_msg )

        
        if cmd == FILES_COMMAND_PREPARE_UPDATE:

            file: c_virtual_file = self._files.search_file( arguments[ 0 ] )
            if file is None:
                return
            
            if client.get_file_name( ) != arguments[ 0 ]:
                return
            
            line = int( arguments[ 1 ] )
            is_locked = file.is_line_locked( line )

            response = is_locked and "1" or "0"
            
            if not is_locked:
                file.lock_line( line )
                self.__lock_line_for_all_clients( file, line, client )

            msg = self._files.format_message( FILES_COMMAND_PREPARE_RESPONSE, [ file.name( ), arguments[ 1 ], response ] )
            client_network.send( msg )

        return
    
    def __lock_line_for_all_clients( self, file: c_virtual_file, line: int, exception: c_client_handle ):
        """
            Notify all the clients in a specific file that this line is locked.

            Receive :
            - file - File handle
            - line - Line number
            - exception - The only client that dont notify

            Returns :   None
        """

        for client in self._clients:
            client: c_client_handle = client

            if not client == exception and client.get_file_name( ) == file.name( ):

                msg = self._files.format_message( FILES_COMMAND_PREPARE_UPDATE, [ file.name( ), str( line ) ] )
                client.network( ).send( msg )

    # endregion

    # region : Events

    def __event_server_start( self ):
        """
            Event callback for server start.

            Receive :   None

            Returns :   None
        """

        # Invoke the event
        event: c_event = self._events[ "server_start" ]
        event.invoke( )

    
    def __event_server_stop( self ):
        """
            Event callback for server stop.
            
            Receive :   None

            Returns :   None
        """

        # Invoke the event
        event: c_event = self._events[ "server_stop" ]
        event.invoke( )

    
    def __event_client_connect( self, socket_obj: socket, address: tuple ):
        """
            Event callback for new client connect.

            Receive :
            - socket_obj    - Client socket
            - address       - Client address ( ip, port )

            Returns :   None
        """

        # Create new client handle
        new_client = c_client_handle( )

        # Save it
        self._clients.append( new_client )

        # Set for each client events
        new_client.set_event( "disconnect",     self.__event_client_disconnect,             "Server_Disconnect_Callback" )
        new_client.set_event( "register_cmd",   self.__event_client_register_cmd,           "Server_RegisterCommand_Callback" )
        new_client.set_event( "log",            lambda event: self.log( event( "text" ) ),  "Server_RegisterCommand_Callback" )

        # Complete the connection
        new_client.connect( socket_obj, address )

        # Call the event
        event: c_event = self._events[ "client_connect" ]
        event.invoke( )
        
    
    def __event_client_disconnect( self, event ):
        """
            Event callback for client disconnect.

            Receive :
            - event - Event information

            Returns :   None
        """

        if event( "notify" ) == "0":
            client: c_client_handle = event( "client" )

            self._clients.remove( client )

        # Call the event
        event: c_event = self._events[ "client_disconnect" ]
        event.invoke( )


    def __event_client_register_cmd( self, event ):
        """
            Event callback for client that registers command on server.

            Receive :
            - event - Event information

            Returns :   None
        """

        command: c_cmd = event( "command" )
        self.add_command( command )
    
    # endregion

    # region : Access

    def find_client( self, username: str ) -> c_client_handle | None:
        """
            Search specific client based on username.

            Receive :
            - username - Client's username

            Returns :   Client handle or None on fail
        """

        for client in self._clients:
            client: c_client_handle = client

            if client( "username" ) == username:
                return client
            
        return None
    

    def files( self ) -> c_files_manager_protocol:
        """
            Access files or the server.

            Receive :   None

            Returns :   Files handler
        """

        return self._files


    def clients( self ) -> list[c_client_handle]:
        return self._clients
    
    # endregion

    # region : Logging

    def log( self, text: str ):
        self._logs.append( text )

    def get_logs( self ) -> list:
        return self._logs
    
    

    # endregion