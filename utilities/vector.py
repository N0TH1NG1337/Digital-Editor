"""
    project     : Digital Editor

    type        : Utility
    file        : Vector

    description : Represents a 3D vector, which can also be used for 2D
                  operations as the z-component defaults to zero. Provides
                  various vector operations such as addition, subtraction,
                  multiplication, division, distance calculation, linear
                  interpolation, and equality checks.
"""

import math             as      original_math
from utilities.math     import  math

class vector:

    x: float    # X-Axis value 
    y: float    # Y-Axis value
    z: float    # Z-Axis value

    # region : Initialize object

    def __init__( self, x: any = 0, y: any = 0, z: any = 0 ):
        """
        Initializes a new Vector object with optional x, y, and z components.

        Receive:
        - x (int | float, optional): The initial value for the x-axis component. Defaults to 0.
        - y (int | float, optional): The initial value for the y-axis component. Defaults to 0.
        - z (int | float, optional): The initial value for the z-axis component. Defaults to 0.

        Returns:
        - Vector: A new Vector object with the specified initial components.
        """

        self.x = x
        self.y = y
        self.z = z


    def raw( self, tuple_object: tuple ) -> any:
        """
        Alternative constructor for the Vector class, initializing from a tuple.

        Receive:
        - tuple_object (tuple): A tuple containing two values. The first value
                                will be assigned to the x-axis, and the second
                                to the y-axis.

        Returns:
        - Vector: The Vector object initialized with the values from the input tuple.
        """

        self.x = tuple_object[ 0 ]
        self.y = tuple_object[ 1 ]
        self.z = 0

        return self

    # endregion

    # region : Utilities

    def copy( self ) -> any:
        """
        Creates and returns a new Vector object with the same component values.

        This method generates a distinct copy of the current Vector object,
        ensuring that modifications to the copy do not affect the original.

        Receive:
        - None

        Returns:
        - Vector: A new Vector object that is an exact copy of the calling instance.
        """

        return vector( self.x, self.y, self.z )

    # endregion

    # region : Calculations

    def is_in_bounds( self, start_vector: any, width: any, height: any ) -> bool:
        """
        Checks if the vector's x and y components lie within a defined rectangular area.

        Receive:
        - start_vector (Vector): The Vector object representing the top-left
                                 corner of the rectangle.
        - width (int | float): The width of the rectangle.
        - height (int | float): The height of the rectangle.

        Returns:
        - bool: True if the vector is within or on the boundary of the rectangle;
                False otherwise.
        """

        if self.x < start_vector.x or self.x > (start_vector.x + width):
            return False
        
        if self.y < start_vector.y or self.y > (start_vector.y + height):
            return False
        
        return True
    

    def distance( self, other_vector: any ) -> float:
        """
        Calculates the Euclidean distance between the current vector and another vector.

        Receive:
        - other_vector (Vector): The other Vector object to which the distance
                                 is to be calculated.

        Returns:
        - float: The distance between the two vectors.
        """

        return original_math.sqrt( ( other_vector.x - self.x )**2 + ( other_vector.y - self.y ) **2 )
    

    def linear( self, other: any, weight: float, hold: float = 0.01 ) -> any:
        """
        Performs linear interpolation between the current vector and another vector.

        Receive:
        - other (Vector): The other Vector object to interpolate towards.
        - weight (float): A value between 0.0 and 1.0 representing the interpolation
                          amount. 0.0 returns the current vector, 1.0 returns the
                          'other' vector, and values in between return a vector
                          along the line segment.
        - hold (float, optional): A small positive value that can affect the
                                   interpolation if the weight is very close to
                                   0.0 or 1.0. Defaults to 0.01.

        Returns:
        - Vector: A new Vector object representing the interpolated point.
        """

        return vector(
            math.linear( self.x, other.x, weight, hold ),
            math.linear( self.y, other.y, weight, hold ),
            math.linear( self.z, other.z, weight, hold )
        )

    # endregion

    # region : Operators overload
    
    def __str__( self ):
        """
        Overrides the default string representation of the Vector object.

        Receive:
        - None

        Returns:
        - str: A string representation of the Vector object in the format
               "vector(x, y, z)".
        """

        return f"vector({ self.x }, { self.y }, { self.z })"
    

    def __add__( self, other ):
        """
        Overrides the addition operator (+) for Vector objects.

        Receive:
        - other (Vector | int | float): The value to add. It can be another
                                       Vector object or a numerical value.

        Returns:
        - Vector: A new Vector object representing the result of the addition.

        Raises:
        - Exception: If the 'other' operand is not a Vector, int, or float.
        """

        other_type = type( other )

        if other_type == vector:
            return vector( self.x + other.x, self.y + other.y, self.z + other.z )

        if other_type == int or other_type == float:
            return vector( self.x + other, self.y + other, self.z + other )

        raise Exception( "Invalid other data type. Must be vector / int / float" )
    

    def __sub__( self, other ):
        """
        Overrides the subtraction operator (-) for Vector objects.

        Receive:
        - other (Vector | int | float): The value to subtract. It can be another
                                       Vector object or a numerical value.

        Returns:
        - Vector: A new Vector object representing the result of the subtraction.

        Raises:
        - Exception: If the 'other' operand is not a Vector, int, or float.
        """

        other_type = type( other )

        if other_type == vector:
            return vector( self.x - other.x, self.y - other.y, self.z - other.z )

        if other_type == int or other_type == float:
            return vector( self.x - other, self.y - other, self.z - other )

        raise Exception( "Invalid other data type. Must be vector / int / float" )
    

    def __mul__( self, other ):
        """
        Overrides the multiplication operator (*) for Vector objects.

        Receive:
        - other (Vector | int | float): The value to multiply by. It can be
                                       another Vector object or a numerical value.

        Returns:
        - Vector: A new Vector object representing the result of the multiplication.

        Raises:
        - Exception: If the 'other' operand is not a Vector, int, or float.
        """

        other_type = type( other )

        if other_type == vector:
            return vector( self.x * other.x, self.y * other.y, self.z * other.z )

        if other_type == int or other_type == float:
            return vector( self.x * other, self.y * other, self.z * other )

        raise Exception("Invalid other data type. Must be vector / int / float")


    def __truediv__( self, other ):
        """
        Overrides the true division operator (/) for Vector objects.

        Receive:
        - other (Vector | int | float): The divisor. It can be another Vector
                                       object or a numerical value.

        Returns:
        - Vector: A new Vector object representing the result of the division.

        Raises:
        - Exception: If the 'other' operand is not a Vector, int, or float.
        """

        other_type = type( other )

        if other_type == vector:
            return vector( self.x / other.x, self.y / other.y, self.z / other.z )

        if other_type == int or other_type == float:
            return vector( self.x / other, self.y / other, self.z / other )

        # Throw error
        raise Exception( "Invalid other data type. Must be vector / int / float" )


    def __eq__( self, other ):
        """
        Overrides the equality operator (==) for Vector objects.

        Receive:
        - other (Vector | tuple): The value to compare with. It can be another
                                  Vector object or a tuple of length 3.

        Returns:
        - bool: True if the vector is equal to the 'other' operand; False otherwise.

        Raises:
        - Exception: If the 'other' operand is not a Vector or a tuple.
        """

        other_type = type( other )

        if other_type == vector:
            return self.x == other.x and self.y == other.y and self.z == other.z

        if other_type == tuple:
            return self.x == other[ 0 ] and self.y == other[ 1 ] and self.z == other[ 2 ]

        raise Exception( "Invalid other data type. Must be vector / tuple" )
    

    # endregion