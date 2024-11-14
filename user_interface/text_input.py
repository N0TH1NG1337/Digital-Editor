# User Interface. Widget -> Text input .py

import OpenGL.GL as gl
import glfw

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.math     import  math
from utilities.wrappers import  safe_call
from utilities.image    import  c_image
from utilities.font     import  c_font
from utilities.event    import  c_event

from user_interface.render      import c_renderer
from user_interface.animation   import c_animations
from user_interface.scene       import c_scene

class c_signle_input_logic:

    # Logic class for single line text input
    # NOTE ! This is not full render class. rather a main idea behind all the calculations for inputs
    # NOTE ! This cannot be used for multi line text input since here calculations are only for 1 line.

    # WARNING ! Be careful with _size because it may clip out some parts of the text.
    # WARNING ! Will fix later, but dont even try to change the x axis of _position since it will break the input offset

    _position:          vector
    _size:              vector

    _font:              c_font

    _render:            c_renderer
    _animations:        c_animations

    _is_background:     bool

    _is_hovered:        bool
    _is_typing:         bool
    _is_ctrl:           bool
    _is_password:       bool

    _mouse_position:    vector
    _text_size:         vector
    _click_delta:       int
    _input_index:       int
    _input_offset:      float
    _set_end:           bool

    _config:            dict

    def __init__( self, font: c_font, size: vector, is_password: bool, default_input: str = "", should_draw_back: bool = False ):
        
        self._font              = font
        
        self._size              = size.copy( )

        self._is_password       = is_password

        self._input             = default_input
        self._is_background     = should_draw_back


    def setup( self, parent: any, position: vector ):
        # Complete the setup

        # Get render instance
        self._render       = parent.render( )

        # Create animations handler
        self._animations   = c_animations( )

        # Set position
        self._position     = position

        # Find config
        self.__init_config( parent )

        # Finish and set up all inside class values
        self.__on_init( )


    def __on_init( self ):
        # Called on class set up

        self._is_hovered        = False
        self._is_typing         = False
        self._is_ctrl           = False
        self._set_end           = False

        self._mouse_position    = vector( )
        self._text_size         = vector( )

        self._click_delta       = None
        self._input_index       = 0

        self._input_offset      = 0

        if self._is_background:
            self._animations.prepare( "Add", 0 )

    def __init_config( self, parent ):
        """
            Set up config search
        """

        # Since in out user interface, we can have like a sub parent and more,
        # We dont know exactly how much parents we have before but in the end, we will receive the c_application object

        # Receive config information
        first_parent = parent
        while str( type( first_parent ) ).find( "c_application" ) == -1:
            first_parent = first_parent.parent( )
        
        self._config = first_parent.config( "Text Input" )

    # region : Access values

    def get( self ) -> str:
        # Returns current value that written.

        return self._input
    
    def set( self, value: str ) -> None:
        self._input = value
        self._input_index = len( value )
        self._input_offset = 0

        self._set_end = True

    
    def is_typing( self, new_value: bool = None ) -> bool | None:

        if new_value is None:
            return self._is_typing
        
        self._is_typing = new_value

    def position( self, new_value: vector = None ) -> vector | None:

        if new_value is None:
            return self._position
        
        self._position = new_value.copy( )

    def size( self, new_value: vector = None ) -> vector | None:

        if new_value is None:
            return self._size
        
        self._size = new_value.copy( )

    def correct_size( self ) -> vector:

        pad = self._config[ "pad" ] * 2

        return self._size + pad

    def is_hovered( self ) -> bool:

        return self._is_hovered
    
    def config( self, value: str ) -> any:

        return self._config[ value ] 

    # endregion

    # region : Draw

    def draw( self, fade: float ):

        self._animations.update( )

        pad                     = self._config[ "pad" ]

        start_clip              = self._position + pad
        end_clip                = start_clip + self._size

        correct_input           = self.correct_text( self._input )
        correct_input_by_index  = self.correct_text( self._input[ :self._input_index ] )

        correct_size            = self._render.measure_text( self._font, correct_input )
        correct_by_index_size   = self._render.measure_text( self._font, correct_input_by_index )

        self.__preform_set_index( correct_input )
        self.__preform_correct_offset( start_clip, vector( end_clip.x, start_clip.x ), correct_by_index_size )

        self.__draw_back( fade, self._position, self._position + self._size + ( pad * 2 ) )

        self._render.push_clip_rect( start_clip, start_clip + self._size )

        self.__draw_text( fade, start_clip, correct_input, correct_size )
        self.__draw_index( fade, start_clip, correct_by_index_size )

        self._render.pop_clip_rect( )


    def __draw_back( self, fade: float, start: vector, end: vector ):
        if not self._is_background:
            return
        
        add         = self._animations.preform( "Add", self._is_hovered and 1 or 0, self._config[ "speed" ] )

        color       = self._config[ "color_raw_back" ]
        roundness   = self._config[ "rounding" ]

        self._render.rect( start - add, end + add, color * fade, roundness )


    def __draw_text( self, fade: float, start_position: vector, text: str, text_size: vector ):

        color_value = self._config[ "color_value" ]

        self._render.text(
            self._font,
            vector(
                start_position.x + self._input_offset,
                start_position.y + ( self._size.y - text_size.y ) / 2
            ),
            color_value * fade,
            text
        )
    

    def __draw_index( self, fade: float, start_position: vector, text_size: vector ):

        if not self._is_typing:
            return
        
        color_index = self._config[ "color_index" ]

        self._render.rect( 
            vector( start_position.x + self._input_offset + text_size.x - 1, start_position.y + 2 ),
            vector( start_position.x + self._input_offset + text_size.x + 1, start_position.y + self._size.y - 1 ),
            color_index * fade
        )


    def correct_text( self , text: str ) -> str:
        # If is password is True, conver the text into password type

        if self._is_password:
            return "*" * len( text )
        
        return text
    

    def __preform_correct_offset( self, start_position: vector, end_clip: vector, text_size: vector ):

        if not self._is_typing and not self._set_end:
            return
        
        set_offset = start_position.x + self._input_offset + text_size.x + 1

        if set_offset > end_clip.x:
            self._input_offset -=  set_offset - end_clip.x

        if ( set_offset - 2 ) < end_clip.y:
            self._input_offset +=  end_clip.y - ( set_offset - 2 )

        self._set_end = False


    def __preform_set_index( self, text: str ):

        if not self._is_typing:
            return

        if self._click_delta == None:
            return
        
        selected_index: int     = 0
        input_width:    float   = 0.0

        while selected_index < len( text ):
            width = self._render.measure_text( self._font, text[ selected_index ] ).x

            if input_width + ( width * 0.5 ) > self._click_delta:
                break

            input_width += width
            selected_index += 1

        self._click_delta = None
        self._input_index = selected_index
    
    # endregion

    # region : Input 

    def insert( self, text: str  ) -> None:
        # Inserts specific text into selected index

        self._input = self._input[ :self._input_index ] + text + self._input[ self._input_index: ]
        self._input_index += len( text )


    def pop( self ) -> str | None:
        # Pops char from input in selected index

        if self._input_index == 0:
            return None
        
        char = self._input[ self._input_index - 1 ]

        self._input = self._input[ :self._input_index - 1 ] + self._input[ self._input_index: ]
        self._input_index -= 1

        return char
    

    def event_mouse_position( self, event ) -> None:
        # Mouse Position change callback

        x = event( "x" )
        y = event( "y" )

        # Just update. There is no need to create new object
        self._mouse_position.x = x
        self._mouse_position.y = y

        correct_pad = self._config[ "pad" ] * 2
        self._is_hovered = self._mouse_position.is_in_bounds( self._position, self._size.x + correct_pad, self._size.y + correct_pad )


    def event_mouse_input( self, event ) -> None:
        # Mouse buttons input callback
        
        button = event( "button" )
        action = event( "action" )

        if button != glfw.MOUSE_BUTTON_LEFT or action != glfw.PRESS:
            return

        if not self._is_hovered:
            return

        #self._click_position = self._mouse_position.copy( )
        self._click_delta = self._mouse_position.x - ( self._position.x + self._config[ "pad" ] + self._input_offset )


    def event_char_input( self, event ) -> None:
        # Captures what char was pressed

        if not self._is_typing:
            return
        
        char = chr( event( "char" ) )

        self.insert( char )


    def event_keyboard_input( self, event ) -> None:
        # General keyboard input handle

        if not self._is_typing:
            return
        
        key         = event( "key" )
        action      = event( "action" ) 

        self.__ctrl_handle( key, action )

        if action == glfw.PRESS:
            self.__repeat_handle( key )

            self.__paste_handle( key )

            if key == glfw.KEY_ENTER:
                self._is_typing = False

        if action == glfw.REPEAT:
            self.__repeat_handle( key )


    def __ctrl_handle( self, key, action ):
        # Exception capture for Ctrl key input
        
        if key != glfw.KEY_LEFT_CONTROL and key != glfw.KEY_RIGHT_CONTROL:
            return

        if action == glfw.PRESS:
            self._is_ctrl = True

        if action == glfw.RELEASE:
            self._is_ctrl = False


    def __repeat_handle( self, key ):
        # Executable input handle for PRESS and REPEAT calls

        # Remove
        if key == glfw.KEY_BACKSPACE:
            self.pop( )

        # Move index left
        if key == glfw.KEY_LEFT and self._input_index > 0:
            self._input_index -= 1

        # Move index right
        if key == glfw.KEY_RIGHT and self._input_index < len( self._input ):
            self._input_index += 1


    def __paste_handle( self, key ):
        # Handle text paste event

        if not self._is_ctrl:
            return

        if key != glfw.KEY_V:
            return

        result: bytes = glfw.get_clipboard_string( None )
        result: str = result.decode( )

        self.insert(result)

    # endregion


