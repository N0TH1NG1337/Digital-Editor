# Utils. Font .py

# Changes : 
# - file init


import  imgui

from utilities.vector     import  vector

INVALID_ID = -1


class c_font:
    # Font object class

    _object:    any
    _size:      vector
    

    def __init__( self ):
        """
            Default constructor for class
        """

        self._object    = INVALID_ID
        self._size      = vector( )


    def load( self, path: str, size: int, ranges_index: str ) -> any:
        """
            Loads font based on path
        """

        io      = imgui.get_io( )
        ranges  = self.get_range( ranges_index )

        # Create and save font object
        self._object = io.fonts.add_font_from_file_ttf( path, size, None, ranges )

        # Get font sizes
        height, width, pixels = io.fonts.get_tex_data_as_rgba32()
        self._size.y = size

        return self


    def get_range( self, index: str ) -> any:

        io = imgui.get_io( )
        
        if index == "extand":
            # Supports :
            #   - English 32    - 126 (basic)
            #   - Russian 1024  - 1279
            #   - Hebrew  1424  - 1535
            # can support more just didn't have time to check everything
            return imgui.core.GlyphRanges( [ 32, 1535, 0 ] )
        
        return io.fonts.get_glyph_ranges_default( )
    

    def size( self ) -> vector:
        """
            Get Font sizes
        """

        return self._size.copy( )
    
    
    def __call__( self ):
        """
            Get Font object
        """
        return self._object
