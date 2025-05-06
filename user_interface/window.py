"""
    project     : Digital Editor

    type        : User Interface
    file        : Window

    description : Represents a top-level window within the application's
                  user interface. Manages its own state (active, focused,
                  hovered), rendering, event handling, and layout of child
                  widgets. Provides methods for attaching and accessing
                  widgets, handling user input, and interacting with the
                  parent scene's resources (renderer, animations).
"""

import OpenGL.GL as gl
import glfw

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
    speed:              int     
    roundness:          int     

    show_bar:           bool    
    bar_title:          str     
    title_font:         c_font  

    back_color:         color   
    outline_color:      color   
    shadow_color:       color   

    bar_color:          color   

    def __init__( self ):

        self.speed:              int     = 7
        self.roundness:          int     = 10

        self.show_bar:           bool    = False
        self.bar_title:          str     = ""
        self.title_font:         c_font  = None

        self.back_color:         color   = color( 0, 0, 0, 150 )
        self.outline_color:      color   = color( 100, 100, 100, 150 )
        self.shadow_color:       color   = color( 216, 208, 215, 255 )

        self.bar_color:          color   = color( )



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

    _mouse_position:    vector          # Mouse position vector
    _move_delta:        vector          # Moving window padding
    _is_moving:         bool            # Is moving the window

    # region : Initialize window

    def __init__( self, parent: any, position: vector, size: vector, config: window_config_t = None ):
        """
        Initializes a new Window object.

        Receive:
        - parent (Scene): The Scene object to which this window will be attached.
        - position (vector): A Vector object representing the initial position (x, y) of the window.
        - size (vector): A Vector object representing the initial size (width, height) of the window.
        - config (window_config_t, optional): An optional configuration object
                                               containing custom settings for the window.
                                               Defaults to None.

        Returns:
        - Window: A new Window object with the specified parent, position, size,
                  and configuration.
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
        Sets the default internal state values for the Window object.

        Receive: None

        Returns: None
        """

        self._index             = -1
        self._show              = True

        self._elements          = [ ]
        self._close             = vector( )
        self._mouse_position    = vector( )
        self._move_delta        = vector( )

        self._active_handle     = -1

        self._is_moving         = False

    
    def __initialize_draw( self ) -> None:
        """
        Initializes the drawing-related attributes for the Window object.

        Receive: None

        Returns: None
        """

        self._render        = self._parent.render( )
        self._animations    = c_animations( )

        self._animations.prepare( "Fade", 0 )


    def __initialize_events( self ) -> None:
        """
        Initializes the event handlers for the Window object.

        Receive: None

        Returns: None
        """

        self._events = { 
            
            "draw":             c_event( ),

            "keyboard_input":   c_event( ),
            "char_input":       c_event( ),
            "mouse_position":   c_event( ),
            "mouse_input":      c_event( ),
            "mouse_scroll":     c_event( )
        }

    # endregion

    # region : Draw

    def draw( self ):
        """
        Renders the window and its widgets within the scene.

        Receive : None

        Returns : None
        """

        self._animations.update( )

        if self._show:
            is_this_last_window = self._parent.last_window( ) is self
            fade: float = self._animations.perform( "Fade", is_this_last_window and 1 or 0.3, self._config.speed )
        else:
            fade: float = self._animations.perform( "Fade", 0, self._config.speed )

        self._render.push_position( self._position )

        self.__draw_background( fade )

        self._render.push_clip_rect( vector( ), self._size, True )

        self.__event_draw( )

        # Render elements
        for item in self._elements:
            item.draw( fade )

        self._render.pop_position( )

        self._render.pop_clip_rect( )

        self.__unload_window( )


    def __draw_background( self, fade: float ) -> None:
        """
        Renders the background of the window with a specified fade factor.

        Receive :
        - fade (float): A value between 0.0 and 1.0 representing the fade
                        amount of the background color.

        Returns : None
        """

        remove_height: int = 0
        self._close = vector( self._size.x - 20, -20 )

        if self._config.show_bar:
            remove_height = - 30

        # TODO ! REWORK THE BACKGROUND DRAWING
        # can add layer of blur or something and on top add transparent black.

        self._render.rect(
            vector( 0, remove_height ), 
            self._size, 
            self._config.back_color * fade,
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
            
            bar_text:   str     = self._config.bar_title
            font:       c_font  = self._config.title_font

            if bar_text != "":
                self._render.text( font, vector( 10, -20 ), color( ) * fade, bar_text )

            self._render.line( vector( 10, 0 ), vector( self._size.x - 10, 0 ), self._config.outline_color * fade, 1 )

            self._render.line( self._close + vector( 0, 0 ), self._close + vector( 10, 10 ), color( ) * fade, 2 )
            self._render.line( self._close + vector( 0, 10 ), self._close + vector( 10, 0 ), color( ) * fade, 2 )
        
    # endregion

    # region : Events

    def __event_draw( self ) -> None:
        """
        Handles the drawing-related events for the window.

        Receive: None

        Returns: None
        """

        event: c_event = self._events[ "draw" ]

        event.attach( "parent", self )

        event.invoke( )


    def event_keyboard_input( self, window, key, scancode, action, mods ) -> None:
        """
        Keyboard input callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - key (int): The keyboard key that was pressed or released (GLFW key code).
        - scancode (int): The system-specific scancode of the key.
        - action (int): GLFW action code indicating the state change (e.g., press, release, repeat).
        - mods (int): Bit field describing which modifier keys (Shift, Ctrl, Alt, Super)
                      were held down.

        Returns: None
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
        Character input callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - char (int): The Unicode code point of the character.

        Returns: None
        """

        event: c_event = self._events[ "char_input" ]

        event.attach( "window",      window )
        event.attach( "char",        char )

        event.invoke( )


    def event_mouse_position( self, window, x, y ) -> None:
        """
        Mouse position change callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - x (float): The new x-coordinate of the mouse cursor.
        - y (float): The new y-coordinate of the mouse cursor.

        Returns: None
        """
        
        self._mouse_position.x = x
        self._mouse_position.y = y

        if self._is_moving:
            self._position = self._mouse_position + self._move_delta
            return

        event: c_event = self._events[ "mouse_position" ]

        event.attach( "window",     window )
        event.attach( "x",          x )
        event.attach( "y",          y )

        event.invoke( )


    def event_mouse_input( self, window, button, action, mods ) -> None:
        """
        Mouse button input callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - button (int): The mouse button that was pressed or released (GLFW mouse button code).
        - action (int): GLFW action code indicating the state change (GLFW.PRESS or GLFW.RELEASE).
        - mods (int): Bit field describing which modifier keys (Shift, Ctrl, Alt, Super)
                      were held down when the mouse event occurred.

        Returns: None
        """

        if self._config.show_bar and self._active_handle == -1:

            is_on_close = self._mouse_position.is_in_bounds( self._position + self._close, 10, 10 )
            if is_on_close and button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
                # Close
                return self.show( False )
            
            is_on_hold = self._mouse_position.is_in_bounds( self._position - vector( 0, 30 ), self._close.x, 30 )
            if is_on_hold and button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
                self._is_moving = True
                self._move_delta = self._position - self._mouse_position

            if self._is_moving and button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
                self._is_moving = False


        event: c_event = self._events[ "mouse_input" ]

        event.attach( "window",      window )
        event.attach( "button",      button )
        event.attach( "action",      action )
        event.attach( "mods",        mods )

        event.invoke( )


    def event_mouse_scroll( self, window, x_offset, y_offset ) -> None:
        """
        Mouse scroll wheel input callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - x_offset (float): The amount of horizontal scrolling.
        - y_offset (float): The amount of vertical scrolling.

        Returns: None
        """
        event: c_event = self._events[ "mouse_scroll" ]

        event.attach( "window",      window )
        event.attach( "x_offset",    x_offset )
        event.attach( "y_offset",    y_offset )

        event.invoke( )


    def set_event( self, event_index: str, function: any, function_name: str, allow_arguments: bool = True ) -> None:
        """
        Registers a function to a specific window event.

        Receive:
        - event_index (str): The name or identifier of the event to attach to
                             (e.g., "on_mouse_click", "on_key_press").
        - function (callable): The function to be called when the event occurs.
        - function_name (str): A name or identifier for the registered function.
        - allow_arguments (bool, optional): If True, the registered function will
                                             receive event-specific arguments when invoked.
                                             Defaults to True.

        Returns: None
        """

        if not event_index in self._events:
            raise Exception( f"Failed to index event { event_index }" )
        

        event: c_event = self._events[ event_index ]
        event.set( function, function_name, allow_arguments )

    # endregion

    # region : Elements

    def attach_element( self, item: any ) -> int:
        """
        Attaches a new element (widget) to this window.

        Receive :
        - item (any): The widget object to be added to the window.

        Returns : int: The index of the newly attached element within the window's widget list.
        """

        self._elements.append( item )

        return self._elements.index( item )

    # endregion

    # region : Elements Handle

    def try_to_get_handle( self, index: int ) -> bool:
        """
        Attempts to acquire input handling focus for a specific element.
        This can be used to ensure only one element processes input at a time.

        Receive:
        - index (int): The index of the element (widget) to try and get the handle for.

        Returns:
        - bool: True if the element successfully acquired the input handle;
                False otherwise (e.g., if another element already has the handle).
        """

        if self._active_handle != -1 and index != self._active_handle:
            return False
        
        self._active_handle = index

        return True
    

    def release_handle( self, index: int ) -> None:
        """
        Releases the input handling focus if the provided index matches the
        element that currently holds the handle.

        Receive:
        - index (int): The index of the element that is potentially releasing the handle.

        Returns: None
        """

        if self._active_handle != -1 and self._active_handle == index:
            self._active_handle = -1


    def is_this_active( self, index: int ) -> bool:
        """
        Checks if the element at the given index currently holds the active input handle.

        Receive:
        - index (int): The index of the element to check.

        Returns:
        - bool: True if the element at the specified index has the active input
                handle; False otherwise.
        """

        return self._active_handle == index

    # endregion

    # region : Utilities 

    def index( self, new_value: int = None ) -> int:
        """
        Returns the current window index in the rendering queue.
        Optionally sets a new index value.

        Receive:
        - new_value (int, optional): The new index value to set for the window.
                                     If None, the current index is returned.
                                     Defaults to None.

        Returns:
        - int: The current window index in the queue.
        """

        if new_value is None:
            return self._index
        
        self._index = new_value

    
    def show( self, new_value: bool = None ) -> bool:
        """
        Returns whether the window is currently set to show.
        Optionally sets a new value for whether the window should be shown.

        Receive:
        - new_value (bool, optional): The new value indicating whether the
                                      window should be shown. If None, the
                                      current visibility state is returned.
                                      Defaults to None.

        Returns:
        - bool: True if the window is set to show; False otherwise.
        """

        if new_value is None:
            return self._show
        
        self._show = new_value
        return new_value

    
    def parent( self ) -> any:
        """
        Returns the parent object of the current window.

        Receive: None

        Returns: any: The parent object to which this window is attached.
                     Typically this would be a Scene or Application object.
        """

        return self._parent
    

    def render( self ) -> c_renderer:
        """
        Provides access to the renderer object associated with the parent scene.

        Receive: None

        Returns: c_renderer: The renderer object used for drawing within the scene.
        """

        return self._render
    

    def animations( self ) -> c_animations:
        """
        Provides access to the animations manager object associated with the parent scene.

        Receive: None

        Returns: c_animations: The animations manager object used for handling animations within the scene.
        """

        return self._animations
    

    def element( self, index: int ) -> any:
        """
        Retrieves a specific attached element (widget) by its index.

        Receive :
        - index (int): The index of the element in the window's internal list of widgets.

        Returns : any: The element object at the specified index, or None if the index is out of bounds.
        """

        if index in self._elements:
            return self._elements[ index ]
        
        return None


    def relative_position( self ) -> vector:
        """
        Returns the window's position relative to the parent scene's dimensions.

        Receive : None

        Returns : vector: A Vector object representing the window's position
                         as a fraction of the parent scene's width and height.
        """

        return self._position.copy( )

    # endregion

    # region : Uninitialize

    def __unload_window( self ):
        """
        Unloads the window from its parent scene, effectively removing it
        from the rendering and event handling pipeline.

        Receive : None

        Returns : None
        """

        fade: float = self._animations.value( "Fade" )

        if fade == 0 and not self._show:
            self._parent.deattach_window( self )

    # endregion