"""
    project     : Digital Editor

    type:       : Client
    file        : Business Logic

    description : Client Business Logic class
"""

from protocols.network  import *
from utilities.event    import c_event
from utilities.base64   import base64

import threading

class c_client_business_logic:
    
    _network:       c_network_protocol

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

    
    def __initialize_events( self ):
        """
            Initialize client logic events.

            Receive :   None

            Returns :   None
        """

        # Create dict for events
        self._events = { }

        self._events[ "connect" ]               = c_event( )
        self._events[ "pre_disconnect" ]        = c_event( )
        self._events[ "post_disconnect" ]       = c_event( )


    def __initialize_information( self ):
        """
            Initialize client logic default values.

            Receive :   None

            Returns :   None
        """

        self._information = { }

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
        event: c_event = self._events[ "pre_disconnect" ]
        event.invoke( )

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
        event: c_event = self._events[ "post_disconnect" ]
        event.invoke( )
    
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

        #if receive.startswith( self._files.get_header( ) ):
        #    return self.__handle_file_protocol( receive )

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