# Utils. Image .py

# Changes : 
# - file init

import  OpenGL.GL   as      gl
from    PIL         import  Image
import  numpy

from utilities.vector import vector
from utilities.safe   import safe_call

INVALID_ID = -1


class c_image:
    # Image class

    _id:    any     # Image's Texture ID by OpenGL
    _size:  vector  # Image's size vector

    def __init__( self ):
        """
            Default constructor for class
        """

        self._id    = INVALID_ID
        self._size  = vector( )

    
    @safe_call( None )
    def load( self, path: str, size: vector ) -> any:
        """
            Loads Image based on path
        """

        # Attach wanted size
        self._size.x = size.x
        self._size.y = size.y

        # Open and get image data
        image           = Image.open( path )
        image_data      = numpy.array( image.convert( "RGBA" ), dtype=numpy.uint8 )

        # Generate OpenGL Texture Id
        self._id = gl.glGenTextures( 1 )

        # Bind Texture to id
        gl.glBindTexture( gl.GL_TEXTURE_2D, self._id )

        # Set parameters
        gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )
        gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )

        # Create and set texture
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            self._size.x, self._size.y,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            image_data
        )

        # Return on success
        return self
    

    def size( self ) -> vector:
        """
            Get Image size
        """

        return self._size.copy( )
    
    
    def __call__( self ):
        """
            Get Image ID
        """
        return self._id