"""
    project     : Digital Editor

    type:       : User Interface
    file        : Window

    description : Window class
"""

import OpenGL.GL as gl
import glfw
import imgui

# Import utilities
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


class window_config_t:
    speed:              int     = 7
    roundness:          int     = 10

    show_bar:           bool    = False

    back_color:         color   = color( 0, 0, 0, 100 )
    outline_color:      color   = color( 100, 100, 100, 150 )
    shadow_color:       color   = color( 0, 0, 0, 50 )

    bar_color:          color   = color( )


# Window class
class c_window:
    
    _parent:            any             # c_scene object
    _index:             int             # Window index in scene object

    _events:            dict            # Window events
    _elements:          list            # Window attached elements

    _show:              bool            # Should show wind

    _position:          vector          # Window position in the scene
    _size:              vector          # Window size
    _close:             vector          # Close button position

    _render:            c_renderer      # Render functions
    _animations:        c_animations    # Animations handle

    _config:            window_config_t # Scene config settings

    _active_handle:     int             # Active element handle

    _mouse_position:    vector

    # region : Initialize window

    def __init__( self, parent: any, position: vector, size: vector, config: window_config_t = None ):
        """
            Default constructor for window object

            Receives:   
            - parent            - Scene to attach to
            - position          - Window position
            - size              - Window size
            - config [optional] - Custom window config

            Returns:    Window object
        """

        self._parent    = parent

        self._position  = position.copy( )
        self._size      = size.copy( )

        self._config    = config is None and window_config_t( ) or config

        # Setup default values
        self.__initialize_default_values( )

        # Setup draw information
        self.__initialize_draw( )

        # Setup events
        self.__initialize_events( )


    def __initialize_default_values( self ) -> None:
        """
            Set default values to window object
            
            Receives:   None

            Returns:    None
        """

        self._index             = -1
        self._show              = True

        self._elements          = [ ]
        self._close             = vector( )
        self._mouse_position    = vector( )

        self._active_handle     = -1

    
    def __initialize_draw( self ) -> None:
        """
            Setup draw information
            
            Receives:   None

            Returns:    None
        """

        self._render        = self._parent.render( )
        self._animations    = c_animations( )

        self._animations.prepare( "Fade", 0 )


    def __initialize_events( self ) -> None:
        """
            Setup scene events
            
            Receives:   None

            Returns:    None
        """

        self._events = { }

        self._events[ "draw" ]              = c_event( )

        self._events[ "keyboard_input" ]    = c_event( )
        self._events[ "char_input" ]        = c_event( )
        self._events[ "mouse_position" ]    = c_event( )
        self._events[ "mouse_input" ]       = c_event( )
        self._events[ "mouse_scroll" ]      = c_event( )

    # endregion

    # region : Draw

    def draw( self ):
        """
            Render window object in scene

            Receive :   None

            Returns :   None
        """

        self._animations.update( )

        fade: float = self._animations.preform( "Fade", self._show and 1 or 0, self._config.speed )

        self._render.push_position( self._position + vector( -50 + 50 * fade, 0 ) )

        self.__draw_background( fade )

        self.__event_draw( )

        # Render elemements
        for item in self._elements:
            item.draw( fade )

        self._render.pop_position( )

        self.__unload_window( )


    def __draw_background( self, fade: float ) -> None:
        """
            Render windows background.

            Receive : 
            - fade      - Fade factor of the window

            Returns :   None
        """

        remove_height: int = 0
        self._close = vector( self._size.x - 20, -20 )

        if self._config.show_bar:
            remove_height = - 30

        self._render.gradiant(
            vector( 0, remove_height ), 
            self._size, 
            self._config.back_color * fade,
            self._config.back_color * fade,
            self._config.back_color * 0,
            self._config.back_color * 0,
            self._config.roundness
        )

        self._render.shadow(
            vector( 0, remove_height ),
            self._size,
            self._config.shadow_color,
            fade,
            20,
            self._config.roundness
        )

        if self._config.show_bar:

            self._render.line( vector( 10, 0 ), vector( self._size.x - 10, 0 ), self._config.outline_color * fade, 1 )

            self._render.line( self._close + vector( 0, 0 ), self._close + vector( 10, 10 ), color( ) * fade, 2 )
            self._render.line( self._close + vector( 0, 10 ), self._close + vector( 10, 0 ), color( ) * fade, 2 )
        
    # endregion

    # region : Events

    def __event_draw( self ) -> None:
        """
            Scene draw event

            Receives:   None

            Returns:    None
        """

        event: c_event = self._events[ "draw" ]

        event.attach( "parent", self )

        event.invoke( )


    def event_keyboard_input( self, window, key, scancode, action, mods ) -> None:
        """
            Keyboard input callback.

            Receives:   
            - window ptr  - GLFW Window
            - key         - GLFW Key
            - scancode    - GLFW Scan code
            - action      - GLFW Action
            - mods        - To be honest I have no idea what is this for

            Returns:    None
        """

        event: c_event = self._events[ "keyboard_input" ]

        event.attach( "window",     window )
        event.attach( "key",        key )
        event.attach( "scancode",   scancode )
        event.attach( "action",     action )
        event.attach( "mods",       mods )

        event.invoke( )


    def event_char_input( self, window, char ) -> None:
        """
            Char input callback.

            Receives:   
            - window ptr  - GLFW Window
            - char        - char code

            Returns:    None
        """

        event: c_event = self._events[ "char_input" ]

        event.attach( "window",      window )
        event.attach( "char",        char )

        event.invoke( )


    def event_mouse_position( self, window, x, y ) -> None:
        """
            Mouse position change callback.

            Receives:   
            - window ptr  - GLFW Window
            - x           - x-axis of mouse position
            - y           - y-axis of mouse position

            Returns:    None
        """
        
        self._mouse_position.x = x
        self._mouse_position.y = y

        event: c_event = self._events[ "mouse_position" ]

        event.attach( "window",     window )
        event.attach( "x",          x )
        event.attach( "y",          y )

        event.invoke( )


    def event_mouse_input( self, window, button, action, mods ) -> None:
        """
            Mouse buttons input callback

            Receives:   
            - window ptr  - GLFW Window
            - button      - Mouse button
            - action      - Button action
            - mods        - no idea of mouse position

            Returns:    None
        """

        if self._config.show_bar:
            is_on_close = self._mouse_position.is_in_bounds( self._position + self._close, 10, 10 )
            if is_on_close and button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS and self._active_handle == -1:
                # Close
                self.show( False )

        event: c_event = self._events[ "mouse_input" ]

        event.attach( "window",      window )
        event.attach( "button",      button )
        event.attach( "action",      action )
        event.attach( "mods",        mods )

        event.invoke( )


    def event_mouse_scroll( self, window, x_offset, y_offset ) -> None:
        """
            Mouse scroll input callback

            Receives:   
            - window ptr  - GLFW Window
            - x_offset    - x-axis of mouse wheel change (?)
            - y_offset    - y-axis of mouse wheel change (?)

            Returns:    None
        """

        event: c_event = self._events[ "mouse_scroll" ]

        event.attach( "window",      window )
        event.attach( "x_offset",    x_offset )
        event.attach( "y_offset",    y_offset )

        event.invoke( )


    def set_event( self, event_index: str, function: any, function_name: str ) -> None:
        """
            Registers functions to a event

            Receives:   
            - event_index       - event type index
            - function          - function pointer
            - function_name     - function name

            Returns:    None
        """

        if not event_index in self._events:
            raise Exception( f"Failed to index event { event_index }" )
        

        event: c_event = self._events[ event_index ]
        event.set( function, function_name, True )

    # endregion

    # region : Elements

    def attach_element( self, item: any ) -> int:
        """
            Attach new element to this scene

            Receive :   
            - item - item object

            Returns : Item index
        """

        self._elements.append( item )

        return self._elements.index( item )

    # endregion

    # region : Elements Handle

    def try_to_get_handle( self, index: int ) -> bool:
        """
            Tries to a get handle for specific item.
            Used to proccess 1 input at a time.
            
            Receives:   
            - index - Element index

            Returns:    Result
        """

        if self._active_handle != -1 and index != self._active_handle:
            return False
        
        self._active_handle = index

        return True
    

    def release_handle( self, index: int ) -> None:
        """
            If a specific index called it and active_handle is setted.
            It will release it.
            
            Receives:   
            - index - Element index

            Returns:    Result
        """

        if self._active_handle != -1 and self._active_handle == index:
            self._active_handle = -1


    def is_this_active( self, index: int ) -> bool:
        """
            Gets if this index is active handle
            
            Receives:   
            - index - Element index

            Returns:    Result
        """

        return self._active_handle == index

    # endregion

    # region : Utilities 

    def index( self, new_value: int = None ) -> int:
        """
            Returns / Sets the current window index in the queue
            
            Receives:   
            - new_value [optional] - new window index value

            Returns:    window index value
        """

        if new_value is None:
            return self._index
        
        self._index = new_value

    
    def show( self, new_value: bool = None ) -> bool:
        """
            Return / Sets if the window should show
            
            Receives:   
            - new_value [optional] - new value if should show window

            Returns:    Should show window
        """

        if new_value is None:
            return self._show
        
        self._show = new_value

    
    def parent( self ) -> any:
        """
            Returns current window parent
            
            Receives:   None

            Returns:    Application object
        """

        return self._parent
    

    def render( self ) -> c_renderer:
        """
            Access render object
            
            Receives:   None

            Returns:    Render object
        """

        return self._render
    

    def animations( self ) -> c_animations:
        """
            Access animations object
            
            Receives:   None

            Returns:    Animations object
        """

        return self._animations
    

    def element( self, index: int ) -> any:
        """
            Search and find specific Element that were attached.

            Receive :  
            - index - Element index in list

            Returns : Any type of element
        """

        if index in self._elements:
            return self._elements[ index ]
        
        return None


    def relative_position( self ) -> vector:
        """
            Returns relative position on the screen size.

            Receive :   None

            Returns :   Vector object
        """

        return self._position.copy( )

    # endregion

    # region : Uninitialize

    def __unload_window( self ):
        """
            Unloads window from the scene.

            Receive :   None

            Returns :   None
        """

        fade: float = self._animations.value( "Fade" )

        if fade == 0 and not self._show and self._active_handle == -1:
            self._parent.deattach_window( self )

    # endregion