# Server - Business Logic .py

from protocols.network      import  *
from protocols.file_manager import  *
from utilities.event        import  c_event
from utilities.base64       import  base64

from utilities.paths        import *

import threading

class c_client_handle:
    
    _network:   c_network_protocol

    # Client information
    _information:   dict
    
    _events:        dict
    _thread:        threading.Thread

    def __init__( self ):

        self.__create_events( )
        self.__complete_setup( )

    def __create_events( self ):
        """
            Init events
        """

        self._events = { }

        self._events[ "connect" ]       = c_event( )
        self._events[ "disconnect" ]    = c_event( )

    def __complete_setup( self ):
        """
            Finish all the setups that remain
        """

        self._network   = None
        self._thread    = None

        self._information = { }

    # region : Connection

    def connect( self, socket_object: socket, address: tuple ):
        """
            Attach connection details
        """

        self.__attach_connection( socket_object, address )

        event: c_event = self._events[ "connect" ]
        event.attach( "address", address )

        event.invoke( )

        self._thread = threading.Thread( target=self.__receive )
        self._thread.start( )

    def disconnect( self, notify_the_client: bool = False ):
        """
            Close connection from the server to client
        """

        # Potentially warn the client of closing connection
        if notify_the_client:
            self._network.send( DISCONNECT_MSG )
            # Disconnect message is like warning 

        # Close connection
        self._network.end_connection( )

        # Call the disconnect event 
        event: c_event = self._events[ "disconnect" ]
        event.attach( "client", self )

        event.invoke( )


    def __attach_connection( self, socket_obj: socket, address: tuple ):
        """
            Create new connection object and attach it in the network protocol
        """

        # Create connection
        new_connection = c_connection( )

        # Unlike the default .connect. Here we just give the information. 
        new_connection.attach( address[0], address[1], socket_obj )

        # Create and attach the connection to the protocol
        self._network = c_network_protocol( new_connection )

        self.__register_connection( )

    def __register_connection( self ):
        """
            After client connects. It must send username :
        """

        first_information = self._network.receive( )
        if not first_information.startswith( "username::" ):
            return
        
        parse_username = first_information.split( "::" )
        self._information[ "username" ] = parse_username[ 1 ]

    # endregion 

    # region : Communication

    def __receive( self ):
        """
            Main receive function
        """

        # This function must be within a running thread
        
        while self._network.is_valid( ):
            
            # Get the message from client
            res = self._network.receive( 0.5 )

            # Deside what to do
            self.__resolve_received( res )

    def __resolve_received( self, recieve: str ):
        # This function will get the received message from client, and it will solve what it doest

        if recieve == DISCONNECT_MSG:
            return self.disconnect( False )

        pass

    # endregion

    # region : Server access

    def set_event( self, event_type: str, callback: any, index: str ):

        if not event_type in self._events:
            raise Exception( "Invalid event type" )

        event: c_event = self._events[ event_type ]
        event.set( callback, index, True )

    # endregion


class c_server_business_logic:
    
    _network:       c_network_protocol
    _files:         c_file_manager_protocol

    _info:      dict
    _events:    dict

    _clients:   list

    def __init__( self ):

        self.__init_protocols( )
        self.__init_information( )

        self.__init_events( )

    # region : Setup Server

    def __init_protocols( self ):
        """
            Create Protocols
        """

        self._network       = c_network_protocol( )
        self._files         = c_file_manager_protocol( )

    
    def __init_events( self ):
        """
            Create and setup server events
        """

        self._events = { }

        self._events[ "server_start" ]          = c_event( )
        self._events[ "server_stop" ]           = c_event( )

        self._events[ "client_connect" ]        = c_event( )
        self._events[ "client_disconnect" ]     = c_event( )

    
    def __init_information( self ):
        """
            Completes and creates default information for the server
        """

        self._info = { }
        
        self._info[ "success" ]     = False     # Is the setup process was successful
        self._info[ "last_error" ]  = ""        # Last error occured
        self._info[ "running" ]     = False     # Is server running

        self._clients = [ ]


    def setup( self, ip: str, port: int ):
        """
            Setup server connection
        """

        try:

            self._info[ "ip" ]      = ip
            self._info[ "port" ]    = port

            self._network.start_connection( CONNECTION_TYPE_SERVER, ip, port )

            self._info[ "success" ] = True

        except Exception as e:

            self._info[ "last_error" ] = f"Error occured on .setup() : {e}"

            self._info[ "success" ] = False

    def __attach_process( self ):
        
        self._info[ "process_thread" ] = threading.Thread( target=self.__process )
        self._info[ "process_thread" ].start( )
    
    def __process( self ):
        """
            Server process. Must be called inside a seperate thread from the main thread
        """

        while self._info[ "running" ]:
            client_socket, client_address = self._network.accept_connection( 1 )

            if client_socket and client_address:
                
                self.__event_client_connect( client_socket, client_address )
                
    
    def start( self ):
        """
            Start server execution
        """

        self._info[ "running" ] = True

        event: c_event = self._events[ "server_start" ]
        event.invoke( )

        self._network.look_for_connections( )

        self.__attach_process( )


    def terminate( self ):
        """
            Stop server execution
        """

        # Set running flag to false
        self._info[ "running" ] = False

        # Invoke server stop event
        event: c_event = self._events[ "server_stop" ]
        event.invoke( )

        # Disconnect all the remaining clients
        for client in self._clients:
            client: c_client_handle = client

            client.disconnect( )

        # Close connection
        self._network.end_connection( )


    def generate_project_code( self ):
        """
            Generate Projece code.
            This code can be shared with clients to connect
        """

        local_ip, local_port = self._network.get_address( )

        result = f"{ local_ip }:{ local_port }"

        # TODO ?
        result = base64.encode( result )

        return result

    # endregion

    # region : Files 

    def register_project_path( self, path ):
        """
            Save the project files path.
        """

        self._info[ "original_path" ] = path

        # Besides saving project path. Need also to set up copy files ?
        # Option 1 : Create copy files and modify them
        # Option 2 : Modify the original ones

        self.__register_files( )


    def __register_files( self ):
        """
            Register files by creating copy and saving in files manager
        """

        path = self._files.create_folder( DEFAULT_COPY_FOLDER, self._info[ "original_path" ] )
        if path is None:
            # TODO ! POP Some error
            return
        
        self._info[ "project_path" ] = path

        self.__dump_folder( path )
    

    def __dump_folder( self, path: str, folder_name: str = None ):

        with os.scandir( path ) as entries:

            for entry in entries:

                if entry.is_file( ):
                    # Is File

                    pass
                
                elif entry.is_dir( ):
                    # Is Folder

                    # If it is folder, we need to call again to dump it

                    pass

    # endregion

    # region : Events

    def __event_client_connect( self, socket_obj: socket, address: str ):
        """
            New Client connects to server event
        """

        # Create new client handle object
        new_client = c_client_handle( )

        # Save it
        self._clients.append( new_client )

        # Create connection
        new_client.connect( socket_obj, address )

        # Attach disconnect callback from the server
        new_client.set_event( "disconnect", self.__event_client_disconnect, "Server_Disconnect_Callback" )

        # Execute the event
        event: c_event = self._events[ "client_connect" ]

        event.attach( "socket",     socket_obj )
        event.attach( "address",    address )

        event.invoke( )


    def __event_client_disconnect( self, event ):
        """
            Client disconnects event
        """

        # This callback will be executed from client handle, on disconnect event.
        
        # Receive the client that want to disconnect
        client: c_client_handle = event( "client" )

        # Delete it
        self._clients.remove( client )

    # endregion

    # region : Utils

    # endregion