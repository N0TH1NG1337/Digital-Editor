"""
    project     : Digital Editor

    type        : Utility
    file        : Color

    description : Represents a color with Red, Green, Blue, and Alpha components.
                  Provides functionalities for color manipulation, conversion
                  (to HSV), interpolation, copying, and integration with
                  ImGui's color representation.
"""

from utilities.math import math

import imgui

# Define function from imgui
color32u = imgui.get_color_u32_rgba


class color:

    r: float    # Red   value
    g: float    # Green value
    b: float    # Blue  value
    a: float    # Alpha value

    # region : Initialize object

    def __init__( self, r: any = 255, g: any = 255, b: any = 255, a: any = 255 ):
        """
        Initializes a new Color object with optional RGBA components.

        Receive:
        - r (int | float, optional): The initial value for the red component (0-255). Defaults to 255.
        - g (int | float, optional): The initial value for the green component (0-255). Defaults to 255.
        - b (int | float, optional): The initial value for the blue component (0-255). Defaults to 255.
        - a (int | float, optional): The initial value for the alpha component (0-255). Defaults to 255.

        Returns:
        - Color: A new Color object with the specified initial components.
        """

        self.r = r
        self.g = g 
        self.b = b
        self.a = a

    # endregion

    # region : Utilities

    def copy( self ) -> any:
        """
        Creates and returns a new Color object with the same RGBA values.

        Receive: None

        Returns: Color: A new Color object that is an exact copy of the calling instance.
        """

        return color( self.r, self.g, self.b, self.a ) 
    
    
    def unpack( self ) -> tuple:
        """
        Returns the RGBA components of the color as a tuple.

        Receive: None

        Returns: tuple: A tuple containing the red, green, blue, and alpha
                       components of the color in that order: (r, g, b, a).
        """

        return self.r, self.g, self.b, self.a


    def to_hsv( self ) -> tuple:
        """
        Converts the RGBA color values to HSV (Hue, Saturation, Value) with Alpha.

        Receive : None

        Returns : tuple: A tuple containing the HSV and Alpha values: (H, S, V, A),
                       where H, S, and V are in the range [0.0, 1.0], and A is
                       also in the range [0.0, 1.0].
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
        Creates a new Color object from HSV (Hue, Saturation, Value) and Alpha values.

        Receive:
        - h (float): Hue value in the range [0.0, 1.0].
        - s (float): Saturation value in the range [0.0, 1.0].
        - v (float): Value value in the range [0.0, 1.0].
        - a (float): Alpha value in the range [0.0, 1.0].

        Returns : Color: A new Color object with RGBA components derived from the
                         provided HSV and Alpha values.
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
        Creates a new Color object with the same RGB values but a different alpha value.

        Receive:
        - new_alpha (int | float): The new alpha value (0-255) for the new Color object.

        Returns:
        - Color: A new Color object with the updated alpha component.
        """

        return color( self.r, self.g, self.b, new_alpha )
    

    def linear( self, other: any, weight: float, hold: float = 0.01 ) -> any:
        """
        Performs linear interpolation between the current color and another color.

        Receive:
        - other (Color): The other Color object to interpolate towards.
        - weight (float): A value between 0.0 and 1.0 representing the interpolation
                          amount. 0.0 returns the current color, 1.0 returns the
                          'other' color, and values in between return an interpolated color.
        - hold (float, optional): A small positive value that can affect the
                                   interpolation if the weight is very close to
                                   0.0 or 1.0. Defaults to 0.01.

        Returns:
        - Color: A new Color object representing the interpolated color.
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
        Overrides the default string representation of the Color object.

        Receive: None

        Returns: str: A string representation of the Color object in the format
                     "color(r, g, b, a)".
        """

        return f"color({ self.r }, { self.g }, { self.b }, { self.a })"


    def __mul__( self, over_alpha: any ) -> any:
        """
        Overrides the multiplication operator (*) to adjust the alpha value of the color.

        Receive:
        - over_alpha (int | float): A scaling factor (typically between 0 and 1)
                                    to multiply the current alpha value by.

        Returns:
        - Color: A new Color object with the same RGB values and the adjusted alpha.
        """

        return color( self.r, self.g, self.b, self.a * over_alpha )
    

    def __eq__( self, other: any ) -> bool:
        """
        Overrides the equality operator (==) for Color objects.

        Receive:
        - other (Color): The other Color object to compare with.

        Returns:
        - bool: True if all RGBA components of both Color objects are equal;
                False otherwise.
        """

        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a


    def __call__( self ):
        """
        Returns an ImColor object (u32 color type) suitable for ImGui rendering.

        Receive: None

        Returns: imgui.ImColor: An ImColor object representing the color.
        """

        return color32u(
            self.r / 255,
            self.g / 255,
            self.b / 255,
            self.a / 255
        )

    # endregion