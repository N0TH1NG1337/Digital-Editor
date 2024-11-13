# Utils. Color .py

# Changes : 
# - file init

from utilities.math import math
import imgui

color32u = imgui.get_color_u32_rgba

class color:
    # RGBA Color class

    r: float    # Red       value
    g: float    # Green     value
    b: float    # Blue      value
    a: float    # Alpha     value


    def __init__( self, r: int | float = 255, g: int | float = 255, b: int | float = 255, a: int | float = 255 ):
        """
            Default constructor
        """

        self.r = r
        self.g = g 
        self.b = b
        self.a = a

    def alpha_override( self, new_alpha: int | float ) -> any:
        """
            Modulates current color alpha and returning a new object
        """

        return color( self.r, self.g, self.b, new_alpha )
    

    def unpack( self ) -> tuple:
        """
            Returns tuple with unpacked color data
        """

        return self.r, self.g, self.b, self.a
    

    def copy( self ) -> any:
        """
            Copy current color into new object
        """

        return color( self.r, self.g, self.b, self.a ) 
    

    def lieaner( self, other: any, weight: float, hold: float = 0.01 ) -> any:
        """
            Linear interpolation between 2 colors
        """

        return color(
            math.linear( self.r, other.r, weight, hold ),
            math.linear( self.g, other.g, weight, hold ),
            math.linear( self.b, other.b, weight, hold ),
            math.linear( self.a, other.a, weight, hold )
        )


    def __mul__( self, over_alpha: int | float ) -> any:
        """
            Overrides operator * to override alpha with value from 0 - 1
        """

        return color( self.r, self.g, self.b, self.a * over_alpha )
    

    def __call__( self ):
        """
            Function to return an u32 color type for ImGui Render
        """

        return color32u(
            self.r / 255,
            self.g / 255,
            self.b / 255,
            self.a / 255
        )
    
    
    def __str__( self ):
        """
            ToString override
        """

        return f"color({self.r}, {self.g}, {self.b}, {self.a})"
