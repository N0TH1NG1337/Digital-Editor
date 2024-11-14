# User Interface. Application .py

# Main application file

import OpenGL.GL as gl
import glfw
import imgui

from imgui.integrations.glfw import GlfwRenderer

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

from user_interface.button      import c_button_dynamic
from user_interface.text_input  import c_signle_input_logic, c_text_input
from user_interface.file_dialog import *
from user_interface.editor      import c_editor


class c_application:
    # Main application handler

    _app:               any             # GLFW Window

    _render:            c_renderer      # Render functions
    _impl:              GlfwRenderer    # Impl render backend

    _scenes:            list            # Attached scenes
    _active_scene:      int             # Active scene

    _events:            dict
    _data:              dict

    _last_error:        str

    _config:            dict


    def __init__( self ):
        """
            Default constructor for class
        """

        # Application handle must be at first None
        self._app           = None

        # Create render object
        self._render        = c_renderer( )

        # Set up scenes handlers
        self._scenes        = [ ]
        self._active_scene  = 0

        # On init last error is None
        self._last_error    = "None"

    # region : Window

    def initialize( self, title: str, position: vector, size: vector, vsync: bool = True ) -> bool:
        """
            Initialize window application.
            Returns of completed init call.
        """

        # First load GLFW
        if not self.__init_glfw( ):
            return False

        # Create data handle
        self._data = { }

        # Save received arguments
        self._data[ "position" ]    = position
        self._data[ "size" ]        = size
        self._data[ "title" ]       = title
        self._data[ "vsync" ]       = vsync

        if not self.__init_window( ):
            return False

        if not self.__init_backend( ):
            return False
        
        # Set up default config for application
        self.__init_config( )

        # Prepare to save font objects and images
        self._data[ "fonts" ]   = { }
        self._data[ "images" ]  = { }

        # Success
        return True


    @safe_call( None )
    def __init_glfw( self ) -> bool:
        """
            Creates GLFW Context.
        """

        if not glfw.init( ):
            self._last_error = "Failed to initialize OpenGL context"

            return False

        return True

    
    @safe_call( None )
    def __init_window( self ) -> bool:
        """
            Create and initialize window application itself.
            returns Result if success or not.
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
            glfw.terminate( )

            self._last_error = "Could not initialize Application"
            return False

        glfw.make_context_current( self._app )

        # Disable vsync
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
            Set up imgui context and OpenGL renderer backend.
            If some issue will occur @safe_call will catch it and return None.
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
            Create and stores Font object.
            also returns Font object for faster access
        """

        # Create new font object
        new_font = c_font( )

        # Load it
        new_font.load( path, size, "extand" )

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
            Create and stores Font object.
            Also returns Font object for faster access.

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
        """

        fonts:  dict = self._data[ "fonts" ]

        if index in fonts:
            return fonts[ index ]

        return None


    def image( self, index: str ) -> c_image:
        """
            Search and returns Image object.
        """

        images: dict = self._data[ "images" ]

        if index in images:
            return images[ index ]

        return None

    # endregion

    # region : Config

    def config( self, index: str = None ) -> dict:
        """
            Access config data
        """

        if index is None:
            return self._config
        
        if index in self._config:
            return self._config[ index ]
        
        raise Exception( "Failed to index config section" )


    def __init_config( self ) -> None:
        """
            Set up config data
        """

        self._config        = { }

        self._config[ "Application" ] = { 
            "background_color": [
                color( 203, 185, 213 ),
                color( 253, 231, 236 ),
                color( 156, 140, 182 ),
                color( 224, 205, 224 ) ]
        } 

        self._config[ "Scene" ] = {
            "fade_speed": 7
        }

        self._config[ "Button" ] = {
            "speed":        10,
            "pad":          10,
            "rounding":     10,
            "color_back":   color( 253, 231, 236 ),
            "color_icon":   color( 156, 140, 182 ),
            "color_text":   color( 156, 140, 182 )
        }

        self._config[ "Text Input" ] = {
            "speed":            10,
            "pad":              10,
            "rounding":         10,
            "seperator":        4,
            "color_raw_back":   color( 253, 231, 236 ),
            "color_back":       color( 253, 231, 236 ),
            "color_text":       color( 156, 140, 182 ),
            "color_value":      color( 156, 140, 182 ),
            "color_icon":       color( 156, 140, 182 ),
            "color_index":      color( 156, 140, 182 ),
            "color_seperate":   color( 156, 140, 182 )
        }

        self._config[ "File Dialog" ] = {
            "speed":            10,
            "rounding":         10,
            "pad":              10,
            "color_back":       color( 253, 231, 236 ),
            "color_button":     color( 156, 140, 182 ),
            "color_folder":     color( 156, 140, 182 )
        }

        self._config[ "Editor" ] = {
            "speed":            10,
            "rounding":         10,
            "pad":              20,
            "pad_for_number":   40,
            "color_back":       color( 253, 231, 236 ),
            "color_line":       color( 156, 140, 182, 20 ),
            "color_text":       color( 156, 140, 182 )
        }

    # endregion

    # region : Scenes

    def new_scene( self ) -> c_scene:
        """
            Create and returns new scene object
        """

        new_scene: c_scene = c_scene( self )

        # Push back our new scene
        self._scenes.append( new_scene )

        # Looks strange, but we just save the current scene index in it
        new_scene.index( self._scenes.index( new_scene ) )

        return new_scene
    
    
    def active_scene( self, new_index: int = None ) -> c_scene:
        """
            Returns the active scene ptr.
            used mainly to change input handle between different scenes.

            but can also be used to check what is being currently displayed for the user
        """

        if new_index is None:
            return self._scenes[ self._active_scene ]
        
        self._active_scene = math.clamp( new_index, 0, len( self._scenes ) )


    def next_scene( self ) -> None:
        """
            Moves to the next scene
        """

        self._active_scene = math.clamp( self._active_scene + 1, 0, len( self._scenes ) - 1 )


    def previous_scene( self ) -> None:
        """
            Moves to the previous scene
        """
        
        self._active_scene = math.clamp( self._active_scene - 1, 0, len( self._scenes ) - 1 )
    
    # endregion

    # region : Events

    def initialize_events( self ) -> None:
        """
            Initialize events and set them up.

            warning ! call before .run()
        """

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

            receives :  window ptr  - GLFW Window
                        key         - GLFW Key
                        scancode    - GLFW Scan code
                        action      - GLFW Action
                        mods        - To be honest I have no idea what is this for
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

            receives :  window ptr  - GLFW Window
                        char        - char code
        """

        self.active_scene( ).event_char_input( window, char )

        event: c_event = self._events[ "char_input" ]

        event.attach( "window",      window )
        event.attach( "char",        char )

        event.invoke( )


    def __event_mouse_position( self, window, x, y ) -> None:
        """
            Mouse position change callback

            receives :  window ptr  - GLFW Window
                        x           - x-axis of mouse position
                        y           - y-axis of mouse position
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

            receives :  window ptr  - GLFW Window
                        button      - Mouse button
                        action      - Button action
                        mods        - no idea
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

            receives :  window ptr  - GLFW Window
                        x_offset    - x-axis of mouse wheel change (?)
                        y_offset    - y-axis of mouse wheel change (?)
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

            receives :  window ptr  - GLFW Window
                        width       - new width of window
                        height      - new height of window
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

            receives :  window ptr  - GLFW Window
                        x_pos       - x-axis position of the monitor
                        y_pos       - y-axis position of the monitor
        """

        event: c_event = self._events[ "window_position" ]

        event.attach( "window",      window )
        event.attach( "x_pos",       x_pos )
        event.attach( "y_pos",       y_pos )

        event.invoke( )


    def __event_window_maximize( self, window, maximized ) -> None:
        """
            Window maximized or not callback

            receives :  window ptr  - GLFW Window
                        maximized   - is window maximized or not
        """

        event: c_event = self._events[ "window_maximize" ]

        event.attach( "window",      window )
        event.attach( "maximized",   maximized )

        event.invoke( )


    def __event_path_drop( self, window, count, paths ) -> None:
        """
            Window maximized or not callback

            receives :  window ptr  - GLFW Window
                        count       - count of dropped files
                        paths       - list paths of files that were droped
        """

        event: c_event = self._events[ "path_drop" ]

        event.attach( "window",      window )
        event.attach( "count",      count )
        event.attach( "paths",      paths )

        event.invoke( )


    def set_event( self, event_index: str, function: any, function_name: str) -> bool:
        """
            Register function to a specific event
        """

        if not event_index in self._events:
            self._last_error = "Invalid Event Name"

            return False
        
        event: c_event = self._events[ event_index ]
        event.set(function, function_name, True)

        return True

    # endregion

    # region : Run Time

    def run( self ) -> None:
        """
            Main application window loop
        """

        if not self._app:
            raise Exception( "Failed to find application window. make sure you have first called .create_window()" )
        
        if not "is_events_initialize" in self._data:
            raise Exception( "Failed to verify events initialize. make sure you have first called .initialize_events() before .run()" )
        
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
        """

        size: vector = self.get_window_size( )
        colors: list = self._config[ "Application" ][ "background_color" ]

        self._render.gradiant(
            vector( ), size, 
            colors[ 0 ],
            colors[ 1 ],
            colors[ 2 ],
            colors[ 3 ]
        )


    def __draw_scenes( self ) -> None:
        """
            Draw all scenes
        """

        for scene in self._scenes:
            scene: c_scene = scene

            scene.show( scene.index( ) == self._active_scene )
            scene.draw( )

    def __process_input( self ) -> None:
        """
            Pulls and process window events and input
        """

        glfw.poll_events( )
        self._impl.process_inputs( )


    def __pre_new_frame( self ) -> None:
        """
            Before .new_frame was called
        """

        event: c_event = self._events[ "pre_draw" ]
        event.attach( "ui", self )

        event.invoke( )

        imgui.new_frame( )


    def __post_new_frame( self ) -> None:
        """
            After new frame was done, render it
        """

        imgui.render( )
        self._impl.render( imgui.get_draw_data( ) )

        event: c_event = self._events[ "post_draw" ]
        event.attach( "ui", self )

        event.invoke( )


    def __clean_buffer( self ) -> None:
        """
            Clears color buffer
        """

        gl.glClearColor( 1, 1, 1, 1 )
        gl.glClear( gl.GL_COLOR_BUFFER_BIT )


    def __unload( self ) -> None:
        """
            Application unload function
        """

        event: c_event = self._events[ "unload" ]
        event.attach( "ui", self )

        event.invoke( )

        self._impl.shutdown( )
        glfw.terminate( )

    # endregion

    # region : Access data

    def render( self ) -> c_renderer:
        """
            Access render object
        """

        return self._render
    

    def get_clipboard( self ) -> str:
        """
            Gets clipboard data
        """

        result: bytes = glfw.get_clipboard_string( None )
        return result.decode( )
    

    def set_clipboard( self, text: str ) -> None:
        """
            Sets clipboard data
        """

        glfw.set_clipboard_string( None, text )


    def get_window_size( self ) -> vector:
        """
            Returns draw place size of window (Not windows top bar)
        """

        return vector( ).raw( glfw.get_window_size( self._app ) )
    

    def maximize_window( self ) -> None:
        """
            Set window to be maximized or disable it
        """

        glfw.maximize_window( self._app )

    
    def restore_window( self ) -> None:
        """
            Disable maximize or other staff
        """

        glfw.restore_window( self._app )


    def exit( self ) -> None:
        """
            Stops the main loop
        """

        # using sys.exit() mid callback result exception...
        glfw.set_window_should_close( self._app, True )

    # endregion 
