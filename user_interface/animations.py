"""
    project     : Digital Editor
    type        : User Interface
    file        : Animations

    description : Manages animations and value interpolation for the
                  Digital Editor's user interface elements, providing
                  smooth transitions and dynamic visual effects.
"""

import imgui

from utilities.math     import math


class c_animations:
    
    _cache:             dict    # Animations values stored by name
    _interpolation:     float   # Animations interpolation factor

    def __init__( self ):
        """
        Default constructor for the animations handler.

        Initializes the animation cache and the interpolation factor.

        Receives: None

        Returns: c_animations object
        """

        self._cache             = { }
        self._interpolation     = 0


    def clear( self ):
        """
        Clears all stored animation values from the cache.

        Receives: None

        Returns: None
        """

        self._cache.clear( )

    
    def delete_value( self, value_index: str ):
        """
        Deletes a specific animation value from the cache based on its index.

        Receive :
        - value_index (str): The string index of the animation value to delete.

        Returns : None
        """

        #if value_index in self._cache:
        del self._cache[ value_index ]


    def interpolation( self, new_value: float = None ) -> float:
        """
        Gets or sets the current animation interpolation factor.

        Receives:
        - new_value (float, optional): The new interpolation value to set.
                                        If None, the current value is returned. Defaults to None.

        Returns:
        - float: The current interpolation value.
        """

        if new_value is None:
            return self._interpolation
        
        self._interpolation = new_value
        return new_value


    def value( self, index: str, new_value: any = None ) -> any:
        """
        Gets or sets a specific animation value based on its index.

        Receives:
        - index (str): The unique index of the animation value to access.
        - new_value (any, optional): The new value to set for the animation.
                                      If None, the current value is returned. Defaults to None.

        Returns:
        - any: The current value associated with the given index. 
        """

        if new_value is None:
            return self._cache[ index ]
        
        self._cache[ index ] = new_value


    def prepare( self, index: str, value: any ) -> None:
        """
        Caches a starting value for a specific animation index.
        This is typically used to store the initial value before an animation begins.

        Receives:
        - index (str): The unique index of the animation value to prepare.
        - value (any): The starting value to cache for the given index.

        Returns: None
        """

        if not index in self._cache:
            self._cache[ index ] = value


    def update( self ) -> None:
        """
        Updates the interpolation factor based on the time elapsed since the last frame,
        typically using ImGui's delta time to ensure smooth, frame-rate independent animations.

        Receives: None

        Returns: None
        """

        self._interpolation = imgui.get_io( ).delta_time


    def perform( self, index: str, value: any, speed: int = 10, hold: float = 0.01 ) -> any:
        """
        Performs a linear interpolation animation for a specific value.

        Receives:
        - index (str): The unique index of the animation value to animate.
        - value (any): The target end value for the animation.
        - speed (int, optional): The speed of the interpolation. Higher values result in faster animation. Defaults to 10.
        - hold (float, optional): A small threshold to determine when the interpolation is considered complete. Defaults to 0.01.

        Returns:
        - any: The interpolated value between the cached starting value and the target value.
               The return type will match the type of the 'value' argument.
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
    
    
    def fast_perform( self, start_value: any, value: any, speed: int = 10, hold: float = 0.01 ) -> any:
        """
        Performs a linear interpolation animation between two provided values.
        This method does not rely on the animation cache.

        Receives:
        - start_value (any): The starting value for the animation.
        - value (any): The target end value for the animation.
        - speed (int, optional): The speed of the interpolation. Higher values result in faster animation. Defaults to 10.
        - hold (float, optional): A small threshold to determine when the interpolation is considered complete. Defaults to 0.01.

        Returns:
        - any: The interpolated value between the 'start_value' and the 'value'.
               The return type will match the type of the 'start_value' argument.
        """

        value_type = type( start_value )

        # Check if regular numnbers
        if value_type == float or value_type == int:
            return math.linear( start_value, value, speed * self._interpolation, hold )

        # If not, prob its vector or color
        else:
            return start_value.linear( value, speed * self._interpolation, hold )

