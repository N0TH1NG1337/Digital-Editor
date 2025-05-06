"""
    project     : Digital Editor

    type        : Utility
    file        : Event

    description : Implements an event system that allows associating multiple
                  callback functions with a specific event. When the event
                  is triggered, all registered callbacks are executed with
                  predefined arguments.
"""


class c_event:

    _information:   dict    # Event information
    _calls:         list    # Event callback functions

    # region : Initialize object

    def __init__( self ):
        """
        Initializes a new Event object.

        Receive: None

        Returns: Event: A new Event object with initialized handlers for
                       event information and callback functions.
        """

        # Setup event information handler
        self._information   = { }

        # Setup event callbacks handler
        self._calls         = [ ]

    # endregion

    # region : Access Calls and Information

    def attach( self, index: str, value: any ) -> None:
        """
        Attaches or updates information associated with the event.

        Receive:
        - index (str): The key or identifier for the information.
        - value (any): The data to be stored for the given index.

        Returns: None
        """

        self._information[ index ] = value


    def set( self, callback: any, index: str, allow_arguments: bool = True ) -> None:
        """
        Registers a new callback function to be executed when the event is triggered.

        Receive:
        - callback (callable): The function to be called when the event occurs.
        - index (str): An identifier for this specific callback.
        - allow_arguments (bool, optional): If True, the callback function will
                                             receive the event's attached information
                                             as arguments when executed. Defaults to True.

        Returns: None
        """

        self._calls.append( {
            "index":        index,
            "call":         callback,
            "is_args":      allow_arguments
        } )

    
    def unset( self, index: str ):
        """
        Removes a registered callback function from the event based on its index.

        Receive:
        - index (str): The identifier of the callback function to remove.

        Returns: None
        """

        for call in self._calls:
            if call[ "index" ] == index:
                self._calls.remove( call )
                return

    # endregion

    # region : Invoke and Execute

    def invoke( self ) -> None:
        """
        Triggers the event, executing all registered callback functions.

        Receive: None

        Returns: None
        """

        for item in self._calls:
            
            if item[ "is_args" ]:
                item[ "call" ]( self.__request )

            else:
                item[ "call" ]( )


    def __request( self, index: str ) -> any:
        """
        Retrieves information attached to the event.

        This method is intended to be called from within a callback function
        during the event's invocation to access specific data associated with
        the event.

        Receive:
        - index (str): The key or identifier of the information being requested.

        Returns:
        - any: The value associated with the given index, or None if the index
               is not found in the event's information.
        """

        if index in self._information:
            return self._information[ index ]
        
        return None

    # endregion
