# User Interface. Widget -> Button .py

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


class c_button_dynamic:
    # Dynamic button.
    # Contains Icon and Text.

    # As the user hover the button, the background exntands reveal the text

    _parent:        c_scene
    _index:         int

    _position:      vector
    _height:        int

    _font:          c_font
    _icon:          c_image
    _text:          str

    _callback:      any

    _render:        c_renderer
    _animations:    c_animations

    _config:        dict
    _data:          dict

    def __init__( self, parent: c_scene, position: vector, height: int, font: c_font, icon: c_image, text: str, callback: any ):
        """
            Default constructor for class
        """

        self.__init_parent( parent )

        self.__init_config( )

        self.__init_vectors( position, height )
        self.__init_visuals( font, icon, text )

        self.__init_animations( )

        self.__complete_init( callback )


    def __init_parent( self, parent: c_scene ):
        """
            Saves parent object and receives data from it
        """

        # Save parent
        self._parent = parent

        # Get render object
        self._render = self._parent.render( )

        # Attach button object to scene
        self._index = self._parent.attach_element( self )

        # Register events
        this_id = f"Button:Dynamic::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )

    def __init_vectors( self, position: vector, height: int ):
        """
            Saves all the vectors information
        """

        self._position = position.copy( )
        self._height = height


    def __init_visuals( self, font: c_font, icon: c_image, text: str ):
        """
            Set up visuals data
        """

        self._font = font
        self._icon = icon

        self._text = text


    def __init_animations( self ):
        """
            Set up animations and related staff
        """

        self._animations = c_animations( )

        self._animations.prepare( "Add",    0 )
        self._animations.prepare( "Press",  0 )
        self._animations.prepare( "Width",  self._height )

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
        
        self._config = first_parent.config( "Button" )


    def __complete_init( self, callback: any ):
        """
            Finish all the init calls
        """

        self._callback = callback

        self._data = { }

        self._data[ "is_hovered" ]      = False
        self._data[ "complete_width" ]  = 0
        self._data[ "text_size" ]       = vector( )

    # region : Draw

    def draw( self, fade: float ):
        """
            Draw button function
        """

        self.__calculate( )
        self.__animations( )

        self.__draw_background( fade )
        self.__draw_icon( fade )
        self.__draw_text( fade )

        self._render.pop_clip_rect( )

    
    def __calculate( self ):
        """
            Complete all calculations
        """

        pad: int = self._config[ "pad" ]

        self._data[ "text_size" ]       = self._render.measure_text( self._font, self._text )

        self._data[ "complete_width" ]  = pad * 3 + self._icon.size( ).x + self._data[ "text_size" ].x


    def __animations( self ):
        """
            Complete all the animations
        """

        self._animations.update( )

        speed           = self._config[ "speed" ]
        is_hovered      = self._data[ "is_hovered" ]
        complete_width  = self._data[ "complete_width" ]

        self._animations.preform( "Add",    is_hovered and 1 or 0, speed )
        self._animations.preform( "Press",  0, speed )
        
        self._animations.preform( "Width",  is_hovered and complete_width or self._height, speed, 1 )


    def __draw_background( self, fade: float ):
        """
            Render background
        """

        width:      float       = self._animations.value( "Width" )
        add:        float       = self._animations.value( "Add" )
        press:      float       = self._animations.value( "Press" )

        add = add - press

        rounding:   int         = self._config[ "rounding" ]
        color_back: color       = self._config[ "color_back" ]

        start_vector    = vector( self._position.x - add, self._position.y - add  )
        end_vector      = vector( self._position.x + width + add, self._position.y + self._height + add )

        self._render.rect( 
            start_vector, 
            end_vector,
            color_back * fade,
            rounding
        )

        self._render.push_clip_rect( start_vector, end_vector )


    def __draw_icon( self, fade: float ):
        """
            Render icon
        """

        pad:            int     = self._config[ "pad" ]
        half_size:      vector  = self._icon.size( ) / 2
        position:       vector  = vector( self._position.x + pad, self._position.y + self._height / 2 - half_size.y )

        color_icon:     color   = self._config[ "color_icon" ]

        self._render.image( self._icon, position, color_icon * fade )


    def __draw_text( self, fade: float ):
        """
            Render text
        """

        pad:            int     = self._config[ "pad" ]
        color_text:     color   = self._config[ "color_text" ]
        icon_size:      vector  = self._icon.size( )
        text_size:      vector  = self._data[ "text_size" ]

        position:       vector  = vector( self._position.x + pad * 2 + icon_size.x, self._position.y + ( self._height - text_size.y ) / 2 )

        self._render.text( self._font, position, color_text * fade, self._text )
    
    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        """
            Event of mouse position change
        """

        x = event( "x" )
        y = event( "y" )

        if not x or not y:
            return
        
        mouse_positon:  vector  = vector( x, y )
        width:          float   = self._animations.value( "Width" )

        if mouse_positon.is_in_bounds( self._position, width, self._height ):
            
            # Check if we hovered and can have the handle. Also register self object
            self._data[ "is_hovered" ] = self._parent.try_to_get_handle( self._index )

        else:

            # Release if we hold the handle
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._data[ "is_hovered" ] = False

        # In general. The button doesnt even need the handle. Only when it hovered.
        
    
    def __event_mouse_input( self, event ) -> None:
        """
            Event of mouse input register
        """

        if not self._data[ "is_hovered" ]:
            return

        button = event( "button" )
        if not button == glfw.MOUSE_BUTTON_LEFT:
            return
        
        action = event( "action" )
        if not action == glfw.PRESS:
            return
        
        if self._callback is not None:
            self._callback( )

        self._animations.value( "Press", 5 )

    # endregion

    # region : Access 

    def position( self, new_value: vector = None ) -> vector | None:

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

    def size( self ) -> vector:

        return vector( self._animations.value( "Width" ), self._height )
    # endregion