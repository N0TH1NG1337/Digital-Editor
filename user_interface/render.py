"""
    project     : Digital Editor

    type:       : User Interface
    file        : Render functions

    description : Renderer class
"""

import imgui

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.image    import  c_image
from utilities.font     import  c_font

# Pure render functions
# Wraps Imgui DrawList options with some other custom ones,
# Each function must be called each frame since the render type is immediate mode

class c_renderer:

    _draw_list:         any     # ImDrawList*
    _position_queue:    list    # Last added position
    _measures:          dict    # Measures

    # region : Initialize object

    def __init__( self ):
        """
            Renderer class constructor

            Receives:   None

            Returns:    Renderer object
        """

        # Set default values and Setup things
        self._draw_list         = None
        self._position_queue    = [ ]
        self._measures          = { }

        # Add zero vector as default one
        self._position_queue.append( vector( ) )


    def update( self ) -> None:
        """
            Updates the DrawList pointer

            Receives:   None

            Returns:    None
        """

        self._draw_list = imgui.get_background_draw_list( )

        for index in self._measures:
            measure = self._measures[ index ]

            measure[ 0 ] = self.measure_text( measure[ 1 ], measure[ 2 ] )

    # endregion

    # region : Vectors and Interactions

    def push_position( self, new_vector: vector ) -> None:
        """
            Applies the new relative position for all subsequent elements.

            Receives:   
            - new_vector - New relative position on the screen

            Returns:    None
        """

        self._position_queue.append( new_vector )


    def push_clip_rect( self, position: vector, end_position: vector, intersect: bool = False ) -> None:
        """
            Applies the clip region to the given rectangle for all subsequent elements.

            Receives:   
            - position              - start of the clip
            - end_position          - end of the clip
            - intersect [optional]  - interact with others cliped rects

            Returns:    None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position
        end_position    = end_position + add_position

        self._draw_list.push_clip_rect( position.x, position.y, end_position.x, end_position.y, intersect )

    
    def pop_position( self ) -> None:
        """
            Discards an early set relative position.

            Receives:   None

            Returns:    None
        """

        length = len( self._position_queue )

        if length > 1:
            self._position_queue.pop( length - 1 )

    
    def pop_clip_rect( self ) -> None:
        """
            Discards an early set rectangle clipping region.

            Receives:   None

            Returns:    None
        """

        self._draw_list.pop_clip_rect( )

    # endregion

    # region : Measurements

    def measure_text( self, font: c_font, text: str ) -> vector:
        """
            Returns the measured size of the text.

            Receives:   
            - font - Font object
            - text - Text that will be measured

            Returns:    Vector object
        """

        imgui.push_font( font( ) )

        result      = vector( )
        result.y    = imgui.calc_text_size( text )[ 1 ]

        result.x = 0
        for c in text:
            result.x += imgui.calc_text_size( c )[ 0 ]

        imgui.pop_font( )

        return result
    
    
    def cache_measures( self, index: str, font: c_font, text: str ) -> vector:
        """
            Returns the cached value of measured size of the text.
            Can be used outside of render callback

            Receives:   
            - index - cache index
            - font  - Font object
            - text  - Text that will be measured

            Returns:    Vector object
        """

        if not index in self._measures:
            self._measures[ index ] = [ vector( ), font, text ]

        return self._measures[ index ][ 0 ]

    
    def delete_cache_measures( self, index: str ) -> None:
        """
            Deletes the cache of specific measure.

            Receives:   
            - index - cache index

            Returns:    None
        """

        del self._measures[ index ]

    # endregion

    # region : Show Textures

    def image( self, img: c_image, position: vector, clr: color, size: vector = None ) -> None:
        """
            Renders Image in a specific place with specific size.
            Recommended : use original size for the image while loading and while using

            Receives:   
            - img               - Image object
            - position          - Position
            - clr               - Color 
            - size [optional]   - Image size

            Returns:    None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position

        # If our size is None its mean we want to use the size
        # we declared when create the image
        if size is None:
            size = img.size( )

        self._draw_list.add_image(
            img( ), 
            ( position.x, position.y ), 
            ( position.x + size.x, position.y + size.y ), 
            col=clr( )
        )

    
    def text( self, font: c_font, position: vector, clr: color, text: str, flags: str = "" ) -> None:
        """
            Renders Image in a specific place with specific size.
            Recommended : use original size for the image while loading and while using

            Receives:   
            - font              - Font object
            - position          - Position
            - clr               - Color 
            - text              - Text to render
            - flags [optional]  - Text render flags

            Returns:    None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position

        # WARNING ! FULL TEXT WIDTH WILL BE SHOERTER THAN EACH CHAR RENDER
        # I AM LOSING EACH MINUTE A BRAINCELL

        imgui.push_font( font( ) )

        # Use to center text
        text_size = vector( )
        if 'c' in flags:
            text_size = self.measure_text( font, text )

        # Draw text
        offset = 0
        for c in text:
            self._draw_list.add_text( 
                position.x - text_size.x / 2 + offset, 
                position.y - text_size.y / 2, 
                clr( ), 
                c 
            )

            offset += imgui.calc_text_size( c )[ 0 ]

        imgui.pop_font( )

        # Return text size if centered to use if need
        return text_size


    def gradient_text( self, font: c_font, position: vector, clr1: color, clr2: color, text: str ) -> None:
        pass

    # endregion

    # region : Shapes

    def rect( self, position: vector, end_position: vector, clr: color, roundness: int = 0 ):
        """
            Renders filled rectangle

            Receives:   
            - position              - Start position
            - end_position          - End position
            - clr                   - Color 
            - roundness [optional]  - Roundness factor

            Returns:    None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position
        end_position    = end_position + add_position

        self._draw_list.add_rect_filled(
            position.x, position.y,          # unpack the position 2d cords      [ignore .z]
            end_position.x, end_position.y,  # unpack the end position 2d cords  [ignore .z]
            clr( ),                          # call color object to return ImColor u32 type
            rounding=roundness               # assignee rounding if need
        )

    
    def rect_outline( self, position: vector, end_position: vector, clr: color, thick: float = 1, roundness: int = 0 ):
        """
            Renders outline rectangle

            Receives:   
            - position              - Start position
            - end_position          - End position
            - clr                   - Color 
            - thick [optional]      - Thinkness of the lines
            - roundness [optional]  - Roundness factor

            Returns:    None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position
        end_position    = end_position + add_position

        self._draw_list.add_rect(
            position.x, position.y,             # unpack the position 2d cords      [ignore .z]
            end_position.x, end_position.y,     # unpack the end position 2d cords  [ignore .z]
            clr( ),                             # call color object to return ImColor u32 type
            rounding=roundness,                 # assignee rounding if need
            thickness=thick                     # set outline thickness
        )

    
    def gradiant( self, position: vector, end_position: vector, clr_up_left: color, clr_up_right: color, clr_bot_left: color, clr_bot_right: color, roundness: int = 0 ):
        """
            Renders gradiant rectangle

            Receives:   
            - position              - Start position
            - end_position          - End position
            - clr_up_left           - Top Left Color
            - clr_up_right          - Top Right Color
            - clr_bot_left          - Bottom Left Color
            - clr_bot_right         - Bottom Right Color
            - roundness [optional]  - Roundness factor

            Returns:    None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position
        end_position    = end_position + add_position

        if roundness == 0:
            self._draw_list.add_rect_filled_multicolor(
                position.x, position.y,                 # unpack the position 2d cords      [ignore .z]
                end_position.x, end_position.y,         # unpack the end position 2d cords  [ignore .z]
                clr_up_left( ),                         # Convert Top Left color
                clr_up_right( ),                        # Convert Top Right color
                clr_bot_right( ),                       # Convert Bottom Right color
                clr_bot_left( )                         # Convert Bottom Left color
            )   

        else:
            
            # FIXME ! (I am not sure if possible) when we move it, some pixels reset and doesnt register as corners
            # TODO ! Try to optimize the code, a lot of trash here

            pass


    def line( self, position: vector, end_position: vector, clr: color, thickness: float = 1 ):
        """
            Renders gradiant rectangle

            Receives:   
            - position              - Start position
            - end_position          - End position
            - clr                   - Color
            - thickness [optional]  - Thickness factor

            Returns:    None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position
        end_position    = end_position + add_position

        self._draw_list.add_line(
            position.x, position.y,             # Unpack start position
            end_position.x, end_position.y,     # Unpack end position
            clr( ),                             # Convert color
            thickness                           # Set line thickness
        )

    # endregion

    # region : Private functions

    def __get_last_position( self ) -> vector:
        """
            Receives the last position in queue

            Receives:   None

            Returns:    Vector object
        """

        return self._position_queue[ len( self._position_queue ) - 1 ]

    # endregion