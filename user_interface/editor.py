# User Interface. Widget -> Editor .py

import glfw
import os

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.math     import  math
from utilities.safe     import  safe_call
from utilities.image    import  c_image
from utilities.font     import  c_font
from utilities.event    import  c_event

from user_interface.render      import c_renderer
from user_interface.animation   import c_animations
from user_interface.scene       import c_scene


EXCEPTIONS = {
    "{": "{}",
    "(": "()",
    "[": "[]",
    "\"": "\"\""
}


SELECTION_MODE_NORMAL = 1
SELECTION_MODE_WORD = 2
SELECTION_MODE_LINE = 3

INVALID_POSITION = vector( -1, -1 )


class c_editor:
    
    
    _parent:            c_scene
    _index:             int

    _position:          vector
    _size:              vector

    _font:              c_font

    _render:            c_renderer
    _animations:        c_animations
    _config:            dict

    # region : Private data

    _lines:             list    # Each line will be a list for glyphs
    _line_height:       int     # Default line height data

    _height_offset:     float   # Scroll down offset
    _mouse_position:    vector  # Mouse relative position | No coords

    _is_hovered:        bool

    # Will remove for now the interact with the text
    # Need to crate a system to catch / request lines and edit them only

    _selected:          vector  # Allowed to edit
    # x -> start line index
    # y -> last line index
    # Used to determine the lines that are allowed to modify

    _cursor:            vector  # Pointer char position

    # endregiod

    # region : Init Editor

    def __init__( self, parent: c_scene, position: vector, size: vector, font: c_font ):
        self._parent    = parent
        self._position  = position.copy( )
        self._size      = size.copy( )
        self._font      = font

        self.__init_attach( )
        self.__init_config( )
        self.__init_animations( )

        self.__init( )

    def __init_attach( self ):
        # Complete the attach of the editor

        self._render = self._parent.render( )

        self._index = self._parent.attach_element( self )

        this_id = f"Editor::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,           this_id )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,          this_id )
        self._parent.set_event( "char_input",       self.__event_char_input,            this_id )
        self._parent.set_event( "keyboard_input",   self.__event_keyboard_input,        this_id )

    def __init_config( self ):

        first_parent = self._parent
        while str( type( first_parent ) ).find( "c_application" ) == -1:
            first_parent = first_parent.parent( )
        
        self._config = first_parent.config( "Editor" )

    def __init_animations( self ):
        self._animations = c_animations( )

        self._animations.prepare( "Scroll", 0 )


    def __init( self ):
        # Complete the init thing

        self._height_offset     = 0
        self._mouse_position    = vector( )

        self._selected          = INVALID_POSITION.copy( ) # Avoid giving the object it self at any cost
        self._cursor            = vector( )

        self._is_hovered        = False

        self._line_height       = self._font.size( ).y + 4

        self._lines             = [ ]

        self._lines.append( "" )


    # endregion

    # region : Draw

    def draw( self, fade: float ):
        self._animations.update( )

        # Call all the calculations before the render
        self.__preform_scroll( )

        # Render
        self.__draw_background( fade )

        # Render all the staff of the editor here
        self.__draw_text( fade )
        self.__draw_index( fade )

        # End clip rect of this editor
        self._render.pop_clip_rect( )

    def __draw_background( self, fade: float ):

        rounding    = self._config[ "rounding" ]
        color_back  = self._config[ "color_back" ]

        start_position  = self._position
        end_position    = self._position + self._size

        self._render.push_clip_rect( start_position, end_position )
        self._render.rect( start_position - vector( rounding, 0 ), end_position + vector( 0, rounding ), color_back * fade, rounding )

    def __draw_text( self, fade: float ):
        # Render Text of the editor.

        color_text      = self._config[ "color_text" ]
        pad_for_number  = self._config[ "pad_for_number" ]
        pad             = self._config[ "pad" ]
        drop            = 0
        index           = 0
        height_offset   = self._animations.value( "Scroll" )
        start_position  = self._position + vector( pad_for_number + pad, pad + height_offset )

        for line in self._lines:
            index += 1

            line_number = str( index )

            show_line   = start_position + vector( 0, drop + 2 )
            show_index  = start_position + vector( - self._render.measure_text( self._font, line_number ).x - pad, drop + 2 )

            self._render.text( self._font, show_index, color_text * fade, line_number )
            self._render.text( self._font, show_line, color_text * fade, line )

            drop = drop + self._line_height

    def __draw_index( self, fade: float ):
        
        if not self._is_typing:
            return

        color_text      = self._config[ "color_text" ]

        position = self.char_vec_to_relative( self._cursor )

        self._render.rect( position, position + vector( 2, self._line_height ), color_text * fade )

    # endregion

    # region : Render Calculations

    def __preform_scroll( self ):

        speed = self._config[ "speed" ]

        self._animations.preform( "Scroll", self._height_offset, speed, 1 )

    # endregion

    # region : Events and Callbacks

    def __event_mouse_position( self, event ):
        
        x = event( "x" )
        y = event( "y" )

        self._mouse_position.x = x
        self._mouse_position.y = y

        # if self._mouse_position.is_in_bounds( self._position, self._size.x, self._size.y ):

        #    self._is_hovered = self._parent.try_to_get_handle( self._index )

        # else:

        #    if self._parent.is_this_active( self._index ):
        #        self._parent.release_handle( self._index )

        #    self._is_hovered = False


    def __event_mouse_input( self, event ):
        
        button = event( "button" )
        action = event( "action" )

        #if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS: 
            
        #    if not self._is_typing and self._is_hovered:
        #        self._is_typing = True

        #    if self._is_typing and not self._is_hovered:
        #        self._is_typing = False


    def __event_mouse_scroll( self, event ):
        # Mouse scroll input event

        y_offset = event( "y_offset" )

        self.clamp_scroll( y_offset * 26 )


    def __event_char_input( self, event ):
        
        pass
        #if not self._is_typing:
        #    return
        
        #received_char = event( "char" )
        #char = chr( received_char )

        #self.insert_at( self._cursor, char )
        #self._cursor += self.calculate_move( char )


    def __event_keyboard_input( self, event ):
        if not self._is_typing:
            return
        
        key         = event( "key" )
        action      = event( "action" )

        if action == glfw.PRESS or action == glfw.REPEAT:
            self.__repeat_handle( key )
        

    def __repeat_handle( self, key ):
        # Executable input handle for PRESS and REPEAT calls

        if key == glfw.KEY_BACKSPACE:
            # removed = self.remove( self._cursor - vector( 1, 0 ), self._cursor )
            # self._cursor = removed

            # self.clamp_scroll( 0 )

            return 
        
        if key == glfw.KEY_TAB:
            #self.insert_at( self._cursor, "    " )
            #self._cursor += self.calculate_move( "    " )
            return 
        
        if key == glfw.KEY_ENTER:
            return #self.__enter_handle( )
        
        if key == glfw.KEY_LEFT:
            #self._cursor.x = math.clamp( self._cursor.x - 1, 0, len( self._lines[ self._cursor.y ] ) )
            return

        if key == glfw.KEY_RIGHT:
            #self._cursor.x = math.clamp( self._cursor.x + 1, 0, len( self._lines[ self._cursor.y ] ) )
            return
        
        if key == glfw.KEY_UP:
            return
        
        if key == glfw.KEY_DOWN:
            return

    def __enter_handle( self ):

        # Get line
        line = self._cursor.y
        input_index = self._cursor.x

        # Get what left from the index
        save_text = self._lines[ line ][ input_index: ]

        # Remove this text
        self._lines[ line ] = self._lines[ line ][ :input_index ]

        self.insert_line( save_text, line + 1 )
        self._cursor.y += 1
        self._cursor.x = 0

    # endregion

    # region : Utils

    def char_vec_to_relative( self, char_position: vector ) -> vector:
        
        result = vector( )

        result.y = ( char_position.y ) * self._line_height

        line = self._lines[ char_position.y ]   # TODO Maybe add clamp ?
        result.x = self._render.measure_text( self._font, line[ :char_position.x ] ).x

        # Add the padding
        pad                 = self._config[ "pad" ]
        pad_for_number      = self._config[ "pad_for_number" ]
        scroll              = self._animations.value( "Scroll" )

        return result + self._position + vector( pad + pad_for_number, pad + scroll )

    def relative_to_char_vec( self, relative: vector ) -> vector:

        # Relative vector is from the scene start position. means vector(0, 0)
        # However our editor not always is from the zero.

        result = vector( )

        pad                 = self._config[ "pad" ]
        pad_for_number      = self._config[ "pad_for_number" ]
        scroll              = self._animations.value( "Scroll" )

        # Create copy. Otherwise our relative object will get messed
        relative_vector = relative.copy( )

        # Clear the padding
        relative_vector.y = relative_vector.y - self._position.y - pad - scroll
        relative_vector.x = relative_vector.x - self._position.x - pad_for_number - pad

        # Now after we cleared the y axis. We can extract the line
        result.y = math.clamp( int( relative_vector.y // self._line_height ), 0, len( self._lines ) - 1 )

        line:               str     = self._lines[ result.y ]
        selected_index:     int     = 0
        input_width:        float   = 0.0

        # Find the desired index from the center of each char
        while selected_index < len( line ):
            width = self._render.measure_text( self._font, line[ selected_index ] ).x
            
            if input_width + ( width * 0.5 ) > relative_vector.x:
                break

            input_width += width
            selected_index += 1

        result.x = selected_index

        return result

    """
    def select_text( self, start_position: vector, end_position: vector ):
        # Concats into a list all the indication what lines and what in lines is selected
        # start_vector and end_vector are char position in chars array. not relative position

        # Note ! We dont need to this here, but before, we need to check what vector is first and what is the second.

        # Must be careful with line 0. If we will try to mess it negetive index or something. This will endup in stackoverflow
        if start_position.y == 0:
            start_position.x = math.clamp( start_position.x, 0, len( self._lines[ 0 ] ) )

        result = [ ]

        if end_position.y == start_position.y:
            # Single line
            line_data = [ 0, 0, 0 ]
            line_data[ 0 ] = start_position.y
            line_data[ 1 ] = start_position.x
            line_data[ 2 ] = end_position.x

            result.append(line_data)
        else:
            # Multi line
            
            for i in range( start_position.y, end_position.y + 1 ):
                
                line_data = [ i, 0, 0 ]
                this_line = len( self._lines[ i ] )

                if i == start_position.y:
                    line_data[ 1 ] = start_position.x
                    line_data[ 2 ] = this_line
                elif i == end_position.y:
                    line_data[ 1 ] = -1
                    line_data[ 2 ] = end_position.x
                else:
                    line_data[ 1 ] = -1 # We in some cases want to use the select as delete.
                    # Only Delete option will know what does -1 mean. others will just convert it to 0
                    line_data[ 2 ] = this_line

                result.append( line_data )

        return result

    def insert_at( self, position: vector, text: str ):
        
        texts = text.split( "\n" )
        length = len( texts )

        line = position.y
        input_index = position.x

        # Since we may insert inside a line. we need to be aware if we need to remove the last
        # Attach it to the last string we will add.
        texts[ length - 1 ] += self._lines[ line ][ input_index: ]

        self._lines[ line ] = self._lines[ line ][ :input_index ] + texts[ 0 ]
        
        for i in range( 1, length ):
            selected_line = self._position.y + i

            self._lines.insert( selected_line, texts[ i ] )

    def insert_line( self, text: str, index: int = None ):
        # Can be used to insert multi line text / code at start

        if index is None:
            return self._lines.append( text )

        self._lines.insert( index, text )

    def clear_lines( self ):
        # Full clear lines

        self._lines.clear( )

    def remove( self, from_position: vector, to_position: vector ):

        selected_text = self.select_text( from_position, to_position )

        # Amount of lines removed

        last_line = selected_text[ len( selected_text ) - 1 ]
        save = self._lines[ last_line[ 0 ] ][ last_line[ 2 ]: ]

        is_removed = False

        for line in reversed( selected_text ):
            
            line_number = line[ 0 ]
            if line[ 1 ] == -1 and line_number != 0:
                # Remove line

                # We dont need to save anything. Just delete
                self._lines.pop( line_number ) 
                is_removed = True
            else:
                self._lines[ line_number ] = self._lines[ line_number ][ :line[ 1 ] ] + self._lines[ line_number ][ line[ 2 ]: ]

        # Just clamping
        self.clamp_cursor( from_position )

        if is_removed:
            from_position.x = len( self._lines[ from_position.y ] )
            self.insert_at( from_position, save )

        return from_position

    def remove_char( self ):

        # This is different from remove.
        # When you call .remove(...) you just delete the selected.
        
        pass

    def calculate_move( self, text: str ):
        # Calculates how much we need to move our cursor based on text
        result = vector( )

        texts = text.split( "\n" )
        length = len( texts ) - 1

        result.y = length
        result.x = len( texts[ length ] )

        return result
    
    def clamp_line( self, position: vector ):

        length = len( self._lines[ position.y ] )
        position.x = math.clamp( position.x, 0, length )

    def clamp_cursor( self , position: vector = None):

        position.y = math.clamp( position.y, 0, len( self._lines ) - 1 )

        self.clamp_line( position )

    """

    def clamp_scroll( self, add: float | int ):

        drop = self._line_height * len( self._lines )

        if drop > self._size.y:
            pad         = self._config[ "pad" ]
            drop_min    = self._size.y - drop - pad * 2 
        else:
            drop_min    = 0

        self._height_offset = math.clamp( self._height_offset + add, drop_min, 0 )

    def position( self, new_value: vector ) -> vector | None:

        if new_value is None:
            return self._position.copy( )

        self._position.x = new_value.x
        self._position.y = new_value.y

    def size( self, new_value: vector ) -> vector | None:

        if new_value is None:
            return self._size.copy( )

        self._size.x = new_value.x
        self._size.y = new_value.y
    
    # endregion
