# Server - Business Logic .py

from protocols.network      import  *
from protocols.file_manager import  *
from utilities.event        import  c_event
from utilities.base64       import  base64
from utilities.wrappers     import  safe_call, standalone_execute

from utilities.paths        import *

import threading
import queue
import time


DEFAULT_FOLDER_NAME = "Digital Files"


class c_cmd:
    # Example:
    
    # cmd -> FILE_PROC::REG_COPY->c:\\files\\folder->test.py

    # Protocol  : File Protocol
    # Command   : Register copy file
    # Arguments :   1. path
    #               2. name
    
    _username:  str     # Clients username that requested the command
    _raw:       str     # Raw message

    _command:   str     # Command it self. 

    _arguments: list    # Arguments

    def __init__( self, username: str, raw: str ):

        self._username  = username
        self._raw = raw

        self._command   = ""
        self._arguments = [ ]

    def username( self ) -> str:
        return self._username
    
    def raw( self ) -> str:
        return self._raw
    
    def command( self ) -> str:
        return self._command
    
    def set_command( self, command: str ):
        self._command = command
    
    def arguments( self ) -> list:
        return self._arguments
    
    def add_argument( self, value: any ):
        self._arguments.append( value )


class c_client_handle:

    _network:       c_network_protocol      # Clients handle network connection

    _information:   dict                    # Clients information
    _events:        dict                    # Each client events

    # region : Initialize client handle

    def __init__( self ):
        """
            Default constructor
        """

        self.__initialize_events( )

        self.__initialize_information( )

    
    def __initialize_events( self ):
        """
            Initialize each client handle events
        """

        self._events = { }

        self._events[ "connect" ]       = c_event( )
        self._events[ "disconnect" ]    = c_event( )

        self._events[ "register_cmd" ]  = c_event( )
    
    def __initialize_information( self ):
        """
            Initialize client handle information handle
        """

        self._network       = None

        self._information   = { }

    # endregion

    # region : Connection

    def connect( self, socket_object: socket, address: tuple ):
        """
            Attach client connection details
        """

        # Attach connection
        self.__attach_connection( socket_object, address )

        # Register connection
        self.__register_connection( )

        # Call the event
        self.__event_connect( address )

        # Complete the connection by running the receive process attachment
        self.__attach_receive_process( )


    def disconnect( self, notify_the_client: bool = True ):
        """
            Close connection from the server to client
        """

        # Potentially warn the client of closing connection
        if notify_the_client:
            self._network.send( DISCONNECT_MSG )

        # Close connection
        self._network.end_connection( )

        # Call the event
        self.__event_disconnect( )


    def __attach_connection( self, socket_object: socket, address: tuple ):
        """
            Create new connection object and attach it in the network protocol
        """

        # Create connection
        new_connection = c_connection( )

        # Unlike the default .connect. Here we just give the information. 
        new_connection.attach( address[0], address[1], socket_object )

        # Create and attach the connection to the protocol
        self._network = c_network_protocol( new_connection )
    

    def __attach_receive_process( self ):
        """
            Receive process attachment
        """

        self._information[ "receive_thread" ] = threading.Thread( target=self.__receive_process )
        self._information[ "receive_thread" ].start( )


    def __register_connection( self ):
        """
            Register the client with username.
        """

        raw_msg: str = self._network.receive( )
        if not raw_msg.startswith( "username::" ):
            return
        
        parse_username = raw_msg.split( "::" )
        self._information[ "username" ] = parse_username[ 1 ]

    # endregion

    # region : Communication

    def __receive_process( self ):
        """
            Main receive function
        """

        while self._network.is_valid():
            res = self._network.receive( 0.5 )

            if res == DISCONNECT_MSG:
                self.disconnect( False )

            # Manuall checks

            # Create new command object
            new_cmd = c_cmd( self._information[ "username" ], res )

            # Pass it to the server command queue
            self.__event_register_cmd( new_cmd )

    # endregion

    # region : Events

    def __event_connect( self, address: tuple ):
        """
            Event client connect to server
        """

        event: c_event = self._events[ "connect" ]
        event.attach( "ip",     address[ 0 ] )
        event.attach( "port",   address[ 1 ] )

        event.invoke( )

    
    def __event_disconnect( self ):
        """
            Event client disconnect from the server
        """

        event: c_event = self._events[ "disconnect" ]
        event.attach( "client", self )

        event.invoke( )


    def __event_register_cmd( self, command: c_cmd ):
        """
            Event register command to server
        """

        event: c_event = self._events[ "register_cmd" ]
        event.attach( "command", command )

        event.invoke( )


    def set_event( self, event_type: str, callback: any, index: str ):
        """
            Set specific event callback
        """

        if not event_type in self._events:
            raise Exception( "Invalid event type" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, True )

    # endregion

    # region : Utils

    def __call__( self, index: str ) -> any:
        """
            Index clients information
        """

        if index in self._information:
            return self._information[ index ]
        
        return None

    # endregion


