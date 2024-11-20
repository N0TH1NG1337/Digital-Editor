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

    background_color:   color   = color( )
    bar_color:          color   = color( )


# Window class
class c_window:
    
    _parent:        any             # c_scene object
    _index:         int             # Window index in scene object

    _events:        dict            # Window events
    _elements:      list            # Window attached elements

    _show:          bool            # Should show wind

    _render:        c_renderer      # Render functions
    _animations:    c_animations    # Animations handle

    _config:        window_config_t # Scene config settings

    _active_handle: int             # Active element handle

    # region : Initialize window

    def __init__( self, parent: any, config: window_config_t = None ):
        """
            Default constructor for window object

            Receives:   
            - parent            - Scene to attach to
            - config [optional] - Custom window config

            Returns:    Window object
        """

        self._parent = parent
        self._config = config is None and window_config_t( ) or config

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

        self._index         = -1
        self._show          = False

        self._elements      = [ ]

        self._active_handle = -1

    
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

        self.__event_draw( )

        # Render elemements
        for item in self._elements:
            item.draw( fade )

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

        return self._elements.append( item )

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

    # endregion

    # region : Uninitialize

    def unload_window( self ):
        """
            Unloads window from the scene.

            Receive :   None

            Returns :   None
        """

        fade: float = self._animations.value( "Fade" )

        if fade == 0 and not self._show and self._active_handle == -1:
            self._parent.deattach_window( self )

    # endregion