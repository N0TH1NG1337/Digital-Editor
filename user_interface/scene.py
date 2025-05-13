"""
    project     : Digital Editor

    type        : User Interface
    file        : Scene

    description : Represents a self-contained visual and interactive area
                  within the application. Manages a collection of windows
                  and elements, handles events, performs drawing operations,
                  and orchestrates animations. Scenes can be stacked or
                  switched to create different application states or views.
"""

import random

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
from user_interface.window      import c_window, window_config_t


class scene_config_t:
    speed:              int

    animate_movement:   bool

    enable_stars:       bool
    stars_speed:        int
    stars_count:        int

    background_image:   c_image
    background_descale: float
    background_color:   color

    movement_factor:    int

    def __init__( self ):

        self.speed:              int     = 8

        self.animate_movement:   bool    = False

        self.enable_stars:       bool    = True
        self.stars_speed:        int     = 10
        self.stars_count:        int     = 140

        self.background_image:   c_image = None
        self.background_descale: float   = 1.2
        self.background_color:   color   = color( 21, 21, 25 )

        self.movement_factor:    int     = 0.1


# Scene class
class c_scene:

    _parent:        any             # c_application
    _index:         int             # Scene index in application queue

    _show:          bool            # Is showing this scene
    _events:        dict            # Scene events
    _elements:      list            # Scene attached elements
    _windows:       list            # Windows attached to scene

    _render:        c_renderer      # Render functions
    _animations:    c_animations    # Animations handle

    _config:        scene_config_t  # Scene config settings

    _stars:         list            # Special

    _active_handle: int             # Active element handle

    _mouse_position: vector

    # region : Initialize scene

    def __init__( self, parent: any, config: scene_config_t = None ):
        """
        Initializes a new Scene object.

        Receive:
        - parent (Application): The Application object to which this scene will be attached.
        - config (scene_config_t, optional): An optional configuration object
                                               containing custom settings for the scene.
                                               Defaults to None.

        Returns:
        - Scene: A new Scene object associated with the given application and configuration.
        """

        # Save early information
        self._parent = parent
        self._config = config is None and scene_config_t( ) or config

        # Setup default values
        self.__initialize_default_values( )

        # Setup draw information
        self.__initialize_draw( )

        # Setup events
        self.__initialize_events( )

        if self._config.enable_stars:
            self._stars = [ ]
            self.__initialize_stars( )


    def __initialize_default_values( self ) -> None:
        """
        Sets the default internal state values for the Scene object.

        Receive: None

        Returns: None
        """

        self._index         = -1
        self._show          = False

        self._elements      = [ ]
        self._windows       = [ ]

        self._active_handle = -1

        self._mouse_position = vector( )

    
    def __initialize_draw( self ) -> None:
        """
        Sets up the drawing-related resources for the Scene object.

        Receive: None

        Returns: None
        """

        self._render        = self._parent.render( )
        self._animations    = c_animations( )

        self._animations.prepare( "Fade", 0 )
        self._animations.prepare( "Slide", -50 )
        self._animations.prepare( "Mouse", vector( ) )

        if self._config.enable_stars:
            self._animations.prepare( "StarsVelocity", vector( ) )


    def __initialize_events( self ) -> None:
        """
        Initializes the event dictionary for the Scene object.

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
    

    def __initialize_stars( self ) -> None:
        """
        Sets up the starfield effect for the scene.

        Receive: None

        Returns: None
        """

        self._stars.clear( )

        screen_size: vector = self._parent.window_size( )

        for i in range( self._config.stars_count ):

            star = [ vector( ), vector( ), 0, 0 ]

            # position
            star[ 0 ].x = random.randint( 0, screen_size.x )
            star[ 0 ].y = random.randint( 0, screen_size.y )

            # alpha
            star[ 2 ] = random.uniform( 0.1, 0.5 )

            # size
            star[ 3 ] = random.uniform( 1, 2 )

            # velocity
            star[ 1 ].x = random.uniform( -2, 2 ) * self._config.stars_speed
            star[ 1 ].y = random.uniform( -2, 2 ) * self._config.stars_speed

            self._stars.append( star )

    # endregion

    # region : Events

    def __event_draw( self ) -> None:
        """
        Handles the drawing of the scene and its elements.

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
        - action (int): GLFW action code indicating the state change (GLFW.PRESS,
                        GLFW.RELEASE, GLFW.REPEAT).
        - mods (int): Bit field describing which modifier keys (Shift, Ctrl, Alt,
                      Super) were held down.

        Returns: None
        """

        if self.is_any_window_active( ):
            return self.last_window( ).event_keyboard_input( window, key, scancode, action, mods )

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

        if self.is_any_window_active( ):
            return self.last_window( ).event_char_input( window, char )

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

        if self.is_any_window_active( ):
            return self.last_window( ).event_mouse_position( window, x, y )
        
        self._mouse_position.x = x
        self._mouse_position.y = y

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

        if self.is_any_window_active( ):
            return self.last_window( ).event_mouse_input( window, button, action, mods )

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

        if self.is_any_window_active( ):
            return self.last_window( ).event_mouse_scroll( window, x_offset, y_offset )

        event: c_event = self._events[ "mouse_scroll" ]

        event.attach( "window",      window )
        event.attach( "x_offset",    x_offset )
        event.attach( "y_offset",    y_offset )

        event.invoke( )

    
    def event_window_resize( self ) -> None:
        """
        Window resize callback function.

        Receive: None

        Returns: None
        """

        if self._config.enable_stars:
            self.__initialize_stars( )


    def set_event( self, event_index: str, function: any, function_name: str, get_arguments: bool = True ) -> None:
        """
        Registers a function to a specific scene event.

        Receive:
        - event_index (str): The name or identifier of the event to attach to
                             (e.g., "draw", "keyboard_input").
        - function (callable): The function to be called when the event occurs.
        - function_name (str): A name or identifier for the registered function.
        - get_arguments (bool, optional): If True, the registered function will
                                           receive event-specific arguments when invoked.
                                           Defaults to True.

        Returns: None
        """

        if not event_index in self._events:
            raise Exception( f"Failed to index event { event_index }" )

        event: c_event = self._events[ event_index ]
        event.set( function, function_name, get_arguments )

    # endregion

    # region : Pop up windows

    def create_window( self, position: vector, size: vector, config: window_config_t = None ) -> c_window:
        """
        Creates a new Window object, attaches it to the current scene,
        and returns the new window instance.

        Receive:
        - position (vector): The initial position (x, y) of the new window.
        - size (vector): The initial size (width, height) of the new window.
        - config (window_config_t, optional): An optional configuration object
                                               for the new window. Defaults to None.

        Returns:
        - c_window: The newly created and attached Window object.
        """

        new_window = c_window( self, position, size, config )

        self.attach_window( new_window )

        return new_window
    

    def attach_window( self, window: c_window ) -> None:
        """
        Attaches an existing Window object to the current scene.

        Receive:
        - window (c_window): The Window object to be added to the scene.

        Returns: None
        """

        self._windows.append( window )
        window.index( self._windows.index( window ) )

    
    def deattach_window( self, window: c_window ) -> None:
        """
        Detaches a Window object from the current scene.

        Receive :
        - window (c_window): The Window object to be removed from the scene.

        Returns : None
        """

        self._windows.remove( window )


    def disable_window( self, window: c_window = None ) -> None:
        """
        Disables a window, preventing it from being drawn or receiving input.
        If no window is provided, it disables the last added window.

        Receive :
        - window (c_window, optional): The Window object to disable.
                                       If None, the last window in the list is disabled.
                                       Defaults to None.

        Returns : None
        """

        if window is None:
            window = self._windows[ len( self._windows ) - 1 ]

        window.show( False )

    
    def is_any_window_active( self ) -> bool:
        """
        Checks if there is at least one active (visible) window attached to the scene.

        Receives: None

        Returns: bool: True if there is one or more active windows; False otherwise.
        """

        return len( self._windows ) != 0 and self._windows[ 0 ].show( )
    

    def last_window( self ) -> c_window:
        """
        Returns the last window that was attached to the scene.

        Receives: None

        Returns: c_window: The last attached Window object, or None if no
                          windows are currently attached.
        """

        return self._windows[ len( self._windows ) - 1 ]

    # endregion

    # region : Elements

    def attach_element( self, item: any ) -> int:
        """
        Attaches a new element to the scene. This could be a graphical
        element or any other object that the scene needs to manage.

        Receive :
        - item (any): The object to be attached to the scene.

        Returns : int: The index of the newly attached item within the
                       scene's internal list of elements.
        """

        self._elements.append( item )

        return self._elements.index( item )


    def deattach_element( self, item: any ) -> None:
        """
        Detaches an element from the scene.

        Receive :
        - item (any): The object to be removed from the scene.

        Returns : None
        """

        # TODO ! Deattach element's callbacks from the scene
        
        self._elements.remove( item )
        for item in self._elements:
            item.index( self._elements.index( item ) )

    # endregion

    # region : Elements Handle

    def try_to_get_handle( self, index: int ) -> bool:
        """
        Attempts to acquire the input handling focus for a specific element
        within the scene. This ensures that only one element processes input
        at a time.

        Receive:
        - index (int): The index of the element attempting to acquire the handle.

        Returns:
        - bool: True if the element successfully acquired the input handle;
                False otherwise (if another element currently holds the handle).
        """

        if self._active_handle != -1 and index != self._active_handle:
            return False
        
        self._active_handle = index

        return True
    

    def release_handle( self, index: int ) -> None:
        """
        Releases the input handling focus if the element at the provided index
        currently holds it.

        Receive:
        - index (int): The index of the element that is releasing the handle.

        Returns: None
        """

        if self._active_handle != -1 and self._active_handle == index:
            self._active_handle = -1


    def is_this_active( self, index: int ) -> bool:
        """
        Checks if the element at the given index currently holds the active
        input handle for the scene.

        Receive:
        - index (int): The index of the element to check.

        Returns:
        - bool: True if the element at the specified index has the active
                input handle; False otherwise.
        """

        return self._active_handle == index

    # endregion

    # region : Draw

    def draw( self ) -> None:
        """
        Draws the current scene, including its background, stars (if enabled),
        and all attached windows. The windows are drawn in the order of their
        assigned index, ensuring proper layering.

        Receive: None

        Returns: None
        """

        self.__animations( )

        fade:       float   = self._animations.value( "Fade" )
        
        mouse:              vector  = self._animations.value( "Mouse" )
        animate_movement:   bool    = self._config.animate_movement

        if animate_movement:
            self._render.push_position( mouse )

        self.__draw_stars( fade )

        if animate_movement:
            self._render.pop_position( )

        self.__draw_background_image( fade )

        if fade == 0:
            return

        self.__event_draw( )

        # Render elemements
        for item in self._elements:
            item.draw( fade )

        # Render windows
        for window in self._windows:
            window: c_window = window

            window.show( window.show( ) and self._show )
            window.draw( )


    def __draw_stars( self, fade: float ):
        """
        Renders the starfield effect with an optional fade factor.

        Receive :
        - fade (float): A value between 0.0 and 1.0 representing
                        the fade amount of the stars.

        Returns : None
        """

        if not self._config.enable_stars:
            return
        
        frame_time:     float   = self._animations.interpolation( )
        velocity:       vector  = self._animations.value( "StarsVelocity" )
        screen_size:    vector  = self._parent.window_size( )

        for star in self._stars:
            
            velocity.x = star[ 1 ].x * frame_time
            velocity.y = star[ 1 ].y * frame_time

            if star[ 0 ].x + velocity.x > screen_size.x or star[ 0 ].x + velocity.x < 0:
                star[ 1 ].x = -star[ 1 ].x
                velocity.x = -velocity.x

            if star[ 0 ].y + velocity.y > screen_size.y or star[ 0 ].y + velocity.y < 0:
                star[ 1 ].y = -star[ 1 ].y
                velocity.y = -velocity.y

            star[ 0 ].x = star[ 0 ].x + velocity.x
            star[ 0 ].y = star[ 0 ].y + velocity.y

            self._render.circle( star[ 0 ], color( ) * star[ 2 ] * fade, star[ 3 ] )
    

    def __draw_background_image( self, fade: float ):
        """
        Draws the background image of the scene with a specified fade factor.

        Receive :
        - fade (float): A value between 0.0 and 1.0 representing the fade
                        amount of the background image.

        Returns : None
        """

        image = self._config.background_image
        if image is None:
            return
        
        screen      = self._parent.window_size( )
        image_size  = screen / self._config.background_descale

        self._render.image( image, screen - image_size, self._config.background_color * fade, image_size )


    def __animations( self ):
        """
        Performs the general animations specific to the current scene.
        This method updates animation values and triggers any necessary actions
        based on the animation states.

        Receive : None

        Returns : None
        """

        self._animations.update( )
        
        speed: int = self._config.speed

        if self._show:
            fade    = self._animations.perform( "Fade",     self.is_any_window_active( ) and 0.3 or 1, speed )
        else:
            fade    = self._animations.perform( "Fade",     0, speed )

        if not self._config.animate_movement or self._active_handle != -1:
            return
        
        center  = self._parent.window_size( ) / 2
        delta   = ( center - self._mouse_position ) * self._config.movement_factor
        
        self._animations.perform( "Mouse", delta * fade, speed )

    # endregion

    # region : Utilities

    def index( self, new_value: int = None ) -> int:
        """
        Returns the current scene's index in the rendering queue.
        Optionally sets a new index value for the scene.

        Receive:
        - new_value (int, optional): The new index value to set for the scene.
                                     If None, the current index is returned.
                                     Defaults to None.

        Returns:
        - int: The current scene index in the queue.
        """

        if new_value is None:
            return self._index
        
        self._index = new_value
        return new_value

    
    def show( self, new_value: bool = None ) -> bool:
        """
        Returns whether the scene is currently set to be shown.
        Optionally sets a new value for the scene's visibility.

        Receive:
        - new_value (bool, optional): The new value indicating whether the
                                      scene should be shown. If None, the
                                      current visibility state is returned.
                                      Defaults to None.

        Returns:
        - bool: True if the scene is set to show; False otherwise.
        """

        if new_value is None:
            return self._show
        
        self._show = new_value
        return new_value

    
    def parent( self ) -> any:
        """
        Returns the parent object of the current scene.

        Receive: None

        Returns: c_application: The parent object to which this scene is attached.
        """

        return self._parent
    

    def render( self ) -> c_renderer:
        """
        Provides access to the renderer object managed by the parent application.

        Receive: None

        Returns: c_renderer: The renderer object used for drawing within the application.
        """

        return self._render
    

    def animations( self ) -> c_animations:
        """
        Provides access to the animations manager object associated with this scene.

        Receive: None

        Returns: c_animations: The animations manager object for controlling
                              animations within this scene.
        """

        return self._animations


    def element( self, index: int ) -> any:
        """
        Retrieves a specific attached element by its index.

        Receive :
        - index (int): The index of the element in the scene's internal list of elements.

        Returns : any: The element object at the specified index, or None if the index is out of bounds.
        """

        if index in self._elements:
            return self._elements[ index ]
        
        return None
    

    def relative_position( self ) -> vector:
        """
        Returns the scene's position as a relative value based on the
        parent application's window size. The returned vector components
        will be 0, 0.

        Receive : None

        Returns : vector: A Vector object representing the scene's position
                         relative to the application window dimensions.
        """

        return vector( )
    
    # endregion
