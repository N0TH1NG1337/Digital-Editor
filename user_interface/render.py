# User Interface. Render .py

import OpenGL.GL as gl
import imgui

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.image    import  c_image
from utilities.font     import  c_font


# Pure render functions
# Wraps Imgui DrawList options with some other custom ones,
# Each function must be called each frame since the render type is immediate mode

class c_renderer:

    _draw_list:         any # ImDrawList*
    _position_queue:    list

    def __init__( self ):
        """
            Default constructor for class
        """

        self._draw_list = None
        self._position_queue = [ ]

        self._position_queue.append( vector(  ) )


    def update( self ) -> None:
        """
            Updates each frame ImDrawList*
        """

        self._draw_list = imgui.get_background_draw_list( )

    def push_position( self, new_vector: vector ):

        self._position_queue.append( new_vector )

    def pop_position( self ):
        
        length = len( self._position_queue )

        if length > 1:
            self._position_queue.pop( length - 1 )

    def __get_last_position( self ) -> vector:
        return self._position_queue[ len( self._position_queue ) - 1 ]

    def push_clip_rect( self, position: vector, end_position: vector, intersect: bool = False ) -> None:
        """
            Push start vector and end vector to clip area,
            this will crop every render that is outside the rect area
        """

        add_position = self.__get_last_position( )
        position += add_position
        end_position += add_position

        self._draw_list.push_clip_rect( position.x, position.y, end_position.x, end_position.y, intersect )


    def pop_clip_rect( self ) -> None:
        """
            Pops clip rect and restores everything else
        """

        self._draw_list.pop_clip_rect( )


    def measure_text( self, font: c_font, text: str) -> vector:
        """
            Measures and returns a vector of text size based on custom font
        """

        # TODO ! ADD OPTION TO CACHE SIZES BASED ON TEXT

        # Push font
        imgui.push_font( font( ) )

        # Use calculate text size by Imgui (returns a tuple)
        result = vector( )
        result.y = imgui.calc_text_size( text )[ 1 ]

        result.x = 0
        for c in text:
            result.x += imgui.calc_text_size( c )[ 0 ]

        # Pop font
        imgui.pop_font( )

        # Return size as vector
        return result
    

    def image( self, img: c_image, position: vector, clr: color, size: vector = None ) -> None:
        """
            Renders Image in a specific place with specific size.
            recommended : use original size for the image while loading and while using
        """

        add_position = self.__get_last_position( )
        position += add_position


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

    
    def text( self, font: c_font, position: vector, clr: color, text: str, flags: str = "" ) -> vector:
        """
            Renders text with custom fond.
            can also use flags

            flags :
            - "c" will center the text
        """

        add_position = self.__get_last_position( )
        position += add_position

        # WARNING ! FULL TEXT WIDTH WILL BE SHOERTER THAN EACH CHAR RENDER
        # I AM LOSING EACH MINUTE A BRAINCELL

        # Push font
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

        # Pop font
        imgui.pop_font( )

        # Return text size if centered to use if need
        return text_size
    

    def gradient_text( self, font: c_font, position: vector, clr1: color, clr2: color, text: str ) -> None:
        """
            Render gradient text.

            clr1 - start color,
            clr2 - end color

            waring : DO NOT RENDER 1 CHAR WITH THAT
        """

        add_position = self.__get_last_position( )
        position += add_position

        # Besides fps killer function.
        # This looks dope

        # Extract values
        r1, g1, b1, a1 = clr1.unpack( )
        r2, g2, b2, a2 = clr2.unpack( )

        # Get text length
        string_len = len( text ) - 1

        # Create a percentage that will be added for each char
        percentage = color(
            ( r2 - r1 ) / string_len,
            ( g2 - g1 ) / string_len,
            ( b2 - b1 ) / string_len,
            ( a2 - a1 ) / string_len
        )

        # Text pad to find where last char located
        text_pad = 0

        imgui.push_font( font( ) )

        # Loop through each character
        for char in text:

            # Render each character
            self._draw_list.add_text( 
                position.x + text_pad, 
                position.y, 
                color( r1, g1, b1, a1 )( ), 
                char 
            )

            # Populate the pad for next cha
            text_pad = text_pad + imgui.calc_text_size( char )[ 0 ]

            # Change the color for the next char
            r1 = r1 + percentage.r
            g1 = g1 + percentage.g
            b1 = b1 + percentage.b
            a1 = a1 + percentage.a

        imgui.pop_font( )

    
    def rect( self, position: vector, end_position: vector, clr: color, roundness: int = 0 ) -> None:
        """
            Render fulled rect.
        """

        add_position = self.__get_last_position( )
        position += add_position
        end_position += add_position

        self._draw_list.add_rect_filled(
            position.x, position.y,          # unpack the position 2d cords      [ignore .z]
            end_position.x, end_position.y,  # unpack the end position 2d cords  [ignore .z]
            clr( ),                          # call color object to return ImColor u32 type
            rounding=roundness               # assignee rounding if need
        )

    
    def rect_outline( self, position: vector, end_position: vector, clr: color, thick: float = 1, roundness: int = 0 ):
        """
            Render outline rect.
        """

        add_position = self.__get_last_position( )
        position += add_position
        end_position += add_position

        self._draw_list.add_rect(
            position.x, position.y,             # unpack the position 2d cords      [ignore .z]
            end_position.x, end_position.y,     # unpack the end position 2d cords  [ignore .z]
            clr( ),                             # call color object to return ImColor u32 type
            rounding=roundness,                 # assignee rounding if need
            thickness=thick                     # set outline thickness
        )

    
    def gradiant( self, position: vector, end_position: vector, clr_up_left: color, clr_up_right: color, clr_bot_left: color, clr_bot_right: color, roundness: int = 0 ):
        """
            Render gradient rect.

            with rounding option (Prefer not to animate size / position since there will be glitched with corners)
        """

        add_position = self.__get_last_position( )
        position += add_position
        end_position += add_position

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

    
    def circle( self, position: vector, clr: color, radius: float, segments: int = 0 ):
        """
            Render circle.
        """

        add_position = self.__get_last_position( )
        position += add_position

        self._draw_list.add_circle_filled(
            position.x, position.y,     # Unpack position
            radius,                     # Set radius
            clr( ),                     # Convert color
            segments                    # Set segments [0 - auto segments calculation]
        )


    def circle_outline( self, position: vector, clr: color, radius: float, segments: int = 0, thickness: float = 1 ):
        """
            Render outline circle
        """

        add_position = self.__get_last_position( )
        position += add_position

        self._draw_list.add_circle(
            position.x, position.y,     # Unpack position
            radius,                     # Set radius
            clr( ),                     # Convert color
            segments,                   # Set segments
            thickness                   # Set outline thickness
        )


    def line( self, position: vector, end_position: vector, clr: color, thickness: float = 1 ):
        """
            Render line
        """

        add_position = self.__get_last_position( )
        position += add_position
        end_position += add_position

        self._draw_list.add_line(
            position.x, position.y,             # Unpack start position
            end_position.x, end_position.y,     # Unpack end position
            clr( ),                             # Convert color
            thickness                           # Set line thickness
        )

    
    def triangle( self, position1: vector, position2: vector, position3: vector, clr: color ):
        """
            Render triangle
        """

        add_position = self.__get_last_position( )
        position1 += add_position
        position2 += add_position
        position3 += add_position

        self._draw_list.add_triangle_filled(
            position1.x, position1.y,
            position2.x, position2.y,
            position3.x, position3.y,
            clr( )
        )