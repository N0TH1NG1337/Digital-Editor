"""
    project     : Digital Editor

    type:       : User Interface
    file        : Application

    description : Main Application class
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
from utilities.image    import c_image
from utilities.font     import c_font
from utilities.event    import c_event

# Import user interface related things
from user_interface.render      import c_renderer
from user_interface.animations  import c_animations
from user_interface.scene       import c_scene, scene_config_t

# Import Widgets


class application_config_t:
    back_color_1 = color( 203, 185, 213 )
    back_color_2 = color( 253, 231, 236 )
    back_color_3 = color( 156, 140, 182 )
    back_color_4 = color( 224, 205, 224 )


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

    # region : Initialize object

    def __init__( self, config: application_config_t = None ):
        """
            Default constructor for application

            Receives:   
            - config [optional] - Application config

            Returns:    Application object
        """

        # Application handle must be at first None
        self._app           = None

        self._config = config is None and application_config_t( ) or config

        # Create render object
        self._render        = c_renderer( )

        # Set up scenes handlers
        self._scenes        = [ ]
        self._active_scene  = 0

        # On init last error is None
        self._last_error    = "None"

    # endregion

    # region : Initialize Window

    def initialize_window( self, title: str, position: vector, size: vector, vsync: bool = True ) -> bool:
        """
            Initialize application window

            Receives:   
            - title             - Application title
            - position          - Application position on the screen
            - size              - Application size
            - vsync [optional]  - Enable vsync on the application

            Returns:    Result state
        """

        # 1. Load GLFW context
        if not self.__init_glfw( ):
            return False
        
        # 2. Create data handle
        self._data = { }

        # Save received arguments
        self._data[ "position" ]    = position
        self._data[ "size" ]        = size
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


    @safe_call( None )
    def __init_glfw( self ) -> bool:
        """
            Initialize GLFW context

            Receives:   None

            Returns:    Result state
        """

        if not glfw.init( ):
            self._last_error = "Failed to initialize OpenGL context"

            return False
        
        return True
    

    @safe_call( None )
    def __init_window( self ) -> bool:
        """
            Initialize window's application

            Receives:   None

            Returns:    Result state
        """

        # Set up glfw window hints
        glfw.window_hint( glfw.CONTEXT_VERSION_MAJOR,   3 )                             # Context related staff
        glfw.window_hint( glfw.CONTEXT_VERSION_MINOR,   3 )                             # Context related staff
        glfw.window_hint( glfw.OPENGL_PROFILE,          glfw.OPENGL_CORE_PROFILE )      # OpenGl related staff
        glfw.window_hint( glfw.OPENGL_FORWARD_COMPAT,   gl.GL_TRUE )                    # OpenGl related staff

        # Save localy 
        local_size: vector  = self._data[ "size" ].copy( )
        local_title: str    = self._data[ "title" ]

        # Create window
        self._app = glfw.create_window( local_size.x, local_size.y, local_title, None, None )

        # Validate
        if not self._app:
            self.close_window( )

            self._last_error = "Could not initialize Application"
            return False
        
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
    

    @safe_call( None )
    def __init_backend( self ) -> bool:
        """
            Initialize imgui context and OpenGL renderer backend.

            Receives:   None

            Returns:    Result state
        """

        # Create ImGui context
        imgui.create_context( )

        # Create Renderer
        self._impl = GlfwRenderer( self._app, False )

        # Success
        return True

    # endregion

    # region : Assets

    @safe_call( None )
    def create_font( self, index: str, path: str, size: int ) -> c_font:
        """
            Create new font object, save and return it

            Receives:   
            - index     - Font index
            - path      - Font path
            - size      - Font height

            Returns:    Font object
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
    

    @safe_call( None )
    def create_image( self, index: str, path: str, size: vector ) -> c_image:
        """
            Create new image object, save and return it

            Receives:   
            - index     - Image index
            - path      - Image path
            - size      - Image size

            Returns:    Image object

            Warning ! setting other size here from original image size will kill it.
            change image size in c_renderer.image( ..., size=vector( othersize ) )
        """

        # Create new image object
        new_image = c_image( )

        # Load it
        new_image.load( path, size )

        # Save
        images: dict = self._data[ "images" ]
        images[ index ] = new_image

        # Return object
        return new_image


    def font( self, index: str ) -> c_font:
        """
            Search and returns Font object.

            Receives:   
            - index     - Font index

            Returns:    Font object
        """

        fonts:  dict = self._data[ "fonts" ]

        if index in fonts:
            return fonts[ index ]

        return None


    def image( self, index: str ) -> c_image:
        """
            Search and returns Image object.

            Receives:   
            - index     - Image index

            Returns:    Image object
        """

        images: dict = self._data[ "images" ]

        if index in images:
            return images[ index ]

        return None

    # endregion

    # region : Scenes

    def new_scene( self, config: scene_config_t = None ) -> c_scene:
        """
            Create and attach new scene to the application

            Receives:   
            - config [optional] - Scene config settings

            Returns:    Scene object
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
            Returns the active scene ptr.
            used mainly to change input handle between different scenes.

            Receives:   
            - new_index [optional] - New scene index

            Returns:    Scene object
        """

        if new_index is None:
            return self._scenes[ self._active_scene ]
        
        self._active_scene = math.clamp( new_index, 0, len( self._scenes ) )


    def next_scene( self ) -> None:
        """
            Moves to the next scene

            Receives:   None

            Returns:    None
        """

        self._active_scene = math.clamp( self._active_scene + 1, 0, len( self._scenes ) - 1 )


    def previous_scene( self ) -> None:
        """
            Moves to the previous scene

            Receives:   None

            Returns:    None
        """
        
        self._active_scene = math.clamp( self._active_scene - 1, 0, len( self._scenes ) - 1 )

    # endregion

    # region : Events

    def initialize_events( self ) -> None:
        """
            Initialize events and set them up.

            Receives:   None

            Returns:    None
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
        glfw.set_cursor_pos_callback(       self._app, self.__event_mouse_position )
        glfw.set_mouse_button_callback(     self._app, self.__event_mouse_input )
        glfw.set_scroll_callback(           self._app, self.__event_mouse_scroll )
        glfw.set_drop_callback(             self._app, self.__event_path_drop )
        glfw.set_window_size_callback(      self._app, self.__event_window_resize )
        glfw.set_window_pos_callback(       self._app, self.__event_window_position )
        glfw.set_window_maximize_callback(  self._app, self.__event_window_maximize )
        
        # Register that we done initializing events
        self._data[ "is_events_initialize" ] = True

    
    def __event_keyboard_input( self, window, key, scancode, action, mods ) -> None:
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
            Char input callback.

            Receives:   
            - window ptr  - GLFW Window
            - char        - char code

            Returns:    None
        """

        self.active_scene( ).event_char_input( window, char )

        event: c_event = self._events[ "char_input" ]

        event.attach( "window",      window )
        event.attach( "char",        char )

        event.invoke( )


    def __event_mouse_position( self, window, x, y ) -> None:
        """
            Mouse position change callback.

            Receives:   
            - window ptr  - GLFW Window
            - x           - x-axis of mouse position
            - y           - y-axis of mouse position

            Returns:    None
        """

        self.active_scene( ).event_mouse_position( window, x, y )

        event: c_event = self._events[ "mouse_position" ]

        event.attach( "window",      window )
        event.attach( "x",           x )
        event.attach( "y",           y )

        event.invoke( )


    def __event_mouse_input( self, window, button, action, mods ) -> None:
        """
            Mouse buttons input callback

            Receives:   
            - window ptr  - GLFW Window
            - button      - Mouse button
            - action      - Button action
            - mods        - no idea of mouse position

            Returns:    None
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
            Mouse scroll input callback

            Receives:   
            - window ptr  - GLFW Window
            - x_offset    - x-axis of mouse wheel change (?)
            - y_offset    - y-axis of mouse wheel change (?)

            Returns:    None
        """

        self.active_scene( ).event_mouse_scroll( window, x_offset, y_offset )

        event: c_event = self._events[ "mouse_scroll" ]

        event.attach( "window",      window )
        event.attach( "x_offset",    x_offset )
        event.attach( "y_offset",    y_offset )

        event.invoke( )


    def __event_window_resize( self, window, width, height ) -> None:
        """
            Window resize callback

            Receives:   
            - window ptr  - GLFW Window
            - width       - new width of window
            - height      - new height of window

            Returns:    None
        """

        event: c_event = self._events[ "window_resize" ]

        event.attach( "window",      window )
        event.attach( "width",       width )
        event.attach( "height",      height )

        event.invoke( )


    def __event_window_position( self, window, x_pos, y_pos ) -> None:
        """
            Window position change callback.
            relative to the top left corner of the monitor it displayed on

            Receives:   
            - window ptr  - GLFW Window
            - x_pos       - x-axis position of the monitor
            - y_pos       - y-axis position of the monitor

            Returns:    None
        """

        event: c_event = self._events[ "window_position" ]

        event.attach( "window",      window )
        event.attach( "x_pos",       x_pos )
        event.attach( "y_pos",       y_pos )

        event.invoke( )


    def __event_window_maximize( self, window, maximized ) -> None:
        """
            Window maximized or not callback

            Receives:   
            - window ptr  - GLFW Window
            - maximized   - is window maximized or not

            Returns:    None
        """

        event: c_event = self._events[ "window_maximize" ]

        event.attach( "window",      window )
        event.attach( "maximized",   maximized )

        event.invoke( )


    def __event_path_drop( self, window, count, paths ) -> None:
        """
            Window maximized or not callback

            Receives:   
            - window ptr  - GLFW Window
            - count       - count of dropped files
            - paths       - list paths of files that were droped

            Returns:    None
        """

        event: c_event = self._events[ "path_drop" ]

        event.attach( "window",      window )
        event.attach( "count",      count )
        event.attach( "paths",      paths )

        event.invoke( )

    # endregion

    # region : Run Time

    def run( self ) -> None:
        """
            Main application window loop execution

            Receive :   None

            Returns :   None
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
            Render background for application

            Receive :   None

            Returns :   None
        """

        size:       vector  = self.window_size( )

        self._render.gradiant(
            vector( ), size, 
            self._config.back_color_1,
            self._config.back_color_2,
            self._config.back_color_3,
            self._config.back_color_4
        )


    def __draw_scenes( self ) -> None:
        """
            Draw all scenes

            Receive :   None

            Returns :   None
        """

        for scene in self._scenes:
            scene: c_scene = scene

            scene.show( scene.index( ) == self._active_scene )
            scene.draw( )


    def __process_input( self ) -> None:
        """
            Pulls and process window events and input

            Receive :   None

            Returns :   None
        """

        glfw.poll_events( )
        self._impl.process_inputs( )


    def __pre_new_frame( self ) -> None:
        """
            Before .new_frame was called

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "pre_draw" ]
        event.attach( "application", self )

        event.invoke( )

        imgui.new_frame( )


    def __post_new_frame( self ) -> None:
        """
            After new frame was done, render it

            Receive :   None

            Returns :   None
        """

        imgui.render( )
        self._impl.render( imgui.get_draw_data( ) )

        event: c_event = self._events[ "post_draw" ]
        event.attach( "application", self )

        event.invoke( )


    def __clean_buffer( self ) -> None:
        """
            Clears color buffer

            Receive :   None

            Returns :   None
        """

        gl.glClearColor( 1, 1, 1, 1 )
        gl.glClear( gl.GL_COLOR_BUFFER_BIT )


    def __unload( self ) -> None:
        """
            Application unload function

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "unload" ]
        event.attach( "ui", self )

        event.invoke( )

        self._impl.shutdown( )
        glfw.terminate( )

    # endregion

    # region : Utilities

    def window_size( self ) -> vector:
        """
            Get window size.
            Note ! Doesnt include the top bar windows adds.

            Receive :   None

            Returns :   Vector object
        """

        return vector( ).raw( glfw.get_window_size( self._app ) )


    def close_window( self, avoid_glfw_terminate: bool = False ) -> None:
        """
            Close application window.
            Moreover, cleans up the leftover

            Receives:   
            - avoid_glfw_terminate [optional] - Dont terminate glfw context on call

            Returns:    None
        """

        if self._app is not None:
            glfw.set_window_should_close( self._app, True )

        if not avoid_glfw_terminate:
            glfw.terminate( )

    # endregion
