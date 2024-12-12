"""
    project     : Digital Editor

    type:       : Utility
    file        : Vector

    description : Vector class
"""

# Import extensitions
import math             as      original_math
from utilities.math     import  math


# 3D Vector class
# Can be also used as 2D since we dont have in the project 3D objects

class vector:

    x: float    # X-Axis value 
    y: float    # Y-Axis value
    z: float    # Z-Axis value

    # region : Initialize object

    def __init__( self, x: any = 0, y: any = 0, z: any = 0 ):
        """
            Vector class constructor

            Receives:   

            - x [optional] - start value for x-axis [ int | float ] 
            - y [optional] - start value for y-axis [ int | float ] 
            - z [optional] - start value for z-axis [ int | float ] 

            Returns:    Vector object
        """

        self.x = x
        self.y = y
        self.z = z


    def raw( self, tuple_object: tuple ) -> any:
        """
            Vector class second constructor.
            Converts tuple values into vector object

            Receives:   
            - tuple_object - 2 value tuple

            Returns:    Vector object
        """

        self.x = tuple_object[ 0 ]
        self.y = tuple_object[ 1 ]
        self.z = 0

        return self

    # endregion

    # region : Utilities

    def copy( self ) -> any:
        """
            Create another instance of vector object as the one called from

            Receives:   None

            Returns:    Vector object
        """

        return vector( self.x, self.y, self.z )

    # endregion

    # region : Calculations

    def is_in_bounds( self, start_vector: any, width: any, height: any ) -> bool:
        """
            Is this vector in between 2 other vectors representing a rect 
        
            Receives:   
            - start_vector  - start of the rect
            - width         - width of the rect  [ int | float ] 
            - height        - height of the rect [ int | float ] 

            Returns:    Bool value
        """

        assert( type( start_vector ) == vector, "start_vector must be a vector" )

        if self.x < start_vector.x or self.x > (start_vector.x + width):
            return False
        
        if self.y < start_vector.y or self.y > (start_vector.y + height):
            return False
        
        return True
    

    def distance( self, other_vector: any ) -> float:
        """
            Calculate the distance between current vector and other vector
        
            Receives:   
            - other_vector - other vector to calculate distance to

            Returns:    Float value
        """

        # assert( type( other_vector ) == vector, "other_vector must be a vector" )

        return original_math.sqrt( ( other_vector.x - self.x )**2 + ( other_vector.y - self.y ) **2 )
    

    def linear( self, other: any, weight: float, hold: float = 0.01 ) -> any:
        """
            Linear interpolation between 2 vectors
        
            Receives:   
            - other             - other vector
            - weight            - weight between the 2 vectors 
            - hold [optional]   - breaks limit interpolation.

            Returns:    New Vector object
        """

        # assert( type( other ) == vector, "other must be a vector" )

        return vector(
            math.linear( self.x, other.x, weight, hold ),
            math.linear( self.y, other.y, weight, hold ),
            math.linear( self.z, other.z, weight, hold )
        )

    # endregion

    # region : Operators overload
    
    def __str__( self ):
        """
            Override ToString function for vector object
        
            Receives:   None

            Returns:    string representing vector
        """

        return f"vector({ self.x }, { self.y }, { self.z })"
    

    def __add__( self, other ):
        """
            Override Add operator between vector to vector / number
        
            Receives:   
            - other: add value. can be vector or int or float

            Returns:    New vector object
        """

        other_type = type( other )

        if other_type == vector:
            return vector( self.x + other.x, self.y + other.y, self.z + other.z )

        if other_type == int or other_type == float:
            return vector( self.x + other, self.y + other, self.z + other )

        raise Exception( "Invalid other data type. Must be vector / int / float" )
    

    def __sub__( self, other ):
        """
            Override Subtruct operator between vector to vector / number
        
            Receives:   
            - other: sub value. can be vector or int or float

            Returns:    New vector object
        """

        other_type = type( other )

        if other_type == vector:
            return vector( self.x - other.x, self.y - other.y, self.z - other.z )

        if other_type == int or other_type == float:
            return vector( self.x - other, self.y - other, self.z - other )

        raise Exception( "Invalid other data type. Must be vector / int / float" )
    

    def __mul__( self, other ):
        """
            Override Multiply operator between vector to vector / number
        
            Receives:   
            - other: mult value. can be vector or int or float

            Returns:    New vector object
        """

        other_type = type( other )

        if other_type == vector:
            return vector( self.x * other.x, self.y * other.y, self.z * other.z )

        if other_type == int or other_type == float:
            return vector( self.x * other, self.y * other, self.z * other )

        raise Exception("Invalid other data type. Must be vector / int / float")


    def __truediv__( self, other ):
        """
            Override Devide operator between vector to vector / number
        
            Receives:   
            - other: div value. can be vector or int or float

            Returns:    New vector object
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
            Override Equal operator between vector to vector / tuple
        
            Receives:   
            - other: sub value. can be vector or tuple

            Returns:    Bool value
        """

        other_type = type( other )

        if other_type == vector:
            return self.x == other.x and self.y == other.y and self.z == other.z

        if other_type == tuple:
            return self.x == other[ 0 ] and self.y == other[ 1 ] and self.z == other[ 2 ]

        raise Exception( "Invalid other data type. Must be vector / tuple" )

    # endregion