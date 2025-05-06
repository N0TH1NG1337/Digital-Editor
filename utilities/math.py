"""
    project     : Digital Editor

    type        : Utility
    file        : Math

    description : Provides a collection of static mathematical utility functions
                  such as linear interpolation and value clamping.
"""


class math:

    @staticmethod
    def linear( start_value: any, end_value: any, interpolation: float, hold: float = 0.01 ):
        """
        Performs linear interpolation between two numerical values.

        Receive:
        - start_value (int | float): The initial value.
        - end_value (int | float): The target value.
        - interpolation (float): A weight between 0.0 and 1.0.
        - hold (float, optional): A small positive threshold.

        Returns:
        - float: The interpolated value.
        """

        # Submit the end value and avoid over calculations on end
        if start_value == end_value:
            return end_value
        
        delta = end_value - start_value
        delta = delta * interpolation
        delta = delta + start_value

        # Used to avoid pixel glitch
        if abs( delta - end_value ) < hold:
            return end_value
        
        return delta
    

    @staticmethod
    def clamp( value: any, min_value: any, max_value: any ):
        """
        Clamps a given value within a specified range.

        Receive:
        - value (any): The value to be clamped.
        - min_value (any): The lower bound of the clamping range.
        - max_value (any): The upper bound of the clamping range.

        Returns:
        - any: The clamped value, which will be within the [min_value, max_value]
               range (inclusive).
        """

        if value > max_value:
            return max_value
        
        if value < min_value:
            return min_value
        
        return value
    

    @staticmethod
    def cast_to_number( value: any ) -> any:
        """
        Attempts to convert a given value to an integer.

        Receive:
        - value (any): The value to attempt conversion on.

        Returns:
        - int: The integer representation of the value if successful.
        - None: If the conversion to an integer fails.
        """

        try:
            return int( value )
        except:
            return None