class c_server_business_logic:

    _network:       c_network_protocol          # Network procotol class
    _files:         c_file_manager_protocol     # Files manager protocol class

    _information:   dict                        # Server logic information
    _events:        dict                        # Server behind the scenes events

    _cmds_pool:     queue.Queue                 # Server command queue

    _clients:       list                        # Clients list

    # region : Initialize server logic

    def __init__( self ):
        """
            Default constructor
        """
        
        # Create the protocols
        self.__initialize_protocols( )

        # Create events
        self.__initialize_events( )

        # Create information
        self.__initialize_information( )
    

    def __initialize_protocols( self ):
        """
            Initialize protocols objects
        """

        self._network   = c_network_protocol( )
        self._files     = c_file_manager_protocol( )


    def __initialize_events( self ):
        """
            Initialize server logic events
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
            Complete server logic setup
        """

        self._information = { }

        self._information[ "success" ]      = False     # Is the setup process was successful
        self._information[ "running" ]      = False     # Is server running

        self._information[ "last_error" ]   = ""        # Last error occured

        # Create clients list.
        self._clients = [ ]

        # Create commands queue
        self._cmds_pool = queue.Queue( )
    
    # endregion

    # region : Connection

    def setup( self, ip: str, port: int ) -> None:
        """
            Setup server connection
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
            Start the server
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
        self.__attach_process( )

        return True

    
    def terminate( self ):
        """
            Stop server execution
        """

        # Update is Running flag
        self._information[ "running" ] = False

        # Call event
        self.__event_server_stop( )

        # Disconnect all the remaining clients
        for client in self._clients:
            client: c_client_handle = client

            #client.disconnect( True )
            pass

        # Close connection
        self._network.end_connection( )


    def generate_code( self ) -> str:
        """
            Generate project code
        """

        local_ip, local_port = self._network.get_address( )

        result = f"{ local_ip }:{ local_port }"
        result = base64.encode( result )

        return result


    def __attach_process( self ):
        """
            Create a threads for processes
        """

        self._information[ "connection_thread" ]    = threading.Thread( target=self.__process_connections )
        self._information[ "commands_thread" ]      = threading.Thread( target=self.__process_commands )

        
        self._information[ "connection_thread" ].start( )
        self._information[ "commands_thread" ].start( )


    def __process_connections( self ):
        """
            Server process. Must be called inside a seperate thread from the main thread
        """

        while self._information[ "running" ]:

            client_socket, client_address = self._network.accept_connection( 0.5 )

            if client_socket and client_address:
                
                self.__event_client_connect( client_socket, client_address )

    # endregion

    # region : Commands

    def add_command( self, command: c_cmd ):
        """
            Callback to add command for server commands pool
        """

        self._cmds_pool.put( command )

    
    def __process_commands( self ):
        """
            Server process. Handle commands pool
        """

        while self._information[ "running" ]:
            
            # Check if the command pool is not empty
            if not self._cmds_pool.empty( ):

                # Pull command
                command: c_cmd = self._cmds_pool.get( block=False )

                self.__handle_command( command )
            else:

                # If our command queue is empty, just sleep for 0.5 seconds.
                # Othersize this thread will run million times per second.
                time.sleep( 0.5 )


    def __handle_command( self, command: c_cmd ):
        """
            Handle command request
        """

        username    = command.username( )
        raw         = command.raw( )

        client: c_client_handle = self.find_client( username )

        if raw.startswith( self._files.get_header( ) ):
            # File Protocol command
            pass

    # endregion

    # region : Files

    def initialize_path( self, path: str ):
        """
            Create and setup the project files path.
        """

        self._information[ "original_path" ]    = path
        
        self.__setup_path( )
        self.__setup_files( )

    def __setup_path( self ):
        
        original_path   = self._information[ "original_path" ]
        normal_path     = f"{ original_path }\\{ DEFAULT_FOLDER_NAME }"

        self._information[ "normal_path" ] = normal_path
        
        if not os.path.exists( normal_path ):
            os.mkdir( normal_path )

    def __setup_files( self ):

        # Here need to make a copy of each file to the new path.
        # Besides, create for each file another file that stores all the changes
        original_path   = self._information[ "original_path" ]

        self.__dump_path( original_path )

    def __dump_path( self, path: str ):
        
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
    
    # endregion

    # region : Clients operations

    def find_client( self, username: str ) -> c_client_handle:
        """
            Tries to find client by username
        """

        for client in self._clients:
            client: c_client_handle = client

            if client( "username" ) == username:
                return client
            
        return None

    # endregion

    # region : Server Events

    def __event_server_start( self ):
        """
            Event callback for server start
        """

        # Invoke the event
        event: c_event = self._events[ "server_start" ]
        event.invoke( )


    def __event_server_stop( self ):
        """
            Event callback for server stop
        """

        # Invoke the event
        event: c_event = self._events[ "server_stop" ]
        event.invoke( )

    
    def __event_client_connect( self, socket_obj: socket, address: tuple ):
        """
            Event callback for new client connect
        """

        # Create new client handle
        new_client = c_client_handle( )

        # Save it
        self._clients.append( new_client )

        # Complete the connection
        new_client.connect( socket_obj, address )

        # Set for each client events
        new_client.set_event( "disconnect",     self.__event_client_disconnect,     "Server_Disconnect_Callback" )
        new_client.set_event( "register_cmd",   self.__event_client_register_cmd,   "Server_RegisterCommand_Callback" )

        # Call the event
        event: c_event = self._events[ "client_connect" ]
        event.invoke( )


    def __event_client_disconnect( self, event ):
        """
            Event callback for client disconnect
        """

        client: c_client_handle = event( "client" )

        self._clients.remove( client )

        # Call the event
        event: c_event = self._events[ "client_disconnect" ]
        event.invoke( )


    def __event_client_register_cmd( self, event ):
        """
            Event callback for client that registers command on server
        """

        command: c_cmd = event( "command" )
        self.add_command( command )

    # endregion