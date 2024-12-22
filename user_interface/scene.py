"""
    project     : Digital Editor

    type:       : User Interface
    file        : Scene

    description : Scene class
"""

import OpenGL.GL as gl
import glfw
import imgui
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
    speed:              int     = 8

    animate_entrance:   bool    = True
    animate_movement:   bool    = False

    enable_background:  bool    = True
    stars_speed:        int     = 10
    stars_count:        int     = 140

    background_image:   c_image = None
    background_descale: float   = 1.2
    background_color:   color   = color( 21, 21, 25 )

    movement_factor:    int     = 0.1


# Scene class
class c_scene:

    _parent:        any             # c_application
    _index:         int             # Scene index in application queue

    _show:          bool            # Is showing this scene
    _events:        dict            # Scene events
    _elements:      list            # Scene attached elements
    _windows:       list

    _render:        c_renderer      # Render functions
    _animations:    c_animations    # Animations handle

    _config:        scene_config_t  # Scene config settings

    _stars:         list            # Special

    _active_handle: int             # Active element handle

    _mouse_position: vector

    # region : Initialize scene

    def __init__( self, parent: any, config: scene_config_t = None ):
        """
            Default constructor for scene object

            Receives:   
            - parent            - Application to attach to
            - config [optional] - Custom scene config

            Returns:    Scene object
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

        if self._config.enable_background:
            self.__initialize_stars( )


    def __initialize_default_values( self ) -> None:
        """
            Set default values to scene object
            
            Receives:   None

            Returns:    None
        """

        self._index         = -1
        self._show          = False

        self._elements      = [ ]
        self._windows       = [ ]

        self._active_handle = -1

        self._mouse_position = vector( )

    
    def __initialize_draw( self ) -> None:
        """
            Setup draw information
            
            Receives:   None

            Returns:    None
        """

        self._render        = self._parent.render( )
        self._animations    = c_animations( )

        self._animations.prepare( "Fade", 0 )
        self._animations.prepare( "Slide", -50 )
        self._animations.prepare( "Mouse", vector( ) )

        if self._config.enable_background:
            self._animations.prepare( "StarsVelocity", vector( ) )


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
    

    def __initialize_stars( self ) -> None:
        """
            Setup stars for the scene
            
            Receives:   None

            Returns:    None
        """

        self._stars = [ ]

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
            Char input callback.

            Receives:   
            - window ptr  - GLFW Window
            - char        - char code

            Returns:    None
        """

        if self.is_any_window_active( ):
            return self.last_window( ).event_char_input( window, char )

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
            Mouse buttons input callback

            Receives:   
            - window ptr  - GLFW Window
            - button      - Mouse button
            - action      - Button action
            - mods        - no idea of mouse position

            Returns:    None
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
            Mouse scroll input callback

            Receives:   
            - window ptr  - GLFW Window
            - x_offset    - x-axis of mouse wheel change (?)
            - y_offset    - y-axis of mouse wheel change (?)

            Returns:    None
        """

        if self.is_any_window_active( ):
            return self.last_window( ).event_mouse_scroll( window, x_offset, y_offset )

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

    # region : Pop up windows

    def create_window( self, position: vector, size: vector, config: window_config_t = None ) -> c_window:
        """
            Create new pop up window and attach it
            
            Receives:   
            - position              - Window position
            - size                  - Window size
            - config [optional]     - Window config

            Returns:    Window object
        """

        new_window = c_window( self, position, size, config )

        self.attach_window( new_window )

        return new_window
    

    def attach_window( self, window: c_window ) -> None:
        """
            Attach new window to the scene
            
            Receives:   
            - window - new window object

            Returns:    None
        """

        self._windows.append( window )
        window.index( self._windows.index( window ) )

    
    def deattach_window( self, window: c_window ) -> None:
        """
            De Attach window from the scene

            Receive : 
            - window - Window object to remove from the scene

            Returns :   None
        """

        self._windows.remove( window )


    def disable_window( self, window: c_window = None ) -> None:
        """
            Disables window in the windows list.
            If None provided, disables the last window

            Receive :   
            - window [optional] - window to disable

            Returns :   None
        """

        if window is None:
            window = self._windows[ len( self._windows ) - 1 ]

        window.show( False )

    
    def is_any_window_active( self ) -> bool:
        """
            Is there any attached window 
            
            Receives:   None

            Returns:    Bool if true or false
        """

        return len( self._windows ) != 0
    

    def last_window( self ) -> c_window:
        """
            Return last attached window
            
            Receives:   None

            Returns:    Window object
        """

        return self._windows[ len( self._windows ) - 1 ]

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

    # region : Draw

    def draw( self ) -> None:
        """
            Draw current scene
            
            Receives:   None

            Returns:    None
        """

        self.__animations( )

        fade:       float   = self._animations.value( "Fade" )
        slide:      float   = self._animations.value( "Slide" )
        mouse:      vector  = self._animations.value( "Mouse" )

        animate_entrance:   bool = self._config.animate_entrance
        animate_movement:   bool = self._config.animate_movement

        if animate_movement:
            self._render.push_position( mouse )

        self.__draw_background( fade )

        if animate_movement:
            self._render.pop_position( )

        self.__draw_city( fade )

        if animate_entrance:
            self._render.push_position( vector( 0, slide ) )

        self.__event_draw( )

        # Render elemements
        for item in self._elements:
            item.draw( fade )

        # Render windows
        for window in self._windows:
            window: c_window = window

            window.show( window.show( ) and self._show )
            window.draw( )

        if animate_entrance:
            self._render.pop_position( )


    def __draw_background( self, fade: float ) -> None:
        """
            Render background things.

            Receive :   
            - fade - Scene fade factor

            Returns :   None
        """

        if not self._config.enable_background:
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
    

    def __draw_city( self, fade: float ):

        image = self._config.background_image
        
        screen = self._parent.window_size( )
        image_size = screen / self._config.background_descale

        if image is not None:
            pass
            #self._render.image( image, screen - image_size, self._config.background_color * fade, image_size )


    def __animations( self ):
        """
        """

        self._animations.update( )
        
        speed: int = self._config.speed

        if self._show:
            fade    = self._animations.preform( "Fade",     1, speed )
            slide   = self._animations.preform( "Slide",    0, speed, 1 )
        else:
            fade    = self._animations.preform( "Fade",     0, speed )
            slide   = self._animations.preform( "Slide",    -50, speed )

        if not self._config.animate_movement or self._active_handle != -1:
            return
        
        center = self._parent.window_size( ) / 2
        delta = ( center - self._mouse_position ) * self._config.movement_factor
        
        self._animations.preform( "Mouse", delta * fade, speed )

    # endregion

    # region : Utilities

    def index( self, new_value: int = None ) -> int:
        """
            Returns / Sets the current scene index in the queue
            
            Receives:   
            - new_value [optional] - new scene index value

            Returns:    Scene index value
        """

        if new_value is None:
            return self._index
        
        self._index = new_value

    
    def show( self, new_value: bool = None ) -> bool:
        """
            Return / Sets if the scene should show
            
            Receives:   
            - new_value [optional] - new value if should show scene

            Returns:    Should show scene
        """

        if new_value is None:
            return self._show
        
        self._show = new_value

    
    def parent( self ) -> any:
        """
            Returns current scene parent
            
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

        return vector( )
    
    # endregion
