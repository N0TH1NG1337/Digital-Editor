"""
    project     : Digital Editor

    type:       : Utility
    file        : Image

    description : Image class. Used for User Interface
"""

import  OpenGL.GL   as      gl
from    PIL         import  Image
import  numpy

from utilities.vector       import vector
from utilities.wrappers     import safe_call


INVALID = -1    # Invalid image id


# Image class
class c_image:

    _id:    any     # Image's Texture ID by OpenGL
    _size:  vector  # Image's size vector

    # region : Initialize object

    def __init__( self ):
        """
            Image class constructor

            Receives:   None

            Returns:    Image object
        """

        self._id    = INVALID
        self._size  = vector( )


    @safe_call( None )
    def load( self, path: str, size: vector ) -> any:
        """
            Load Image object from specific path

            Receives:   
            - path - image location path
            - size - font height

            Returns:    Image object
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

    # endregion

    # region : Access

    def __call__( self ):
        """
            Receive OpenGL Image ID

            Receives:   None

            Returns:    OpenGL Image ID
        """

        return self._id
    

    def size( self ) -> vector:
        """
            Receive Image size

            Receives:   None

            Returns:    Vector object
        """

        return self._size

    # endregion