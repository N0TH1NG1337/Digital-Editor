"""
    project     : Digital Editor
    type        : User Interface
    file        : Application

    description : Defines the main Application class, which manages the
                  lifecycle, windowing, rendering, and event handling
                  for the Digital Editor application.
"""
 
import OpenGL.GL as gl
import glfw
import imgui

# Import renderer backend
from imgui.integrations.glfw import GlfwRenderer

# Import utilities for application
from utilities.color    import color
from utilities.vector   import vector
from utilities.math     import math
from utilities.wrappers import safe_call
from utilities.image    import c_image, IMAGE_FILTER_BLUR
from utilities.font     import c_font
from utilities.event    import c_event
from utilities.debug    import c_debug

# Import user interface related things
from user_interface.render      import c_renderer
from user_interface.animations  import c_animations
from user_interface.scene       import *

# Import Widgets
from user_interface.widgets.button              import *
from user_interface.widgets.text_input          import *
from user_interface.widgets.select_list         import *
from user_interface.widgets.path_select         import *
from user_interface.widgets.editor              import *
# from user_interface.widgets.color_picker        import * # No use for now
from user_interface.widgets.solution_explorer   import *
from user_interface.widgets.slider              import *
from user_interface.widgets.label               import *


class application_config_t:
    back_color_1:   color       = color( 30, 30, 50 )
    back_color_2:   color       = color( 30, 30, 70 )
    back_color_3:   color       = color( 30, 30, 39 )
    back_color_4:   color       = color( 20, 20, 24 )

    wallpaper:      c_image     = None


