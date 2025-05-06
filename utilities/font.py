"""
    project     : Digital Editor

    type        : Utility
    file        : Font

    description : Manages font resources for the User Interface, handling
                  loading, configuration, and providing access to ImGui font objects
                  and font size information.
"""

import imgui
from utilities.vector import vector


INVALID = -1    # Invalid font value


class c_font:

    _object:    any     # Imgui Font object
    _size:      int     # Height

    # region : Initialize object

    def __init__( self ):
        """
        Initializes a new Font object.

        Receive:
        - None

        Returns:
        - Font: A new Font object with default initial values.
        """

        self._object    = INVALID
        self._size      = INVALID


    def load( self, path: str, size: int ) -> any:
        """
        Loads a font from a specified file path with a given size.

        Receive:
        - path (str): The file path to the TrueType font (.ttf) file.
        - size (int): The desired height of the font in pixels.

        Returns:
        - Font: The Font object with the loaded font data.
        """

        io              = imgui.get_io( )
        glyths_range    = self.get_range( )
        font_config     = self.get_config( )

        self._object    = io.fonts.add_font_from_file_ttf( path, size, font_config, glyths_range )

        self._size      = size

        return self
 

    def get_range( self ) -> any:
        """
        Defines the set of glyphs to be included in the font atlas.

        Receive:
        - None

        Returns:
        - imgui.core.GlyphRanges: An object specifying the Unicode ranges
                                    for the desired glyphs. Currently includes
                                    basic English, Russian, and Hebrew characters.
        """
        # Supports :
        #   - English 32    - 126 (basic)
        #   - Russian 1024  - 1279
        #   - Hebrew  1424  - 1535
        # can support more just didn't have time to check everything
        return imgui.core.GlyphRanges( [ 32, 1535, 0 ] )


    def get_config( self ) -> any:
        """
        Creates a custom configuration object for loading the font.

        Receive : None

        Returns : imgui.core.FontConfig: A font configuration object with
                                       specific settings for glyph rendering.
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
        Returns the ImGui font object.

        Receive: None

        Returns: imgui.Font: The ImGui font object loaded by this Font instance.
        """

        return self._object
    

    def size( self ) -> int:
        """
        Returns the height of the loaded font.

        Receive: None

        Returns: int: The font size in pixels.
        """

        return self._size

    # endregion