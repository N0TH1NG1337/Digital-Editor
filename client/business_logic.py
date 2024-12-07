"""
    project     : Digital Editor

    type:       : Client
    file        : Business Logic

    description : Client Business Logic class
"""

from protocols.network          import *
from protocols.files_manager    import *
from utilities.event            import c_event
from utilities.base64           import base64

import threading

class c_client_business_logic:
    
    _network:       c_network_protocol
    _files:         c_files_manager_protocol

    _information:   dict
    _events:        dict

    # region :  Initialize server logic

    def __init__( self ):
        """
            Default constructor for client logic object.

            Receive :   None

            Returns :   Client Logic object
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

        self._network = c_network_protocol( )

        self._files = c_files_manager_protocol( )

    
    def __initialize_events( self ):
        """
            Initialize client logic events.

            Receive :   None

            Returns :   None
        """

        # Create dict for events
        self._events = { }

        # Default events
        self._events[ "connect" ]               = c_event( )
        self._events[ "pre_disconnect" ]        = c_event( )
        self._events[ "post_disconnect" ]       = c_event( )

        # Complex events.
        self._events[ "refresh_files" ]         = c_event( )    # Event for refresh files list
        self._events[ "register_file" ]         = c_event( )    # Event for file receive

        self._events[ "set_file" ]              = c_event( )
        self._events[ "update_file" ]           = c_event( )    
        self._events[ "accept_line" ]           = c_event( )    
        self._events[ "lock_line" ]             = c_event( )    


    def __initialize_information( self ):
        """
            Initialize client logic default values.

            Receive :   None

            Returns :   None
        """

        self._information   = { }

        self._information[ "is_connected" ] = False

        self._information[ "last_error" ]   = ""     # Last error occured

    # endregion

    # region : Connection

    def connect( self, project_code: str, username: str ):
        """
            Establish connection with server.

            Receive :
            - project_code  - Project code received from host
            - username      - Current username

            Receive :   None
        """

        # We receive code that need to be resolved into ip and port
        ip, port = self.__resolve_code( project_code )

        # NOTE ! We can use @safe_call here but i prefer to do in this way, 
        self._information[ "is_connected" ] = self.__try_to_connect( ip, port )

        # Attach username to this client 
        self.__attach_username( username )

        self.__attach_process( )

        self.__event_connect( ip, port)

        self.request_files( )


    def __try_to_connect( self, ip: str, port: int ) -> bool:
        """
            Try to establish connection with the server.

            Receive : 
            - ip    - Server IP
            - port  - Server Port

            Returns :   Result
        """

        # TODO ! Maybe add all the checks inside .start_connection and it to return result values
        
        try:
            self._network.start_connection( CONNECTION_TYPE_CLIENT, ip, port )
            
            return True
        except Exception as e:

            # TODO ! ADD DEBUG OPTIONS LATER
            return False


    def __attach_username( self, username: str ):
        """
            Attach a specific username with this client in the server.

            Receive :
            - username - Client username

            Returns :   None
        """

        if not self._information[ "is_connected" ]:
            return
        
        msg = f"username::{username}"
        self._network.send( msg )
    

    @safe_call( None )
    def __resolve_code( self, project_code: str ):
        """
            Convert the code into information. 
            
            Receive :
            - project_code - String value

            Returns : Tuple ( ip, port )
        """

        result = base64.decode( project_code )

        data = result.split( ":" )

        return data[0], int( data[1] )
    
    def disconnect( self ):
        """
            Disconnect from the server.

            Receive :   None

            Returns :   None
        """

        if not self._information[ "is_connected" ]:
            raise Exception( "Cannot disconnect if you are not connected" )
        
        # Before we disconnect, in somecases, we would like to do some more operations,
        # Like send some information to server so it will save it.
        # Therefore, we can use the pre_disconnect event to send all unsaved information
        # or do this kinds of operations
        self.__event_pre_disconnect( )

        # Notify the server we disconnect
        self._network.send( DISCONNECT_MSG )

        # In general words, we just notify the server we are going to disconnect from it,
        # and if the server tries to send more information, it will be just lost.
        # TODO ! Need later to add check if the client received a DISCONNECT_MSG from server while working, just end connection
        self.__end_connection( )

    def __end_connection( self ):
        """
            Forcely end connection with server, without notifing it.

            Receive :   None

            Returns :   None
        """

        self._network.end_connection( )

        # Invoke post_disconnect event
        # After we done with the connection, in some cases we will just need to clean up somethings.
        self.__event_post_disconnect( )
    
    # endregion

    # region : Process

    def __attach_process( self ):
        """
            Attach different processes into threads.

            Receive :   None

            Returns :   None
        """
 
        self._information[ "thread" ] = threading.Thread( target=self.__process_receive )
        self._information[ "thread" ].start( )

    def __process_receive( self ):
        """
            Process function to receive messages from server.

            Receive :   None

            Returns :   None
        """

        while self._network.is_valid( ):
            rec = self._network.receive( 0.5 )

            if rec is not None:
                self.__handle_receive( rec.decode( ) )

    # endregion

    # region : Messages handle

    def __handle_receive( self, receive: str ):
        """
            Handles messages.

            Receive :   
            - receive - Message from server

            Returns :   None
        """

        if receive == DISCONNECT_MSG:
            return self.__end_connection( )

        if receive.startswith( self._files.get_header( ) ):
            return self.__handle_file_protocol( receive )

        return

    # endregion

    # region : Files

    def request_files( self ):
        """
            Request files from the server.

            Receive :   None

            Returns :   None
        """

        message: str = self._files.format_message( FILES_COMMAND_REQ_FILES, ["unk"] )
        
        self._network.send( message )

    
    def request_file( self, name: str ):
        """
            Request specific file based on name.

            Receive :
            - name - File's name

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( name )
        if file is None:
            return
        
        #print( name )
        message: str = self._files.format_message( FILES_COMMAND_GET_FILE, [name] )
        self._network.send( message )


    def request_line( self, file_name: str, line: int ):
        """
            Request specific line.

            Receive : 
            - line - Line number

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if file is None:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_PREPARE_UPDATE, [ file_name, str( line ) ] )
        self._network.send( message )


    def __handle_file_protocol( self, receive: str ):
        """
            Handle message from Files Protocol.

            Receive :
            - receive - Message

            Returns :   None
        """

        command, arguments = self._files.parse_message( receive )

        if command == FILES_COMMAND_RES_FILES:

            self.__event_refresh_files( )

            for file in arguments:
                # Each file is a name.
                self._files.create_new_file( file )

                self.__event_register_file( file )

            return

        
        if command == FILES_COMMAND_SET_FILE:

            file_name = arguments[ 0 ]
            length = arguments[ 1 ]

            self.__event_set_file( )

            data = self._network.receive( )
            data = data.decode( )

            lines = data.splitlines( )

            file: c_virtual_file = self._files.search_file( file_name )
            if file is not None:
            
                for line in lines:
                    file.add_file_content( line )

                self.__event_update_file( file )

            return


        if command == FILES_COMMAND_PREPARE_RESPONSE:
            file_name = arguments[ 0 ]
            line_number = arguments[ 1 ]
            is_locked = arguments[ 2 ]

            self.__event_accept_line( file_name, int( line_number ), is_locked == "0" )
        

        if command == FILES_COMMAND_PREPARE_UPDATE:
            file_name = arguments[ 0 ]
            line_number = int( arguments[ 1 ] )

            file: c_virtual_file = self._files.search_file( file_name )
            if file is not None:
                file.lock_line( line_number )

                self.__event_lock_line( file.name( ), line_number )
                

        return

    # endregion

    # region : Events

    def __event_connect( self, ip: str, port: int ):
        """
            Event callback for user to connection for server.

            Receive : 
            - ip    - Server ip
            - port  - Server port

            Returns :   None 
        """

        event: c_event = self._events[ "connect" ]

        event.attach( "ip",         ip )
        event.attach( "port",       port )
        event.attach( "success",    self._information[ "is_connected" ] )

        event.invoke( )


    def __event_refresh_files( self ):
        """
            Event callback for start process of files refresh.

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "refresh_files" ]
        event.invoke( )

    
    def __event_register_file( self, file_name: str ):
        """
            Event callback for register new file.

            Receive :
            - file_name - New file name

            Returns :   None
        """

        event: c_event = self._events[ "register_file" ]
        event.attach( "file_name", file_name )

        event.invoke( )


    def __event_set_file( self ):
        """
            Event callback for setting new file content.

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "set_file" ]

        event.invoke( )

    
    def __event_update_file( self, file: c_virtual_file ):
        """
            Event callback for updating a file

            Receive :
            - line - Line Text

            Returns :   None
        """

        event: c_event = self._events[ "update_file" ]
        event.attach( "file", file.name( ) )

        for line in file.read_file_content( ):
            event.attach( "line_text", line )

            event.invoke( )


    def __event_accept_line( self, file_name: str, line: int, accept: bool ):
        """
            Event callback for accepting or not specific line.

            Receive : 
            - file_name - File's name
            - line      - Line number
            - accept    - Did server accept

            Returns :   None
        """

        event: c_event = self._events[ "accept_line" ]
        event.attach( "file",   file_name )
        event.attach( "line",   line )
        event.attach( "accept", accept )

        event.invoke( )


    def __event_lock_line( self, file_name: str, line: int ):
        """
            Event callback for locking a line.

            Receive :
            - file_name - File's name
            - line      - Line number

            Returns :   None
        """

        event: c_event = self._events[ "lock_line" ]
        event.attach( "file",   file_name )
        event.attach( "line",   line )

        event.invoke( )

    def __event_pre_disconnect( self ):
        """
            Event callback before disconnect process

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "pre_disconnect" ]
        event.invoke( )
    

    def __event_post_disconnect( self ):
        """
            Event callback post disconnect process

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "post_disconnect" ]
        event.invoke( )

    # endregion

    # region : Access

    def __call__( self, index ):

        if index == "network":
            return self._network
        
        if index in self._information:
            return self._information[ index ]
        
        return None
    

    def set_event( self, event_type: str, callback: any, index: str ):

        if not event_type in self._events:
            raise Exception( "Invalid event type to attach" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, True )

    # endregion