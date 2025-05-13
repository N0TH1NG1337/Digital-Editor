"""
    project     : Digital Editor

    type        : Utility
    file        : Image

    description : Represents an image resource, primarily used for rendering
                  elements within the User Interface. Handles loading,
                  storing, and providing access to image data for OpenGL.
"""

import  OpenGL.GL   as      gl
from    PIL         import  Image, ImageFilter
import  numpy
import  glfw

from utilities.vector       import vector
from utilities.wrappers     import safe_call
from utilities.debug        import c_debug


INVALID:            int = -1    # Invalid image id
IMAGE_FILTER_BLUR:  int = 1


class c_image:

    _id:    any     # Image's Texture ID by OpenGL
    _size:  vector  # Image's size vector

    # region : Initialize object

    def __init__( self ):
        """
        Initializes a new Image object.

        Receive:
        - None

        Returns:
        - Image: A new Image object with default initial values.
        """

        self._id    = INVALID
        self._size  = vector( )


    @safe_call( c_debug.log_error )
    def load( self, path: str, size: vector, flags: list = [ ] ) -> any:
        """
        Loads an image from a specified path and configures it for OpenGL.

        Receive:
        - path (str): The file path of the image to load.
        - size (vector): A Vector object representing the desired dimensions (width, height) of the image.
        - flags (list, optional): A list of image processing flags. Defaults to an empty list.

        Returns:
        - Image: The Image object with the loaded image data and OpenGL texture ID.
        """

        # Attach wanted size
        self._size.x = size.x
        self._size.y = size.y

        # Open and get image data
        image           = Image.open( path )

        if IMAGE_FILTER_BLUR in flags:
            image       = image.filter( ImageFilter.GaussianBlur( 40 ) )

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


    def load_glfw( self, path: str ) -> any:
        """
        Loads an image from specific path as GLFWImage object.

        Receive:
        - path (str): The file path of the image to load.
        - size (vector): A Vector object representing the desired dimensions (width, height) of the image.
        - flags (list, optional): A list of image processing flags. Defaults to an empty list.

        Returns:
        - GLFWImage: Image object pointer
        """

        # Attach wanted size
        self._size.x = 0
        self._size.y = 0

        # Open and get image data
        image           = Image.open( path ).convert( "RGBA" )
        self._id = image

        return self

    # endregion

    # region : Access

    def __call__( self ):
        """
        Returns the OpenGL/GLFWImage texture ID of the loaded image.

        Receive:
        - None

        Returns:
        - any: The OpenGL/GLFWImage texture associated with this Image object.
        """

        return self._id
    

    def size( self ) -> vector:
        """
        Returns the dimensions (width and height) of the image.

        Receive:
        - None

        Returns:
        - vector: A Vector object representing the width (x) and height (y) of the image.
        """

        return self._size

    # endregion