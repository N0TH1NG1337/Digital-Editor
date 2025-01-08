

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

TIMEOUT_MESSAGE = 0.5

class c_user_business_logic:

    # region : Private Attributes

    _network:       c_network_protocol
    _files:         c_files_manager_protocol
    _registration:  c_registration_protocol

    _information:   dict
    _events:        dict
    _commands:      dict

    # endregion

    # region : Initialization user business logic

    def __init__( self ):
        """
            Default constructor for user business logic.

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

        self._network       = c_network_protocol()
        self._files         = c_files_manager_protocol()
        self._registration  = c_registration_protocol( )
    

    def __initialize_events( self ):
        """
            Initialize events for user business logic.

            Receive:    None

            Returns:    None
        """

        self._events = {

            "on_connect":           c_event( ),

            "on_pre_disconnect":    c_event( ),
            "on_post_disconnect":   c_event( ),

            # Complex events 
            "on_refresh_files":     c_event( ), # Called when user request to refresh files list
            "on_register_file":     c_event( ), # ?

            "on_set_file":          c_event( ), # Called whenever the host is going to send the user specific file content.
            "on_update_file":       c_event( ), # ?

            "on_accept_file":       c_event( ), # Called when the host response with the line lock request.
            "on_line_lock":         c_event( ), # Called when the host forces the user to lock a specific line. ( Used for other users locked lines )
            "on_line_unlock":       c_event( ), # Called when the host unlocks a specific line for this user.

            "on_line_update":       c_event( ), # Called when the host updates line / lines. 
            "on_line_delete":       c_event( ), # Called when the host deletes a specific line. ( Line removal is other process than update )
        }

    
    def __initialize_information( self ):
        """
            Initialize information for user business logic.

            Receive:    None

            Returns:    None
        """

        self._information = {
            "is_connected":     False,  # Is the user connected
            "last_error":       ""      # Last error message
        }

        self._commands = {
            FILES_COMMAND_RES_FILES: self.__command_received_files
        }

    # endregion

    # region : Connection

    def connect( self, project_code: str, username: str, password: str, register_type: str ) -> bool:
        """
            Establish connection with the host.

            Receive :
            - project_code  - Project code received from host
            - username      - Current username
            - password      - Current password

            Receive :   None
        """

        # We receive code that need to be resolved into ip and port
        ip, port = self.__resolve_code( project_code )

        self._information[ "is_connected" ] = self.__try_to_connect( ip, port )
        
        # TODO ! Establish safe communication . aka encryption and more

        self.__preform_registration( username, password, register_type )

        self.__attach_process( )

        self.__event_connect( ip, port )

        self.request_files( )

    
    def __resolve_code( self, project_code: str ):
        """
            Convert the code into information. 
            
            Receive :
            - project_code - String value

            Returns : Tuple ( ip, port )
        """

        result = base64.b64decode( project_code ).decode( )

        data = result.split( ":" )

        return data[0], int( data[1] )
    

    def __try_to_connect( self, ip: str, port: int ) -> bool:
        """
            Try to establish connection with the server.

            Receive : 
            - ip    - Server IP
            - port  - Server Port

            Returns :   Result
        """

        try:
            self._network.start_connection( CONNECTION_TYPE_CLIENT, ip, port )
            
            return True
        except Exception as e:

            # TODO ! ADD DEBUG OPTIONS LATER
            return False
        
    
    def __preform_registration( self, username: str, password: str, register_type: str ):
        """
            Preform a registration process for this user.

            Receive :
            - username  - Current user username
            - password  - Current user password

            Returns :   None
        """

        if not self._information[ "is_connected" ]:
            return
        
        register_command = {
            "Register":     REGISTRATION_COMMAND_REG,
            "Login":        REGISTRATION_COMMAND_LOG
        }

        message: str = self._registration.format_message( register_command[ register_type ], [ username, password ] )
        self._network.send( message )

    
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

        self._information[ "messages_thread" ] = self.__process_handle_messages( )

    
    @standalone_execute
    def __process_handle_messages( self ):
        """
            Process function to receive messages from server.

            Receive :   None

            Returns :   None
        """

        while self._network.is_valid( ):

            receive = self._network.receive( TIMEOUT_MESSAGE )

            if receive is not None:
                self.__handle_receive( receive.decode( ) )

    # endregion

    # region : Messages handle

    def __handle_receive( self, receive: str ):
        """
            Handles messages received from the host.

            Receive :
            - receive - Message content

            Returns :   None
        """

        print( receive )

        if receive == DISCONNECT_MSG:
            return self.__end_connection( )
        
        if receive.startswith( self._files.get_header( ) ):
            return self.__handle_files_message( receive )

    
    def __handle_files_message( self, message: str ):
        """
            Handle file's protocol message.

            Receive :   None
            - message - Message from server

            Returns :   None
        """

        command, arguments = self._files.parse_message( message )

        if command in self._commands:
            return self._commands[ command ]( arguments )

    # endregion

    # region : Commands

    def __command_received_files( self, arguments: list ):
        """
            Command method for receiving files.

            Receive :
            - arguments - List containing files details

            Returns : None
        """

        length = len( arguments )

        if length % 2 != 0:
            raise Exception("Invalid arguments list. Number of arguments must be even.")

        for i in range( 0, length, 2 ):

            name:           str = arguments[ i ] 
            access_level:   int = int( arguments[ i + 1 ] ) 

            print(f"Name: {name}, Access Level: {access_level}") 

            self._files.create_new_file( name, access_level, False )

    # endregion

    # region : Communication

    def request_files( self ):
        """
            Request files from the host.

            Receive :   None

            Returns :   None
        """

        if not self._network.is_valid( True ):
            return

        message: str = self._files.format_message( FILES_COMMAND_REQ_FILES, ["unk"] )

        self._network.send( message )

    # endregion

    # region : Events

    def __event_connect( self, ip: str, port: int ):
        """
            Event callback when the user connects to the host.

            Receive :
            - ip    - Host IP
            - port  - Port to connect

            Returns :   None
        """

        event: c_event = self._events[ "on_connect" ]

        event.attach( "ip",         ip )
        event.attach( "port",       port )
        event.attach( "success",    self._information[ "is_connected" ] )

        event.invoke( )

    
    def __event_pre_disconnect( self ):
        """
            Event callback before disconnect process.

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "on_pre_disconnect" ]

        event.invoke( )

    
    def __event_post_disconnect( self ):
        """
            Event callback after disconnect process.

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "on_post_disconnect" ]

        event.invoke( )


    def set_event( self, event_type: str, callback: any, index: str, allow_arguments: bool = True ):
        """
            Add function to be called on specific event.

            Receive :
            - event_type    - Event name
            - callback      - Function to execute
            - index         - Function index
        """

        if not event_type in self._events:
            raise Exception( "Invalid event type to attach" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, allow_arguments )

    # endregion

    # region : Access

    def __call__( self, index ):
        """
            Access sepcific information from the user bl.

            Receive : 
            - index - Information index

            Returns : Any ( based on value type )
        """

        if index in self._information:
            return self._information[ index ]
        
        return None

    # endregion
