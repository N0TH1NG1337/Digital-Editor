"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Editor

    description : Text Editor class
"""

import time
import glfw
import math as omath
import re

from utilities.color    import color
from utilities.vector   import vector
from utilities.math     import math
from utilities.wrappers import safe_call

from utilities.image    import c_image
from utilities.font     import c_font
from utilities.event    import c_event


# Import user interface related things
from user_interface.render      import c_renderer
from user_interface.animations  import c_animations

EXCEPTIONS = {
    "{": "{}",
    "(": "()",
    "[": "[]",
    "\"": "\"\""
}


class editor_config_t:
    pad:            int = 10
    pad_for_number: int = 50
    speed:          int = 10

    roundness:      int = 10

    separate:       int = 4

    color_background:   color = color( 0, 0, 0, 150 )
    color_shadow:       color = color( 0, 0, 0, 150 )

    color_text:         color = color( 255, 255, 255 )

    color_linenumber:   color = color( 255, 255, 255 )
    color_linetext:     color = color( 255, 255, 255 )

    color_other_lock:   color = color( 255, 150, 150 )

    color_theme:        color = color( 207, 210, 215 )


class c_line:
    text:           str
    previous:       str

    number:         int
    is_locked:      int # 0 - Not locked, 1 - Locked by me, 2 - Locked by others
    locked_by:      str

    is_hovered:     bool
    is_clickable:   bool

    position:       vector
    size:           vector  # Text size

    fade:           float
    fade_pad:       float
    fade_locked:    float
    fade_show_lock: float


class c_syntax_highlighting:
    
    _config:            editor_config_t
    _languages:         dict

    _selected_language: str

    def __init__( self, config: editor_config_t ):

        self._config = config
        self._languages = {

            # Define default settings.
            "default": {
                "keywords": { },
                "patterns": { }
            }
        }

    
    def add_language( self, language_name: str, language_definition: dict ):

        # Language name is the file ending.
        # For example, if the language is Python, the language name is py
        # For another language, it could be js, cpp, etc.

        # Language definition is a dictionary that contains the language definition.
        # The language definition contains the language keywords, operators, and more.

        self._languages[ language_name ] = language_definition

    
    def define_language( self, file_name: str ):

        # First, parse the file name
        if "." in file_name:
            extension: str = file_name.split( "." )[ -1 ]
        else:
            extension: str = ""

        # Now, check if the extension is in the languages dictionary
        if extension in self._languages:
            self._selected_language = extension
        else:
            self._selected_language = "default"

    
    def highlight( self, text: str ) -> list:

        result:     list = [ ]
        parts:      list = [ ]
        last_end:   int = 0

        language:   dict = self._languages[ self._selected_language ]
        patterns:   dict = language[ "patterns" ]
        keywords:   dict = language[ "keywords" ]

        default_color: color = self._config.color_linetext

        for match in re.finditer( r"\w+|'[^']*'|\"[^\"]*\"|#.*|\S", text ): #match words, strings, comments, or single non-whitespace chars.
            start, end              = match.span( )
            word:           str     = match.group( 0 ) 
            current_color:  color   = default_color

            # Check for language patterns 
            for pattern in patterns:
                pattern_color: color = patterns[ pattern ]

                if re.match( pattern, word ):
                    current_color = pattern_color
                    break

            # Check for language keywords
            if word in keywords:
                current_color = keywords[ word ]

            if start > last_end:
                parts.append( ( text[ last_end:start ], default_color ) )

            parts.append( ( word, current_color ) )
            last_end = end

        if last_end < len( text ):
            parts.append( ( text[ last_end: ], default_color ) )

        for word, word_color in parts: #group same colors.
            if result and result[ -1 ][ 1 ] == word_color:
                result[ -1 ] = ( result[ -1 ][ 0 ] + word, word_color )
            else:
                result.append( ( word, word_color ) )

        return result
        

class c_editor:
    
    _parent:                any
    _index:                 int

    _position:              vector
    _size:                  vector

    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _config:                editor_config_t
    _events:                dict

    # From here we will have the editor properties
    _lines:                 list

    _mouse_position:        vector

    _cursor:                vector
    _clicked_position:      vector  # Use this for clicking and setting cursor
    _selection_position:    vector  # Use this for selection
    _selection_index:       vector  # Use this for selection

    _is_typing:             bool
    _is_hovered:            bool
    _is_ctrl:               bool

    _is_hovered_discard:    bool
    _is_hovered_update:     bool

    _offset:                vector  # Offset for the view on the editor. Use this to scroll the editor x and y axises

    _bar_height:            int
    _line_height:           int

    _discard_size:          vector
    _update_size:           vector

    _buttons_position:      vector

    # Some information about the editor, like what file is open what line is selected and more
    _is_read_only:          bool
    _opened_file:           str
    _opened_lines:          str

    _chosen_line:           int
    _chosen_amount:         int

    # Some pure madness
    _syntax_highlighting:   c_syntax_highlighting
    

    # region : Initialization

    def __init__( self, parent: any, position: vector, size: vector, font: c_font, config: editor_config_t = None ):

        # Set config
        self._config = config is None and editor_config_t( ) or config

        # Set parent
        self._parent    = parent

        # Set position and sizes
        self._position  = position.copy( )
        self._size      = size.copy( )

        # Set display information
        self._font      = font

        # Initialize attachment to parent
        self.__init_attachment( )

        # Initialize animations of the widget
        self.__init_animations( )

        # Initialize default and first values for the widget 
        self.__init_bones( )

        # Initialize events
        self.__init_events( )

        # Initialize syntax highlighting
        self.__init_syntax_highlighting( )


    def __init_attachment( self ):

        # Get renderer
        self._render    = self._parent.render( )

        # Attach widget to parent
        self._index     = self._parent.attach_element( self )

        # Attach this widget's events handlers to parent
        this_widget = f"editor::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_widget )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,           this_widget )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,          this_widget )
        self._parent.set_event( "char_input",       self.__event_char_input,            this_widget )
        self._parent.set_event( "keyboard_input",   self.__event_keyboard_input,        this_widget )

    
    def __init_animations( self ):
        
        # Create standalone animations handler
        self._animations = c_animations( )

        self._animations.prepare( "scroll", vector( ) )
        self._animations.prepare( "cursor", vector( ) ) 

        self._animations.prepare( "bar_filename",   0 )
        self._animations.prepare( "bar_line",       0 )

        self._animations.prepare( "controls_enabled",   0 )
        self._animations.prepare( "controls_show",      0 )
        self._animations.prepare( "discard_hover",      0 )
        self._animations.prepare( "update_hover",       0 )
        self._animations.prepare( "lines_show",         0 )


    def __init_bones( self ):
        
        # Create handle for lines
        self._lines = [ ]

        # Default values for input handle
        self._is_hovered            = False
        self._is_typing             = False

        self._is_ctrl               = False

        self._is_hovered_discard    = False
        self._is_hovered_update     = False

        # Set default values for editor
        self._is_read_only      = False
        self._opened_file       = ""
        self._opened_lines      = ""

        self._chosen_line       = 0
        self._chosen_amount     = 0

        self._line_height       = self._font.size( ) + self._config.pad
        self._bar_height        = self._line_height + self._config.pad

        self._discard_size      = vector( )
        self._update_size       = vector( )

        self._buttons_position  = vector( )

        # Set empty vectors
        self._mouse_position        = vector( )
        self._cursor                = vector( )
        self._clicked_position      = vector( -1, -1 )
        self._selection_position    = vector( None, None, 0 )                                       # x - start, y - end, z - is_holding
        self._selection_index       = vector( vector( -1, -1 ), vector( -1, -1 ), time.time( ) )    # x - start, y - end, z - time

        self._offset                = vector( 0, 0 )
    

    def __init_events( self ):

        self._events = {
            "request_line":     c_event( ),     # Triggered when user presses any line
            "discard_line":     c_event( ),     # Triggered when user presses discard button
            "update_line":      c_event( ),     # Triggered when user presses update button
            "delete_line":      c_event( ),     # Triggered when user deletes an empty line 
            "correct_offset":   c_event( )      # Triggered when lines are updated, and some offsets are shifted
        }


    def __init_syntax_highlighting( self ):

        self._syntax_highlighting = c_syntax_highlighting( self._config )
        
        self._syntax_highlighting.add_language( "py", {
            "keywords": {
                "and":      color( 255, 235, 253 ),
                "as":       color( 255, 235, 253 ),
                "assert":   color( 224, 224, 224 ),
                "async":    color( 224, 224, 224 ),
                "await":    color( 224, 224, 224 ),
                "break":    color( 224, 224, 224 ),
                "class":    color( 224, 224, 224 ),
                "continue": color( 224, 224, 224 ),
                "def":      color( 255, 235, 253 ),
                "del":      color( 224, 224, 224 ),
                "elif":     color( 224, 224, 224 ),
                "else":     color( 224, 224, 224 ),
                "except":   color( 224, 224, 224 ),
                "False":    color( 192, 192, 192 ),
                "finally":  color( 224, 224, 224 ),
                "for":      color( 224, 224, 224 ),
                "from":     color( 224, 224, 224 ),
                "global":   color( 255, 235, 253 ),
                "if":       color( 255, 235, 253 ),
                "import":   color( 224, 224, 224 ),
                "in":       color( 255, 235, 253 ),
                "is":       color( 255, 235, 253 ),
                "lambda":   color( 255, 235, 253 ),
                "None":     color( 192, 192, 192 ),
                "nonlocal": color( 224, 224, 224 ),
                "not":      color( 255, 235, 253 ),
                "or":       color( 255, 235, 253 ),
                "pass":     color( 255, 235, 253 ),
                "raise":    color( 255, 235, 253 ),
                "return":   color( 255, 235, 253 ),
                "True":     color( 192, 192, 192 ),
                "try":      color( 255, 235, 253 ),
                "while":    color( 255, 235, 253 ),
                "with":     color( 255, 235, 253 ),
                "yield":    color( 255, 235, 253 )
            },

            "patterns": {
                r"^\d+$":                          color( 160, 160, 160 ),  # Integers
                r"^\d+\.\d*$":                     color( 160, 160, 160 ),  # Floats
                r"^\.\d+$":                        color( 160, 160, 160 ),  # Floats starting with dot
                r"^\d+\.\d*[eE][+-]?\d+$":         color( 160, 160, 160 ),  # Scientific notation without decimal
                r"^'.*'$":                         color( 208, 208, 208 ),  # Single-quoted strings  
                r'^".*"$':                         color( 208, 208, 208 ),  # Double-quoted strings
                r"^'''.*'''$":                     color( 208, 208, 208 ),  # Triple single quoted strings
                r'^""".*"""$':                     color( 208, 208, 208 ),  # Triple double quoted strings
                r"^#.*$":                          color( 176, 176, 176 ),  # Comments
                r"^@[a-zA-Z_][a-zA-Z0-9_]*":       color( 224, 255, 255 ),  # Decorators
                r"^[a-zA-Z_][a-zA-Z0-9_]*\(.*\)":  color( 224, 255, 224 )   # Function calls
            }
        } )

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        
        # Perform some calculations before drawing
        self.__perform_calculations( )
        self.__perform_animations( )

        self.__update_selection( )

        # Draw background staff here
        self.__draw_top_bar( fade )
        self.__draw_background( fade )

        # Draw the lines content here
        self.__draw_lines( fade )

        self.__draw_cursor( fade )

        self.__draw_selection( fade )

        # Draw the scroll bars
        self.__draw_y_axis_scrollbar( fade )
        self.__draw_x_axis_scrollbar( fade )

        # Close the background cliprect
        self._render.pop_clip_rect( )


    def __perform_calculations( self ):
        
        render:     c_renderer = self._render

        self._update_size   = render.measure_text( self._font, "Update" )
        self._discard_size  = render.measure_text( self._font, "Discard" )

        drop            = len( self._lines ) * self._line_height
        fixed_drop      = self._size.y - self._config.pad

        if drop > fixed_drop:
            drop_min    = fixed_drop - drop
        else:
            drop_min = 0

        if self._offset.z > self._size.x:   
            sideways_min = self._size.x - self._offset.z
        else:
            sideways_min = 0

        self._offset.y = math.clamp( self._offset.y, drop_min, 0 )
        self._offset.x = math.clamp( self._offset.x, sideways_min, 0 )

        if self._is_typing:
            
            if self._chosen_amount > 1:
                self._opened_lines = f"{ self._chosen_line } - { self._chosen_line + self._chosen_amount - 1 }"
            else:
                self._opened_lines = f"{ self._chosen_line }"

        if self._clicked_position.x != -1 and self._clicked_position.y != -1 and self._is_typing:
            index: vector = self.__relative_to_char_vector( self._clicked_position )
            self._cursor.y = math.clamp( index.y, self._chosen_line - 1, self._chosen_line + self._chosen_amount - 2 )
            self._cursor.x = index.x

            self.__clamp_cursor( )

            self._clicked_position.x = -1
            self._clicked_position.y = -1


    def __perform_animations( self ):
        
        # To avoid over indexing the animations object
        animations: c_animations    = self._animations
        render:     c_renderer      = self._render

        animations.update( )

        speed:  int = self._config.speed
        pad:    int = self._config.pad

        double_pad: int = pad * 2

        animations.perform( "scroll", self._offset, speed, 1 )

        animations.perform( "bar_filename", render.measure_text( self._font, self._opened_file ).x + double_pad, speed, 1 )
        animations.perform( "lines_show", render.measure_text( self._font, self._opened_lines ).x + double_pad, speed, 1 )

        controls_enabled: float = animations.perform( "controls_enabled", self._is_typing and 1 or 0, speed )
        animations.perform( "controls_show", controls_enabled == 1 and 1 or 0, speed )

        animations.perform( "discard_hover", self._is_hovered_discard and 1 or 0.3, speed )
        animations.perform( "update_hover", self._is_hovered_update and 1 or 0.3, speed )
        
        if self._is_typing:
            animations.perform( "cursor", self._position + self.__char_vector_to_relative( self._cursor ), speed * 2 )
    

    def __draw_top_bar( self, fade: float ):
        
        pad:                int = self._config.pad
        roundness:          int = self._config.roundness
        color_background:   color = self._config.color_background
        color_shadow:       color = self._config.color_shadow
        color_text:         color = self._config.color_text

        bar_height:         int = self._bar_height

        bar_filename:       float = self._animations.value( "bar_filename" )
        bar_line:           float = self._animations.value( "bar_line" )

        controls_enabled:   float = self._animations.value( "controls_enabled" ) * fade
        controls_show:      float = self._animations.value( "controls_show" ) * controls_enabled
        discard_hover:      float = self._animations.value( "discard_hover" ) * controls_show
        update_hover:       float = self._animations.value( "update_hover" ) * controls_show
        lines_show:         float = self._animations.value( "lines_show" ) * controls_enabled

        filename_size:      vector = self._render.measure_text( self._font, self._opened_file )

        # Do this to avoid over indexing the render object
        render:             c_renderer = self._render

        # First we need to draw the filename box
        end_position_filename: vector = self._position + vector( bar_filename, bar_height )

        render.shadow(
            self._position,
            end_position_filename,
            color_shadow,
            fade,
            20,
            roundness
        )

        render.rect(
            self._position,
            end_position_filename,
            color_background * fade,
            roundness
        )

        render.push_clip_rect( self._position, end_position_filename, True )

        render.text(
            self._font,
            self._position + vector( pad, ( bar_height - filename_size.y ) / 2 ),
            color_text * fade,
            self._opened_file
        )

        render.pop_clip_rect( )

        bar_line += bar_filename + pad

        # Draw the buttons here
        button_discard_size:    vector = vector( ( self._discard_size.x + pad * 2 ) * controls_enabled, bar_height )
        button_update_size:     vector = vector( ( self._update_size.x + pad * 2 ) * controls_enabled, bar_height )
        
        add_for_active_buttons: float = controls_enabled * 2 * pad

        if controls_enabled > 0:
            position_for_buttons:   vector = vector( self._position.x + self._size.x - button_discard_size.x, self._position.y )

            # Button Discard
            render.shadow( position_for_buttons, position_for_buttons + button_discard_size, color_shadow, controls_show, 20, roundness )
            render.rect( position_for_buttons, position_for_buttons + button_discard_size, color_background * controls_show, roundness )
            render.text(
                self._font,
                position_for_buttons + vector( pad, ( bar_height - self._discard_size.y ) / 2 ),
                color_text * discard_hover,
                "Discard"
            )
            
            position_for_buttons.x -= pad + button_update_size.x

            self._buttons_position.x = position_for_buttons.x
            self._buttons_position.y = position_for_buttons.y

            # Button Update
            render.shadow( position_for_buttons, position_for_buttons + button_update_size, color_shadow, controls_show, 20, roundness )
            render.rect( position_for_buttons, position_for_buttons + button_update_size, color_background * controls_show, roundness )
            render.text(
                self._font,
                position_for_buttons + vector( pad, ( bar_height - self._update_size.y ) / 2 ),
                color_text * update_hover,
                "Update"
            )

            position_for_lines:     vector = vector( self._position.x + bar_line, self._position.y )
            end_position_for_lines: vector = vector( position_for_lines.x + lines_show, position_for_lines.y + bar_height )

            render.shadow( position_for_lines, end_position_for_lines, color_shadow, controls_enabled, 20, roundness )
            render.rect( position_for_lines, end_position_for_lines, color_background * controls_enabled, roundness )
            render.text(
                self._font,
                position_for_lines + vector( pad, ( bar_height - self._update_size.y ) / 2 ),
                color_text * controls_enabled,
                self._opened_lines
            )

            bar_line += ( lines_show + pad ) * controls_enabled


        # Now just draw empty bar
        begin_position: vector = self._position + vector( bar_line, 0 )
        end_position:   vector = begin_position + vector( self._size.x - bar_line - button_discard_size.x - button_update_size.x - add_for_active_buttons, bar_height )

        render.shadow(
            begin_position,
            end_position,
            color_shadow,
            fade,
            20,
            roundness
        )

        render.rect(
            begin_position,
            end_position,
            color_background * fade,
            roundness
        )


    def __draw_background( self, fade: float ):

        pad:                int = self._config.pad
        roundness:          int = self._config.roundness
        color_background:   color = self._config.color_background
        color_shadow:       color = self._config.color_shadow
        color_text:         color = self._config.color_text

        bar_height:         int = self._bar_height

        # Do this to avoid over indexing the render object
        render:             c_renderer = self._render

        start_position:     vector = self._position + vector( 0, bar_height + pad )
        end_position:       vector = self._position + vector( self._size.x, self._size.y )

        render.shadow(
            start_position,
            end_position,
            color_shadow,
            fade,
            20,
            roundness
        )

        render.rect(
            start_position,
            end_position,
            color_background * fade,
            roundness
        )

        render.push_clip_rect( start_position, end_position, True )
        # Close this cliprect in the draw function
    

    def __draw_lines( self, fade: float ):
        
        pad_for_number: int = self._config.pad_for_number
        pad: int = self._config.pad

        scroll:             vector = self._animations.value( "scroll" )
        start_position:     vector = self._position + vector( pad, self._bar_height + pad * 2 )

        index:  int = 0
        drop:   float = 0

        self._offset.z = 0

        for line in self._lines:

            line: c_line    = line
            index           = index + 1

            normalized_drop = drop + pad / 2

            # Set the line number here
            line.number = index

            # Calculate the line position here.
            # Dont create new vector for this. just update the existing one
            line.position.x = start_position.x + scroll.x + pad + pad_for_number
            line.position.y = start_position.y + scroll.y + normalized_drop

            # Calculate the size of the line text
            temp_size: vector = self._render.measure_text( self._font, line.text )
            line.size.x = temp_size.x
            line.size.y = temp_size.y
            del temp_size

            # Draw the line here
            self.__draw_line( fade, line, start_position )

            # Update the drop value here
            drop = drop + self._line_height

        self._offset.z += pad_for_number + pad * 3


    def __draw_line( self, fade: float, line: c_line, start_position: vector ):
        
        speed:              int = self._config.speed
        pad:                int = self._config.pad
        pad_for_number:     int = self._config.pad_for_number

        color_linetext:     color = self._config.color_linetext
        color_linenumber:   color = self._config.color_linenumber
        color_other_lock:   color = self._config.color_other_lock
        color_theme:        color = self._config.color_theme

        animations:         c_animations    = self._animations
        render:             c_renderer      = self._render

        line_number:        str = str( line.number )

        size:               vector = self._size

        is_line_selected:   bool = not self._is_read_only and line.number >= self._chosen_line and line.number < self._chosen_line + self._chosen_amount
        is_line_outside:    bool = line.position.y < start_position.y or line.position.y + self._line_height - pad > self._position.y + size.y

        # From here we need to animate the line properties here
        line.fade_pad       = animations.fast_perform( line.fade_pad, ( not is_line_outside ) and 1 or 0, speed ) * fade
        line.fade           = animations.fast_perform( line.fade, ( is_line_selected or ( line.is_hovered and line.is_locked == 0 ) ) and fade or 0.5, speed ) * line.fade_pad
        line.fade_locked    = animations.fast_perform( line.fade_locked, ( line.is_locked != 0 and not self._is_ctrl ) and 0.4 or 0, speed ) * line.fade_pad
        line.fade_show_lock = animations.fast_perform( line.fade_show_lock, ( line.is_hovered and line.is_locked == 2 ) and 1 or 0, speed ) * fade

        if line.size.x > self._offset.z:
            self._offset.z = line.size.x

        if line.fade_pad == 0:
            return
        
        number_size:        vector = render.measure_text( self._font, line_number )
        locked_size:        vector = render.measure_text( self._font, line.locked_by )

        locked_size.x += pad * 2

        text_position:      vector = line.position.copy( )
        number_position:    vector = vector( start_position.x + pad_for_number - number_size.x, line.position.y )  # TODO : Create a number position here

        text_position.x     -= ( line.fade_pad - 1 ) * 50
        number_position.x   += ( line.fade_pad - 1 ) * 20
        
        locked_by_value: float = line.fade_show_lock * ( locked_size.x + pad )

        locked_color:           color  = ( line.is_locked == 2 ) and color_other_lock or color_theme
        start_lock_gradient:    vector = vector( start_position.x + pad + pad_for_number, line.position.y - pad / 2 )
        end_lock_gradient:      vector = vector( start_position.x + size.x * line.fade_pad - locked_by_value, line.position.y + line.size.y + pad / 2 )

        render.gradiant( start_lock_gradient, end_lock_gradient, locked_color * 0, locked_color * line.fade_locked, locked_color * 0, locked_color * line.fade_locked )

        render.push_clip_rect( vector( start_position.x + pad + pad_for_number, line.position.y ), vector( start_position.x + size.x - locked_by_value, line.position.y + line.size.y ), True )

        # Draw the line here
        highlighted_text = self._syntax_highlighting.highlight( line.text )
        for word, word_color in highlighted_text:
            render.text( self._font, text_position, word_color * line.fade, word )
            text_position.x += render.measure_text( self._font, word ).x
        #render.text( self._font, text_position, color_linetext * line.fade, line.text )

        render.pop_clip_rect( )

        # Draw the line number here
        render.text( self._font, number_position, color_linenumber * line.fade, line_number )
        render.text( self._font, vector( start_position.x + size.x - locked_size.x, line.position.y ), color_linetext * line.fade_show_lock, line.locked_by )


    def __draw_cursor( self, fade: float ):
        
        if not self._is_typing:
            return
        
        height:         int     = self._line_height
        
        position:       vector  = self._animations.value( "cursor" )
        start:          vector  = vector( position.x - 1, position.y )
        end:            vector  = vector( position.x + 1, position.y + height )

        # If you dont check this, it will crash the application
        if position.x < self._position.x:
            return
    
        color_theme:    color   = self._config.color_theme

        self._render.shadow(
            start,
            end,
            color_theme,
            fade,
            15
        )

        self._render.rect(
            start,
            end,
            color_theme * fade
        )


    def __draw_selection( self, fade: float ):

        if fade == 0:
            return self.__reset_selection( )
        
        if self._selection_position.x is None or self._selection_position.y is None:
            return

        if self._selection_index.x.x == -1 and self._selection_index.x.y == -1:
            start_index = self.__relative_to_char_vector( self._selection_position.x )

            self._selection_index.x.x = start_index.x
            self._selection_index.x.y = start_index.y

        if self._selection_position.z == 1:
            end_index = self.__relative_to_char_vector( self._selection_position.y )

            self._selection_index.y.x = end_index.x
            self._selection_index.y.y = end_index.y

        if self._selection_position.z == 0 and self._selection_index.x == self._selection_index.y:
            return self.__reset_selection( )
        
        color_theme:    color   = self._config.color_theme
        pad:            int     = self._config.pad
        separate:       int     = self._config.separate
        line_height:    int     = self._line_height

        lines: list = self.get_selection( )
        for line_info in lines:
            start_position = self._position + self.__char_vector_to_relative( vector( line_info.x, line_info.z ) ) + vector( 0, line_height - separate )
            end_position = self._position + self.__char_vector_to_relative( vector( line_info.y, line_info.z ) ) + vector( pad, line_height )

            self._render.neon( start_position, end_position, color_theme * fade, 18, separate / 2 )


    def __draw_y_axis_scrollbar( self, fade: float ):
        
        separate:       int     = self._config.separate
        color_theme:    color   = self._config.color_theme

        bar_height:     int     = self._bar_height + self._config.pad

        window_delta:   float   = self._size.y - bar_height
        drop                    = len( self._lines ) * self._line_height

        if drop == 0:
            return
        
        if drop <= window_delta:
            return
        
        scroll_y        = self._animations.value( "scroll" ).y
        scroll_delta    = window_delta / drop

        fixed           = window_delta * scroll_delta
        value           = abs( scroll_y ) * scroll_delta

        position:       vector  = vector( self._position.x + self._size.x - separate, self._position.y + bar_height )
        start_position: vector  = vector( position.x, position.y + value )
        end_position:   vector  = vector( position.x + separate, start_position.y + fixed )

        self._render.shadow( start_position, end_position, color_theme, fade, 15, separate / 2 )
        self._render.rect( start_position, end_position, color_theme * fade, separate / 2 )

    
    def __draw_x_axis_scrollbar( self, fade: float ):

        separate:       int     = self._config.separate
        color_theme:    color   = self._config.color_theme

        window_delta:   float   = self._size.x

        drop:           float   = self._offset.z

        if drop == 0:
            return
        
        if drop <= window_delta:
            return 
        
        scroll_x        = self._animations.value( "scroll" ).x
        scroll_delta    = window_delta / drop

        fixed           = window_delta * scroll_delta
        value           = abs( scroll_x ) * scroll_delta

        position:       vector  = vector( self._position.x, self._position.y + self._size.y - separate )
        start_position: vector  = vector( position.x + value, position.y )
        end_position:   vector  = vector( start_position.x + fixed, position.y + separate )

        self._render.shadow( start_position, end_position, color_theme, fade, 15, separate / 2 )
        self._render.rect( start_position, end_position, color_theme * fade, separate / 2 )

    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        
        self._mouse_position.x = event( "x" )
        self._mouse_position.y = event( "y" )

        self.__hover_editor( )

        if self._is_read_only:
            return
        
        if self.__hover_buttons( ):
            return
        
        self.__hover_lines( )


    def __event_mouse_input( self, event ) -> None:
        
        if self._is_read_only:
            return
        
        button: int = event( "button" )
        action: int = event( "action" )

        if not button == glfw.MOUSE_BUTTON_LEFT:
            return
        
        is_press:   bool = action == glfw.PRESS
        is_release: bool = action == glfw.RELEASE

        if is_press:
            self.__handle_press( )

        if ( self._is_ctrl and not self._is_typing ) or self._is_typing:
            value: vector = self._mouse_position.copy( )

            not_hovered_buttons: bool = not self._is_hovered_discard and not self._is_hovered_update
            if self._is_hovered and not_hovered_buttons and is_press:
                
                if self._selection_position.y is not None:
                    self.__reset_selection( )

                self._selection_position.x = value
                self._selection_position.z = 1
                self._selection_index.z = time.time( )

                return
            
            if is_release and self._selection_position.x is not None:
                self._selection_position.y = value

                if ( time.time( ) - self._selection_index.z ) < 0.1:
                    self.__reset_selection( )

                self._selection_position.z = 0

                return
        else:
            self.__reset_selection( )

        if not is_press:
            return
        
        if self.__handle_buttons( ):
            return

        self.__handle_lines( )
        

    def __event_mouse_scroll( self, event ) -> None:
        
        if not self._is_hovered:
            return

        x_offset = event( "x_offset" )
        y_offset = event( "y_offset" )

        # We update here
        # But clamp it in the __perform_calculations function
        self._offset.y = self._offset.y + y_offset * 20
        self._offset.x = self._offset.x + x_offset * 30


    def __event_char_input( self, event ) -> None:
        
        if not self._is_typing:
            return
        
        char = chr( event( "char" ) )
        self.__insert( char )


    def __event_keyboard_input( self, event ) -> None:
        
        key:    int = event( "key" )
        action: int = event( "action" )

        self.__handle_ctrl( key, action )

        self.__handle_selection_actions( key, action )

        if not self._is_typing:
            return

        if action == glfw.PRESS:

            is_safe = self.__repeat_handle( key )

            if key == glfw.KEY_BACKSPACE and is_safe:
                return self.__custom_event_delete_line( )
            
        if action == glfw.REPEAT:
            self.__repeat_handle( key )

    # endregion

    # region : Input Helpers

    def __hover_editor( self ):

        is_in_bounds    = self._mouse_position.is_in_bounds( self._position, self._size.x, self._size.y )
        is_selected     = self._chosen_line > 0

        if is_in_bounds or is_selected:

            self._is_hovered = self._parent.try_to_get_handle( self._index )
        else:

            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False


    def __hover_buttons( self ) -> bool:

        if self._chosen_line <= 0:
            self._is_hovered_discard    = False
            self._is_hovered_update     = False
            return
        
        pad:        int = self._config.pad
        bar_height: int = self._bar_height

        discard_size:   vector = vector( self._discard_size.x + pad * 2, bar_height )
        update_size:    vector = vector( self._update_size.x + pad * 2, bar_height )

        self._is_hovered_update  = self._mouse_position.is_in_bounds( self._buttons_position, update_size.x, update_size.y )
        self._buttons_position.x += pad + update_size.x
        self._is_hovered_discard = self._mouse_position.is_in_bounds( self._buttons_position, discard_size.x, discard_size.y )

        return self._is_hovered_update or self._is_hovered_discard

    
    def __hover_lines( self ):

        if self._chosen_line > 0:
            return
        
        text_height:        int = self._font.size( )
        bar_height:         int = self._bar_height + self._config.pad

        is_inside_the_box:  bool = self._mouse_position.is_in_bounds( 
            self._position + vector( 0, bar_height ), 
            self._size.x, self._size.y - bar_height 
        ) and not self._is_read_only

        if self._is_ctrl and not self._is_typing:
            is_inside_the_box = False

        width:              float = self._size.x
        start:              float = self._position.x

        # TODO ! Maybe do the check for only the lines that are inside the box ?

        for line in self._lines:
            line: c_line = line

            line_position:  vector = line.position

            line.is_hovered = is_inside_the_box and self._mouse_position.is_in_bounds( vector( start, line_position.y ), width, text_height )
    

    def __handle_buttons( self ) -> bool:
        
        if self._chosen_line <= 0:
            return False
        
        if self._is_hovered_discard:
            self.__custom_event_discard_line( )
            return True
        
        if self._is_hovered_update:
            self.__custom_event_update_line( )
            return True
        
        return True


    def __handle_lines( self ):

        if not self._is_hovered:
            return
        
        if self._is_ctrl and not self._is_typing:
            return
        
        if self._chosen_line > 0:
            return
        
        for line in self._lines:
            line: c_line = line

            if line.is_hovered and line.is_locked == 0:
                return self.__custom_event_request_line( line.number )


    def __handle_press( self ):
        
        value: vector = self._mouse_position.copy( )
        self._clicked_position.x = value.x
        self._clicked_position.y = value.y


    def __handle_ctrl( self, key: int, action: int ):
        
        if key != glfw.KEY_LEFT_CONTROL and key != glfw.KEY_RIGHT_CONTROL:
            return

        if action == glfw.PRESS:
            self._is_ctrl = True

        if action == glfw.RELEASE:
            self._is_ctrl = False 


    def __handle_selection_actions( self, key: int, action: int ):
        
        # We have only 3 actions. PRESS, RELEASE, REPEAT. we want to check for press or repeat
        if action == glfw.RELEASE:
            return
        
        if key == glfw.KEY_C:
            # Copy selected text
            lines: list = self.get_selection( )
            result: list = [ ]
            for line_details in lines:
                result.append( self._lines[ line_details.z ].text[ line_details.x:line_details.y+1 ] )

            return glfw.set_clipboard_string( None, "\n".join( result ) )
    

    def __repeat_handle( self, key: int ) -> bool:
        
        # Remove
        if key == glfw.KEY_BACKSPACE:
            return self.__pop( ) is None
        
        # Tab shift
        if key == glfw.KEY_TAB:
            self.__tab( )
            return True
        
        # Enter press
        if key == glfw.KEY_ENTER:
            self.__enter( )
            return True
        
        # Move index to left
        if key == glfw.KEY_LEFT and self._cursor.x > 0:
            self._cursor.x -= 1
            return True
        
        # Move index to right
        if key == glfw.KEY_RIGHT and self._cursor.x < len( self.get_cursor_line( ).text ):
            self._cursor.x += 1
            return True
        
        if self._chosen_amount > 1:
            if key == glfw.KEY_UP and self._cursor.y >= self._chosen_line:
                self._cursor.y -= 1
                self.__clamp_cursor( )

                return True
            
            if key == glfw.KEY_DOWN and self._cursor.y < self._chosen_line + self._chosen_amount - 2:
                self._cursor.y += 1
                self.__clamp_cursor( )

                return True

        return True


    def __reset_selection( self ):
        
        # This looks hella confusing :P
        self._selection_index.x.x = -1
        self._selection_index.x.y = -1

        self._selection_index.y.x = -1
        self._selection_index.y.y = -1

        self._selection_position.x = None
        self._selection_position.y = None

    
    def __update_selection( self ):

        if self._selection_position.z == 0:
            return
        
        value: vector = self._mouse_position.copy( )

        if self._selection_position.x is not None:
            self._selection_position.y = value
    
    # endregion

    # region : Events

    def __custom_event_request_line( self, line_number: int ) -> None:
        
        # This thing will define that we are waiting for a response.
        self._chosen_line = line_number * ( -1 )

        event: c_event = self._events[ "request_line" ]

        event.attach( "file", self._opened_file )
        event.attach( "line", line_number )

        event.invoke( )


    def __custom_event_discard_line( self ) -> None:
        
        event: c_event = self._events[ "discard_line" ]

        event.attach( "file", self._opened_file )
        event.attach( "line", self._chosen_line )

        event.invoke( )

        # Call the discard action
        self.discard_action( )
    

    def __custom_event_update_line( self ) -> None:
        
        if self._chosen_line <= 0:
            return
        
        event: c_event = self._events[ "update_line" ]

        event.attach( "file", self._opened_file )
        event.attach( "line", self._chosen_line )

        changed_lines:      list = self.__get_edited_lines( )
        correct_changes:    list = [ ]

        for line in changed_lines:
            line: c_line = line
            correct_changes.append( line.text )
            
            line.previous   = line.text
            line.is_locked  = 0

        event.attach( "lines", correct_changes )
        
        event.invoke( )

        self.__disable_edit( )


    def __custom_event_delete_line( self ) -> None:
        
        if self._chosen_line <= 0:
            return
        
        if self._chosen_amount > 1:
            return
        
        if self._cursor.y + 1 != self._chosen_line:
            return
        
        selected_line: c_line = self.get_cursor_line( )

        if selected_line.text != "":
            return # TODO ! Remove this and add warning that the action will delete the line
        
        self._lines.remove( selected_line )

        event: c_event = self._events[ "delete_line" ]

        event.attach( "file", self._opened_file )
        event.attach( "line", self._chosen_line )

        event.invoke( )

        self.__disable_edit( )
    

    def __custom_event_correct_offset( self, offset: int ) -> None:
        
        event: c_event = self._events[ "correct_offset" ]

        event.attach( "file", self._opened_file )
        event.attach( "offset", offset )

        event.invoke( )


    def set_event( self, event_index: str, function: any, function_name: str ) -> None:
        
        if not event_index in self._events:
            raise Exception( f"Failed to index event { event_index }" )
        
        event: c_event = self._events[ event_index ]
        event.set( function, function_name, True )

    # endregion

    # region : Utilities

    def position( self, new_value: vector = None ) -> vector:
        
        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

        return new_value


    def size( self, new_value: vector = None ) -> vector:
        
        if new_value is None:
            return self._size
        
        self._size.x = new_value.x
        self._size.y = new_value.y

        return new_value


    def read_only( self, new_value: bool = None ) -> bool:
        
        if new_value is None:
            return self._is_read_only
        
        self._is_read_only = new_value

        return new_value


    def get_cursor_line( self ) -> c_line:

        return self._lines[ self._cursor.y ]

    
    def get_selection( self ) -> list:

        start   = self.__get_start_vector( self._selection_index.x, self._selection_index.y )
        end     = self.__get_end_vector( self._selection_index.x, self._selection_index.y )

        result: list = [ ]

        # Returns the list of line numbers and indexes of selection
        if start.y == end.y:
            result.append( vector( start.x, end.x, start.y ) )

        else:

            for line_index in range( start.y, end.y + 1 ):

                line_length: int = len( self._lines[ line_index ].text )

                if line_index == start.y:
                    result.append( vector( start.x, line_length, line_index ) )
                elif line_index == end.y:
                    result.append( vector( 0, end.x, line_index ) )
                else:
                    result.append( vector( 0, line_length, line_index ) )

        return result


    # endregion

    # region : Private utilities

    def __get_edited_lines( self ) -> list:
        
        start_index:    int = self._chosen_line - 1  # Adjust for 0-based indexing
        end_index:      int = start_index + self._chosen_amount

        # Ensure start_index is not negative
        if start_index < 0:
            return [ ]

        return self._lines[ start_index:end_index ]


    def __disable_edit( self ):
        
        # Set the typing flag to false
        self._is_typing     = False

        # Clear the chosen values
        self._chosen_line   = 0
        self._chosen_amount = 0

        # Release the widget handle
        if self._parent.is_this_active( self._index ):
            self._parent.release_handle( self._index )

    
    def __set_cursor_at_end( self ):
        
        self._cursor.x = len( self.get_cursor_line( ).text )

    
    def __clamp_cursor( self ):

        self._cursor.x = math.clamp( self._cursor.x, 0, len( self.get_cursor_line( ).text ) )

    
    def __char_vector_to_relative( self, char_position: vector ) -> vector:

        result = vector( )

        result.y = ( char_position.y ) * self._line_height

        line:   c_line  = self._lines[ char_position.y ]
        result.x        = self._render.measure_text( self._font, line.text[ :char_position.x ] ).x

        pad:            int     = self._config.pad
        pad_for_number: int     = self._config.pad_for_number
        bar_height:     int     = self._bar_height
        scroll:         vector  = self._animations.value( "scroll" )

        return result + vector( pad * 2 + pad_for_number + scroll.x, bar_height + pad * 2 + scroll.y )


    def __relative_to_char_vector( self, relative_position: vector ) -> vector:

        result = vector( )

        pad:                int = self._config.pad
        pad_for_numbers:    int = self._config.pad_for_number
        bar_height:         int = self._bar_height

        scroll: vector = self._animations.value( "scroll" )

        # Create copy. Otherwise our relative object will get messed
        relative_vector:    vector  = relative_position.copy( )

        # Clear the padding
        relative_vector.y = relative_vector.y - self._position.y - pad * 2 - scroll.y - bar_height
        relative_vector.x = relative_vector.x - self._position.x - pad_for_numbers - pad * 2 - scroll.x

        # Now after we cleared the y axis. We can extract the line
        result.y = math.clamp( int( relative_vector.y / self._line_height ), 0, len( self._lines ) - 1 )

        line:           c_line = self._lines[ result.y ]
        text_length:    int = len( line.text )
        selected_index: int = 0

        for i in range( text_length + 1 ):

            substring:  str     = line.text[ :i ]
            width:      float   = self._render.measure_text( self._font, substring ).x

            if width > relative_vector.x:
                
                fixed_index:    int     = max( 0, i - 1 )
                prev_width:     float   = self._render.measure_text( self._font, line.text[ :fixed_index ] ).x

                if abs( width - relative_vector.x ) < abs( prev_width - relative_vector.x ):
                    selected_index = i
                else:
                    selected_index = fixed_index

                break

            else:
                selected_index = i

        result.x = selected_index

        return result


    def __complete_new_line( self, new_line: c_line ):

        new_line.number         = -1

        new_line.fade           = 0
        new_line.fade_pad       = 0
        new_line.fade_locked    = 0
        new_line.fade_show_lock = 0

        new_line.is_hovered     = False

        new_line.is_locked      = 0

        new_line.locked_by      = "?"

        new_line.position       = vector( )
        new_line.size           = vector( )
    

    def __get_start_vector( self, first_vector: vector, second_vector: vector ) -> vector:
        
        if first_vector.y == second_vector.y:
            return min( first_vector.x, second_vector.x ) == first_vector.x and first_vector or second_vector
        
        return min( first_vector.y, second_vector.y ) == first_vector.y and first_vector or second_vector


    def __get_end_vector( self, first_vector: vector, second_vector: vector ) -> vector:

        if first_vector.y == second_vector.y:
            return max( first_vector.x, second_vector.x ) == first_vector.x and first_vector or second_vector
        
        return max( first_vector.y, second_vector.y ) == first_vector.y and first_vector or second_vector
    
    # endregion

    # region : Public changes

    def clear( self ):

        self._lines.clear( )


    def open_file( self, file_name: str = None ) -> str:
        
        if file_name is None:
            return self._opened_file
        
        self._opened_file = file_name
        self._syntax_highlighting.define_language( file_name )
        
        return file_name


    def add_line( self, text: str ):

        new_line = c_line( )

        new_line.text       = text
        new_line.previous   = text

        self.__complete_new_line( new_line )

        self._lines.append( new_line )

    # endregion

    # region : Private changes

    def __insert( self, text: str ):
        
        # Get the new value length
        length = len( text )

        # Change if apeares in exceptions
        if text in EXCEPTIONS:
            text = EXCEPTIONS[ text ]

        # Get the line to enter the value
        line_obj: c_line = self._lines[ self._cursor.y ]

        # Insert the value and move the cursor
        line_obj.text   = line_obj.text[ :self._cursor.x ] + text + line_obj.text[ self._cursor.x: ]
        self._cursor.x += length

    
    def __pop( self ) -> str:
        
        if self._cursor.x == 0:

            # Potential to remove line
            if self._cursor.y >= self._chosen_line:

                # Remove line
                line: c_line = self.get_cursor_line( )
                self._lines.remove( line )

                self._cursor.y      -= 1
                self._chosen_amount -= 1

                previous_line: c_line   = self.get_cursor_line( )
                self.__set_cursor_at_end( )
                previous_line.text      = previous_line.text + line.text

                return line.text
            
            return None
        
        line:   c_line  = self.get_cursor_line( )
        char:   str     = line.text[ self._cursor.x - 1 ]

        if self._cursor.x % 4 == 0 and line.text[ self._cursor.x - 4:self._cursor.x ] == "    ":
            line.text       = line.text[ :self._cursor.x - 4 ] + line.text[ self._cursor.x: ]
            self._cursor.x -= 4

        else:
        
            line.text       = line.text[ :self._cursor.x - 1 ] + line.text[ self._cursor.x: ]
            self._cursor.x -= 1

        return char
    

    def __tab( self ):

        cursor_placement:   int = self._cursor.x
        add_to_tab:         int = 4 - ( cursor_placement % 4 )

        self.__insert( " " * add_to_tab )

    
    def __enter( self ):
        
        new_line:       c_line = c_line( )
        current_line:   c_line = self.get_cursor_line( )

        # Get the tabbing to add to the next line 
        spaces: int = len( current_line.text ) - len( current_line.text.lstrip( ) )

        # Copy the right text
        new_line.text       = spaces * " " + current_line.text[ self._cursor.x: ]
        new_line.previous   = ""

        # Remove the right text
        current_line.text = current_line.text[ :self._cursor.x ]

        # Set default values for new line
        self.__complete_new_line( new_line )
        new_line.is_locked = 1

        # Add the line
        self._lines.insert( self._cursor.y + 1, new_line )

        # Change the cursor placement
        self._cursor.y += 1
        self._cursor.x  = spaces

        # Increase the amount
        self._chosen_amount += 1

    # endregion

    # region : Quick actions

    def accept_line( self, file_name: str, line_number: int, did_accept: bool ):
        
        if not did_accept:
            return

        if self._opened_file != file_name:
            return

        # Set the chosen line to be normalized value
        correct_index = self._chosen_line * ( -1 )
        if correct_index != line_number:
            return

        # Enable typing
        self._chosen_line   = line_number
        self._is_typing     = True

        # Select the first line
        self._chosen_amount = 1

        # Set the cursor indexes
        self._cursor.x = 0
        self._cursor.y = line_number - 1

        line: c_line = self.get_cursor_line( )
        line.is_locked = 1


    def discard_action( self ):
        
        if self._chosen_line <= 0:
            return
        
        # Get the changed lines
        changed_lines:  list    = self.__get_edited_lines( )
        first_line:     c_line  = changed_lines[ 0 ]

        # Avoid deleting the first line that existed before changes
        changed_lines.remove( first_line )

        # Set the text to the value before edit
        first_line.text         = first_line.previous
        first_line.is_locked    = 0

        # Remove the lines from the lines list
        for line in changed_lines:
            self._lines.remove( line )

        # Clear memory
        del changed_lines

        # Disable the edit mode
        self.__disable_edit( )


    def change_lines( self, file_name: str, line: int, lines: list ):
        
        if self._opened_file != file_name:
            return
        
        # Correct the changes if the local input is big
        if self._chosen_line > 0 and self._chosen_line < line:
            new_amount = self._chosen_amount - 1
            line += new_amount

        # Remove first line to add a new one
        line -= 1
        self._lines.pop( line )

        # Correct your input offset
        if self._chosen_line > line:
            add = len( lines ) - 1

            self._chosen_line   += add
            self._cursor.y      += add

            self.__custom_event_correct_offset( add )
        
        # Add each new line
        for line_str in lines:
            new_line: c_line = c_line( )

            new_line.text       = line_str
            new_line.previous   = line_str

            self.__complete_new_line( new_line )

            self._lines.insert( line, new_line )
            line += 1


    def delete_line( self, file_name: str, line: int ):

        if self._opened_file != file_name:
            return
        
        # Fix line index
        if self._chosen_line > 0 and self._chosen_line < line:
            new_amount = self._chosen_amount - 1
            line += new_amount

        # Remove the line
        self._lines.pop( line - 1 )

        # Correct offset if need
        if self._chosen_line > line:
            self._chosen_line   -= 1
            self._cursor.y      -= 1

            self.__custom_event_correct_offset( -1 )
    

    def lock_line( self, line: int, locked_by: str = "?" ):
        
        if self._chosen_line > 0 and self._chosen_line < line:
            new_amount = self._chosen_amount - 1
            line += new_amount

        line -= 1

        if line < 0 or line > len( self._lines ):
            return
        
        line_obj: c_line = self._lines[ line ]

        line_obj.is_locked = 2
        line_obj.locked_by = locked_by


    def unlock_line( self, line: int ):

        if self._chosen_line > 0 and self._chosen_line < line:
            new_amount = self._chosen_amount - 1
            line += new_amount

        line -= 1

        if line < 0 or line > len( self._lines ):
            return
        
        line_obj: c_line = self._lines[ line ]
        line_obj.is_locked = 0

    # endregion


