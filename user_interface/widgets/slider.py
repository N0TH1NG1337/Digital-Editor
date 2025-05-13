"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Slider

    description : Slider classes
"""

import glfw
import time
import math as omath

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


class slider_config_t:
    speed:              int
    pad:                int
    separate:           int

    height:             int
    thickness:          int

    min_radius:         int
    max_radius:         int

    theme_color:        color
    back_color:         color
    value_color:        color

    def __init__( self ):

        self.speed:             int     = 7
        self.pad:               int     = 10
        self.separate:          int     = 4

        self.height:            int     = 20    
        self.thickness:         int     = 4

        self.min_radius:        int     = 4
        self.max_radius:        int     = 6

        self.theme_color:       color   = color( 207, 210, 215 )
        self.back_color:        color   = color( 30, 30, 30, 255 )
        self.value_color:       color   = color( 255, 255, 255 )



class c_slider_int:

    _parent:                any    # c_scene / c_window
    _index:                 int

    _position:              vector
    _relative_position:     vector
    _width:                 int

    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _mouse_position:        vector

    _config:                slider_config_t

    _is_visible:            bool
    _is_hovered:            bool
    _is_holding:            bool

    _value:                 int

    _minimum_value:         int
    _maximum_value:         int

    _text_size:             vector
    _work_width:            int

    _callback:              c_event

    # region : Initialize

    def __init__( self, parent: any, position: vector, width: int, font: c_font, minimum: int, maximum: int, default_value: int, config: slider_config_t = None ):
        """
        Default constructor for the integer slider.

        Receives:
        - parent (any): The parent object or container for this slider.
        - position (vector): The initial position (x, y) of the slider.
        - width (int): The width of the slider.
        - font (c_font): The font object to use for rendering text.
        - minimum (int): The minimum allowed value for the slider.
        - maximum (int): The maximum allowed value for the slider.
        - default_value (int): The initial value of the slider.
        - config (slider_config_t, optional): Configuration settings for the slider. Defaults to None.

        Returns:
        - c_slider_int: The newly created c_slider_int object.
        """

        # Set config
        self._config = config is None and slider_config_t( ) or config

        # Set parent 
        self._parent = parent

        # Set position and width
        self._position  = position.copy( )
        self._width     = width

        # Set display information
        self._font = font
        
        # Set default values
        self._minimum_value = minimum
        self._maximum_value = maximum
        self._value         = default_value

        # Initialize attachment to parent
        self.__init_attachment( )

        # Initialize animations of the widget
        self.__init_animations( )

        # Initialize widget bones
        self.__init_bones( )


    def __init_attachment( self ):
        """
        Initializes the attachment of the slider to its parent.

        Retrieves the renderer from the parent and attaches the slider as an element, 
        registering its mouse position and input event handlers with the parent.

        Receives: None

        Returns: None
        """
        
        # Get renderer
        self._render = self._parent.render( )

        # Attach widget to parent
        self._index = self._parent.attach_element( self )

        # Attach this widget's events handlers to parent
        this_widget = f"slider_int::{ self._index }"

        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_widget )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,           this_widget )


    def __init_animations( self ):
        """
        Initializes the animations for the slider.

        Sets up an animation manager and prepares animations for fade, 
        circle radius, and the slider value.

        Receives: None

        Returns: None
        """
        
        # Create standalone animations handler
        self._animation = c_animations( )

        self._animation.prepare( "fade",    0 )
        self._animation.prepare( "circle",  self._config.min_radius )
        self._animation.prepare( "value",   self._value )

    
    def __init_bones( self ):
        """
        Initializes the core attributes of the slider.

        Sets initial values for relative position, visibility, hover and holding states, 
        work width, mouse position, text size, and the callback event.

        Receives: None

        Returns: None
        """

        self._relative_position = self._position.copy( )

        self._is_visible = True
        self._is_hovered = False
        self._is_holding = False

        self._work_width = self._width

        self._mouse_position    = vector( )
        self._text_size         = vector( )

        self._callback          = c_event( )

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        """
        Draws the integer slider.

        Performs pre-drawing calculations and animations, then draws the slider bar and its current value.

        Receives:
        - fade (float): The fade value to apply during drawing.

        Returns: None
        """

        # Perform some calculations before drawing
        self.__perform_calculations( )
        self.__perform_animations( )

        fade = fade * self._animation.value( "fade" )
        if fade == 0:
            return
        
        self.__draw_slider( fade )
        self.__draw_value( fade )


    def __perform_calculations( self ):
        """
        Performs calculations needed before drawing the slider.

        Calculates the relative position, measures the text size for minimum and maximum values, 
        and determines the available width for the slider bar.

        Receives: None

        Returns: None
        """
        
        pad: int = self._config.pad

        parent_position:            vector  = self._parent.relative_position( )
        self._relative_position:    vector  = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

        min_size: vector = self._render.measure_text( self._font, str( self._minimum_value ) )
        max_size: vector = self._render.measure_text( self._font, str( self._maximum_value ) )

        self._text_size.x = max( min_size.x, max_size.x )
        self._text_size.y = max( min_size.y, max_size.y )

        self._work_width = self._width - pad - self._text_size.x


    def __perform_animations( self ):
        """
        Updates and performs animations for the slider.

        Updates the animation manager and performs animations for fade, value, and 
        the circle radius based on the holding state.

        Receives: None

        Returns: None
        """

        self._animation.update( )
    
        speed: int = self._config.speed

        self._animation.perform( "fade", self._is_visible and 1 or 0, speed )
        self._animation.perform( "value", self._value, speed, 1 )
        self._animation.perform( "circle", self._is_holding and self._config.max_radius or self._config.min_radius, speed )

    
    def __draw_slider( self, fade: float ):
        """
        Draws the slider bar and the indicator.

        Draws the background of the slider, the progress bar indicating the current animated value, 
        and a circle representing the current actual value with a neon effect.

        Receives:
        - fade (float): The fade value to apply during drawing.

        Returns: None
        """
        
        height:         int = self._config.height
        thickness:      int = self._config.thickness

        back_color:     color = self._config.back_color
        theme_color:    color = self._config.theme_color

        start_slider:   vector = self._position + vector( 0, ( height - thickness ) / 2 )
        end_slider:     vector = start_slider   + vector( self._work_width, thickness )

        delta                   = ( self._work_width ) / ( self._maximum_value - self._minimum_value )
        animated_pixel_value    = omath.floor( ( self._animation.value( "value" ) - self._minimum_value ) * delta )
        pixel_value             = omath.floor( ( self._value - self._minimum_value ) * delta )

        self._render.rect( start_slider , end_slider, back_color * fade, thickness / 2 )
        self._render.neon( start_slider, start_slider + vector( animated_pixel_value, thickness ), theme_color * fade, 15, thickness / 2 )

        radius: float   = self._animation.value( "circle" )
        center: vector  = start_slider + vector( pixel_value, thickness / 2 )
        self._render.neon( center - radius, center + radius, theme_color * fade, 15, radius )

        self.__handle_input( delta )

    
    def __draw_value( self, fade: float ):
        """
        Draws the current value of the slider as text.

        Receives:
        - fade (float): The fade value to apply to the text color.

        Returns: None
        """

        height:         int     = self._config.height

        value: str = str( self._value )

        value_color:    color   = self._config.value_color
        value_size:     vector = self._render.measure_text( self._font, value )
        
        position: vector = vector( self._position.x + self._width - value_size.x, self._position.y + ( height - value_size.y ) / 2 )
        self._render.text( self._font, position, value_color * fade, value )

    # endregion

    # region : Events

    def __event_mouse_position( self, event ):
        """
        Handles mouse position change events.

        Receives:
        - event (callable): Event information.

        Returns: None
        """
        
        if not self._is_visible:
            return
        
        self._mouse_position.x = event( "x" )
        self._mouse_position.y = event( "y" )

        if self._mouse_position.is_in_bounds( self._relative_position, self._width, self._config.height ):
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:
            if self._parent.is_this_active( self._index ) and not self._is_holding:
                self._parent.release_handle( self._index )

            self._is_hovered = False


    def __event_mouse_input( self, event ):
        """
        Handles mouse button input events.

        Receives:
        - event (callable): Event information.

        Returns: None
        """

        if not self._is_visible:
            return
        
        button = event( "button" )
        action = event( "action" )

        if not button == glfw.MOUSE_BUTTON_LEFT:
            return

        if action == glfw.PRESS and self._is_hovered:
            self._is_holding = True

        if action == glfw.RELEASE and self._is_holding:
            self._is_holding = False


    def __handle_input( self, delta ):
        """
        Handles user input while the mouse button is held down.

        Receives:
        - delta (float): The pixel distance per unit value.

        Returns: None
        """

        if not self._is_holding:
            return
        
        temp_value: int = self._minimum_value + int( ( self._mouse_position.x - self._relative_position.x ) / delta )
        temp_value: int = math.clamp( temp_value, self._minimum_value, self._maximum_value )

        if temp_value != self._value:
            self._callback.attach( "old_value", self._value )
            self._callback.attach( "new_value", temp_value )

            self._callback.invoke( )

        self._value = temp_value
        
    # endregion

    # region : Utilities

    def position( self, new_value: vector = None ) -> vector:

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y
        return new_value
    
    
    def width( self, new_value: int = None ) -> int:
        """
        Access or update the width of the slider.

        Receives:
        - new_value (int, optional): The new width. If None, returns the current width. Defaults to None.

        Returns:
        - int: The current width.
        """

        if new_value is None:
            return self._width
        
        self._width = new_value
        return new_value


    def visible( self, new_value: bool = None ) -> bool:
        """
        Access or update the visibility of the slider.

        Receives:
        - new_value (bool, optional): The new visibility. If None, returns the current visibility. Defaults to None.

        Returns:
        - bool: The current visibility.
        """

        if new_value is None:
            return self._is_visible

        self._is_visible = new_value
        return new_value
    

    def get( self ) -> int:
        """
        Returns the current value of the slider.

        Receives: None

        Returns:
        - int: The current value.
        """

        return self._value
    

    def set_callback( self, value: any ):
        """
        Sets the callback function to be invoked when the slider value changes.

        Receives:
        - value (any): The callable function to set as the callback.

        Returns: None
        """

        self._callback.set( value, value.__name__, True )

    # endregion