# User Interface. Animation .py

import imgui

from utilities.color    import color
from utilities.vector   import vector
from utilities.math     import math

# Animation handle object.
# use to cache / preform animations,
# can use int / float / color / vector.

class c_animations:

    _cache:             dict    # Animations values stored by name
    _interpolation:     float   # Animations interpolation factor

    def __init__( self ):
        """
            Constructor for animation handler
        """

        self._cache             = { }
        self._interpolation     = 0

    def clear( self ):
        """
            Clears the animations cache
        """

        self._cache.clear( )

    def interpolation( self, new_value: float = None ) -> float | None:
        """
            Returns / changes current interpolation factor
        """

        if new_value is None:
            return self._interpolation
        
        self._interpolation = new_value

    def value( self, index: str, new_value: any = None ) -> any:
        """
            Returns / changes specific value
        """

        if new_value is None:
            return self._cache[ index ]
        
        self._cache[ index ] = new_value

    def prepare( self, index: str, value: any ) -> None:
        """
            Cache specific index by start value
        """

        if not index in self._cache:
            self._cache[ index ] = value

    def update( self ) -> None:
        """
            Update each frame our interpolation
        """

        self._interpolation = imgui.get_io( ).delta_time

    def preform( self, index: str, value: any, speed: int = 10, hold: float = 0.01 ) -> any:
        """
            Preform animation of specific index and return end value
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