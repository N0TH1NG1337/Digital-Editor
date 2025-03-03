"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Text Input

    description : Text input classes
"""

import glfw
import time

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


class text_input_config_t:
    speed:      int = 10    # Animations speed
    pad:        int = 10    # Default pad
    seperate:   int = 4     # Seperate line
    roundness:  int = 10    # Background roundness

    color_background:   color = color( 0, 0, 0, 100 )
    color_shadow:       color = color( 0, 0, 0, 100 )
    color_theme:        color = color( 216, 208, 215 )
    color_selection:    color = color( 216, 208, 215 )

    color_icon:         color = color(  )
    color_label:        color = color(  )

    color_input:        color = color(  )


class c_single_input_logic:
    # Logic class for single line text input

    # region : Protected attributes

    _parent:                any                     # Parent object - c_scene / c_window

    _position:              vector                  # Relative to parent position
    _relative_position:     vector                  # Relative to application position

    _size:                  vector                  # Input logic size

    _input:                 str                     # Actual value
    _font:                  c_font                  # Render font

    _render:                c_renderer              # Renderer object
    _animations:            c_animations            # Animation object

    _is_hovered:            bool
    _is_typing:             bool
    _is_ctrl:               bool
    _is_password:           bool
    _is_holding:            bool

    _mouse_position:        vector
    _text_size:             vector

    _cursor_index:          vector
    _selection_position:    vector
    _selection_index:       vector

    _offset:                float

    _config:                text_input_config_t

    # endregion

    def __init__( self, parent: any, position: vector, size: vector, font: c_font, default_value: str = "", is_password: bool = False, config: text_input_config_t = None ):
        
        # Set config
        self._config = config is None and text_input_config_t( ) or config

        # Set parent
        self._parent = parent

        # Set position and size
        self._position  = position.copy( )
        self._size      = size.copy( )

        # Set default value
        self._input = default_value

        # Set font for render
        self._font = font

        # Is this password input ?!?
        self._is_password = is_password

        # Initialize complete attachment
        self.__init_attachment( )

        # Initialize animations of the widget
        self.__init_animations( )

        # Initialize default and first values for the widget 
        self.__init_bones( )

    # region : Initialization

    def __init_attachment( self ):
        
        self._render = self._parent.render( )


    def __init_animations( self ):

        # Create standalone animations handler
        self._animations = c_animations( )

        self._animations.prepare( "width",      0 )
        self._animations.prepare( "text_width", 0 )
        self._animations.prepare( "index_fade", 0 )
        self._animations.prepare( "typing",     0 )
        self._animations.prepare( "offset",     0 )


    def __init_bones( self ):
        
        self._relative_position = self._position.copy( )

        self._is_hovered    = False
        self._is_typing     = False
        self._is_ctrl       = False
        self._is_holding    = False

        self._mouse_position    = vector( )
        self._text_size         = vector( )

        self._cursor_index           = vector( 0, None )
        self._selection_position     = vector( None, None, 0 )
        self._selection_index        = vector( -1, -1, time.time( ) )

        self._offset = 0

    # endregion

    # region : Drawing

    def draw( self, fade: float ):
        
        # This thing will be a little bit complicated.
        # In here we want to avoid and minimize as possible the performance loss

        # Therefore, most of the operations we perform in a raw way here, without creating a lot of 
        # functions and etc

        if fade == 0:
            return

        # Do some updates
        self._animations.update( )
        self.__update_relative_position( )
        self.__update_selection( )

        # Get values to work with
        speed:          int     = self._config.speed
        pad:            int     = self._config.pad

        # Get texts based on configuration and events
        visible_text:   str = self.__get_visible_text( )
        cursor_text:    str = self.__get_cursor_text( )

        # Calculate the cursor text sizes
        vis_sizes:  vector = self._render.measure_text( self._font, visible_text )
        cur_sizes:  vector = self._render.measure_text( self._font, cursor_text )

        # Convert the clicked position into index
        if self._cursor_index.y is not None:
            self._cursor_index.x = self.__relative_to_index( self._cursor_index.y, visible_text )
            self._cursor_index.y = None

        show_cursor: bool = self._is_typing and ( self._selection_position.x is None and self._selection_position.y is None )

        # Animate the cursor index when typing and not
        index_fade:     float = self._animations.preform( "index_fade", show_cursor and 1 or 0, speed) * fade
        typing_fade:    float = self._animations.preform( "typing", self._is_typing and 1 or 0, speed ) * fade
        offset:         float = self._animations.preform( "offset", self._offset, speed, 1 )

        # Create clipping rect vectors
        start_clip: vector = vector( self._position.x + pad, self._position.y )
        end_clip:   vector = vector( start_clip.x + self._size.x, start_clip.y + self._size.y )

        self.__update_offset( start_clip, vector( end_clip.x, start_clip.x ), cur_sizes, vis_sizes )

        # Start the clip
        self._render.push_clip_rect( vector( start_clip.x - 1, start_clip.y ), vector( end_clip.x + 1, end_clip.y ), True )

        # Render everything here
        self.__draw_text( fade, start_clip, visible_text, offset )
        self.__draw_cursor( index_fade, start_clip, cur_sizes.x + offset )
        self.__draw_selection( typing_fade, start_clip, offset, visible_text )

        # Stop the clip
        self._render.pop_clip_rect( )

        # Animate the width after everything is done rendering
        correct_pad = pad * 2
        self._animations.preform( "width",      correct_pad + self._size.x, speed, 1 )
        self._animations.preform( "text_width", correct_pad + self._text_size.x, speed, 1 )


    def __update_relative_position( self ):
        parent_position:            vector  = self._parent.relative_position( )

        self._relative_position.x = parent_position.x + self._position.x
        self._relative_position.y = parent_position.y + self._position.y

    
    def __update_offset( self, position: vector, edges: vector, cursor_text_size: vector, visible_text_size: vector ):
        if not self._is_typing:
            return
        
        if (visible_text_size.x < self._size.x):
            self._offset = 0
            return
        
        pad: int = self._config.pad

        set_offset = position.x + self._offset + cursor_text_size.x + 1

        edges.x -= pad * 2
        edges.y += pad * 2

        if self.is_something_selected( ):

            if self._selection_position.z == 1:

                right_delta = edges.x - self._mouse_position.x
                left_delta = self._mouse_position.x - edges.y

                if right_delta < 10:
                    self._offset -= 1

                if left_delta < 10:
                    self._offset += 1

        else:
            # Right edge
            if set_offset > edges.x:
                self._offset -= set_offset - edges.x

            if ( set_offset - 1 ) < edges.y:
                self._offset += edges.y - ( set_offset - 1 )
            

        self._offset = math.clamp( self._offset, self._size.x - visible_text_size.x, 0 )

    
    def __update_selection( self ):
        
        if self._selection_position.z == 0:
            return

        value: float = self._mouse_position.x - ( self._relative_position.x + self._config.pad + self._offset )

        if self._selection_position.x is not None:
            self._selection_position.y = value
    

    def __draw_text( self, fade: float, position: vector, text: str, offset: float ):
        color_input:        color  = self._config.color_input
        self._text_size:    vector = self._render.measure_text( self._font, text )

        self._render.text( self._font, vector( position.x + offset, position.y + ( self._size.y - self._text_size.y ) / 2 ), color_input * fade, text )


    def __draw_cursor( self, fade: float, position: vector, offset: float ):

        if fade == 0:
            return

        color_theme: color = self._config.color_theme

        self._render.rect(
            vector( position.x + offset - 1, position.y + 2 ),
            vector( position.x + offset + 1, position.y + self._size.y - 2 ),
            color_theme * fade
        )

    
    def __draw_selection( self, fade: float, position: vector, offset: float, text: str ):

        if fade == 0:
            self._selection_position.x = None
            self._selection_position.y = None
            return
        
        if self._selection_position.x is None or self._selection_position.y is None:
            return
        
        start:  float = min( self._selection_position.x, self._selection_position.y ) 
        end:    float = max( self._selection_position.x, self._selection_position.y )

        self._selection_index.x = self.__relative_to_index( start, text )
        self._selection_index.y = self.__relative_to_index( end, text )

        if self._selection_position.z == 0 and self._selection_index.x == self._selection_index.y:
            self.__reset_selection( )
            return

        color_selection:    color   = self._config.color_selection
        seperate:           int     = self._config.seperate

        if self._selection_position.z == 1:

            self._render.neon(
                vector( position.x + offset + start, position.y + self._size.y - seperate ),
                vector( position.x + offset + end, position.y + self._size.y ),
                color_selection * fade,
                18,
                seperate / 2
            )

        else:
            start_text  = self._render.measure_text( self._font, text[ :self._selection_index.x ] ).x
            end_text    = self._render.measure_text( self._font, text[ :self._selection_index.y ] ).x

            self._render.neon(
                vector( position.x + offset + start_text, position.y + self._size.y - seperate ),
                vector( position.x + offset + end_text, position.y + self._size.y ),
                color_selection * fade,
                18,
                seperate / 2
            )


    def __get_visible_text( self ) -> str:
        return self._is_password and "*" * len( self._input ) or self._input
    

    def __get_cursor_text( self ) -> str:
        return self.__get_visible_text( )[ :self._cursor_index.x ]

    
    def __relative_to_index( self, relative_width: float, text: str ) -> int:
        
        # Credit - My friend
        # The use of https://github.com/BalazsJako/ImGuiColorTextEdit/blob/master/TextEditor.cpp#L324
        # logic is complete cancer since ImGui calculations for each char and whole text are diffrent...

        selected_index: int = 0
        length:         int = len( text )

        for i in range( length + 1 ):

            substring:  str     = text[ :i ]
            width:      float   = self._render.measure_text( self._font, substring ).x

            if width > relative_width:
                
                fixed_index:    int     = max( 0, i - 1 )
                prev_width:     float   = self._render.measure_text( self._font, text[ :fixed_index ] ).x

                if abs( width - relative_width ) < abs( prev_width - relative_width ):
                    selected_index = i
                else:
                    selected_index = fixed_index

                break

            else:
                selected_index = i

        return selected_index
    
    # endregion

    # region : Input handle

    # SOME IDEAS :
    # FIRST OF ALL, THE INPUT KINDA REMAINS THE SAME, EXCEPT FOR ADDING SELECTION
    # MOREOVER, THE OVERPADDING ON SIDES IS ONLY WHEN HOLDING/REPEAT ACTION IN GENERAL

    def event_mouse_position( self, event ):

        x = event( "x" )
        y = event( "y" )

        self._mouse_position.x = x
        self._mouse_position.y = y

        pad: int = self._config.pad * 2

        self._is_hovered = self._mouse_position.is_in_bounds( self._relative_position, self._size.x + pad, self._size.y )


    def event_mouse_input( self, event ):
        
        button = event( "button" )
        action = event( "action" )

        if button != glfw.MOUSE_BUTTON_LEFT:
            return

        value: float = self._mouse_position.x - ( self._relative_position.x + self._config.pad + self._offset )

        if self._is_hovered and action == glfw.PRESS:
            self._cursor_index.y = value

            self._selection_position.x = value
            self._selection_position.z = 1
            self._selection_index.z = time.time( )

            return

        if action == glfw.RELEASE and self._selection_position.x is not None:
            self._selection_position.y = value

            if ( time.time( ) - self._selection_index.z ) < 0.1:
                self.__reset_selection( )

            self._selection_position.z = 0

            return


    def event_char_input( self, event ):
        
        if not self._is_typing:
            return

        self.insert( chr( event( "char" ) ) )


    def event_keyboard_input( self, event ):
        
        if not self._is_typing:
            return

        key         = event( "key" )
        action      = event( "action" ) 

        self.__handle_ctrl( key, action )

        if action == glfw.PRESS:
            self.__handle_clipboard( key )
            return self.__handle_default_actions( key, False )

        if action == glfw.REPEAT:
            return self.__handle_default_actions( key, True )
    
    # endregion

    # region : Utilities

    def value( self, new_value: str = None ) -> str:

        if new_value is None:
            return self._input
        
        self._input = new_value
        return new_value
    

    def is_typing( self, new_value: bool = None ) -> bool:

        if new_value is None:
            return self._is_typing
        
        self._is_typing = new_value
        return new_value
    

    def position( self, new_value: vector = None ) -> vector:

        if new_value is None:
            return self._position
        
        self._position = new_value.copy( )
        return new_value
    

    def size( self, new_value: vector = None ) -> vector:

        if new_value is None:
            return self._size
        
        self._size = new_value.copy( )
        return new_value


    def fixed_size( self ) -> vector:

        return vector( self._animations.value( "width" ), self._size.y )
    

    def text_width( self ) -> float:

        return self._animations.value( "text_width" )
    

    def is_hovered( self ) -> bool:

        return self._is_hovered
    

    def insert( self, text: str ):

        self.__remove_selected( )

        self._input             = self._input[ :self._cursor_index.x ] + text + self._input[ self._cursor_index.x: ]
        self._cursor_index.x   += len( text )

    
    def pop( self ):

        if self.is_something_selected( ):
            self._input             = self._input[ :self._selection_index.x ] + self._input[ self._selection_index.y: ]
            self._cursor_index.x    = ( self._selection_index.x )

            self.__reset_selection( )
            return

        if self._cursor_index.x == 0:
            return

        char: str = self._input[ self._cursor_index.x - 1 ]

        self._input             = self._input[ :self._cursor_index.x - 1 ] + self._input[ self._cursor_index.x: ]
        self._cursor_index.x   -= 1

        return char


    def __handle_ctrl( self, key: int, action: int ):
        
        if key != glfw.KEY_LEFT_CONTROL and key != glfw.KEY_RIGHT_CONTROL:
            return

        if action == glfw.PRESS:
            self._is_ctrl = True

        if action == glfw.RELEASE:
            self._is_ctrl = False


    def __handle_default_actions( self, key: int, is_repeat: bool ):

        # Remove action
        if key == glfw.KEY_BACKSPACE:
            return self.pop( )

        # Move index left
        if key == glfw.KEY_LEFT and self._cursor_index.x > 0:
            self._cursor_index.x -= 1
            return

        # Move index right
        if key == glfw.KEY_RIGHT and self._cursor_index.x < len( self._input ):
            self._cursor_index.x += 1
            return

    
    def __handle_clipboard( self, key: int ):

        if not self._is_ctrl:
            return

        if key == glfw.KEY_V:
            result: bytes   = glfw.get_clipboard_string( None )
            result: str     = result.decode( )

            return self.insert( result )
            
        if key == glfw.KEY_C:
            result: str = self.get_selection_string( )

            if result != "":
                glfw.set_clipboard_string( None, result )
        

    def __reset_selection( self ):
        self._selection_index.x = -1
        self._selection_index.y = -1

        self._selection_position.x = None
        self._selection_position.y = None

    
    def get_selection_string( self ) -> str:
        if self._selection_index.x == -1 or self._selection_index.y == -1:
            return ""
        
        return self._input[ self._selection_index.x:self._selection_index.y ]

    
    def is_something_selected( self ):
        return self._selection_index.x != -1 and self._selection_index.y != -1
    

    def __remove_selected( self ):

        if not self.is_something_selected( ):
            return
        
        self._input             = self._input[ :self._selection_index.x ] + self._input[ self._selection_index.y: ]
        self._cursor_index.x    = ( self._selection_index.x )

        self.__reset_selection( )

    # endregion


class c_text_input:

    # region : Protected attributes

    _parent:                any                     # Parent object - c_scene / c_window
    _index:                 int                     # Widget index

    _position:              vector                  # Relative to parent position
    _relative_position:     vector                  # Relative to application position

    _height:                int                     # Height of the text input ( in pixels )

    _handle:                c_single_input_logic    # Logic of the text input 

    _render:                c_renderer              # Renderer object
    _animations:            c_animations            # Animation object

    _font:                  c_font                  # Font object
    _icon:                  c_image                 # Icon object
    _text:                  str                     # Label value

    _is_visibe:             bool                    # Is this widget visible
    _is_disabled:           bool                    # Is this widget disabled

    _is_hovered:            bool                    # Is user hovered the text box widget
    _should_type:           bool                    # Should the text input start handle

    _mouse_position:        vector                  # Mouse position
    _text_size:             vector                  # Label text size
    
    _config:                text_input_config_t     # Config for text input

    # endregion

    def __init__( self, parent: any, position: vector, height: int, size_of_input: vector, font: c_font, icon: c_image, text: str, default_value: str = "", is_password: bool = False, config: text_input_config_t = None ):
        
        # Set config
        self._config = config is None and text_input_config_t( ) or config

        # Set parent
        self._parent = parent

        # Set position and sizes
        self._position  = position.copy( )
        self._height    = height

        # Set display information
        self._font = font
        self._icon = icon
        self._text = text

        # Create text logic handle
        self._handle = c_single_input_logic( self._parent, position, size_of_input, font, default_value, is_password, self._config )

        # Initialize attachment to parent
        self.__init_attachment( )

        # Initialize animations of the widget
        self.__init_animations( )

        # Initialize default and first values for the widget 
        self.__init_bones( )

    # region : Initialization

    def __init_attachment( self ):
        
        # Get renderer
        self._render    = self._parent.render( )

        # Attach widget to parent
        self._index     = self._parent.attach_element( self )

        # Attach this widget's events handlers to parent
        this_widget = f"text_input::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_widget )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,           this_widget )
        self._parent.set_event( "char_input",       self.__event_char_input,            this_widget )
        self._parent.set_event( "keyboard_input",   self.__event_keyboard_input,        this_widget )


    def __init_animations( self ):

        # Create standalone animations handler
        self._animations = c_animations( )

        # Preallocate animations values
        self._animations.prepare( "fade",               0 ) 
        self._animations.prepare( "background_width",   0 )

        self._animations.prepare( "hover",  0 )
        self._animations.prepare( "typing", 0 )


        self._animations.prepare( "label",      0 )
        self._animations.prepare( "seperate",   0 )


    def __init_bones( self ):
        
        # At first, copy the position and set as relative vector
        self._relative_position = self._position.copy( )

        # Set first values for specific behavior
        self._is_visibe     = True
        self._is_disabled   = False

        # Set first values for input handle
        self._is_hovered    = False
        self._should_type   = False

        # Set first some empty vectors
        self._mouse_position    = vector( )
        self._text_size         = vector( )


    # endregion

    # region : Drawing

    def draw( self, fade: float ):
        
        # Perform some calculations before drawing
        self.__perform_calculations( )
        self.__perform_animations( )

        fade = self._animations.value( "fade" ) * fade
        if fade == 0:
            return

        # Draw background
        self.__draw_background( fade )

        # Draw input
        self.__draw_input( fade )


    def __perform_calculations( self ):
        
        pad:        int = self._config.pad
        seperate:   int = self._config.seperate

        parent_position:            vector  = self._parent.relative_position( )
        self._relative_position:    vector  = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

        self._text_size:            vector  = self._render.measure_text( self._font, self._text )

        self._handle.position( 
            vector(
                self._position.x + pad * 3 + self._icon.size( ).x + seperate + self._text_size.x,
                self._position.y + ( self._height - self._handle.fixed_size( ).y ) / 2
            )
        )

        self._handle.is_typing( self._should_type )
        

    def __perform_animations( self ):
        
        self._animations.update( )

        seperate:   int     = self._config.seperate
        speed:      int     = self._config.speed
        pad:        int     = self._config.pad

        if not self._is_visibe:
            fade: float = self._animations.preform( "fade", 0, speed )
        else:
            fade: float = self._animations.preform( "fade", self._is_disabled and 0.3 or 1, speed )

        if fade == 0:
            return
        
        hover_fade:     float = self._animations.preform( "hover",  self._is_hovered and 1 or 0, speed )
        typing_fade:    float = self._animations.preform( "typing", self._should_type and 1 or 0, speed )

        if self._should_type:
            self._animations.preform( "label", 0.7, speed )
            self._animations.preform( "seperate", ( self._height - 10 ) / 2, speed )
        else:
            self._animations.preform( "label", self._is_hovered and 0.5 or 0.3, speed )
            
            seperate_remove = self._is_hovered and 15 or 20
            self._animations.preform( "seperate", ( self._height - seperate_remove ) / 2, speed )


        if self._handle.is_typing( ):
            input_width: float = self._handle.fixed_size( ).x - pad
        
        else:
            input_width: float = min( self._handle.text_width( ), self._handle.fixed_size( ).x ) - pad

        if self._handle.value( ) != "":
            typing_fade = 1

        fixed_width: int = pad * 4 + self._icon.size( ).x + seperate + self._text_size.x
        self._animations.preform( "background_width", fixed_width + max( pad * hover_fade, input_width * typing_fade ), speed * 2 )


    def __draw_background( self, fade: float ):
        
        pad:        int = self._config.pad
        seperate:   int = self._config.seperate
        roundness:  int = self._config.roundness


        color_background:   color = self._config.color_background
        color_shadow:       color = self._config.color_shadow
        color_theme:        color = self._config.color_theme

        color_icon:         color = self._config.color_icon
        color_label:        color = self._config.color_label

        icon_size:  vector = self._icon.size( )

        icon_position:      vector = vector( self._position.x + pad, self._position.y + ( self._height - icon_size.y ) / 2 )
        seperate_position:  vector = vector( icon_position.x + icon_size.x + pad, self._position.y + self._height / 2 )
        label_position:     vector = vector( seperate_position.x + seperate + pad, self._position.y + ( self._height - self._text_size.y ) / 2 )

        label_fade:     float = self._animations.value( "label" ) * fade
        seperate_fade:  float = self._animations.value( "seperate" )
        hover_fade:     float = self._animations.value( "hover" )
        typing_fade:    float = self._animations.value( "typing" )

        positioned_size: vector  = vector( self._position.x + self._animations.value( "background_width" ), self._position.y + self._height )

        # Draw the drop shadow first
        self._render.shadow(
            self._position,
            positioned_size,
            color_shadow.linear( color_theme, hover_fade ),
            fade,
            20,
            roundness
        )
        
        # Draw the background
        self._render.rect(
            self._position,
            positioned_size,
            color_background * fade,
            roundness
        )

        # Create cliprect to avoid glow escaping out of scope of the widget
        self._render.push_clip_rect( self._position, positioned_size, True )

        self._render.image( self._icon, icon_position, color_icon.linear( color_theme, typing_fade ) * label_fade )

        self._render.neon( vector( seperate_position.x, seperate_position.y - seperate_fade ), vector( seperate_position.x + seperate, seperate_position.y + seperate_fade ), color_theme * fade, 18, seperate / 2 )

        self._render.text( self._font, label_position, color_label * label_fade, self._text )

        self._render.pop_clip_rect( )


    def __draw_input( self, fade: float ):
        
        self._render.push_clip_rect( self._position, vector( self._position.x + self._animations.value( "background_width" ), self._position.y + self._height ), True )

        self._handle.draw( fade )

        self._render.pop_clip_rect( )

    # endregion

    # region : Input handle

    def __event_mouse_position( self, event ) -> None:

        if not self._is_visibe or self._is_disabled:
            return

        self._handle.event_mouse_position( event )

        self._mouse_position.x  = event( "x" )
        self._mouse_position.y  = event( "y" )

        width                   = self._animations.value( "background_width" )

        if self._mouse_position.is_in_bounds( self._relative_position, width, self._height ):
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:
            if self._parent.is_this_active( self._index ) and not self._should_type:
                self._parent.release_handle( self._index )

            self._is_hovered = False
            

    def __event_mouse_input( self, event ) -> None:

        if not self._is_visibe or self._is_disabled:
            return

        self._handle.event_mouse_input( event )

        button = event( "button" )
        action = event( "action" )

        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self._should_type = self._is_hovered


    def __event_char_input( self, event ) -> None:

        if not self._is_visibe or self._is_disabled:
            return

        self._handle.event_char_input( event )


    def __event_keyboard_input( self, event ) -> None:
        
        if not self._is_visibe or self._is_disabled:
            return
        
        key         = event( "key" )
        action      = event( "action" ) 

        if action == glfw.PRESS:
            if key == glfw.KEY_ENTER or key == glfw.KEY_ESCAPE:
                self._should_type = False

        self._handle.event_keyboard_input( event )

    # endregion

    # region : Utilities

    def position( self, new_value: vector = None ) -> vector:

        if new_value is None:
            return self._position
        
        self._position = new_value.copy( )
        return new_value
    

    def size( self ) -> vector:

        return vector( self._animations.value( "background_width" ), self._height )

    
    def visible( self, new_value: bool = None ) -> bool:

        if new_value is None:
            return self._is_visibe

        self._is_visibe = new_value
        return new_value

    
    def get( self ) -> str:

        return self._handle.value( )

    # endregion