"""
    project     : Digital Editor

    type:       : Utility
    file        : Event

    description : Event class.
                used to create option to callback more than 1 function 
                with specific arguments based on needs
"""

class c_event:

    _information:   dict    # Event information
    _calls:         dict    # Event callback functions

    # region : Initialize object

    def __init__( self ):
        """
            Event class constructor

            Receives:   None

            Returns:    Event object
        """

        # Setup event information handler
        self._information   = { }

        # Setup event callbacks handler
        self._calls         = { }

    # endregion

    # region : Access Calls and Information

    def attach( self, index: str, value: any ) -> None:
        """
            Attach new/update information for the event

            Receives:   
            - index     - information index
            - value     - specific value

            Returns:    None
        """

        self._information[ index ] = value


    def set( self, callback: any, index: str, allow_arguments: bool = True ) -> None:
        """
            Attach new callback for the event

            Receives:   
            - callback                      - executable function pointer
            - index                         - function index
            - allow_arguments [optional]    - allow the function to request information

            Returns:    None
        """

        self._calls[ index ] = {
            "call":     callback,
            "is_args":  allow_arguments
        }

    
    def unset( self, index: str ):
        """
            Detach callback from the event

            Receives:   
            - index                         - function index

            Returns:    None
        """

        del self._calls[ index ]

    # endregion

    # region : Invoke and Execute

    def invoke( self ) -> None:
        """
            Executes the event and calls all the functions

            Receives:   None

            Returns:    None
        """

        for index in self._calls:
            info:   dict = self._calls[ index ]

            if info[ "is_args" ]:
                info[ "call" ]( self.__request )

            else:
                info[ "call" ]( )


    def __request( self, index: str ) -> any:
        """
            Request information from the event.
            Called inside a callback on event invoke

            Receives:   
            - index - specific information index

            Returns:    Any value, or None on fail
        """

        if index in self._information:
            return self._information[ index ]
        
        return None

    # endregion
