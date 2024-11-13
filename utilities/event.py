# Utils. Event .py

# Changes : 
# - file init

# Event class
# Very usefull to handle multiple functions that should be
# executed all at once with the same arguments.

class c_event:

    _event_data:    dict
    _event_calls:   dict

    def __init__( self ):
        """
            Default constructor for class
        """

        # Setup event data handler
        self._event_data    = { }

        # Setup event functions handler
        self._event_calls   = { }

    
    def __get( self, index: str ) -> any:
        """
            Executable function to receive event data based on index
        """

        if index in self._event_data:
            return self._event_data[ index ]
        
        # Return None on invalid index
        return None
    

    def attach( self, index: str, value: any ) -> None:
        """
            Attaches (Creates/Updates) value based on index
        """

        self._event_data[ index ] = value


    def set( self, callback: any, index: str, allow_arguments: bool = True ) -> None:
        """
            Registers new callback function to be executed on event call
        """

        self._event_calls[ index ] = {
            "call":         callback,
            "is_args":      allow_arguments
        }   


    def unset( self, index: str ) -> None:
        """
            Removes callback based on index
        """

        del self._event_calls[ index ]


    def invoke( self ) -> None:
        """
            Invokes event. Calls all the functions
        """

        for index in self._event_calls:
            info: dict = self._event_calls[ index ]

            # Maybe add safecall ?
            if info[ "is_args" ]:
                info[ "call" ]( self.__get )

            else:
                info[ "call" ]( )