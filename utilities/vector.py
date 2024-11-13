# Utils. Vector .py

import math as o_math
from utilities.math import math

class vector:
    # 3D Vector class

    x: float
    y: float
    z: float

    def __init__( self, x: int | float = 0, y: int | float = 0, z: int | float = 0 ):
        """
            Default constructor
        """

        self.x = x
        self.y = y
        self.z = z


    def raw( self, tpl: tuple ) -> any:
        """
            Create vector based on tuple data
        """

        self.x = tpl[ 0 ]
        self.y = tpl[ 1 ]

        # No need now. anyway we dont use 3D vectors
        # if len( tpl ) == 3:
        #    self.z = tpl[ 2 ]

        return self
    

    def copy( self ) -> any:
        """
            Create new vector object with same values
        """

        return vector( self.x, self.y, self.z )
    
    
    def is_in_bounds( self, start_vector: any, width: int | float, height: int | float ) -> bool:
        """
            Is this vector is in rect
        """

        if self.x < start_vector.x or self.x > (start_vector.x + width):
            return False
        
        if self.y < start_vector.y or self.y > (start_vector.y + height):
            return False
        
        return True
    

    def distance_2d( self, other_vector: any ) -> float:
        """
            Calculates distance from this vector to another.
        """

        return o_math.sqrt( ( other_vector.x - self.x )**2 + ( other_vector.y - self.y ) **2 )
    

    def linear( self, other: any, weight: float, hold: float = 0.01 ) -> any:
        """
            Linear function for current vector and other one
        """

        return vector( 
            math.linear( self.x, other.x, weight, hold ),
            math.linear( self.y, other.y, weight, hold ), 
            math.linear( self.z, other.z, weight, hold )
        )
    

    def __str__( self ):
        """
            ToString override
        """

        return f"vector({self.x}, {self.y}, {self.z})"
    

    def __add__( self, other ):
        """
            Add vector or number to current vector
        """

        # Get the new value type
        other_type = type( other )

        # If its vector
        if other_type == vector:
            return vector( self.x + other.x, self.y + other.y, self.z + other.z )

        # If its number
        if other_type == int or other_type == float:
            return vector( self.x + other, self.y + other, self.z + other )

        # Throw error
        raise Exception( "Invalid other data type. Must be vector / int / float" )
    

    def __sub__( self, other ):
        """
            Subtruct vector or number from current vector
        """

        # Get the new value type
        other_type = type( other )

        # If its vector
        if other_type == vector:
            return vector( self.x - other.x, self.y - other.y, self.z - other.z )

        # If its number
        if other_type == int or other_type == float:
            return vector( self.x - other, self.y - other, self.z - other )

        # Throw error
        raise Exception( "Invalid other data type. Must be vector / int / float" )
    

    def __mul__( self, other ):
        """
            Mults vector or number with current vector
        """

        # Get the new value type
        other_type = type( other )

        # If its vector
        if other_type == vector:
            return vector( self.x * other.x, self.y * other.y, self.z * other.z )

        # If its number
        if other_type == int or other_type == float:
            return vector( self.x * other, self.y * other, self.z * other )

        # Throw error
        raise Exception("Invalid other data type. Must be vector / int / float")


    def __truediv__( self, other ):
        """
            Devides vector or number with current vector
        """

        # Get the new value type
        other_type = type( other )

        # If its vector
        if other_type == vector:
            return vector( self.x / other.x, self.y / other.y, self.z / other.z )

        # If its number
        if other_type == int or other_type == float:
            return vector( self.x / other, self.y / other, self.z / other )

        # Throw error
        raise Exception( "Invalid other data type. Must be vector / int / float" )


    def __eq__( self, other ):
        """
            Checks if vector or tuple equle to current vector
        """

        # Get the new value type
        other_type = type( other )

        # If its vector
        if other_type == vector:
            return self.x == other.x and self.y == other.y and self.z == other.z

        # If its tuple
        if other_type == tuple:
            return self.x == other[ 0 ] and self.y == other[ 1 ] and self.z == other[ 2 ]

        # Thorw error
        raise Exception( "Invalid other data type. Must be vector / tuple" )