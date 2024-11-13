# Utils. Math .py

# Changes :
# - file init

def _linear(t, b, c, d):
    return c * t / d + b

def _in_quad(t, b, c, d):
    t /= d
    return c * t * t + b

def _out_quad(t, b, c, d):
    t /= d
    return -c * t * (t - 2) + b


class math:

    @staticmethod
    def linear( start_value: any, end_value: any, interpolation: float, hold: float = 0.01 ):
        """
            Linear interpolation function
        """

        if start_value == end_value:
            return end_value
        
        delta = end_value - start_value
        delta = delta * interpolation
        delta = delta + start_value

        # Use to avoid pixel glitch.
        if abs(delta - end_value) < hold:
            return end_value
        
        return delta
    
    #@staticmethod
    #def new_linear( start_value: any, end_value: any, interpolation: float, speed: float ):

    #    value = _out_quad( interpolation * 2, start_value, end_value - start_value, speed )
    
    #    return value
    
    
    @staticmethod
    def clamp( value: any, min_value: any, max_value: any ):
        """
            Simple math clamp function
        """

        if value > max_value:
            return max_value
        
        if value < min_value:
            return min_value
        
        return value
