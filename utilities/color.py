"""
    project     : Digital Editor

    type:       : Utility
    file        : Color

    description : Color class
"""

from utilities.math import math

import imgui

# Define function from imgui
color32u = imgui.get_color_u32_rgba

# RGBA Color class

class color:

    r: float    # Red   value
    g: float    # Green value
    b: float    # Blue  value
    a: float    # Alpha value

    # region : Initialize object

    def __init__( self, r: any = 255, g: any = 255, b: any = 255, a: any = 255 ):
        """
            Color class constructor

            Receives:   
            - r [optional] - start value for red    int | float
            - g [optional] - start value for green  int | float
            - b [optional] - start value for blue   int | float
            - a [optional] - start value for alpha  int | float

            Returns:    Color object
        """

        self.r = r
        self.g = g 
        self.b = b
        self.a = a

    # endregion

    # region : Utilities

    def copy( self ) -> any:
        """
            Create another instance of color object as the one called from

            Receives:   None

            Returns:    Color object
        """

        return color( self.r, self.g, self.b, self.a ) 
    
    
    def unpack( self ) -> tuple:
        """
            Unpacks and returns tuple value from color object

            Receives:   None

            Returns:    Tuple
        """

        return self.r, self.g, self.b, self.a


    def to_hsv( self ) -> tuple:
        """
            Convert RGBA Into HSV value,

            Receive :   None

            Returns :   Tuple ( H, S, V, A )
        """

        r, g, b = self.r / 255, self.g / 255, self.b / 255

        max_value, min_value = max( r, g, b ), min( r, g, b )
        h, s, v = 0.0, 0.0, 0.0

        v = max_value

        d = max_value - min_value
        if max_value == 0:
            s = 0
        else:
            s = d / max_value

        if max_value == min_value:
            h = 0  # achromatic
        else:
            if max_value == r:
                h = (g - b) / d
                if g < b:
                    h += 6
            elif max_value == g:
                h = (b - r) / d + 2
            elif max_value == b:
                h = (r - g) / d + 4
            h /= 6

        return h, s, v, self.a / 255
    

    def as_hsv( self, h: float, s: float, v: float, a: float ) -> any:
        """
            Convert HSV value to RGBA Color object.

            Receive:
            - h - Hue value
            - s - Saturation value
            - v - Value value
            - a - Alpha value

            Returns :   Color object
        """

        i = int(h * 6.0)
        f = h * 6.0 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)

        i %= 6

        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q

        self.r = int(r * 255)
        self.g = int(g * 255)
        self.b = int(b * 255)
        self.a = int(a * 255)

        return self


    # endregion

    # region : Operations

    def alpha_override( self, new_alpha: any ) -> any:
        """
            Create new instance of color object with new alpha

            Receives:   
            - new_alpha - new alpha value for new color [ int | float ]

            Returns:    Color object
        """

        return color( self.r, self.g, self.b, new_alpha )
    

    def lieaner( self, other: any, weight: float, hold: float = 0.01 ) -> any:
        """
            Linear interpolation between 2 colors
        
            Receives:   
            - other             - other color
            - weight            - weight between the 2 colors 
            - hold [optional]   - breaks limit interpolation.

            Returns:    New Color object
        """

        return color(
            math.linear( self.r, other.r, weight, hold ),
            math.linear( self.g, other.g, weight, hold ),
            math.linear( self.b, other.b, weight, hold ),
            math.linear( self.a, other.a, weight, hold )
        )

    # endregion

    # region : Operators overload

    def __str__( self ):
        """
            Override ToString function for color object
        
            Receives:   None

            Returns:    string representing color
        """

        return f"color({ self.r }, { self.g }, { self.b }, { self.a })"


    def __mul__( self, over_alpha: any ) -> any:
        """
            Override Multipy operator to adjust alpha value

            Receives:   
            - over_alpha - from 0 or 1 value adjust [ int | float ]

            Returns:    Color object
        """

        return color( self.r, self.g, self.b, self.a * over_alpha )
    

    def __call__( self ):
        """
            Function to return an u32 color type for ImGui Render

            Receives:   None

            Returns:    ImColor object
        """

        return color32u(
            self.r / 255,
            self.g / 255,
            self.b / 255,
            self.a / 255
        )

    # endregion