# Main application class
class c_application:

    _app:               any             # GLFW Window

    _render:            c_renderer      # Render functions
    _impl:              GlfwRenderer    # Impl render backend

    _scenes:            list            # Attached scenes
    _active_scene:      int             # Active scene

    _events:            dict            # Application events
    _data:              dict            # Application private data

    _last_error:        str             # Last application error      

    _config:            application_config_t

    _mouse_position:    vector

    # region : Initialize object

    def __init__( self, config: application_config_t = None ):
        """
        Default constructor for the Application class.

        Initializes the application with optional configuration, sets up
        the rendering context, scene management, error handling, and mouse
        position tracking.

        Receives:
        - config (application_config_t, optional): Application-specific
                                                    configuration settings.
                                                    If None, default configuration
                                                    is used. Defaults to None.

        Returns: Application object
        """

        # Application handle must be at first None
        self._app               = None

        self._config            = config is None and application_config_t( ) or config

        # Create render object
        self._render            = c_renderer( )

        # Set up scenes handlers
        self._scenes            = [ ]
        self._active_scene      = 0

        # On init last error is None
        self._last_error        = "None"

        self._mouse_position    = vector( )

    # endregion

    # region : Initialize Window

    def initialize_window( self, title: str, position: vector, size: vector, vsync: bool = True ) -> bool:
        """
        Initializes the application window with the specified title, position,
        size, and optional vertical synchronization.

        Receives:
        - title (str): The title to be displayed in the application window's
                       title bar.
        - position (vector): The initial position (x, y coordinates) of the
                           application window on the screen.
        - size (vector): The initial size (width, height) of the application
                         window.
        - vsync (bool, optional): A boolean indicating whether vertical
                                   synchronization should be enabled for the
                                   application's rendering. Defaults to True.

        Returns:
        - bool: True if the window was initialized successfully; False otherwise.
        """

        # 1. Load GLFW context
        if not self.__init_glfw( ):
            return False
        
        # 2. Create data handle
        self._data = { }

        # Save received arguments
        self._data[ "position" ]    = position.copy( )
        self._data[ "size" ]        = size.copy( )
        self._data[ "title" ]       = title
        self._data[ "vsync" ]       = vsync

        # 3. Init window
        if not self.__init_window( ):
            return False
        
        # 4. Init backend
        if not self.__init_backend( ):
            return False
        

        # 5. Prepare to save font and image objects
        self._data[ "fonts" ]   = { }
        self._data[ "images" ]  = { }

        return True


    @safe_call( c_debug.log_error )
    def __init_glfw( self ) -> bool:
        """
        Initializes the GLFW (Graphics Library Framework) context.
        GLFW is used for window creation and input handling.

        Receives: None

        Returns:
        - bool: True if GLFW was initialized successfully; False otherwise.
        """

        if not glfw.init( ):
            self._last_error = "Failed to initialize OpenGL context"

            return False
        
        return True
    

    @safe_call( c_debug.log_error )
    def __init_window( self ) -> bool:
        """
        Initializes the application window with OpenGL context.

        Sets up GLFW window hints, creates the window, makes the OpenGL context current,
        disables vsync if specified, and sets the window position.

        Receives: None

        Returns:
        - bool: True if the window was initialized successfully; False otherwise.
        """

        # Set up glfw window hints
        glfw.window_hint( glfw.CONTEXT_VERSION_MAJOR,   3 )                             # Context related staff
        glfw.window_hint( glfw.CONTEXT_VERSION_MINOR,   3 )                             # Context related staff
        glfw.window_hint( glfw.OPENGL_PROFILE,          glfw.OPENGL_CORE_PROFILE )      # OpenGl related staff
        glfw.window_hint( glfw.OPENGL_FORWARD_COMPAT,   gl.GL_TRUE )                    # OpenGl related staff
        glfw.window_hint( glfw.DOUBLEBUFFER,            gl.GL_TRUE )                    # Enable doublebuffering

        # Save locally 
        local_size: vector  = self._data[ "size" ].copy( )
        local_title: str    = self._data[ "title" ]

        # Create window
        self._app = glfw.create_window( local_size.x, local_size.y, local_title, None, None )

        # Validate
        if not self._app:
            glfw.terminate( )

            self._last_error = "Could not initialize Application"
            return False
        
        # Without this line... OPEN GL CANNOT LOAD ??????
        glfw.make_context_current( self._app )

        # Disable vsync if need
        if not self._data[ "vsync" ]:
            glfw.swap_interval( 0 )

        # Set position
        local_position: vector = self._data[ "position" ].copy( )
        glfw.set_window_pos( self._app, local_position.x, local_position.y )

        # Clear data
        del self._data[ "position" ]
        del self._data[ "size" ]
        del self._data[ "title" ]
        del self._data[ "vsync" ]

        # Success
        return True
    

    @safe_call( c_debug.log_error )
    def __init_backend( self ) -> bool:
        """
        Initializes the ImGui context and the GLFW + OpenGL renderer backend
        for ImGui.

        Receives: None

        Returns:
        - bool: True if the backend was initialized successfully; False otherwise.
        """

        # Create ImGui context
        imgui.create_context( )

        # Create Renderer
        self._impl = GlfwRenderer( self._app, False )

        # Success
        return True

    # endregion

    # region : Assets

    @safe_call( c_debug.log_error )
    def create_font( self, index: str, path: str, size: int ) -> c_font:
        """
        Creates a new font object, loads it from a file, adds it to the application's font cache, and returns it.

        Receives:
        - index (str): The unique index to identify the font.
        - path (str): The file path to the font file (e.g., .ttf).
        - size (int): The desired height of the font in pixels.

        Returns:
        - c_font: The newly created and loaded font object.
        """

        # Create new font object
        new_font = c_font( )

        # Load it
        new_font.load( path, size )

        # Must do it
        self._impl.refresh_font_texture( )

        # Save
        fonts:  dict = self._data[ "fonts" ]
        fonts[ index ] = new_font

        # Return object
        return new_font
    

    @safe_call( c_debug.log_error )
    def create_image( self, index: str, path: str, size: vector, flags: list = [ ] ) -> c_image:
        """
        Creates a new image object, loads it from a file, saves it to the application's image cache, and returns it.

        Receives:
        - index (str): The unique index to identify the image.
        - path (str): The file path to the image file.
        - size (vector): The desired size (width and height) of the image.
        - flags (list, optional): A list of flags to apply to the image loading process. Defaults to an empty list.

        Returns:
        - c_image: The newly created and loaded image object.

        Warning! Setting a different size here than the original image size during loading can negatively impact image quality.
                 To render the image at a different size, use the 'size' parameter in the 'c_renderer.image()' function.
        """

        # Create new image object
        new_image = c_image( )

        # Load it
        new_image.load( path, size, flags )

        # Save
        images: dict = self._data[ "images" ]
        images[ index ] = new_image

        # Return object
        return new_image


    def font( self, index: str ) -> c_font:
        """
        Searches the application's font cache for a font object with the given index and returns it.

        Receives:
        - index (str): The unique index of the font to retrieve.

        Returns:
        - c_font: The font object associated with the given index, or None if the font is not found.
        """

        fonts:  dict = self._data[ "fonts" ]

        if index in fonts:
            return fonts[ index ]

        return None


    def image( self, index: str ) -> c_image:
        """
        Searches the application's image cache for an image object with the given index and returns it.

        Receives:
        - index (str): The unique index of the image to retrieve.

        Returns:
        - c_image: The image object associated with the given index, or None if the image is not found.
        """

        images: dict = self._data[ "images" ]

        if index in images:
            return images[ index ]

        return None

    # endregion

    # region : Scenes

    def new_scene( self, config: scene_config_t = None ) -> c_scene:
        """
        Creates a new scene object, attaches it to the application's scene list, and returns the new scene object.

        Receives:
        - config (scene_config_t, optional): Configuration settings for the new scene. 
                                             If None, default scene configuration is used. 
                                             Defaults to None.

        Returns:
        - c_scene: The newly created and attached scene object.
        """

        # Create new scene
        new_scene = c_scene( self, config )

        # Push back our new scene
        self._scenes.append( new_scene )

        # Looks strange, but we just save the current scene index in it
        new_scene.index( self._scenes.index( new_scene ) )

        return new_scene
    

    def active_scene( self, new_index: int = None ) -> c_scene:
        """
        Returns the currently active scene object. Optionally sets a new active scene by its index.

        Receives:
        - new_index (int, optional): The index of the scene to set as active. 
                                     If None, the current active scene is returned. 
                                     Defaults to None.

        Returns:
        - c_scene: The currently active scene object.
        """

        if new_index is None:
            return self._scenes[ self._active_scene ]
        
        self._active_scene = math.clamp( new_index, 0, len( self._scenes ) )


    @safe_call( None )
    def search_scene( self, index: int ) -> c_scene:
        """
        Searches for a specific scene within the application's scene list based on its index.

        Receive :
        - index (int): The index of the scene to search for.

        Returns :
        - c_scene: The scene object at the specified index, or None if no scene exists at that index.
        """

        return self._scenes[ index ]


    def next_scene( self ) -> None:
        """
        Moves the application to the next scene in the scene list.

        Receives: None

        Returns: None
        """

        self._active_scene = math.clamp( self._active_scene + 1, 0, len( self._scenes ) - 1 )


    def previous_scene( self ) -> None:
        """
        Moves the application to the previous scene in the scene list.

        Receives: None

        Returns: None
        """
        
        self._active_scene = math.clamp( self._active_scene - 1, 0, len( self._scenes ) - 1 )

    # endregion

    # region : Events

    def initialize_events( self ) -> None:
        """
        Initializes the event handling mechanisms for the application, 
        setting up callbacks for various input events.

        Receives: None

        Returns: None
        """

        # Create handle
        self._events = { }

        # General application events
        self._events[ "pre_draw" ]          = c_event( )
        self._events[ "post_draw" ]         = c_event( )
        self._events[ "unload" ]            = c_event( )

        # User input events
        self._events[ "keyboard_input" ]    = c_event( )
        self._events[ "char_input" ]        = c_event( )
        self._events[ "mouse_position" ]    = c_event( )
        self._events[ "mouse_input" ]       = c_event( )
        self._events[ "mouse_scroll" ]      = c_event( )

        self._events[ "path_drop" ]         = c_event( )

        # Application's window events
        self._events[ "window_resize" ]     = c_event( )
        self._events[ "window_position" ]   = c_event( )
        self._events[ "window_maximize" ]   = c_event( )

        # Attach glfw callbacks
        glfw.set_key_callback(              self._app, self.__event_keyboard_input )
        glfw.set_char_callback(             self._app, self.__event_char_input )
        glfw.set_cursor_pos_callback(       self._app, self.__event_mouse_position_change )
        glfw.set_mouse_button_callback(     self._app, self.__event_mouse_input )
        glfw.set_scroll_callback(           self._app, self.__event_mouse_scroll )
        glfw.set_drop_callback(             self._app, self.__event_path_drop )
        glfw.set_window_size_callback(      self._app, self.__event_window_resize )
        glfw.set_window_pos_callback(       self._app, self.__event_window_position )
        glfw.set_window_maximize_callback(  self._app, self.__event_window_maximize )
        
        # Register that we done initializing events
        self._data[ "is_events_initialize" ] = True

    
    def set_event( self, event_type: str, callback: any, index: str, allow_arguments: bool = True ):
        """
        Adds a callback function to be executed when a specific event type occurs.

        Receive :
        - event_type (str): The name of the event to listen for (e.g., "mouse_button_down", "key_press").
        - callback (any): The function to be called when the event occurs.
        - index (str): A unique identifier for this specific callback within the event type.
        - allow_arguments (bool, optional): A flag indicating whether the callback function should receive event-specific arguments. Defaults to True.

        Raises:
        - Exception: If the provided 'event_type' is not a valid event type that the application is listening for.
        """

        if not event_type in self._events:
            raise Exception( "Invalid event type to attach" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, allow_arguments )

    
    def __event_keyboard_input( self, window, key, scancode, action, mods ) -> None:
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

        self.active_scene( ).event_keyboard_input( window, key, scancode, action, mods )

        event: c_event = self._events[ "keyboard_input" ]

        event.attach( "window",      window )
        event.attach( "key",         key )
        event.attach( "scancode",    scancode )
        event.attach( "action",      action )
        event.attach( "mods",        mods )

        event.invoke( )


    def __event_char_input( self, window, char ) -> None:
        """
        Character input callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - char (int): Unicode code point of the character entered.

        Returns: None
        """

        self.active_scene( ).event_char_input( window, char )

        event: c_event = self._events[ "char_input" ]

        event.attach( "window",      window )
        event.attach( "char",        char )

        event.invoke( )


    def __event_mouse_position_change( self, window, x, y ) -> None:
        """
        Mouse position change callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - x (float): The new x-coordinate of the mouse cursor within the window.
        - y (float): The new y-coordinate of the mouse cursor within the window.

        Returns: None
        """

        self._mouse_position.x = x
        self._mouse_position.y = y

    
    def __event_mouse_position( self ) -> None:
        """
        Updates the application's internal record of the current mouse cursor position.

        Receive : None

        Returns : None
        """

        # This solution is much better, 
        # it avoids unwanted input if we didn't move the mouse

        x = self._mouse_position.x
        y = self._mouse_position.y

        self.active_scene( ).event_mouse_position( None, x, y )

        event: c_event = self._events[ "mouse_position" ]

        event.attach( "window",      None )
        event.attach( "x",           x )
        event.attach( "y",           y )

        event.invoke( )

    
    def __event_mouse_input( self, window, button, action, mods ) -> None:
        """
        Mouse button input callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - button (int): The mouse button that was pressed or released (GLFW mouse button code).
        - action (int): GLFW action code indicating the state change (GLFW.PRESS, GLFW.RELEASE).
        - mods (int): Bit field describing which modifier keys (Shift, Ctrl, Alt, Super) were held down during the mouse event.

        Returns: None
        """

        self.active_scene( ).event_mouse_input( window, button, action, mods )

        event: c_event = self._events[ "mouse_input" ]

        event.attach( "window",      window )
        event.attach( "button",      button )
        event.attach( "action",      action )
        event.attach( "mods",        mods )

        event.invoke( )


    def __event_mouse_scroll( self, window, x_offset, y_offset ) -> None:
        """
        Mouse scroll input callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - x_offset (float): The amount of horizontal scrolling.
        - y_offset (float): The amount of vertical scrolling.

        Returns: None
        """

        self.active_scene( ).event_mouse_scroll( window, x_offset, y_offset )

        event: c_event = self._events[ "mouse_scroll" ]

        event.attach( "window",      window )
        event.attach( "x_offset",    x_offset )
        event.attach( "y_offset",    y_offset )

        event.invoke( )


    def __event_window_resize( self, window, width, height ) -> None:
        """
        Window resize callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - width (int): The new width of the window, in screen coordinates.
        - height (int): The new height of the window, in screen coordinates.

        Returns: None
        """

        self.active_scene( ).event_window_resize( )

        event: c_event = self._events[ "window_resize" ]

        event.attach( "window",      window )
        event.attach( "width",       width )
        event.attach( "height",      height )

        event.invoke( )


    def __event_window_position( self, window, x_pos, y_pos ) -> None:
        """
        Window position change callback function.
        Reports the new position of the window relative to the top-left corner of the monitor it is displayed on.

        Receive:
        - window: GLFW Window object that received the event.
        - x_pos (int): The new x-coordinate of the window on the monitor.
        - y_pos (int): The new y-coordinate of the window on the monitor.

        Returns: None
        """

        event: c_event = self._events[ "window_position" ]

        event.attach( "window",      window )
        event.attach( "x_pos",       x_pos )
        event.attach( "y_pos",       y_pos )

        event.invoke( )


    def __event_window_maximize( self, window, maximized ) -> None:
        """
        Window maximization state change callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - maximized (int): GLFW boolean value indicating whether 
                           the window was maximized (GLFW_TRUE) or unmaximized (GLFW_FALSE).

        Returns: None
        """

        event: c_event = self._events[ "window_maximize" ]

        event.attach( "window",      window )
        event.attach( "maximized",   maximized )

        event.invoke( )


    def __event_path_drop( self, window, paths ) -> None:
        """
        File path drop callback function.

        Receive:
        - window: GLFW Window object that received the event.
        - paths (list): A list of strings, where each string is the absolute path 
                        of a file or directory that was dropped onto the window.

        Returns: None
        """

        event: c_event = self._events[ "path_drop" ]

        event.attach( "window",     window )
        event.attach( "paths",      paths )

        event.invoke( )

    # endregion

    # region : Run Time

    def run( self ) -> None:
        """
        The main loop of the application, responsible for continuously rendering frames,
        handling events, and updating the active scene.

        Receive : None

        Returns : None
        """

        # Check if we have window initialized
        if not self._app:
            raise Exception( "Failed to find application window. make sure you have first called .create_window()" )
        
        # Check if initialized events
        if not "is_events_initialize" in self._data:
            raise Exception( "Failed to verify events initialize. make sure you have first called .initialize_events() before .run()" )
        
        # Loop while application is running
        while not glfw.window_should_close( self._app ):

            # Process window events
            self.__process_input( )

            # Create new frame
            self.__pre_new_frame( )

            # Update our render
            self._render.update( )

            # MAIN STAFF HERE
            self.__draw_background( )
            self.__draw_scenes( )

            # Clear color buffer
            self.__clean_buffer( )

            # Complete creation of new frame
            self.__post_new_frame( )

            # Swap buffers
            glfw.swap_buffers( self._app )

        # Exit application
        self.__unload( )


    def __draw_background( self ) -> None:
        """
        Renders the background of the application window.

        Receive : None

        Returns : None
        """

        size:       vector  = self.window_size( )
        wallpaper:  c_image = self._config.wallpaper

        if wallpaper is not None:
            self._render.image( wallpaper, vector( ), color( ), size )


    def __draw_scenes( self ) -> None:
        """
        Iterates through all the scenes managed by the application and triggers their rendering process.

        Receive : None

        Returns : None
        """

        for scene in self._scenes:
            scene: c_scene = scene

            scene.show( scene.index( ) == self._active_scene )
            scene.draw( )


    def __process_input( self ) -> None:
        """
        Polls for and processes pending window events (like keyboard input, mouse movements, etc.)
        and updates the application's input state.

        Receive : None

        Returns : None
        """

        self.__event_mouse_position( )

        glfw.poll_events( )
        self._impl.process_inputs( )


    def __pre_new_frame( self ) -> None:
        """
        Performs any necessary actions or updates that need to occur immediately 
        before ImGui's `new_frame()` function is called at the beginning of a new rendering frame.

        Receive : None

        Returns : None
        """

        event: c_event = self._events[ "pre_draw" ]
        event.attach( "application", self )

        event.invoke( )

        imgui.new_frame( )


    def __post_new_frame( self ) -> None:
        """
        Performs actions immediately after ImGui's `new_frame()` has been called and 
        before the rendering of ImGui elements for the current frame. 
        Typically used for setup or state updates that depend on the new frame being initiated.

        Receive : None

        Returns : None
        """

        imgui.render( )
        self._impl.render( imgui.get_draw_data( ) )

        event: c_event = self._events[ "post_draw" ]
        event.attach( "application", self )

        event.invoke( )


    def __clean_buffer( self ) -> None:
        """
        Clears the color buffer of the OpenGL context with a black color.

        Receive : None

        Returns : None
        """

        gl.glClearColor( 0, 0, 0, 1 )
        gl.glClear( gl.GL_COLOR_BUFFER_BIT )


    def __unload( self ) -> None:
        """
        Performs necessary cleanup operations when the application is shutting down,
        such as destroying the ImGui context and terminating GLFW.

        Receive : None

        Returns : None
        """

        event: c_event = self._events[ "unload" ]
        event.attach( "ui", self )

        event.invoke( )

        self._impl.shutdown( )
        glfw.terminate( )

    # endregion

    # region : Utilities

    def render( self ) -> c_renderer:
        """
        Provides access to the application's rendering object, 
        which contains functions for drawing various graphical elements.

        Receive : None

        Returns :
        - c_renderer: The application's renderer object.
        """

        return self._render


    def window_size( self ) -> vector:
        """
        Retrieves the current size of the application window's 
        client area (excluding window decorations like the title bar).

        Receive : None

        Returns :
        - vector: A vector object representing the width and height of the window's client area.
        """

        return vector( ).raw( glfw.get_window_size( self._app ) )
    

    def maximize_window( self ) -> None:
        """
        Maximizes the application window to fill the screen.

        Receive : None

        Returns : None
        """

        glfw.maximize_window( self._app )

    
    def restore_window( self ) -> None:
        """
        Restores the application window from a maximized or 
        minimized state to its normal size.

        Receive : None

        Returns : None
        """

        glfw.restore_window( self._app )


    def close_window( self, avoid_glfw_terminate: bool = False ) -> None:
        """
        Closes the application window and performs cleanup of resources,
        including marking the window for closure and optionally terminating the GLFW context.

        Receives:
        - avoid_glfw_terminate (bool, optional): If True, the GLFW context will not be terminated.
                                                    This can be useful if you plan to reuse the GLFW context later.
                                                    Defaults to False.

        Returns: None
        """

        if self._app is not None:
            glfw.set_window_should_close( self._app, True )

        if not avoid_glfw_terminate:
            glfw.terminate( )


    def set_window_icon( self, icon: c_image ):
        images = [ icon( ) ]

        glfw.set_window_icon( self._app, len( images ), images )
    
    # endregion
