"""
    project     : Digital Editor

    type:       : Utility
    file        : Math

    description : Math static functions
"""


class math:

    @staticmethod
    def linear( start_value: any, end_value: any, interpolation: float, hold: float = 0.01 ):
        """
            Linear interpolation function.

            Receives:   
            - start_value     - the old value
            - end_value       - goal value
            - interpolation   - weight from 0 to 1
            - hold [optional] - breaks limit interpolation.

            Returns:    Interpolated value from the end to the start
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
            Clamp value between limits

            Receives:   
            - value       - actual value that needs to clamp
            - min_value   - minimun possible value
            - max_value   - maximum possible value

            Returns:    Clamped value
        """

        if value > max_value:
            return max_value
        
        if value < min_value:
            return min_value
        
        return value
    

    @staticmethod
    def cast_to_number( value: any ) -> any:
        """
            Try to cast value to a number.

            Receive :   
            - value - Any type of value

            Returns :   Number or None
        """

        try:
            return int( value )
        except:
            return None