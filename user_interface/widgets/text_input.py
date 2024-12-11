"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Text Input

    description : Text input classes
"""

import glfw

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
    speed:          int     = 10
    pad:            int     = 10
    seperate:       int     = 4

    input_color:    color   = color( )
    index_color:    color   = color( 150, 150, 255 ) # ( 150, 150, 255 )
    image_color:    color   = color( )
    text_color:     color   = color( )
    seperate_color: color   = color( 150, 150, 255 ) # ( 150, 150, 255 )


class c_single_input_logic:

    # Logic class for single line text input
    # NOTE ! This is not full render class. rather a main idea behind all the calculations for inputs
    # NOTE ! This cannot be used for multi line text input since here calculations are only for 1 line.

    _parent:                any

    _position:              vector
    _relative_position:     vector          # Relative position on screen
    _size:                  vector
    
    _input:                 str             # Actual value
    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _is_hovered:            bool
    _is_typing:             bool
    _is_ctrl:               bool
    _is_password:           bool

    _mouse_position:        vector
    _text_size:             vector
    _click_delta:           int
    _input_index:           int
    _input_offset:          float
    _set_end:               bool

    _config:                text_input_config_t

    # region : Initialize logic

    def __init__( self, parent: any, position: vector, font: c_font, size: vector, is_password: bool = False, default_input: str = "", config: text_input_config_t = None ):
        """
            Default constructor for text input logic.

            Receive :
            - parent                    - Parent object that is the widget with this logic is attached.
            - position                  - Input position
            - font                      - Rendered text font
            - size                      - Input box size. (not including pads)
            - is_password [optional]    - Is input ment for password
            - default_value [optional]  - Start value inside the input
            - config [optional]         - Config of text input

            Returns :   Logic object
        """

        self._font = font
        self._size = size.copy( )

        self._is_password   = is_password
        self._input         = default_input

        self._parent    = parent
        self._position  = position.copy( )

        self._render    = self._parent.render( )

        self._config    = config is None and text_input_config_t( ) or config

        self.__initialize_animations( )
        self.__initialize_default_values( )
    

    def __initialize_animations( self ):
        """
            Setup animations for logic.

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Index",          0 )
        self._animations.prepare( "InputOffset",    0 )

    
    def __initialize_default_values( self ):
        """
            Initialize default values for logic.

            Receive :   None

            Returns :   None
        """ 

        self._relative_position = vector( )

        self._is_hovered        = False
        self._is_typing         = False
        self._is_ctrl           = False
        self._set_end           = False

        self._mouse_position    = vector( )
        self._text_size         = vector( )

        self._click_delta       = None
        self._input_index       = 0

        self._input_offset      = 0

    # endregion

    # region : Access data

    def get( self ) -> str:
        """
            Receive the input value. 

            Receive :   None

            Returns :   String value
        """

        return self._input
    

    def set( self, value: str ) -> None:
        """
            Set specific value for the input.

            Receive :   
            - value - New value to insert

            Returns :   None
        """

        self._input         = value
        self._input_index   = len( value )
        self._input_offset  = 0

        self._set_end       = True

    
    def is_typing( self, new_value: bool = None ) -> bool | None:
        """
            Is/Set the user typing in this input.

            Receive :   
            - new_value [optional] - Is the user typing ?

            Returns :   Result or None
        """

        if new_value is None:
            return self._is_typing
        
        self._is_typing = new_value


    def position( self, new_value: vector = None ) -> vector | None:
        """
            Get/Update the position on this input in the parent.

            Receive : 
            - new_value [optional] - New position

            Returns :   Vector or None
        """

        if new_value is None:
            return self._position
        
        self._position = new_value.copy( )


    def size( self, new_value: vector = None ) -> vector | None:
        """
            Get/Update the size of this input in the parent.

            Receive : 
            - new_value [optional] - New size

            Returns :   Vector or None
        """

        if new_value is None:
            return self._size
        
        self._size = new_value.copy( )

    
    def correct_size( self ) -> vector:
        """
            Get correct size of this input.

            Receive :   None

            Returns :   Vector
        """

        pad = self._config.pad * 2

        return self._size + pad
    

    def is_hovered( self ) -> bool:
        """
            Is the user hovered over this input.

            Receive :   None

            Returns :   Result
        """

        return self._is_hovered

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        """
            Main draw function of the input.

            Receive : 
            - fade - Parent / Widget fade factor

            Returns :   None
        """

        self._animations.update( )

        speed:                  int     = self._config.speed

        index_fade:             float   = self._animations.preform( "Index", self._is_typing and 1 or 0, speed ) * fade
        input_offset:           float   = self._animations.preform( "InputOffset", self._input_offset, speed, 1 )

        parent_position:        vector  = self._parent.relative_position( )
        self._relative_position         = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

        pad:                    int     = self._config.pad
        start_clip:             vector  = self._position + pad
        end_clip:               vector  = start_clip + self._size

        correct_input:          str     = self.correct_text( self._input )
        correct_input_by_index: str     = self.correct_text( self._input[ :self._input_index ] )

        correct_size:           vector  = self._render.measure_text( self._font, correct_input )
        correct_by_index_size:  vector  = self._render.measure_text( self._font, correct_input_by_index )

        self.__preform_set_index( correct_input )
        self.__preform_correct_offset( start_clip, vector( end_clip.x, start_clip.x ), correct_by_index_size )

        self._render.push_clip_rect( start_clip, end_clip, True )

        self.__draw_text( fade, start_clip, correct_input, correct_size, input_offset )
        self.__draw_index( index_fade, start_clip, correct_by_index_size, input_offset )

        self._render.pop_clip_rect( )

    
    def __draw_text( self, fade: float, start_position: vector, text: str, text_size: vector, input_offset: float ):
        """
            Draw Input text.

            Receive :
            - fade              - Parent / Widget fade factor
            - start_position    - Start position of the text
            - text              - The text to render
            - text_size         - Text size
            - input_offset      - Position offset

            Returns :   None
        """

        input_color: color  = self._config.input_color

        self._render.text(
            self._font,
            vector( 
                start_position.x + input_offset,
                start_position.y + ( self._size.y - text_size.y ) / 2
            ),
            input_color * fade,
            text
        )

    
    def __draw_index( self, fade: float, start_position: vector, text_size: vector, input_offset: float ):
        """
            Draw input index

            Receive :
            - fade              - Parent / Widget fade factor
            - start_position    - Start position of the text
            - text              - The text to render
            - text_size         - Text size
            - input_offset      - Position offset

            Returns :   None
        """

        if fade == 0:
            return
        
        index_color = self._config.index_color

        self._render.rect(
            vector( start_position.x + input_offset + text_size.x - 1, start_position.y + 2 ),
            vector( start_position.x + input_offset + text_size.x + 1, start_position.y + self._size.y - 2 ),
            index_color * fade
        )


    def __preform_correct_offset( self, start_position: vector, end_clip: vector, text_size: vector ):
        """
            Correct the text offset based on the index.

            Receive : 
            - start_position    - Start position of the clip
            - end_clip          - Vector( Left side, Right side )
            - text_size         - Corrected text size
        """

        if not self._is_typing and not self._set_end:
            return
        
        set_offset = start_position.x + self._input_offset + text_size.x + 1

        if set_offset > end_clip.x:
            self._input_offset -=  set_offset - end_clip.x

        if ( set_offset - 2 ) < end_clip.y:
            self._input_offset +=  end_clip.y - ( set_offset - 2 )

        self._set_end = False


    def __preform_set_index( self, text: str ):
        """
            Determine where the user pressed with the mouse.

            Receive : 
            - text - Corrected text to check

            Returns :   None
        """

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

            input_width     += width
            selected_index  += 1

        self._click_delta = None
        self._input_index = selected_index

    # endregion

    # region : Input

    def insert( self, text: str ) -> None:
        """
            Inserts specific text into selected index.

            Receive : 
            - text - Text to insert

            Returns :   None
        """

        self._input = self._input[ :self._input_index ] + text + self._input[ self._input_index: ]
        self._input_index += len( text )


    def pop( self ) -> str | None:
        """
            Pops char from input in selected index.

            Receive :   None

            Returns :   Char or None
        """

        if self._input_index == 0:
            return None
        
        char                = self._input[ self._input_index - 1 ]

        self._input         = self._input[ :self._input_index - 1 ] + self._input[ self._input_index: ]
        self._input_index  -= 1

        return char


    def event_mouse_position( self, event ) -> None:
        """
            Mouse position change callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        x = event( "x" )
        y = event( "y" )

        # Just update. There is no need to create new object
        self._mouse_position.x = x
        self._mouse_position.y = y

        correct_pad = self._config.pad * 2
        self._is_hovered = self._mouse_position.is_in_bounds( self._relative_position, self._size.x + correct_pad, self._size.y + correct_pad )

    
    def event_mouse_input( self, event ) -> None:
        """
            Mouse buttons input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_hovered:
            return

        button = event( "button" )
        action = event( "action" )

        if button != glfw.MOUSE_BUTTON_LEFT or action != glfw.PRESS:
            return

        #self._click_position = self._mouse_position.copy( )
        self._click_delta = self._mouse_position.x - ( self._relative_position.x + self._config.pad + self._input_offset )


    def event_char_input( self, event ) -> None:
        """
            Captures what char was pressed.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_typing:
            return
        
        char = chr( event( "char" ) )

        self.insert( char )

    
    def event_keyboard_input( self, event ) -> None:
        """
            General keyboard input handle.

            Receive :   
            - event - Event information

            Returns :   None
        """

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
        """
            Exception capture for Ctrl key input.

            Receive :   
            - key       - GLFW Key value
            - action    - GLFW Action value

            Returns :   None
        """
        
        if key != glfw.KEY_LEFT_CONTROL and key != glfw.KEY_RIGHT_CONTROL:
            return

        if action == glfw.PRESS:
            self._is_ctrl = True

        if action == glfw.RELEASE:
            self._is_ctrl = False


    def __repeat_handle( self, key ):
        """
            Executable input handle for PRESS and REPEAT calls.

            Receive :   
            - key       - GLFW Key value

            Returns :   None
        """

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
        """
            Handle text paste event.

            Receive :   
            - key       - GLFW Key value

            Returns :   None
        """

        if not self._is_ctrl:
            return

        if key != glfw.KEY_V:
            return

        result: bytes   = glfw.get_clipboard_string( None )
        result: str     = result.decode( )

        self.insert(result)

    # endregion

    # region : Utilitise

    def correct_text( self, text: str ) -> str:
        """
            Convert the text input value based on settings.

            Receive : 
            - text - String value

            Returns : New string value
        """

        if self._is_password:
            return "*" * len( text )
        
        return text

    # endregion


class c_text_input:

    _parent:                any
    _index:                 int

    _position:              vector
    _relative_position:     vector
    _height:                int

    _handle:                c_single_input_logic

    _render:                c_renderer
    _animations:            c_animations

    _font:                  c_font
    _icon:                  c_image
    _text:                  str

    _is_hovered:            bool
    _should_type:           bool

    _mouse_position:        vector
    _text_size:             vector
    _start_for_input:       int
    
    _config:                text_input_config_t

    # region : Initialize text input

    def __init__( self, parent: any, position: vector, height: int, size_of_input: vector, icon: c_image, font: c_font, text: str, is_password: bool = False, default_value: str = "", config: text_input_config_t = None ):
        """
            Default constructor for text input.

            Receive : 
            - parent                    - Text input parent
            - position                  - Start position in parent
            - height                    - Height of the text input
            - size_of_input             - Size of the input field itself
            - icon                      - Icon for the text input
            - font                      - Font for the text
            - text                      - Text to display
            - is_password [optional]    - Is password field
            - config [optional]         - Config for the text input

            Returns :   Text input object
        """

        self._config = config is None and text_input_config_t( ) or config

        self._parent = parent
        self._position = position.copy( )
        self._height = height

        self._font = font
        self._icon = icon
        self._text = text

        self._handle = c_single_input_logic( self._parent, position, font, size_of_input, is_password, default_value, self._config )

        self.__initialize_parent( )
        self.__initialize_animations( )
        self.__initialize_values( )

    def __initialize_parent( self ):
        """
            Initialize parent attach.

            Receive :   None

            Returns :   None
        """

        self._render = self._parent.render( )

        self._index = self._parent.attach_element( self )

        this_id = f"TextInput::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,           this_id )
        self._parent.set_event( "char_input",       self._handle.event_char_input,      this_id )
        self._parent.set_event( "keyboard_input",   self._handle.event_keyboard_input,  this_id )

    
    def __initialize_animations( self ):
        """
            Initialize button animations values

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Text",       0.3 )
        self._animations.prepare( "Width",      0 )
        self._animations.prepare( "Seperate",   0 )
        self._animations.prepare( "InputWidth", 0 )


    def __initialize_values( self ):
        """
            Initialize defaule button values

            Receive :   None

            Returns :   None
        """

        self._is_hovered        = False
        self._should_type       = False

        self._start_for_input   = 0

        self._relative_position = vector( )
        self._mouse_position    = vector( )
        self._text_size         = vector( )

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        """
            Draw function of the button.

            Receive : 
            - fade - Parent fade factor

            Returns :   None
        """

        self.__preform( )
        self.__animate( )

        self.__draw_back( fade )
        self.__draw_input( fade )

    
    def __preform( self ):
        """
            Preforms all the behind the scenes small calculations.

            Receive :   None

            Returns :   None
        """

        pad:                        int     = self._config.pad
        seperate:                   int     = self._config.seperate

        parent_position:            vector  = self._parent.relative_position( )
        self._relative_position:    vector  = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

        self._text_size:            vector  = self._render.measure_text( self._font, self._text )

        self._start_for_input:      int     = self._icon.size( ).x + self._text_size.x + pad * 4 + seperate

        # Update handle position
        self._handle.position( vector( 
            self._position.x + self._start_for_input, 
            self._position.y + ( self._height - self._handle.correct_size( ).y ) / 2 
        ) )

        self._handle.is_typing( self._should_type )

    
    def __animate( self ):
        """
            Preform animations of the button.

            Receive :   None

            Returns :   None
        """

        self._animations.update( )

        seperate:   int     = self._config.seperate
        speed:      int     = self._config.speed
        pad:        int     = self._config.pad

        regular:    int     = self._icon.size( ).x + pad * 4 + seperate + self._text_size.x
        opened:     int     = regular + self._handle.correct_size( ).x

        if self._should_type:
            self._animations.preform( "Text",           0.7,                                speed )
            self._animations.preform( "InputWidth",     self._handle.correct_size( ).x,     speed )
        else:
            self._animations.preform( "Text",           self._is_hovered and 0.5 or 0.3,    speed )
            self._animations.preform( "InputWidth",     0,                                  speed, 1 )


        if self._is_hovered or self._should_type:
            self._animations.preform( "Seperate",       ( self._height - 10 ) / 2,          speed )
        else:
            self._animations.preform( "Seperate",       ( self._height - 20 ) / 2,          speed )


        if self._handle.get( ) == "":
            self._animations.preform( "Width", self._should_type and opened or regular, speed )
        else:
            self._animations.preform( "Width", opened, speed )

        
    
    def __draw_back( self, fade: float ):
        """
            Render everything that is not the input box it self.

            Receive : 
            - fade - Fade factor for the parent

            Returns :   None
        """

        seperate:       int     = self._config.seperate
        pad:            int     = self._config.pad
        image_color:    color   = self._config.image_color
        seperate_color: color   = self._config.seperate_color
        text_color:     color   = self._config.text_color

        image_size:     vector  = self._icon.size( )

        text_position:      vector  = vector( self._position.x + pad * 3 + image_size.x + seperate, self._position.y + ( self._height - self._text_size.y ) / 2 )
        icon_position:      vector  = vector( self._position.x + pad, self._position.y + ( self._height - image_size.y ) / 2 )
        seperate_position:  vector  = vector( self._position.x + pad * 2 + image_size.x, self._position.y + self._height / 2 )

        text_fade:          float   = self._animations.value( "Text" ) * fade
        seperate_fade:      float   = self._animations.value( "Seperate" )

        self._render.image( self._icon, icon_position, image_color * fade )

        self._render.shadow(
            seperate_position + vector( 0, -seperate_fade ),
            seperate_position + vector( seperate, seperate_fade ),
            seperate_color,
            fade,
            15,
            seperate / 2
        )

        self._render.rect( 
            seperate_position + vector( 0, -seperate_fade ),
            seperate_position + vector( seperate, seperate_fade ),
            seperate_color * fade,
            seperate / 2
        )

        self._render.text( self._font, text_position, text_color * text_fade, self._text )
        
    
    def __draw_input( self, fade: float ):
        """
            Render Input it self.

            Receive :
            - fade - Fade factor of the parent

            Returns :   None
        """

        seperate_color: color   = self._config.seperate_color
        input_width:    float   = self._animations.value( "InputWidth" )
        start_position: vector  = vector( self._position.x + self._start_for_input, self._position.y + self._height )

        self._render.line( 
            start_position,  
            vector( start_position.x + input_width, start_position.y ),
            seperate_color * fade
        )

        self._handle.draw( fade )

    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        """
            Mouse position change callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        self._handle.event_mouse_position( event )

        self._mouse_position.x  = event( "x" )
        self._mouse_position.y  = event( "y" )

        width                   = self._animations.value( "Width" )

        if self._mouse_position.is_in_bounds( self._relative_position, width, self._height ):

            self._is_hovered = self._parent.try_to_get_handle( self._index )
        else:
            
            if self._parent.is_this_active( self._index ) and not self._should_type:
                self._parent.release_handle( self._index )

            self._is_hovered = False
        
    def __event_mouse_input( self, event ) -> None:
        """
            Mouse buttons input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """
        
        self._handle.event_mouse_input( event )

        button = event( "button" )
        action = event( "action" )

        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self._should_type = self._is_hovered

    # endregion

    # region : Utilities

    def position( self, new_value: vector = None ) -> vector | None:
        """
            Access / Update text input's position.

            Receive :
            - new_value - New position in the parent

            Returns : Vector or None
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y


    def size( self ) -> vector:
        """
            Access the text input size.

            Receive :   None

            Returns :   Vector object
        """

        return vector( self._animations.value( "Width" ), self._height )

    def get( self ) -> str:
        """
            Get value.

            Receive :   None

            Returns :   String value
        """

        return self._handle.get( )
    
    # endregion