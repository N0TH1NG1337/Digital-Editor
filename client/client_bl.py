# Client - Business Logic .py

from protocols.network  import  *
from utilities.event    import  c_event
from utilities.base64   import  base64

class c_client_business_logic:
    
    _network:   c_network_protocol

    _info:      dict
    _events:    dict

    def __init__( self ):
        # Default constructor

        self._network = c_network_protocol( )

        self.__init_information( )
        self.__init_events( )

    # region : Initialize business logic

    def __init_events( self ):
        """
            Set up client bl events
        """

        self._events = { }

        self._events[ "connect" ]               = c_event( )
        self._events[ "pre_disconnect" ]        = c_event( )
        self._events[ "post_disconnect" ]       = c_event( )

    def __init_information( self ):
        """
            Set up default client bl information
        """ 

        self._info = { }

        self._info[ "is_connected" ] = False

    # endregion

    # region : Connection

    def connect( self, project_code: str, username: str ):
        """
            Client connection to server event
        """

        ip, port = self.__resolve_code( project_code )

        # NOTE ! We can use @safe_call here but i prefer to do in this way, 
        self._info[ "is_connected" ] = self.__try_to_connect( ip, port )

        self.__attach_username( username )
        self.__attach_receive( )

        event: c_event = self._events[ "connect" ]

        event.attach( "ip",         ip )
        event.attach( "port",       port )
        event.attach( "success",    self._info[ "is_connected" ] )

        event.invoke( )

    def __try_to_connect( self, ip: str, port: int ) -> bool:
        """
            Try to establish connection with the server
        """

        # TODO ! Maybe add all the checks inside .start_connection and it to return result values
        
        try:
            self._network.start_connection( CONNECTION_TYPE_CLIENT, ip, port )
            
            return True
        except Exception as e:

            # TODO ! ADD DEBUG OPTIONS LATER
            return False

    def __attach_username( self, username: str ):

        if not self._info[ "is_connected" ]:
            return
        
        msg = f"username::{username}"
        self._network.send( msg )
    
    @safe_call( None )
    def __resolve_code( self, project_code: str ):
        """
            Convert the code into information. 
            Ip, Port
        """

        result = base64.decode( project_code )

        data = result.split( ":" )

        return data[0], int( data[1] )


    def disconnect( self ):
        """
            Disconnect from the server
        """

        if not self._info[ "is_connected" ]:
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

        # Invoke post_disconnect event
        # After we done with the connection, in some cases we will just need to clean up somethings.
        event: c_event = self._events[ "post_disconnect" ]
        event.invoke( )

    def __end_connection( self ):
        """
            Forcly end connection with server, without notifing it
        """

        print( "End connection" )

        self._network.end_connection( )

    # endregion

    # region : Handle messages

    def __attach_receive( self ):
        """
            Attach receive function into standalone thread
        """

        self._info[ "thread" ] = threading.Thread( target=self.__receive )
        self._info[ "thread" ].start( )

    def __receive( self ):
        """
            Main function to receive messages from server
        """

        while self._network.is_valid( ):
            rec = self._network.receive( 0.5 )

            self.__handle_receive( rec )

    def __handle_receive( self, receive: str ):
        """
            Handles messages.
        """

        if receive == DISCONNECT_MSG:
            return self.__end_connection( )

        return


    # endregion

    # region : Access

    def __call__( self, index ):
        if index == "network":
            return self._network
        
        if index in self._info:
            return self._info[ index ]
        
        return None
    
    def set_event( self, event_type: str, callback: any, index: str ):

        if not event_type in self._events:
            raise Exception( "Invalid event type to attach" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, True )

    # endregion
