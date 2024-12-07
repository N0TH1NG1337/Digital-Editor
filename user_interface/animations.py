"""
    project     : Digital Editor

    type:       : User Interface
    file        : Animations

    description : User Interface Animations handler
"""

import imgui

from utilities.color    import color
from utilities.vector   import vector
from utilities.math     import math

# Animations handler class
class c_animations:
    
    _cache:             dict    # Animations values stored by name
    _interpolation:     float   # Animations interpolation factor

    def __init__( self ):
        """
            Default constructor for animations handler

            Receives:   None

            Returns:    Animations object
        """

        self._cache             = { }
        self._interpolation     = 0


    def clear( self ):
        """
            Clears the animations cache

            Receives:   None

            Returns:    None
        """

        self._cache.clear( )

    
    def delete_value( self, value_index: str ):
        """
            Delete specific value from the animation cache.

            Receive :
            - value_index - String index of the value

            Returns :   None
        """

        #if value_index in self._cache:
        del self._cache[ value_index ]


    def interpolation( self, new_value: float = None ) -> float | None:
        """
            Returns / changes current interpolation factor

            Receives:   
            - new_value [optional] - new interpolation value

            Returns:    Interpolation value or None
        """

        if new_value is None:
            return self._interpolation
        
        self._interpolation = new_value


    def value( self, index: str, new_value: any = None ) -> any:
        """
            Returns / changes specific value

            Receives:   
            - index                 - value index
            - new_value [optional]  - new interpolation value

            Returns:    Value or None
        """

        if new_value is None:
            return self._cache[ index ]
        
        self._cache[ index ] = new_value


    def prepare( self, index: str, value: any ) -> None:
        """
            Cache specific index by start value

            Receives:   
            - index     - value index
            - value     - start value

            Returns:    None
        """

        if not index in self._cache:
            self._cache[ index ] = value


    def update( self ) -> None:
        """
            Update each frame our interpolation

            Receives:   None

            Returns:    None
        """

        self._interpolation = imgui.get_io( ).delta_time

    def preform( self, index: str, value: any, speed: int = 10, hold: float = 0.01 ) -> any:
        """
            Preform animation of specific index and return end value

            Receives:   
            - index             - value index
            - value             - new value
            - speed [optional]  - speed for interpolation
            - hold [optional]   - hold limit interpolation

            Returns:    Interpolated Value
        """

        self.prepare( index, value )

        value_type = type( value )

        # Check if regular numnbers
        if value_type == float or value_type == int:
            self._cache[ index ] = math.linear( self._cache[ index ], value, speed * self._interpolation, hold )

        # If not, prob its vector or color
        else:
            self._cache[ index ] = self._cache[ index ].linear( value, speed * self._interpolation, hold )

        return self._cache[ index ]
    

    def fast_preform( self, start_value: any, value: any, speed: int = 10, hold: float = 0.01 ) -> any:
        """
            Preform animation of specific index and return end value

            Receives:   
            - start_value       - start value
            - value             - new value
            - speed [optional]  - speed for interpolation
            - hold [optional]   - hold limit interpolation

            Returns:    Interpolated Value
        """


        value_type = type( start_value )

        # Check if regular numnbers
        if value_type == float or value_type == int:
            return math.linear( start_value, value, speed * self._interpolation, hold )

        # If not, prob its vector or color
        else:
            return start_value.linear( value, speed * self._interpolation, hold )

