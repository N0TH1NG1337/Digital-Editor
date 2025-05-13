"""
    project     : Digital Editor

    type:       : User Interface
    file        : Render functions

    description : Renderer class
"""

import imgui
import os

import OpenGL.GL    as gl
import numpy        as np

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.image    import  c_image
from utilities.font     import  c_font

import math as original_math

# Pure render functions
# Wraps Imgui DrawList options with some other custom ones,
# Each function must be called each frame since the render type is immediate mode

# TODO ! Rework the push_position. Since now it only get the last added. But we can do so it will sum all the positions.

class c_renderer:

    _draw_list:         any     # ImDrawList*
    _position_queue:    list    # Last added position
    _measures:          dict    # Measures

    # region : Initialize object

    def __init__( self ):
        """
        Renderer class constructor.

        Initializes the internal data structures used for drawing
        operations, such as the draw list, position queue, and measures dictionary.

        Receives: None

        Returns: Renderer object
        """

        # Set default values and Setup things
        self._draw_list         = None
        self._position_queue    = [ ]
        self._measures          = { }

        # Add zero vector as default one
        self._position_queue.append( vector( ) )


    def update( self ) -> None:
        """
        Updates the ImDrawList pointer to the current background draw list
        provided by ImGui. Also iterates through any pending text measurements
        and calculates their dimensions if they haven't been already.

        Receive: None

        Returns: None
        """

        self._draw_list = imgui.get_background_draw_list( )

        for index in self._measures:
            measure = self._measures[ index ]

            if measure[ 0 ].x == 0 and measure[ 0 ].y == 0:
                measure[ 0 ] = self.measure_text( measure[ 1 ], measure[ 2 ] )

    # endregion

    # region : Vectors and Interactions

    def push_position( self, new_vector: vector ) -> None:
        """
        Pushes a new relative position onto the position queue. Subsequent
        drawing calls will have their coordinates offset by the accumulated
        relative positions in the queue.

        Receive:
        - new_vector (vector): The new relative position vector to apply.

        Returns: None
        """

        self._position_queue.append( new_vector )


    def push_clip_rect( self, position: vector, end_position: vector, intersect: bool = False ) -> None:
        """
        Applies a clipping rectangle to the drawing context. Subsequent drawing
        operations will be limited to the area defined by this rectangle.

        Receive:
        - position (vector): The top-left corner of the clipping rectangle.
        - end_position (vector): The bottom-right corner of the clipping rectangle.
        - intersect (bool, optional): If True, the new clip rectangle will be
                                       intersected with the currently active clip
                                       rectangle, further restricting the drawing area.
                                       Defaults to False.

        Returns: None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position
        end_position    = end_position + add_position

        self._draw_list.push_clip_rect( position.x, position.y, end_position.x, end_position.y, intersect )

    
    def pop_position( self ) -> None:
        """
        Removes the last relative position that was pushed onto the position queue.
        This effectively undoes the positional offset applied by the corresponding
        `push_position` call.

        Receives: None

        Returns: None
        """

        length = len( self._position_queue )

        if length > 1:
            self._position_queue.pop( length - 1 )

    
    def pop_clip_rect( self ) -> None:
        """
        Removes the last clipping rectangle that was pushed onto the ImGui
        clip stack. This restores the clipping region to the one that was active
        before the corresponding `push_clip_rect` call.

        Receives: None

        Returns: None
        """

        self._draw_list.pop_clip_rect( )

    # endregion

    # region : Measurements

    def measure_text( self, font: c_font, text: str ) -> vector:
        """
        Calculates and returns the rendered size (width and height) of a given
        text string using the specified font.

        Receive:
        - font (c_font): The font object to use for measuring the text.
        - text (str): The text string to measure.

        Returns:
        - vector: A Vector object containing the width (x) and height (y)
                  of the rendered text.
        """

        imgui.push_font( font( ) )

        result      = vector( )

        temp        = imgui.calc_text_size( text )
        result.y    = temp[ 1 ]
        result.x    = temp[ 0 ]

        imgui.pop_font( )

        return result
    
    
    def cache_measures( self, index: str, font: c_font, text: str ) -> vector:
        """
        Returns the cached measured size of the text. If the measurement
        for the given index doesn't exist in the cache, it creates a new
        entry and the actual measurement will be performed during the
        next `update` call. This allows for text measurement outside of
        the immediate rendering callback.

        Receives:
        - index (str): The unique index to cache the text measurement under.
        - font (c_font): The font object to use for measuring the text.
        - text (str): The text string to be measured and cached.

        Returns:
        - vector: The cached Vector object representing the measured size
                  of the text. If the measurement hasn't been performed yet,
                  it will return a zero vector initially.
        """

        if not index in self._measures:
            self._measures[ index ] = [ vector( ), font, text ]

        return self._measures[ index ][ 0 ]

    
    def delete_cache_measures( self, index: str ) -> None:
        """
        Deletes the cached text measurement associated with the given index.

        Receives:
        - index (str): The index of the cached measurement to delete.

        Returns: None
        """

        if index in self._measures:
            del self._measures[index]

    
    def wrap_text( self, font: c_font, text: str, length: int ) -> str:
        """
        Wraps the given text to fit within a specified maximum width.

        Receive :
        - font (c_font): The font object to use for measuring text width.
        - text (str): The text string to wrap.
        - length (int): The maximum allowed width (in pixels) for a line of text.

        Returns :
        - str: The wrapped text, with lines separated by newline characters.
        """

        lines: list = [ ]
        words = text.split( )

        line = ""
        for word in words:
            temp_line = f"{ line } { word }"

            size: int = self.measure_text( font, temp_line ).x
            
            if size > length:
                lines.append( line.strip( ) )
                line = f"{ word }"
            else:
                line = temp_line

        lines.append( line.strip( ) )
        return "\n".join( lines )

    # endregion

    # region : Show Textures

    def image( self, img: c_image, position: vector, clr: color, size: vector = None, roundness: int = 0 ) -> None:
        """
        Renders an image at a specified position with a given color tint and optional size and roundness.
        It's generally recommended to use the original image size during loading and rendering for optimal quality.

        Receives:
        - img (c_image): The Image object to render.
        - position (vector): The top-left position where the image will be drawn.
        - clr (color): The color tint to apply to the image.
        - size (vector, optional): The width and height to render the image at.
                                   If None, the original image dimensions will be used. Defaults to None.
        - roundness (int, optional): The radius for rounding the corners of the image. Defaults to 0 (no rounding).

        Returns: None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position

        # If our size is None its mean we want to use the size
        # we declared when create the image
        if size is None:
            size = img.size( )

        if roundness == 0:
            self._draw_list.add_image(
                img( ), 
                ( position.x, position.y ), 
                ( position.x + size.x, position.y + size.y ), 
                col=clr( )
            )

        else:
            self._draw_list.add_image_rounded(
                img( ),
                ( position.x, position.y ),
                ( position.x + size.x, position.y + size.y ),
                col=clr( ),
                rounding=roundness
            )

    
    def text( self, font: c_font, position: vector, clr: color, text: str, flags: str = "" ) -> None:
        """
        Renders text at a specific position with a given color and optional flags.

        Receives:
        - font (c_font): The Font object to use for rendering the text.
        - position (vector): The top-left position where the text will be drawn.
        - clr (color): The color of the text.
        - text (str): The text string to render.
        - flags (str, optional): Rendering flags. 'c' for center alignment.
                                 Defaults to "".

        Returns:
        - vector: The size of the rendered text. If the 'c' flag is used,
                  it returns the size that was used for centering.
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position

        imgui.push_font( font( ) )

        # Use to center text
        text_size = vector( )
        if 'c' in flags:
            text_size = self.measure_text( font, text )

        self._draw_list.add_text( 
            position.x - text_size.x / 2,
            position.y - text_size.y / 2,
            clr( ), 
            text
        )

        imgui.pop_font( )

        # Return text size if centered to use if need
        return text_size

    # endregion

    # region : Shapes

    def rect( self, position: vector, end_position: vector, clr: color, roundness: int = 0 ):
        """
        Renders a filled rectangle.

        Receives:
        - position (vector): The top-left corner of the rectangle.
        - end_position (vector): The bottom-right corner of the rectangle.
        - clr (color): The fill color of the rectangle.
        - roundness (int, optional): The radius for rounding the corners of the rectangle. Defaults to 0 (no rounding).

        Returns: None
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
        Renders the outline of a rectangle.

        Receives:
        - position (vector): The top-left corner of the rectangle.
        - end_position (vector): The bottom-right corner of the rectangle.
        - clr (color): The color of the rectangle outline.
        - thick (float, optional): The thickness of the outline lines. Defaults to 1.
        - roundness (int, optional): The radius for rounding the corners of the rectangle. Defaults to 0 (no rounding).

        Returns: None
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
        Renders a rectangle with a color gradient across its corners.

        Receives:
        - position (vector): The top-left corner of the rectangle.
        - end_position (vector): The bottom-right corner of the rectangle.
        - clr_up_left (color): The color at the top-left corner.
        - clr_up_right (color): The color at the top-right corner.
        - clr_bot_left (color): The color at the bottom-left corner.
        - clr_bot_right (color): The color at the bottom-right corner.
        - roundness (int, optional): The radius for rounding the corners of the rectangle. Defaults to 0 (no rounding).

        Returns: None
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

            # Calculate points for the corners
            corenr_tl_x = position.x + roundness
            corenr_tl_y = position.y + roundness

            corenr_tr_x = end_position.x - roundness
            corenr_tr_y = position.y + roundness

            corner_bl_x = position.x + roundness
            corner_bl_y = end_position.y - roundness

            corner_br_x = end_position.x - roundness
            corner_br_y = end_position.y - roundness

            # Render rounded corners
            self._draw_list.path_clear( )
            self._draw_list.path_line_to( corenr_tl_x, corenr_tl_y )
            self._draw_list.path_arc_to_fast( corenr_tl_x, corenr_tl_y, roundness, 6, 9 )
            self._draw_list.path_fill_convex( clr_up_left( ) )

            self._draw_list.path_clear( )
            self._draw_list.path_line_to( corenr_tr_x, corenr_tr_y )
            self._draw_list.path_arc_to_fast( corenr_tr_x, corenr_tr_y, roundness, 9, 12 )
            self._draw_list.path_fill_convex( clr_up_right( ) )

            self._draw_list.path_clear( )
            self._draw_list.path_line_to( corner_bl_x, corner_bl_y )
            self._draw_list.path_arc_to_fast( corner_bl_x, corner_bl_y, roundness, 3, 6 )
            self._draw_list.path_fill_convex( clr_bot_left( ) )

            self._draw_list.path_clear( )
            self._draw_list.path_line_to( corner_br_x, corner_br_y )
            self._draw_list.path_arc_to_fast( corner_br_x, corner_br_y, roundness, 0, 3 )
            self._draw_list.path_fill_convex( clr_bot_right( ) )

            # Render background
            self._draw_list.add_rect_filled_multicolor(
                corenr_tl_x, corenr_tl_y,
                corner_br_x, corner_br_y,
                clr_up_left( ),
                clr_up_right( ),
                clr_bot_right( ),
                clr_bot_left( )
            )

            # Render outline
            self._draw_list.add_rect_filled_multicolor(
                position.x, corenr_tl_y,
                corenr_tl_x, corner_br_y,
                clr_up_left( ),
                clr_up_left( ),
                clr_bot_left( ),
                clr_bot_left( )
            )

            self._draw_list.add_rect_filled_multicolor(
                corenr_tl_x, corner_bl_y,
                corner_br_x, end_position.y,
                clr_bot_left( ),
                clr_bot_right( ),
                clr_bot_right( ),
                clr_bot_left( )
            )

            self._draw_list.add_rect_filled_multicolor(
                corenr_tl_x, position.y,
                corner_br_x, corenr_tl_y,
                clr_up_left( ),
                clr_up_right( ),
                clr_up_right( ),
                clr_up_left( )
            )

            self._draw_list.add_rect_filled_multicolor(
                corner_br_x, corenr_tl_y,
                end_position.x, corner_br_y,
                clr_up_right( ),
                clr_up_right( ),
                clr_bot_right( ),
                clr_bot_right( )
            )


    def line( self, position: vector, end_position: vector, clr: color, thickness: float = 1 ):
        """
        Renders a straight line between two specified points.

        Receives:
        - position (vector): The starting point of the line.
        - end_position (vector): The ending point of the line.
        - clr (color): The color of the line.
        - thickness (float, optional): The thickness of the line. Defaults to 1.

        Returns: None
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

    
    def circle( self, position: vector, clr: color, radius: float, segments: int = 0 ):
        """
        Renders a filled circle.

        Receives:
        - position (vector): The center position of the circle.
        - clr (color): The fill color of the circle.
        - radius (float): The radius of the circle.
        - segments (int, optional): The number of segments to use for drawing the circle.
                                     If 0, ImGui will choose a reasonable default.
                                     Increasing this value makes the circle smoother.
                                     Defaults to 0.

        Returns: None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position

        self._draw_list.add_circle_filled(
            position.x, position.y,     # Unpack position
            radius,                     # Set radius
            clr( ),                     # Convert color
            segments                    # Set segments [0 - auto segments calculation]
        )


    def circle_outline( self, position: vector, clr: color, radius: float, segments: int = 0, thickness: float = 1 ):
        """
        Renders the outline of a circle.

        Receives:
        - position (vector): The center position of the circle.
        - clr (color): The color of the circle outline.
        - radius (float): The radius of the circle.
        - segments (int, optional): The number of segments to use for drawing the circle outline.
                                     If 0, ImGui will choose a reasonable default.
                                     Increasing this value makes the circle smoother.
                                     Defaults to 0.
        - thickness (float, optional): The thickness of the circle outline. Defaults to 1.

        Returns: None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position

        self._draw_list.add_circle(
            position.x, position.y,     # Unpack position
            radius,                     # Set radius
            clr( ),                     # Convert color
            segments,                   # Set segments
            thickness                   # Set outline thickness
        )

    
    def shadow( self, position: vector, end_position: vector, clr: color, alpha: float, glow: float, roundness: int = 0 ):
        """
        Renders a shadow effect behind a rectangle.

        Receives:
        - position (vector): The top-left corner of the element casting the shadow.
        - end_position (vector): The bottom-right corner of the element casting the shadow.
        - clr (color): The base color of the shadow.
        - alpha (float): The overall alpha (opacity) of the shadow (0.0 to 1.0).
        - glow (float): The spread or blur radius of the shadow.
        - roundness (int, optional): The corner roundness of the shadow. Defaults to 0.

        Returns: None
        """

        add_position    = self.__get_last_position( )
        position        = position + add_position
        end_position    = end_position + add_position

        for radius in range( 0, glow + 1 ):
            radius = radius / 2

            fixed_color = color( clr.r, clr.g, clr.b, glow - radius * 2 ) * alpha

            self._draw_list.add_rect(
                position.x - radius, position.y - radius,               # unpack the position 2d cords      [ignore .z]
                end_position.x + radius, end_position.y + radius,       # unpack the end position 2d cords  [ignore .z]
                fixed_color( ),                                         # call color object to return ImColor u32 type
                rounding=( roundness + radius ),                        # assignee rounding if need
                thickness=1                                             # set outline thickness
            )
            
    
    def neon( self, position: vector, end_position: vector, clr: color, glow: float = 18, roundness: int = 0 ):
        """
        Renders a rectangle with a neon glow effect.

        Receives:
        - position (vector): The top-left corner of the rectangle.
        - end_position (vector): The bottom-right corner of the rectangle.
        - clr (color): The base color of the neon effect.
        - glow (float, optional): The spread or blur radius of the neon glow. Defaults to 18.
        - roundness (int, optional): The corner roundness of the rectangle and glow. Defaults to 0.

        Returns: None
        """
        
        self.shadow( position, end_position, clr, clr.a / 255, glow, roundness )
        self.rect( position, end_position, clr, roundness )

    # endregion

    # region : Private functions

    def __get_last_position( self ) -> vector:
        """
        Returns the last relative position that was pushed onto the position queue.
        If the queue is empty, it returns a zero vector.

        Receives: None

        Returns: vector: The last Vector object in the position queue, or a zero
                         vector if the queue is empty.
        """

        return self._position_queue[ len( self._position_queue ) - 1 ]

    # endregion