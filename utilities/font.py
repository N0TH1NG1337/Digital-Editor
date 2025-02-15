"""
    project     : Digital Editor

    type:       : Utility
    file        : Font

    description : Font class. Used for User Interface
"""

import imgui
from utilities.vector import vector


INVALID = -1    # Invalid font value

# Font class
class c_font:

    _object:    any     # Imgui Font object
    _size:      int     # Height

    # region : Initialize object

    def __init__( self ):
        """
            Font class constructor

            Receives:   None

            Returns:    Font object
        """

        self._object    = INVALID
        self._size      = INVALID


    def load( self, path: str, size: int ) -> any:
        """
            Load Font object from specific path

            Receives:   
            - path - font location path
            - size - font height

            Returns:    Font object
        """

        io              = imgui.get_io( )
        glyths_range    = self.get_range( )
        font_config     = self.get_config( )

        self._object    = io.fonts.add_font_from_file_ttf( path, size, font_config, glyths_range )

        self._size      = size

        return self
 

    def get_range( self ) -> any:
        """
            Specify glyphs range

            Receives:   None

            Returns:    Range object
        """

        # Supports :
        #   - English 32    - 126 (basic)
        #   - Russian 1024  - 1279
        #   - Hebrew  1424  - 1535
        # can support more just didn't have time to check everything
        return imgui.core.GlyphRanges( [ 32, 1535, 0 ] )


    def get_config( self ) -> any:
        """
            Create custom config for loading a font.

            Receive :   None

            Returns :   Font config object
        """

        # TODO ! Lower the hoversample since it causes too much lag + lower load up time
        
        return imgui.core.FontConfig( 
            glyph_min_advance_x=10,     # Add kind of spcasing to set symetric look
            #glyph_extra_spacing_x=1     # Idk to be honest
            #oversample_h=2,             # Oversample horizontally 4 times
            #oversample_v=2              # Oversample vertially 4 times
        )
    # endregion

    # region : Access font information

    def __call__( self ):
        """
            Receive ImGui Font object

            Receives:   None

            Returns:    ImGui Font object
        """

        return self._object
    

    def size( self ) -> int:
        """
            Receive Font height

            Receives:   None

            Returns:    number
        """

        return self._size

    # endregion