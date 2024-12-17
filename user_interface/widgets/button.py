"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Button

    description : Buttons classes
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


# Buttons config classes

class button_config_t:
    speed:          int     = 7
    pad:            int     = 10
    seperate:       int     = 4
    roundness:      int     = 10

    show_back:      bool    = True

    back_color:     color   = color( 0, 0, 0, 100 )
    seperate_color: color   = color( 150, 150, 255 )
    text_color:     color   = color( 255, 255, 255 )
    icon_color:     color   = color( 255, 255, 255 )


class c_button:
    
    _parent:                any     # c_scene / c_window
    _index:                 int     # Button index

    _position:              vector  # Position in parent
    _relative_position:     vector  # Relative position on screen
    _height:                int

    _font:                  c_font
    _icon:                  c_image
    _text:                  str

    _callback:              any

    _render:                c_renderer
    _animations:            c_animations

    _config:                button_config_t

    # Private button data 
    _is_hovered:            bool
    _width:                 float
    _icon_width:            int
    _text_size:             vector

    # region : Initialize button

    def __init__( self, parent: any, position: vector, height: int, font: c_font, icon: c_image, text: str, callback: any, config: button_config_t = None ):
        """
            Default constructor for Button object

            Receive :   
            - parent                - Button's parent
            - position              - Position in parent
            - height                - Button's height
            - font                  - Font used for text
            - icon                  - Icon of the button
            - text                  - Text inside the button
            - callback              - Executable on click event
            - config [optional]     - Button config

            Returns :   Button object
        """

        self._config = config is None and button_config_t( ) or config

        self.__initialize_parent( parent )

        self._position = position.copy( )
        self._height = height
        
        self._font = font
        self._icon = icon
        self._text = text

        self._callback = callback

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

        this_id = f"Button::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )


    def __initialize_animations( self ):
        """
            Initialize button animations values

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Add",    0 )
        self._animations.prepare( "Width",  0 )
        self._animations.prepare( "Hover",  0 )


    def __initialize_values( self ):
        """
            Initialize defaule button values

            Receive :   None

            Returns :   None
        """

        self._is_hovered        = False
        self._width             = 0
        self._icon_width        = self._icon.size( ).x + 2 * self._config.pad
        self._text_size         = vector( )

        self._relative_position = self._position.copy( )

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

        self.__draw_background( fade )

        self.__draw( fade )


    def __preform( self ):
        """
            Preforms all the behind the scenes small calculations.

            Receive :   None

            Returns :   None
        """

        pad:                int     = self._config.pad
        seperate:           int     = self._config.seperate

        self._text_size:    vector  = self._render.measure_text( self._font, self._text )
        self._width:        float   = self._animations.value( "Add" ) + self._text_size.x + pad * 2 

        # Do position staff.
        # I could use self._render.push_position, but I dont want.
        # I still need to calculate all the input relatives positions
        parent_position         = self._parent.relative_position( )
        self._relative_position = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )


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
        
        self._animations.preform( "Hover",  self._is_hovered and 1 or 0, speed )
        self._animations.preform( "Add",    self._is_hovered and self._icon_width + seperate or 0, speed, 0.5 )


    def __draw_background( self, fade: float ):
        """
            Draw buttons background. 

            Receive :   
            - fade - Parent background fade factor

            Returns :   None
        """
        if not self._config.show_back:
            return

        roundness:      int     = self._config.roundness
        back_color:     color   = self._config.back_color

        self._render.gradiant(
            self._position,
            self._position + vector( self._width, self._height ),
            back_color * 0,
            back_color * fade,
            back_color * 0,
            back_color * fade,
            roundness
        )
        
        self._render.shadow(
            self._position,
            self._position + vector( self._width, self._height ),
            back_color,
            fade,
            20,
            roundness
        )
            

    def __draw( self, fade: float ):
        """
            Draw buttons text and icon.

            Receive : 
            - fade - Parent background fade factor

            Returns :   None
        """

        seperate:       int     = self._config.seperate
        pad:            int     = self._config.pad
        text_color:     color   = self._config.text_color
        icon_color:     color   = self._config.icon_color

        seperate_color: color   = self._config.seperate_color

        part_height:    int     = ( self._height - 10 ) / 2

        hover:          float   = self._animations.value( "Hover" ) * fade
        add:            float   = self._animations.value( "Add" )
        hover_text:     float   = max( hover, 0.3 ) * fade

        hovered_pad:    float   = pad * hover

        text_position:      vector  = vector( self._position.x + pad + add, self._position.y + ( self._height - self._text_size.y ) / 2 )
        icon_position:      vector  = vector( self._position.x + hovered_pad, self._position.y + ( self._height - self._icon.size( ).y ) / 2 )
        seperate_position:  vector  = self._position + vector( self._icon_width, self._height / 2 )
        
        self._render.push_clip_rect( self._position, vector( text_position.x, self._position.y + self._height ) )

        # self._render.rect( icon_position, icon_position + self._icon.size( ), color( 100, 100, 100, 50 * hover ), 10 )
        self._render.image( self._icon, icon_position, icon_color * hover )

        start_seperate  = seperate_position + vector( 0, -part_height * hover )
        end_seperate    = seperate_position + vector( seperate, part_height * hover )

        self._render.pop_clip_rect( )

        self._render.shadow(
            start_seperate,
            end_seperate,
            seperate_color,
            hover,
            15,
            seperate / 2
        )

        self._render.rect( 
            start_seperate,
            end_seperate,
            seperate_color * hover,
            seperate / 2
        )

        self._render.text( self._font, text_position, text_color * hover_text, self._text )

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

        if not x or not y:
            return
        
        mouse_positon:  vector  = vector( x, y )

        if mouse_positon.is_in_bounds( self._relative_position, self._width, self._height ):
            
            # Check if we hovered and can have the handle. Also register self object
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:

            # Release if we hold the handle
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False

        # In general. The button doesnt even need the handle. Only when it hovered.
        
    
    def __event_mouse_input( self, event ) -> None:
        """
            Mouse buttons input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_hovered:
            return

        button = event( "button" )
        if not button == glfw.MOUSE_BUTTON_LEFT:
            return
        
        action = event( "action" )
        if not action == glfw.PRESS:
            return
        
        if self._callback is not None:
            self._callback( )

    # endregion

    # region : Utilities

    def position( self, new_value: vector = None ) -> any: #vector | None:
        """
            Access / Update buttons position.

            Receive :
            - new_value - New button position in the parent

            Returns : Vector or None
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

    def size( self ) -> vector:
        """
            Access the button size.

            Receive :   None

            Returns :   Vector object
        """

        return vector( self._width, self._height )

    # endregion