"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Color picker

    description : Color picker classes
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


class color_picker_config_t:
    pad:            int = 20

    slider_width:   int = 4


class c_color_picker:

    _parent:                any     # c_scene / c_window
    _index:                 int     # Button index

    _position:              vector  # Position in parent
    _relative_position:     vector  # Relative position on screen
    _size:                  vector

    _render:                c_renderer
    _animations:            c_animations

    _config:                color_picker_config_t

    _color:                 color

    _is_hovered:            bool

    _mouse_position:        vector
    
    _hue:                   float
    _saturation:            float
    _value:                 float
    _alpha:                 float

    _hue_colors:            list[ color ]

    _canvas_axis:           int

    _is_using_hue:          bool
    _is_using_v_s:          bool
    _is_using_alpha:        bool

    # region : Initialize button

    def __init__( self, parent: any, position: vector, size: vector, default_value: color = color( ), config: color_picker_config_t = None ):
        """
            Default constructor for Color picker object

            Receive :   
            - parent                - Pickers's parent
            - position              - Position in parent
            - size                  - Pickers's size
            - config [optional]     - Picker config

            Returns :   Color picker object
        """

        self._config    = config is None and color_picker_config_t or config
        self._color     = default_value.copy( )

        self.__initialize_parent( parent )

        self._position  = position.copy( )
        self._size      = size.copy( )

        self.__initialize_animations( )
        self.__initialize_values( )


    def __initialize_parent( self, parent: any ):
        """
            Initialize parent attach.

            Receive : 
            - parent - Parent object to attach to.

            Returns :   None
        """

        self._parent = parent

        self._render = self._parent.render( )

        self._index = self._parent.attach_element( self )

        this_id = f"ColorPicker::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )


    def __initialize_animations( self ):
        """
            Initialize color picker animations values

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )


    def __initialize_values( self ):
        """
            Initialize defaule color picker values

            Receive :   None

            Returns :   None
        """

        self._hue, self._saturation, self._value, self._alpha = self._color.to_hsv( )

        self._hue_colors = [
            color( 255, 0,      0,      255 ), # red
            color( 255, 255,    0,      255 ), # yellow
            color( 0,   255,    0,      255 ), # green
            color( 0,   255,    255,    255 ), # light blue
            color( 0,   0,      255,    255 ), # blue
            color( 255, 0,      255,    255 ), # pink
            color( 255, 0,      0,      255 )  # red
        ]

        self._canvas_axis = self._size.x - self._config.pad * 2 - self._config.slider_width

        self._relative_position = self._position.copy( )
        self._mouse_position    = vector( )

        self._is_using_hue      = False
        self._is_using_v_s      = False
        self._is_using_alpha    = False

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        """
            Draw function of the color picker.

            Receive : 
            - fade - Parent fade factor

            Returns :   None
        """

        self.__animate( )

        self.__draw_hue_slider( fade )
        self.__draw_alpha_slider( fade )
        self.__draw_value_saturation_block( fade )

        self._color = color( ).as_hsv( self._hue, self._saturation, self._value, self._alpha )


    def __animate( self ):
        """
            Preform animations of the button.

            Receive :   None

            Returns :   None
        """

        self._animations.update( )

    
    def __draw_hue_slider( self, fade: float ):
        """
            Draw hue value slider.

            Receive :
            - fade - Fade factor

            Returns :   None
        """

        pad:            int     = self._config.pad
        slider_width:   int     = self._config.slider_width

        current_hue_color = color( ).as_hsv( self._hue, 1, 1, 1 ) * fade

        position: vector = self._position + vector( 0, self._size.y - pad - slider_width )

        for i in range( 0, 6 ):
            self._render.gradiant(
                position + vector( ( i ) * ( self._canvas_axis / 6 ), 0 ),
                position + vector( ( i + 1 ) * ( self._canvas_axis / 6 ), slider_width ),
                self._hue_colors[ i ] * fade,
                self._hue_colors[ i + 1 ] * fade,
                self._hue_colors[ i ] * fade,
                self._hue_colors[ i + 1 ] * fade
            )

        self._render.circle(
            position + vector( self._canvas_axis * self._hue, slider_width / 2 ),
            current_hue_color * fade,
            6
        )
    
    
    def __draw_alpha_slider( self, fade: float ):
        """
            Draw alpha value slider.

            Receive :
            - fade - Fade factor

            Returns :   None
        """

        pad:            int     = self._config.pad
        slider_width:   int     = self._config.slider_width

        alpha_color = color( 0, 0, 0, 255 ).lieaner( self._color.alpha_override( 255 ), self._alpha )
        position: vector = self._position + vector( self._size.x - pad - slider_width, 0 )

        self._render.gradiant(
            position,
            position + vector( slider_width, self._canvas_axis ),
            self._color.alpha_override( fade * 255 ),
            self._color.alpha_override( fade * 255 ),
            color( 0, 0, 0 ) * fade,
            color( 0, 0, 0 ) * fade,
        )

        self._render.circle(
            position + vector( slider_width / 2, self._canvas_axis * ( 1 - self._alpha ) ),
            alpha_color * fade,
            6
        )

    
    def __draw_value_saturation_block( self, fade: float ):
        """
            Draw the canvas of value/saturation values.

            Receive :
            - fade - Fade factor

            Returns :   None
        """

        pad:            int     = self._config.pad
        slider_width:   int     = self._config.slider_width

        position:   vector = self._position
        size:       vector = vector( self._canvas_axis, self._canvas_axis )

        current_hue_color = color( ).as_hsv( self._hue, 1, 1, 1 ) * fade

        c_back = color( 0, 0, 0 ) * fade
        c_no_black = color( 0, 0, 0, 0 )
        c_white = color( ) * fade

        self._render.gradiant(
            position,
            position + size,
            c_white,
            current_hue_color,
            c_white,
            current_hue_color,
            5
        )

        self._render.gradiant(
            position,
            position + size,
            c_no_black,
            c_no_black,
            c_back,
            c_back,
            5
        )

        position_of_picker = self._position + vector( self._canvas_axis * self._saturation, self._canvas_axis * ( 1 - self._value ) )

        self._render.circle(
            position_of_picker,
            color( 230, 230, 230, 170 ) * fade,
            10
        )

        self._render.circle(
            position_of_picker,
            self._color.alpha_override( 255 ) * fade,
            8
        )


    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        """
            Mouse position change callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        x = event( "x" )
        y = event( "y" )

        self._mouse_position.x = x
        self._mouse_position.y = y

        self.__handle_hue_change( )
        self.__handle_alpha_change( )
        self.__handle_value_saturation_change( )
        
    
    def __event_mouse_input( self, event ) -> None:
        """
            Picker input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        button = event( "button" )
        if not button == glfw.MOUSE_BUTTON_LEFT:
            return
        
        action = event( "action" )
        if action == glfw.PRESS:
            
            pad:            int     = self._config.pad
            slider_width:   int     = self._config.slider_width

            is_nothing_held = not self._is_using_hue and not self._is_using_v_s and not self._is_using_alpha

            if is_nothing_held:
                hovered_hue     = self._mouse_position.is_in_bounds( self._relative_position + vector( 0, self._size.y - pad - slider_width ), self._canvas_axis, slider_width )
                hovered_vs      = self._mouse_position.is_in_bounds( self._relative_position, self._canvas_axis, self._canvas_axis )
                hovered_alpha   = self._mouse_position.is_in_bounds( self._relative_position + vector( self._size.x - pad - slider_width, 0 ), slider_width, self._canvas_axis )

                if hovered_hue:
                    self._is_using_hue = True

                if hovered_vs:
                    self._is_using_v_s = True

                if hovered_alpha:
                    self._is_using_alpha = True

        if action == glfw.RELEASE:
            
            if self._is_using_hue:
                self._is_using_hue = False

            if self._is_using_v_s:
                self._is_using_v_s = False
            
            if self._is_using_alpha:
                self._is_using_alpha = False
    

    def __handle_hue_change( self ):
        """
            Handle if hue is changed.

            Receive :   None

            Returns :   None
        """

        if not self._is_using_hue:
            return
        
        position:       vector  = self._relative_position

        new_hue_value = self._mouse_position.x - position.x
        new_hue_value = math.clamp( new_hue_value, 0, self._canvas_axis - 1 ) # Avoid last pixels since its also red

        self._hue = new_hue_value / self._canvas_axis

    
    def __handle_alpha_change( self ):
        """
            Handle if alpha is changed.

            Receive :   None

            Returns :   None
        """

        if not self._is_using_alpha:
            return
        
        position:       vector  = self._relative_position

        new_alpha_value = self._mouse_position.y - position.y
        new_alpha_value = math.clamp( new_alpha_value, 0, self._canvas_axis )

        self._alpha = 1 - ( new_alpha_value / self._canvas_axis )

    
    def __handle_value_saturation_change( self ):
        """
            Handle if value or saturation are changed.

            Receive :   None

            Returns :   None
        """

        if not self._is_using_v_s:
            return
        
        mouse_in_canvas = self._mouse_position - self._relative_position

        mouse_in_canvas.x = math.clamp( mouse_in_canvas.x, 0, self._canvas_axis )
        mouse_in_canvas.y = math.clamp( mouse_in_canvas.y, 0, self._canvas_axis )

        self._saturation =  mouse_in_canvas.x / self._canvas_axis 
        self._value = 1 - ( mouse_in_canvas.y / self._canvas_axis )

    # endregion

    # region : Utilities

    def get( self ) -> color:
        """
            Get color value.

            Receive :   None

            Returns :   Color object
        """

        return self._color.copy( )

    # endregion
        