class c_text_input:

    _parent:            c_scene
    _index:             int

    _position:          vector
    _height:            int

    _handle:            c_signle_input_logic

    _render:            c_renderer
    _animations:        c_animations

    _font:              c_font
    _icon:              c_image
    _text:              str

    _padding:           int     # How much the image is padded from the top corner,
    # Use to set simetric value for text 

    _is_hovered:        bool
    _should_type:       bool

    _mouse_position:    vector
    _text_size:         vector
    _open_width:        int
    _close_width:       int

    _config:            dict

    def __init__(
            self,
            parent:         c_scene,    # c_scene object
            position:       vector,     # relative position in scene
            height:         int,        # height of input
            size_of_input:  vector,     # size of text field
            is_password:    bool,       # is receiving password
            icon:           c_image,    # icon for text input
            font:           c_font,     # font for text input
            text:           str         # text display while value is None
        ):
        
        # Constructor

        self._parent = parent
        self._position = position.copy( )
        self._height = height

        self._icon = icon
        self._font = font
        self._text = text

        self.__init_config( )

        self._handle = c_signle_input_logic( self._font, size_of_input, is_password, "", False )

        self._padding = ( self._height - self._icon.size( ).x ) / 2

        self._handle.setup( self._parent, vector( ) )

        # Complete the set up of button object
        # Calculate the input it self position
        handle_position_x = ( self._position.x + self._height + self._padding + self._config[ "seperator" ] )
        handle_position_y = ( self._position.y + ( self._height - self._handle.correct_size( ).y ) / 2 )

        self._handle.position( vector( handle_position_x, handle_position_y ) )

        self.__attach( )
        self.__on_init( )

    
    def __attach( self ):
        # Attach current button to scene

        self._index = self._parent.attach_element( self )

        this_id = f"TextInput::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,            this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,               this_id )
        self._parent.set_event( "char_input",       self._handle.event_char_input,          this_id )
        self._parent.set_event( "keyboard_input",   self._handle.event_keyboard_input,      this_id )

    
    def __on_init( self ):

        self._render            = self._parent.render( )
        self._animations        = c_animations( )

        self._is_hovered        = False
        self._should_type       = False
        self._mouse_position    = vector( )
        self._text_size         = vector( )

        self._open_width        = 0
        self._close_width       = 0

        self._animations.prepare( "Add",        0 )
        self._animations.prepare( "Seperate",   0 )
        self._animations.prepare( "ShowText",   1 )
        self._animations.prepare( "Width",      self._height )


    def __init_config( self ):
        """
            Set up config search
        """

        # Since in out user interface, we can have like a sub parent and more,
        # We dont know exactly how much parents we have before but in the end, we will receive the c_application object

        # Receive config information
        first_parent = self._parent
        while str( type( first_parent ) ).find( "c_application" ) == -1:
            first_parent = first_parent.parent( )
        
        self._config = first_parent.config( "Text Input" )

    # region : Draw

    def draw( self, fade: float ):

        self.__preform_calculations( )

        self.__draw_back( fade )
        self.__draw_icon_and_text( fade )

        self.__draw_input( fade )

    
    def __draw_back( self, fade: float ):

        width           = self._animations.value( "Width" )
        add             = self._animations.value( "Add" )
        seperate        = self._animations.value( "Seperate" )

        color_back      = self._config[ "color_back" ]
        color_seperate  = self._config[ "color_seperate" ]
        rounding        = self._config[ "rounding" ]
        seperate_width  = self._config[ "seperator" ]
        
        start_vector    = self._position - add
        end_vector      = self._position + add + vector( width, self._height )

        # Background
        self._render.rect( 
            start_vector, 
            end_vector,
            color_back * fade,
            rounding
        )

        # Seperator
        self._render.rect( 
            self._position + vector( self._height, self._height / 2 - seperate ),
            self._position + vector( self._height + seperate_width, self._height / 2 + seperate ),
            color_seperate * fade,
            seperate_width / 4
        )

    
    def __draw_icon_and_text( self, fade: float ):
        
        show_text               = self._animations.value( "ShowText" )

        seperate_width: int     = self._config[ "seperator" ]
        color_icon:     color   = self._config[ "color_icon" ]
        color_text:     color   = self._config[ "color_text" ]

        self._render.image(
            self._icon,
            self._position + self._height / 2 - self._icon.size( ) / 2,
            color_icon * fade
        )

        if show_text > 0:
            text_position = vector(
                self._position.x + self._height + seperate_width + self._padding,
                self._position.y + ( self._height - self._text_size.y ) / 2
            )
            self._render.text( self._font, text_position, color_text * show_text * fade , self._text )


    def __draw_input( self, fade: float ):

        show_text = self._animations.value( "ShowText" )
        show_text = abs( show_text - 1 )    # Reverse the value

        self._handle.draw( fade )
    

    def __preform_calculations( self ):
        self._animations.update( )

        seperate_width      = self._config[ "seperator" ]
        speed               = self._config[ "speed" ]

        self._text_size     = self._render.measure_text( self._font, self._text )

        regular             = self._height + self._padding * 2 + seperate_width

        self._close_width   = regular + self._text_size.x
        self._open_width    = regular + self._handle.correct_size( ).x

        self._animations.preform( "Add", (self._is_hovered and not self._should_type) and 2 or 0, speed )
        
        if self._should_type:

            self._animations.preform( "Seperate",   ( self._height - 10 ) / 2 ,     speed )
        else:

            self._animations.preform( "Seperate",   10,                             speed )


        if self._should_type or self._handle.get( ) != "":

            self._animations.preform( "Width",      self._open_width ,      speed, 0.5 )
            self._animations.preform( "ShowText",   0,                      speed )

        else:

            self._animations.preform( "ShowText",   1,                      speed )
            self._animations.preform( "Width",      self._close_width,      speed, 0.5 )

        self._handle.is_typing( self._should_type )

    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        # Mouse Position change callback

        self._handle.event_mouse_position( event )

        self._mouse_position.x  = event( "x" )
        self._mouse_position.y  = event( "y" )

        width                   = self._animations.value( "Width" )

        if self._mouse_position.is_in_bounds( self._position, width, self._height ):

            self._is_hovered = self._parent.try_to_get_handle( self._index )
        else:
            
            if self._parent.is_this_active( self._index ) and not self._should_type:
                self._parent.release_handle( self._index )

            self._is_hovered = False
        
    def __event_mouse_input( self, event ) -> None:
        # Mouse buttons input callback
        
        self._handle.event_mouse_input( event )

        button = event( "button" )
        action = event( "action" )

        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self._should_type = self._is_hovered      

    # endregion

    # region : Access 

    def get( self ) -> str:

        return self._handle.get( )
    
    def position( self, new_value: vector = None ) -> vector | None:

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

    # endregion