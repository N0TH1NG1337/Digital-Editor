# User Interface. Scene .py

import OpenGL.GL as gl
import glfw
import imgui

from utilities.color    import  color
from utilities.vector   import  vector
from utilities.math     import  math
from utilities.wrappers import  safe_call
from utilities.image    import  c_image
from utilities.font     import  c_font
from utilities.event    import  c_event

from user_interface.render      import c_renderer
from user_interface.animation   import c_animations
from user_interface.window      import c_window


class c_scene:
    
    _parent:        any     # c_application
    _index:         int

    _show:          bool
    _events:        dict
    _ui:            list

    _windows:        list        # TODO ! pop up windows queue.
    # if this queue is not empty. if disable input for ui and attach only the last one to receive input
    # this islike a sub scene to a specific scene.

    # will have to create a class window popup with interactions

    _render:        c_renderer
    _animations:    c_animations

    _config:        dict

    _active_handle: int


    def __init__( self, parent: any ):
        """
            Default constructor for class
        """

        # Set parent. 
        self._parent            = parent

        # Draw information 
        self._index             = -1
        self._show              = False

        # Create list to save ui elements
        self._ui                = [ ]

        # Use to save floatting windows
        self._windows           = [ ]

        self._active_handle     = -1

        # Get config information
        self._config            = self._parent.config( "Scene" )

        # Complete set up of scene
        self.__initialize_draw( )
        self.__initialize_events( )
        
    
    # region : Draw

    def __initialize_draw( self ) -> None:
        """
            Set up draw data
        """

        self._render        = self._parent.render( )
        self._animations    = c_animations( )

        self._animations.prepare( "Fade", 0 )
        self._animations.prepare( "SlideIn", -50 )

    
    def draw( self ) -> None:
        """
            Draw function for scene.
            called each frame
        """

        self._animations.update( )

        speed = self._config[ "fade_speed" ]
        fade:       float   = self._animations.preform( "Fade", self._show and 1 or 0, speed )

        slide_in:   float   = self._animations.preform( "SlideIn", not self._show and -50 or 0, speed, 1 )

        self._render.push_position( vector( 0, slide_in ) )

        event: c_event = self._events[ "draw" ]
        event.attach( "scene", self )

        event.invoke( )

        for item in self._ui:
            item.draw( fade )

        self._render.pop_position( )

    # endregion

    # region : Events

    def __initialize_events( self ) -> None:
        """
            Set up scene events
        """

        self._events = { }

        self._events[ "draw" ]              = c_event( )

        self._events[ "keyboard_input" ]    = c_event( )
        self._events[ "char_input" ]        = c_event( )
        self._events[ "mouse_position" ]    = c_event( )
        self._events[ "mouse_input" ]       = c_event( )
        self._events[ "mouse_scroll" ]      = c_event( )


    def event_keyboard_input( self, window, key, scancode, action, mods ) -> None:
        """
            Keyboard input callback.

            receives :  window ptr  - GLFW Window
                        key         - GLFW Key
                        scancode    - GLFW Scan code
                        action      - GLFW Action
                        mods        - To be honest I have no idea what is this for
        """

        # Example
        # if self.is_any_window_active( ):
        #     return self.get_last_window( ).event_keyboard_input( window, key, scancode, action, mods )

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

            receives :  window ptr  - GLFW Window
                        char        - char code
        """

        event: c_event = self._events[ "char_input" ]

        event.attach( "window",      window )
        event.attach( "char",        char )

        event.invoke( )


    def event_mouse_position( self, window, x, y ) -> None:
        """
            Mouse position change callback

            receives :  window ptr  - GLFW Window
                        x           - x-axis of mouse position
                        y           - y-axis of mouse position
        """

        event: c_event = self._events[ "mouse_position" ]

        event.attach( "window",     window )
        event.attach( "x",          x )
        event.attach( "y",          y )

        event.invoke( )


    def event_mouse_input( self, window, button, action, mods ) -> None:
        """
            Mouse buttons input callback

            receives :  window ptr  - GLFW Window
                        button      - Mouse button
                        action      - Button action
                        mods        - no idea
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

            receives :  window ptr  - GLFW Window
                        x_offset    - x-axis of mouse wheel change (?)
                        y_offset    - y-axis of mouse wheel change (?)
        """

        event: c_event = self._events[ "mouse_scroll" ]

        event.attach( "window",      window )
        event.attach( "x_offset",    x_offset )
        event.attach( "y_offset",    y_offset )

        event.invoke( )

    
    def set_event( self, event_index: str, function: any, function_name: str ) -> None:
        """
            Registers functions to a event
        """

        if not event_index in self._events:
            raise Exception( f"Failed to index event { event_index }" )
        
        event: c_event = self._events[ event_index ]
        event.set( function, function_name, True )

    # endregion

    # region : General

    def attach_element( self, item: any ) -> int:
        """
            Attach new element to this scene
        """

        self._ui.append( item )

        return self._ui.index( item )
    

    def index( self, new_value: int = None ) -> int:
        """
            Returns / Sets the current scene index in the queue
        """
        if new_value is None:
            return self._index
        
        self._index = new_value

    
    def show( self, new_value: bool = None ) -> bool:
        """
            Return / Sets if the scene should show
        """

        if new_value is None:
            return self._show
        
        self._show = new_value

    
    def parent( self ) -> any:
        """
            Returns current scene parent
        """

        return self._parent
    

    def render( self ) -> c_renderer:
        """
            Access render object
        """

        return self._render
    

    def animations( self ) -> c_animations:
        """
            Access the animations object
        """

        return self._animations
    

    def element( self, index: int ) -> any:
        """
            Returns specific element attached to this scene
        """

        if index in self._ui:
            return self._ui[ index ]
        
        return None

    
    def try_to_get_handle( self, index: int ) -> bool:
        """
            Tries to a get handle for specific item.
            Used to proccess 1 input at a time
        """

        if self._active_handle != -1 and index != self._active_handle:
            return False
        
        self._active_handle = index

        return True
    
    def release_handle( self, index: int ) -> None:
        """
            If a specific index called it and active_handle is setted.
            It will release it.
        """

        if self._active_handle != -1 and self._active_handle == index:
            self._active_handle = -1

    def is_this_active( self, index: int ) -> bool:
        """
            Gets the active handle index
        """

        return self._active_handle == index
    
    # endregion

    # region : Pop up Windows

    def create_window( self ) -> c_window:

        new_window = c_window( )

        self._windows.append( new_window )
        new_window.index( self._windows.index( new_window ) )

    def is_any_window_active( self ) -> bool:

        return len( self._windows ) != 0
    
    def get_last_window( self ) -> c_window:

        return self._windows[ len( self._windows ) - 1 ]

    # endregions 

