"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Editor

    description : Test Editor class
"""

import glfw

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


EXCEPTIONS = {
    "{": "{}",
    "(": "()",
    "[": "[]",
    "\"": "\"\""
}


class editor_config_t:
    speed:          int     = 10
    pad:            int     = 10

    pad_for_number: int     = 50

    roundness:      int     = 6

    text_color:     color   = color( 255, 255, 255)
    line_color:     color   = color( 255, 255, 255 )
    locked_color:   color   = color( 255, 100, 100 )
    back_color:     color   = color( 10, 10, 30, 100 )


class c_line:
    text:       str
    number:     int

    is_used:    bool
    is_locked:  bool
    is_hovered: bool

    position:   vector

    alpha:      float


class c_editor:
    
    _parent:                any
    _index:                 int

    _position:              vector
    _size:                  vector

    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _config:                editor_config_t

    _events:                dict

    _offset:                int
    _mouse_position:        vector
    _is_hovered:            bool
    _is_hovered_discard:    bool
    _is_hovered_update:     bool

    _discard_size:          vector
    _update_size:           vector

    _file:                  str     # File name
    _lines:                 list    # This is a little bit different from default editor
    _line_height:           int

    _selected_line:         int

    # region : Initialize editor

    def __init__( self, parent: any, position: vector, size: vector, font: c_font, config: editor_config_t = None ):
        """
            Default constructor for Editor object.

            Receive 
            - parent                - Parent to attach this editor to
            - position              - Position in the parent
            - size                  - Size of the editor window
            - font                  - Font for the text in editor
            - config [optional]     - Config settings for editor

            Returns :   Editor object
        """

        self._config = config is None and editor_config_t( ) or config

        self._parent    = parent
        self._position  = position.copy( )
        self._size      = size.copy( )
        self._font      = font

        self.__initialize_parent( )
        self.__initialize_animations( )
        self.__initialize_information( )
        self.__initialize_events( )


    def __initialize_parent( self ):
        """
            Initialize parent attach.

            Receive :   None

            Returns :   None
        """

        self._render = self._parent.render( )

        self._index = self._parent.attach_element( self )

        this_id = f"Editor::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,           this_id )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,          this_id )
        self._parent.set_event( "char_input",       self.__event_char_input,            this_id )
        self._parent.set_event( "keyboard_input",   self.__event_keyboard_input,        this_id )


    def __initialize_animations( self ):
        """
            Initialize editor animations values

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Scroll", 0 )
        self._animations.prepare( "ShowActions", 0 )

    
    def __initialize_information( self ):
        """
            Initialize defaule values

            Receive :   None

            Returns :   None
        """
        
        self._lines                 = [ ]

        self._offset                = 0
        self._line_height           = self._font.size( ) + self._config.pad

        self._selected_line         = 0 # -number < will represent that we wait
        self._file                  = ""

        self._mouse_position        = vector( )
        self._discard_size          = vector( )
        self._update_size           = vector( )

        self._is_hovered            = False

        self._is_hovered_discard    = False
        self._is_hovered_update     = False

    
    def __initialize_events( self ):
        """
            Initialize editor events.

            Receive :   None

            Returns :   None
        """

        self._events = { }

        self._events[ "request_line" ] = c_event( )

    
    def add_line( self, text: str ):
        #### ?????

        new_line = c_line( )

        new_line.text = text

        new_line.number     = -1
        new_line.alpha      = 0

        new_line.is_hovered = False
        new_line.is_used    = False
        new_line.is_locked  = False

        new_line.position   = vector( )

        self._lines.append( new_line )

    
    def set_file( self, file_name: str ):
        self._file = file_name
    
    # endregion

    # region : Draw

    def draw( self, fade: float ):
        """
            Draw function of the button.

            Receive : 
            - fade - Parent fade factor

            Returns :   None
        """

        self.__animate( )
        self.__preform( )

        self._render.push_clip_rect( self._position, self._position + self._size )

        self.__draw_lines( fade )

        self.__draw_actions( fade )

        self._render.pop_clip_rect( )


    def __animate( self ):
        """
            Preform animations of the button.

            Receive :   None

            Returns :   None
        """

        speed: int = self._config.speed

        self._animations.update( )

        self._animations.preform( "Scroll", self._offset, speed, 1 )
        self._animations.preform( "ShowActions", self._selected_line > 0 and 1 or 0, speed )

    
    def __preform( self ):
        """
            Preform all the small calculations.

            Receive :   None

            Returns :   None
        """

        self._discard_size  = self._render.measure_text( self._font, "discard" )
        self._update_size   = self._render.measure_text( self._font, "update" )


    def __draw_lines( self, fade: float ):
        """
            Draw the lines.

            Receive : 
            - fade - Parent fade factor

            Returns :   None
        """

        if len( self._lines ) == 0:
            return

        speed:          int     = self._config.speed
        pad:            int     = self._config.pad
        pad_for_number: int     = self._config.pad_for_number
        text_color:     color   = self._config.text_color
        locked_color:   color   = self._config.locked_color
        line_color:     color   = self._config.line_color

        scroll:         float   = self._animations.value( "Scroll" )
        start_position: vector  = vector( self._position.x + pad_for_number + pad * 2, self._position.y + pad + scroll )

        index   = 0
        drop    = 0

        for line in self._lines:
            index = index + 1   # Line index

            line: c_line = line

            line.number         = index
            line_number: str    = str( index )

            normalized_drop = drop + pad / 2
            add_for_selected = 0
            if self._selected_line == index:
                add_for_selected = 10

                self._render.rect( start_position + vector( 0, drop ), start_position + vector( 4, drop + self._line_height ), color( 150, 150, 255 ) * fade, 2 )

            line.position   = vector( 0, normalized_drop + scroll + pad )
            text_position   = start_position + vector( add_for_selected, normalized_drop )
            number_position = start_position + vector( - self._render.measure_text( self._font, line_number ).x - pad * 2, normalized_drop )

            current_line_color = line_color

            if line.is_locked:
                current_line_color = locked_color

            if line.is_hovered:
                line.alpha = self._animations.fast_preform( line.alpha, fade, speed )
            else:
                line.alpha = self._animations.fast_preform( line.alpha, 0.5, speed ) * fade

            self._render.text( self._font, text_position, text_color * line.alpha, line.text )
            self._render.text( self._font, number_position, current_line_color * line.alpha, line_number )

            drop = drop + self._line_height
            

    def __draw_actions( self, fade: float ):
        """
            Draw line actions when selected line.

            Receive :   
            - fade - Fade factor of the parent

            Returns :   None
        """

        pad:            int     = self._config.pad
        roundness:      int     = self._config.roundness
        text_color:     color   = self._config.text_color
        back_color:     color   = self._config.back_color

        alpha:          float   = self._animations.value( "ShowActions" ) * fade

        back_size:      vector  = vector( self._discard_size.x + self._update_size.x + pad * 3, self._discard_size.y + pad )
        position:       vector  = self._position + vector( self._size.x - back_size.x, 0 )

        self._render.rect( position, position + back_size, back_color * alpha, roundness )

        self._render.text( self._font, position + vector( pad, pad / 2 ), text_color * alpha, "discard" )
        self._render.text( self._font, position + vector( pad * 2 + self._discard_size.x, pad / 2 ), text_color * alpha, "update" )

        #ShowActions

    # endregion

    # region : Input

    def __event_mouse_position( self, event ):
        """
            Mouse position change callback.

            Receive :   
            - event - Event information

            Returns :   None
        """
        
        x = event( "x" )
        y = event( "y" )

        self._mouse_position.x = x
        self._mouse_position.y = y

        self.__hover_editor( )
        if not self._is_hovered:
            return

        self.__hover_lines( )


    def __event_mouse_input( self, event ):
        """
            Mouse buttons input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        button = event( "button" )
        action = event( "action" )

        if not button == glfw.MOUSE_BUTTON_LEFT or not action == glfw.PRESS:
            return
        
        self.__handle_lines( )


    def __event_mouse_scroll( self, event ):
        """
            Mouse scroll input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_hovered:
            return

        y_offset = event( "y_offset" )

        amount_items    = len( self._lines )

        drop            = amount_items * self._line_height
        fixed_drop      = self._size.y - self._config.pad

        if drop > fixed_drop:
            drop_min    = fixed_drop - drop
        else:
            drop_min = 0

        self._offset = math.clamp( self._offset + y_offset * 20, drop_min, 0 )


    def __event_char_input( self, event ):
        
        pass


    def __event_keyboard_input( self, event ):
        
        pass


    def __hover_editor( self ):
        """
            Handle if the user hover the editor.

            Receive :   None

            Returns :   None    
        """

        if self._mouse_position.is_in_bounds( self._position, self._size.x, self._size.y ):

            self._is_hovered = self._parent.try_to_get_handle( self._index )
        else:
            
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False


    def __hover_lines( self ):
        """
            Handle if the user hover one of the lines.

            Receive :   None

            Returns :   None
        """
        
        text_height = self._font.size( )

        for line in self._lines:
            line: c_line = line

            line_position   = self._position + line.position
            line.is_hovered = not line.is_locked and self._mouse_position.is_in_bounds( line_position, self._size.x, text_height )

        
    def __handle_lines( self ):
        """
            Handle if the user clicked on a line.
        """

        for line in self._lines:
            line: c_line = line

            if line.is_hovered and not line.is_locked:
                return self.__event_request_line( line.number )


    def __event_request_line( self, line: int ):
        """
            Request specific line.

            Receive : 
            - line - Line number 

            Returns :   None
        """
        
        self._selected_line = line * ( -1 )

        event: c_event = self._events[ "request_line" ]
        event.attach( "file", self._file )
        event.attach( "line", line )

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


    # region : Utilities

    def clear( self ):
        """ 
            Clear editor content.

            Receive :   None

            Returns :   None
        """

        self._lines.clear( )
    

    def get_file( self ):
        return self._file

    
    def lock_line( self, line: int ):
        """
            Lock line.

            Receive :
            - line - Line number

            Returns :   None
        """

        line = line - 1

        if line < 0 or line > len( self._lines ):
            return
        
        line_obj: c_line = self._lines[ line ]
        line_obj.is_locked = True

    
    def unlock_line( self, line: int ):
        """
            UnLock line.

            Receive :
            - line - Line number

            Returns :   None
        """

        line = line - 1

        if line < 0 or line > len( self._lines ):
            return
        
        line_obj: c_line = self._lines[ line ]
        line_obj.is_locked = False

    
    def accept_line( self, file_name: str, line: int, accept: bool ):
        """
            Line request accepted.

            Receive : 
            - line - Line number 

            Returns :   None
        """

        if self._file != file_name:
            return
        
        correct = self._selected_line * ( -1 )
        if correct != line:
            return
        
        if not accept:
            return
        
        self._selected_line = line

    # endregion

