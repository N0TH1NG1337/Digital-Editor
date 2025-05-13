"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Text Input

    description : Text input classes
"""

import glfw
import time

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


class text_input_config_t:
    speed:      int
    pad:        int
    separate:   int
    roundness:  int

    color_background:   color
    color_shadow:       color
    color_theme:        color
    color_selection:    color

    color_icon:         color
    color_label:        color 
    color_input:        color

    def __init__( self ):

        self.speed:      int = 10    # Animations speed
        self.pad:        int = 10    # Default pad
        self.separate:   int = 4     # Separate line
        self.roundness:  int = 10    # Background roundness

        self.color_background:   color = color( 0, 0, 0, 150 )
        self.color_shadow:       color = color( 0, 0, 0, 150 )
        self.color_theme:        color = color( 207, 210, 215 )
        self.color_selection:    color = color( 207, 210, 215 )

        self.color_icon:         color = color(  )
        self.color_label:        color = color(  )

        self.color_input:        color = color(  )


class c_single_input_logic:
    # Logic class for single line text input

    # region : Protected attributes

    _parent:                any     # c_scene / c_window

    _position:              vector                  
    _relative_position:     vector                  

    _size:                  vector                  

    _input:                 str                     
    _font:                  c_font                  

    _render:                c_renderer              
    _animations:            c_animations            

    _is_hovered:            bool
    _is_typing:             bool
    _is_ctrl:               bool
    _is_password:           bool
    _is_holding:            bool

    _mouse_position:        vector
    _text_size:             vector

    _cursor_index:          vector
    _selection_position:    vector
    _selection_index:       vector

    _offset:                float

    _config:                text_input_config_t

    # endregion

    # region : Initialization

    def __init__( self, parent: any, position: vector, size: vector, font: c_font, default_value: str = "", is_password: bool = False, config: text_input_config_t = None ):
        """
            Initializes the single-line text input logic.

            Receives:
            - parent (any): The parent object or container for this input logic.
            - position (vector): The initial position (x, y) of the input.
            - size (vector): The initial size (width, height) of the input.
            - font (c_font): The font object to use for rendering the text.
            - default_value (str, optional): The initial text value of the input. Defaults to "".
            - is_password (bool, optional): A flag indicating if the input should obscure text (e.g., for passwords). Defaults to False.
            - config (text_input_config_t, optional): Configuration settings for the text input. If None, default configuration is used. Defaults to None.

            Returns:
            - c_single_input_logic: The newly initialized single input logic object.
        """

        # Set config
        self._config = config is None and text_input_config_t( ) or config

        # Set parent
        self._parent = parent

        # Set position and size
        self._position  = position.copy( )
        self._size      = size.copy( )

        # Set default value
        self._input = default_value

        # Set font for render
        self._font = font

        # Is this password input ?!?
        self._is_password = is_password

        # Initialize complete attachment
        self.__init_attachment( )

        # Initialize animations of the widget
        self.__init_animations( )

        # Initialize default and first values for the widget 
        self.__init_bones( )


    def __init_attachment( self ):
        """
        Initializes the rendering attachment for the text input logic,
        linking it to the parent's rendering context.

        Receives: None

        Returns: None
        """

        self._render = self._parent.render( )


    def __init_animations( self ):
        """
        Initializes the animation system for the text input widget,

        Receives: None

        Returns: None
        """

        # Create standalone animations handler
        self._animations = c_animations( )

        self._animations.prepare( "width",      0 )
        self._animations.prepare( "text_width", 0 )
        self._animations.prepare( "index_fade", 0 )
        self._animations.prepare( "index_pos",  0 )
        self._animations.prepare( "typing",     0 )
        self._animations.prepare( "offset",     0 )

        if self._is_password:
            self._animations.prepare( "show_value", 0 )


    def __init_bones( self ):
        """
        Initializes default and initial values for internal state variables
        of the text input logic, such as hover state, typing state, and cursor/selection positions.

        Receives: None

        Returns: None
        """

        self._relative_position = self._position.copy( )

        self._is_hovered    = False
        self._is_typing     = False
        self._is_ctrl       = False
        self._is_holding    = False

        self._mouse_position    = vector( )
        self._text_size         = vector( )

        self._cursor_index           = vector( 0, None )
        self._selection_position     = vector( None, None, 0 )
        self._selection_index        = vector( -1, -1, time.time( ) )

        self._offset = 0

    # endregion

    # region : Drawing

    def draw( self, fade: float ):
        """
        Draws the text input logic on the screen.

        This method handles the rendering of the text, cursor, and selection highlights.
        It prioritizes performance by minimizing function calls within the drawing loop.

        Receives:
        - fade (float): The current fade value for the widget (0.0 for invisible, 1.0 for fully visible).

        Returns: None
        """

        if fade == 0:
            return

        # Do some updates
        self._animations.update( )
        self.__update_relative_position( )
        self.__update_selection( )

        # Get values to work with
        speed:          int     = self._config.speed
        pad:            int     = self._config.pad

        # Get texts based on configuration and events
        visible_text:   str = self.__get_visible_text( )
        cursor_text:    str = self.__get_cursor_text( )

        # Calculate the cursor text sizes
        vis_sizes:  vector = self._render.measure_text( self._font, visible_text )
        cur_sizes:  vector = self._render.measure_text( self._font, cursor_text )

        # Convert the clicked position into index
        if self._cursor_index.y is not None:
            self._cursor_index.x = self.__relative_to_index( self._cursor_index.y, visible_text )
            self._cursor_index.y = None

        show_cursor:    bool  = self._is_typing and ( self._selection_position.x is None and self._selection_position.y is None )

        # Animate the cursor index when typing and not
        index_fade:     float = self._animations.perform( "index_fade", show_cursor and 1 or 0, speed) * fade
        typing_fade:    float = self._animations.perform( "typing", self._is_typing and 1 or 0, speed ) * fade
        offset:         float = self._animations.perform( "offset", self._offset, speed, 1 )

        index_pos:      float = self._animations.perform( "index_pos", cur_sizes.x + offset, speed * 2 )

        # Create clipping rect vectors
        start_clip: vector = vector( self._position.x + pad, self._position.y )
        end_clip:   vector = vector( start_clip.x + self._size.x, start_clip.y + self._size.y )

        self.__update_offset( start_clip, vector( end_clip.x, start_clip.x ), cur_sizes, vis_sizes )

        # Start the clip
        self._render.push_clip_rect( vector( start_clip.x - 1, start_clip.y ), vector( end_clip.x + 1, end_clip.y ), True )

        # Render everything here
        self.__draw_text( fade, start_clip, visible_text, offset )
        self.__draw_cursor( index_fade, start_clip, index_pos )
        self.__draw_selection( typing_fade, start_clip, offset, visible_text )

        # Stop the clip
        self._render.pop_clip_rect( )

        # Animate the width after everything is done rendering
        correct_pad = pad * 2
        self._animations.perform( "width",      correct_pad + self._size.x, speed, 1 )
        self._animations.perform( "text_width", correct_pad + self._text_size.x, speed, 1 )


    def __update_relative_position( self ):
        """
        Updates the absolute position of the text input widget based on its
        relative position to its parent.

        Receives: None

        Returns: None
        """

        parent_position:            vector  = self._parent.relative_position( )

        self._relative_position.x = parent_position.x + self._position.x
        self._relative_position.y = parent_position.y + self._position.y

    
    def __update_offset( self, position: vector, edges: vector, cursor_text_size: vector, visible_text_size: vector ):
        """
        Updates the horizontal offset of the text within the input field
        to ensure the cursor and selected text remain visible as the user types
        or interacts with the input.

        Receives:
        - position (vector): The current screen position of the text input field.
        - edges (vector): A vector representing the left and right edges of the visible input area.
        - cursor_text_size (vector): The size (width, height) of the text up to the cursor.
        - visible_text_size (vector): The total size (width, height) of the currently displayed text.

        Returns: None
        """
        
        if (visible_text_size.x < self._size.x):
            self._offset = 0
            return

        
        pad: int = self._config.pad

        set_offset = position.x + self._offset + cursor_text_size.x + 1

        edges.x -= pad * 2
        edges.y += pad * 2

        if self.is_something_selected( ):

            if self._selection_position.z == 1:

                right_delta = edges.x - self._mouse_position.x
                left_delta = self._mouse_position.x - edges.y

                if right_delta < 10:
                    self._offset -= 1

                if left_delta < 10:
                    self._offset += 1

        else:
            # Right edge
            if set_offset > edges.x:
                self._offset -= set_offset - edges.x

            if ( set_offset - 1 ) < edges.y:
                self._offset += edges.y - ( set_offset - 1 )

        
        self._offset = math.clamp( self._offset, self._size.x - visible_text_size.x, 0 )

    
    def __update_selection( self ):
        """
        Updates the end position of the text selection based on the current
        mouse position while a selection is being made.

        Receives: None

        Returns: None
        """
        
        if self._selection_position.z == 0:
            return

        value: float = self._mouse_position.x - ( self._relative_position.x + self._config.pad + self._offset )

        if self._selection_position.x is not None:
            self._selection_position.y = value
    

    def __draw_text( self, fade: float, position: vector, text: str, offset: float ):
        """
        Renders the input text within the text input field.

        Receives:
        - fade (float): The current fade value for the widget.
        - position (vector): The screen position where the text should be drawn.
        - text (str): The text string to render.
        - offset (float): The horizontal offset to apply to the text rendering.

        Returns: None
        """

        color_input:        color  = self._config.color_input
        self._text_size:    vector = self._render.measure_text( self._font, text )

        self._render.text( self._font, vector( position.x + offset, position.y + ( self._size.y - self._text_size.y ) / 2 ), color_input * fade, text )


    def __draw_cursor( self, fade: float, position: vector, offset: float ):
        """
        Renders the cursor within the text input field.

        Receives:
        - fade (float): The current fade value for the widget.
        - position (vector): The screen position where the cursor should be drawn.
        - offset (float): The horizontal offset for the cursor position.

        Returns: None
        """

        if fade == 0:
            return

        color_theme: color = self._config.color_theme

        self._render.rect(
            vector( position.x + offset - 1, position.y + 2 ),
            vector( position.x + offset + 1, position.y + self._size.y - 2 ),
            color_theme * fade
        )

    
    def __draw_selection( self, fade: float, position: vector, offset: float, text: str ):
        """
        Renders the text selection highlight within the input field.

        Receives:
        - fade (float): The current fade value for the widget.
        - position (vector): The screen position of the text input field.
        - offset (float): The horizontal offset of the text.
        - text (str): The currently displayed text.

        Returns: None
        """

        if fade == 0:
            self._selection_position.x = None
            self._selection_position.y = None
            return
        
        if self._selection_position.x is None or self._selection_position.y is None:
            return
        
        start:  float = min( self._selection_position.x, self._selection_position.y ) 
        end:    float = max( self._selection_position.x, self._selection_position.y )

        self._selection_index.x = self.__relative_to_index( start, text )
        self._selection_index.y = self.__relative_to_index( end, text )

        if self._selection_position.z == 0 and self._selection_index.x == self._selection_index.y:
            self.__reset_selection( )
            return

        color_selection:    color   = self._config.color_selection
        separate:           int     = self._config.separate

        if self._selection_position.z == 1:

            self._render.neon(
                vector( position.x + offset + start, position.y + self._size.y - separate ),
                vector( position.x + offset + end, position.y + self._size.y ),
                color_selection * fade,
                18,
                separate / 2
            )

        else:
            start_text  = self._render.measure_text( self._font, text[ :self._selection_index.x ] ).x
            end_text    = self._render.measure_text( self._font, text[ :self._selection_index.y ] ).x

            self._render.neon(
                vector( position.x + offset + start_text, position.y + self._size.y - separate ),
                vector( position.x + offset + end_text, position.y + self._size.y ),
                color_selection * fade,
                18,
                separate / 2
            )


    def __get_visible_text( self ) -> str:
        """
        Returns the text that should be displayed in the input field.
        If the input is a password field, it partially obscures the text
        based on whether the input is currently being held.

        Receives: None

        Returns:
        - str: The text to be displayed.
        """

        if self._is_password:
            length: int = len( self._input )
            value: float = self._animations.perform( "show_value", self._is_holding and length or 0, self._config.speed, 0.1 )
            
            index:  int = int( value )
            start:  str = self._input[ :index ]
            end:    str = "*" * ( length - index )

            return start + end

        return self._input
    

    def __get_cursor_text( self ) -> str:
        """
        Returns the portion of the visible text that appears before the cursor.

        Receives: None

        Returns:
        - str: The text before the cursor.
        """

        return self.__get_visible_text( )[ :self._cursor_index.x ]

    
    def __relative_to_index( self, relative_width: float, text: str ) -> int:
        """
        Calculates the character index in the text based on a given relative width.
        This is used to determine the cursor or selection position based on mouse coordinates.

        Note: This method iterates through the text, measuring the width of substrings
              to find the index that corresponds to the given relative width. It includes
              logic to handle potential discrepancies between individual character widths
              and the width of the entire text.

        Receives:
        - relative_width (float): The horizontal distance from the start of the text input area.
        - text (str): The currently displayed text.

        Returns:
        - int: The character index in the text that corresponds to the given relative width.
        """
        
        # Credit - My friend
        # The use of https://github.com/BalazsJako/ImGuiColorTextEdit/blob/master/TextEditor.cpp#L324
        # logic is complete cancer since ImGui calculations for each char and whole text are different...

        selected_index: int = 0
        length:         int = len( text )

        for i in range( length + 1 ):

            substring:  str     = text[ :i ]
            width:      float   = self._render.measure_text( self._font, substring ).x

            if width > relative_width:
                
                fixed_index:    int     = max( 0, i - 1 )
                prev_width:     float   = self._render.measure_text( self._font, text[ :fixed_index ] ).x

                if abs( width - relative_width ) < abs( prev_width - relative_width ):
                    selected_index = i
                else:
                    selected_index = fixed_index

                break

            else:
                selected_index = i

        return selected_index
    
    # endregion

    # region : Input handle

    def event_mouse_position( self, event ):
        """
        Callback for mouse position change

        Receives:
        - event (callable): An function for receiving information
                             about the event

        Returns: None
        """

        x = event( "x" )
        y = event( "y" )

        self._mouse_position.x = x
        self._mouse_position.y = y

        pad: int = self._config.pad * 2

        self._is_hovered = self._mouse_position.is_in_bounds( self._relative_position, self._size.x + pad, self._size.y )


    def event_mouse_input( self, event ):
        """
        Callback for mouse button input events.

        Handles left and right mouse button presses and releases within the
        text input area, managing focus, text selection, and potential
        contextual actions (like holding for password reveal).

        Receives:
        - event (callable): A function that, when called with a string key,
                          returns information about the mouse event.

        Returns: None
        """
        
        button = event( "button" )
        action = event( "action" )

        if button == glfw.MOUSE_BUTTON_RIGHT:
            if action == glfw.PRESS:
                self._is_holding = self._is_hovered

            if action == glfw.RELEASE and self._is_holding:
                self._is_holding = False
            
            return

        if button != glfw.MOUSE_BUTTON_LEFT:
            return

        value: float = self._mouse_position.x - ( self._relative_position.x + self._config.pad + self._offset )

        if self._is_hovered and action == glfw.PRESS:
            self._cursor_index.y = value

            self._selection_position.x = value
            self._selection_position.z = 1
            self._selection_index.z = time.time( )

            return

        if action == glfw.RELEASE and self._selection_position.x is not None:
            self._selection_position.y = value

            if ( time.time( ) - self._selection_index.z ) < 0.1:
                self.__reset_selection( )

            self._selection_position.z = 0

            return


    def event_char_input( self, event ):
        """
        Callback for character input events.

        Handles the input of printable characters when the text input
        is in the typing state, inserting the entered character at the
        current cursor position.

        Receives:
        - event (callable): A function that, when called with a string key,
                          returns information about the character event.

        Returns: None
        """
        
        if not self._is_typing:
            return

        self.insert( chr( event( "char" ) ) )


    def event_keyboard_input( self, event ):
        """
        Callback for keyboard input events.

        Handles various keyboard actions, including character input,
        cursor movement, text deletion, clipboard operations (copy, paste),
        and control key combinations, when the text input is in the typing state.

        Receives:
        - event (callable): A function that, when called with a string key,
                          returns information about the keyboard event.

        Returns: None
        """
        
        if not self._is_typing:
            return

        key         = event( "key" )
        action      = event( "action" ) 

        self.__handle_ctrl( key, action )

        if action == glfw.PRESS:
            self.__handle_clipboard( key )
            return self.__handle_default_actions( key, False )

        if action == glfw.REPEAT:
            return self.__handle_default_actions( key, True )
    
    # endregion

    # region : Utilities

    def value( self, new_value: str = None ) -> str:
        """
        Gets or sets the current text value of the input field.
        When setting a new value, it also moves the cursor to the end of the text.

        Receives:
        - new_value (str, optional): The new text value to set for the input.
                                      If None, the current value is returned. Defaults to None.

        Returns:
        - str: The current text value of the input field.
        """

        if new_value is None:
            return self._input
        
        self._input = new_value
        self._cursor_index.x = len( self._input )
        return new_value
    

    def is_typing( self, new_value: bool = None ) -> bool:
        """
        Gets or sets the typing state of the input field.

        Receives:
        - new_value (bool, optional): The new typing state to set.
                                       If None, the current typing state is returned.
                                       Defaults to None.

        Returns:
        - bool: The current typing state of the input field.
        """

        if new_value is None:
            return self._is_typing
        
        self._is_typing = new_value
        return new_value
    

    def position( self, new_value: vector = None ) -> vector:
        """
        Gets or sets the local position of the text input field.

        Receives:
        - new_value (vector, optional): The new position (x, y) to set.
                                        If None, the current position is returned.
                                        Defaults to None.

        Returns:
        - vector: The current local position of the text input field.
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y
        return new_value
    

    def size( self, new_value: vector = None ) -> vector:
        """
        Gets or sets the size (width and height) of the text input field.

        Receives:
        - new_value (vector, optional): The new size (width, height) to set.
                                        If None, the current size is returned.
                                        Defaults to None.

        Returns:
        - vector: The current size of the text input field.
        """
        
        if new_value is None:
            return self._size
        
        self._size.x = new_value.x
        self._size.y = new_value.y
        return new_value


    def fixed_size( self ) -> vector:
        """
        Returns the current fixed size of the text input field, where the
        width might be animated, but the height remains constant.

        Receives: None

        Returns:
        - vector: A vector representing the current fixed size (animated width, original height).
        """

        return vector( self._animations.value( "width" ), self._size.y )
    

    def text_width( self ) -> float:
        """
        Returns the current animated width of the text content within the
        input field.

        Receives: None

        Returns:
        - float: The current animated width of the text content.
        """

        return self._animations.value( "text_width" )
    

    def is_hovered( self ) -> bool:
        """
        Returns the current hover state of the text input field.

        Receives: None

        Returns:
        - bool: True if the input is hovered, False otherwise.
        """

        return self._is_hovered
    

    def insert( self, text: str ):
        """
        Inserts a given text string at the current cursor position within the input field,
        replacing any currently selected text. The cursor position is then updated
        to the end of the inserted text.

        Receives:
        - text (str): The text string to insert.

        Returns: None
        """

        self.__remove_selected( )

        self._input             = self._input[ :self._cursor_index.x ] + text + self._input[ self._cursor_index.x: ]
        self._cursor_index.x   += len( text )

    
    def pop( self ):
        """
        Deletes the character immediately before the current cursor position.
        If text is currently selected, it deletes the selected text instead.
        The cursor position is updated accordingly after deletion.

        Receives: None

        Returns:
        - str: The character that was deleted, or None if no character was deleted
               (e.g., at the beginning of the input or if nothing was selected).
        """

        if self.is_something_selected( ):
            self._input             = self._input[ :self._selection_index.x ] + self._input[ self._selection_index.y: ]
            self._cursor_index.x    = ( self._selection_index.x )

            self.__reset_selection( )
            return

        if self._cursor_index.x == 0:
            return

        char: str = self._input[ self._cursor_index.x - 1 ]

        self._input             = self._input[ :self._cursor_index.x - 1 ] + self._input[ self._cursor_index.x: ]
        self._cursor_index.x   -= 1

        return char


    def __handle_ctrl( self, key: int, action: int ):
        """
        Handles the state of the Control (Ctrl) key.

        Sets the internal `_is_ctrl` flag to True when either the left or
        right Control key is pressed and to False when either is released.

        Receives:
        - key (int): The GLFW key code of the key event.
        - action (int): The GLFW action code (press or release).

        Returns: None
        """
        
        if key != glfw.KEY_LEFT_CONTROL and key != glfw.KEY_RIGHT_CONTROL:
            return

        if action == glfw.PRESS:
            self._is_ctrl = True

        if action == glfw.RELEASE:
            self._is_ctrl = False


    def __handle_default_actions( self, key: int, is_repeat: bool ):
        """
        Handles default keyboard actions such as backspace (delete),
        left arrow (move cursor left), and right arrow (move cursor right).

        Receives:
        - key (int): The GLFW key code of the key event.
        - is_repeat (bool): True if the key is being held down (repeat action),
                           False otherwise.

        Returns:
        - str or None: The character that was popped (deleted) if the
                       backspace key was pressed, otherwise None.
        """

        # Remove action
        if key == glfw.KEY_BACKSPACE:
            return self.pop( )

        # Move index left
        if key == glfw.KEY_LEFT and self._cursor_index.x > 0:
            self._cursor_index.x -= 1
            return

        # Move index right
        if key == glfw.KEY_RIGHT and self._cursor_index.x < len( self._input ):
            self._cursor_index.x += 1
            return

    
    def __handle_clipboard( self, key: int ):
        """
        Handles clipboard operations (copy and paste) when the Control key
        is being held down.

        - Ctrl+V: Pastes text from the clipboard into the input field at the
                  current cursor position, replacing any selected text.
        - Ctrl+C: Copies the currently selected text to the clipboard.

        Receives:
        - key (int): The GLFW key code of the key event.

        Returns: None
        """

        if not self._is_ctrl:
            return

        if key == glfw.KEY_V:
            result: bytes   = glfw.get_clipboard_string( None )
            result: str     = result.decode( )

            return self.insert( result )
            
        if key == glfw.KEY_C:
            result: str = self.get_selection_string( )

            if result != "":
                glfw.set_clipboard_string( None, result )
        

    def __reset_selection( self ):
        """
        Resets the text selection state by clearing the selection indices
        and positions. This effectively deselects any currently selected text.

        Receives: None

        Returns: None
        """

        self._selection_index.x = -1
        self._selection_index.y = -1

        self._selection_position.x = None
        self._selection_position.y = None

    
    def get_selection_string( self ) -> str:
        """
        Returns the currently selected text as a string.

        Receives: None

        Returns:
        - str: The selected text. Returns an empty string if no text is selected.
        """

        if self._selection_index.x == -1 or self._selection_index.y == -1:
            return ""
        
        return self._input[ self._selection_index.x:self._selection_index.y ]

    
    def is_something_selected( self ):
        """
        Checks if any text is currently selected in the input field.

        Receives: None

        Returns:
        - bool: True if text is selected, False otherwise.
        """

        return self._selection_index.x != -1 and self._selection_index.y != -1
    

    def __remove_selected( self ):
        """
        Removes the currently selected text from the input field.
        After removal, the cursor is positioned at the beginning of
        where the selection was, and the selection is reset.

        Receives: None

        Returns: None
        """

        if not self.is_something_selected( ):
            return
        
        self._input             = self._input[ :self._selection_index.x ] + self._input[ self._selection_index.y: ]
        self._cursor_index.x    = ( self._selection_index.x )

        self.__reset_selection( )

    # endregion


class c_text_input:

    # region : Protected attributes

    _parent:                any                     # Parent object - c_scene / c_window
    _index:                 int                     # Widget index

    _position:              vector                  # Relative to parent position
    _relative_position:     vector                  # Relative to application position

    _height:                int                     # Height of the text input ( in pixels )

    _handle:                c_single_input_logic    # Logic of the text input 

    _render:                c_renderer              # Renderer object
    _animations:            c_animations            # Animation object

    _font:                  c_font                  # Font object
    _icon:                  c_image                 # Icon object
    _text:                  str                     # Label value

    _is_visible:             bool                   # Is this widget visible
    _is_disabled:           bool                    # Is this widget disabled

    _is_hovered:            bool                    # Is user hovered the text box widget
    _should_type:           bool                    # Should the text input start handle

    _mouse_position:        vector                  # Mouse position
    _text_size:             vector                  # Label text size
    
    _config:                text_input_config_t     # Config for text input

    # endregion

    def __init__( self, parent: any, position: vector, height: int, size_of_input: vector, font: c_font, icon: c_image, text: str, default_value: str = "", is_password: bool = False, config: text_input_config_t = None ):
        """
        Initializes a new text input.

        Receives:
        - parent (any): The parent object or container for this text input.
        - position (vector): The initial position (x, y) of the text input.
        - height (int): The height of the text input widget.
        - size_of_input (vector): The size (width, height) of the editable input area.
        - font (c_font): The font object to use for rendering text.
        - icon (c_image): The image object to display as an icon.
        - text (str): The label text to display.
        - default_value (str, optional): The initial text to display in the input field. Defaults to "".
        - is_password (bool, optional): A flag indicating if the input should obscure text. Defaults to False.
        - config (text_input_config_t, optional): Configuration settings for the text input. Defaults to None.

        Returns:
        - c_text_input: The newly initialized single input logic object.
        """

        # Set config
        self._config = config is None and text_input_config_t( ) or config

        # Set parent
        self._parent = parent

        # Set position and sizes
        self._position  = position.copy( )
        self._height    = height

        # Set display information
        self._font = font
        self._icon = icon
        self._text = text

        # Create text logic handle
        self._handle = c_single_input_logic( self._parent, position, size_of_input, font, default_value, is_password, self._config )

        # Initialize attachment to parent
        self.__init_attachment( )

        # Initialize animations of the widget
        self.__init_animations( )

        # Initialize default and first values for the widget 
        self.__init_bones( )

    # region : Initialization

    def __init_attachment( self ):
        """
        Initializes the attachment of the text input widget to its parent,
        including obtaining the renderer and registering event handlers.

        Receives: None

        Returns: None
        """
        
        # Get renderer
        self._render    = self._parent.render( )

        # Attach widget to parent
        self._index     = self._parent.attach_element( self )

        # Attach this widget's events handlers to parent
        this_widget = f"text_input::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_widget )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,           this_widget )
        self._parent.set_event( "char_input",       self.__event_char_input,            this_widget )
        self._parent.set_event( "keyboard_input",   self.__event_keyboard_input,        this_widget )


    def __init_animations( self ):
        """
        Initializes the animation system for the text input widget,
        preparing animation values for properties like fade, background width,
        hover and typing states, label visibility, and separator position.

        Receives: None

        Returns: None
        """

        # Create standalone animations handler
        self._animations = c_animations( )

        # Preallocate animations values
        self._animations.prepare( "fade",               0 ) 
        self._animations.prepare( "background_width",   0 )

        self._animations.prepare( "hover",  0 )
        self._animations.prepare( "typing", 0 )

        self._animations.prepare( "label",      0 )
        self._animations.prepare( "separate",   0 )


    def __init_bones( self ):
        """
        Initializes default and initial state values for the text input widget,
        such as visibility, disabled state, hover state, typing intention,
        and initial mouse and text size vectors.

        Receives: None

        Returns: None
        """
        
        # At first, copy the position and set as relative vector
        self._relative_position = self._position.copy( )

        # Set first values for specific behavior
        self._is_visible     = True
        self._is_disabled   = False

        # Set first values for input handle
        self._is_hovered    = False
        self._should_type   = False

        # Set first some empty vectors
        self._mouse_position    = vector( )
        self._text_size         = vector( )

    # endregion

    # region : Drawing

    def draw( self, fade: float ):
        """
        Draws the complete text input widget, including its background and the
        editable input field. It first performs necessary calculations and
        updates animations before rendering the visual elements.

        Receives:
        - fade (float): The current fade value of the parent,
                        which is multiplied by the internal fade animation value.

        Returns: None
        """
        
        # Perform some calculations before drawing
        self.__perform_calculations( )
        self.__perform_animations( )

        fade = self._animations.value( "fade" ) * fade
        if fade == 0:
            return

        # Draw background
        self.__draw_background( fade )

        # Draw input
        self.__draw_input( fade )


    def __perform_calculations( self ):
        """
        Performs pre-drawing calculations, such as updating the widget's
        absolute position based on its parent, measuring the size of the label text,
        positioning the input field, and setting the typing state of the input handle.

        Receives: None

        Returns: None
        """
        
        pad:        int = self._config.pad
        separate:   int = self._config.separate

        parent_position:            vector  = self._parent.relative_position( )
        self._relative_position:    vector  = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

        self._text_size:            vector  = self._render.measure_text( self._font, self._text )

        self._handle.position( 
            vector(
                self._position.x + pad * 3 + self._icon.size( ).x + separate + self._text_size.x,
                self._position.y + ( self._height - self._handle.fixed_size( ).y ) / 2
            )
        )

        self._handle.is_typing( self._should_type )
        

    def __perform_animations( self ):
        """
        Updates the animation values for various visual properties of the
        text input widget, such as fade, hover effect, and typing indicator,
        based on the widget's current state (visibility, disabled, hovered, typing).

        Receives: None

        Returns: None
        """
        
        self._animations.update( )

        separate:   int     = self._config.separate
        speed:      int     = self._config.speed
        pad:        int     = self._config.pad

        if not self._is_visible:
            fade: float = self._animations.perform( "fade", 0, speed )
        else:
            fade: float = self._animations.perform( "fade", self._is_disabled and 0.3 or 1, speed )

        if fade == 0:
            return
        
        hover_fade:     float = self._animations.perform( "hover",  self._is_hovered and 1 or 0, speed )
        typing_fade:    float = self._animations.perform( "typing", self._should_type and 1 or 0, speed )

        if self._should_type:
            self._animations.perform( "label", 0.7, speed )
            self._animations.perform( "separate", ( self._height - 10 ) / 2, speed )
        else:
            self._animations.perform( "label", self._is_hovered and 0.5 or 0.3, speed )
            
            separate_remove = self._is_hovered and 15 or 20
            self._animations.perform( "separate", ( self._height - separate_remove ) / 2, speed )


        if self._handle.is_typing( ):
            input_width: float = self._handle.fixed_size( ).x - pad
        
        else:
            input_width: float = min( self._handle.text_width( ), self._handle.fixed_size( ).x ) - pad

        if self._handle.value( ) != "":
            typing_fade = 1

        fixed_width: int = pad * 4 + self._icon.size( ).x + separate + self._text_size.x
        self._animations.perform( "background_width", fixed_width + max( pad * hover_fade, input_width * typing_fade ), speed * 2 )


    def __draw_background( self, fade: float ):
        """
        Draws the background elements of the text input widget, including
        the main background, shadow, icon, separator, and label, with
        their respective colors and fade effects.

        Receives:
        - fade (float): The current overall fade value for the widget.

        Returns: None
        """
        
        pad:        int = self._config.pad
        separate:   int = self._config.separate
        roundness:  int = self._config.roundness

        color_background:   color = self._config.color_background
        color_shadow:       color = self._config.color_shadow
        color_theme:        color = self._config.color_theme

        color_icon:         color = self._config.color_icon
        color_label:        color = self._config.color_label

        icon_size:          vector = self._icon.size( )

        icon_position:      vector = vector( self._position.x + pad, self._position.y + ( self._height - icon_size.y ) / 2 )
        separate_position:  vector = vector( icon_position.x + icon_size.x + pad, self._position.y + self._height / 2 )
        label_position:     vector = vector( separate_position.x + separate + pad, self._position.y + ( self._height - self._text_size.y ) / 2 )

        label_fade:     float = self._animations.value( "label" ) * fade
        separate_fade:  float = self._animations.value( "separate" )
        hover_fade:     float = self._animations.value( "hover" )
        typing_fade:    float = self._animations.value( "typing" )

        positioned_size: vector  = vector( self._position.x + self._animations.value( "background_width" ), self._position.y + self._height )

        # Draw the drop shadow first
        self._render.shadow(
            self._position,
            positioned_size,
            color_shadow.linear( color_theme, hover_fade ),
            fade,
            20,
            roundness
        )
        
        # Draw the background
        self._render.rect(
            self._position,
            positioned_size,
            color_background * fade,
            roundness
        )

        # Create cliprect to avoid glow escaping out of scope of the widget
        self._render.push_clip_rect( self._position, positioned_size, True )

        self._render.image( self._icon, icon_position, color_icon.linear( color_theme, typing_fade ) * label_fade )

        self._render.neon( vector( separate_position.x, separate_position.y - separate_fade ), vector( separate_position.x + separate, separate_position.y + separate_fade ), color_theme * fade, 18, separate / 2 )

        self._render.text( self._font, label_position, color_label * label_fade, self._text )

        self._render.pop_clip_rect( )


    def __draw_input( self, fade: float ):
        """
        Draws the editable input field portion of the text input widget,
        applying a clipping rectangle to ensure the text and cursor are
        contained within the visual bounds of the input area.

        Receives:
        - fade (float): The current overall fade value for the widget.

        Returns: None
        """
        
        self._render.push_clip_rect( self._position, vector( self._position.x + self._animations.value( "background_width" ), self._position.y + self._height ), True )

        self._handle.draw( fade )

        self._render.pop_clip_rect( )

    # endregion

    # region : Input handle

    def __event_mouse_position( self, event ) -> None:
        """
        Handles mouse position events for the entire text input widget.

        Receives:
        - event (callable): A function that, when called with a string key,
                          returns information about the mouse event.

        Returns: None
        """

        if not self._is_visible or self._is_disabled:
            return

        self._handle.event_mouse_position( event )

        self._mouse_position.x  = event( "x" )
        self._mouse_position.y  = event( "y" )

        width                   = self._animations.value( "background_width" )

        if self._mouse_position.is_in_bounds( self._relative_position, width, self._height ):
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:
            if self._parent.is_this_active( self._index ) and not self._should_type:
                self._parent.release_handle( self._index )

            self._is_hovered = False
            

    def __event_mouse_input( self, event ) -> None:
        """
        Handles mouse button input events for the text input widget.

        Receives:
        - event (callable): A function that, when called with a string key,
                          returns information about the mouse event.

        Returns: None
        """

        if not self._is_visible or self._is_disabled:
            return

        self._handle.event_mouse_input( event )

        button = event( "button" )
        action = event( "action" )

        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self._should_type = self._is_hovered


    def __event_char_input( self, event ) -> None:
        """
        Handles character input events for the text input widget, forwarding
        the event to the internal input handling logic.

        Receives:
        - event (callable): A function that, when called with a string key,
                          returns information about the character event.

        Returns: None
        """

        if not self._is_visible or self._is_disabled:
            return

        self._handle.event_char_input( event )


    def __event_keyboard_input( self, event ) -> None:
        """
        Handles keyboard input events for the text input widget, forwarding
        the event to the internal input handling logic and managing the
        typing state based on Enter and Escape key presses.

        Receives:
        - event (callable): A function that, when called with a string key,
                          returns information about the keyboard event.

        Returns: None
        """
        
        if not self._is_visible or self._is_disabled:
            return
        
        key         = event( "key" )
        action      = event( "action" ) 

        if action == glfw.PRESS:
            if key == glfw.KEY_ENTER or key == glfw.KEY_ESCAPE:
                self._should_type = False

        self._handle.event_keyboard_input( event )

    # endregion

    # region : Utilities

    def position( self, new_value: vector = None ) -> vector:
        """
        Gets or sets the local position of the text input widget.

        Receives:
        - new_value (vector, optional): The new position (x, y) to set.
                                        If None, the current position is returned.
                                        Defaults to None.

        Returns:
        - vector: The current local position of the text input widget.
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y
        return new_value
    

    def size( self ) -> vector:
        """
        Returns the current size (width and height) of the text input widget.

        Receives: None

        Returns:
        - vector: A vector representing the current size (animated width, fixed height).
        """

        return vector( self._animations.value( "background_width" ), self._height )

    
    def visible( self, new_value: bool = None ) -> bool:
        """
        Gets or sets the visibility state of the text input widget.

        Receives:
        - new_value (bool, optional): The new visibility state to set.
                                       If None, the current visibility state is returned.
                                       Defaults to None.

        Returns:
        - bool: The current visibility state of the text input widget.
        """

        if new_value is None:
            return self._is_visible

        self._is_visible = new_value
        return new_value

    
    def get( self ) -> str:
        """
        Retrieves the current text value from the internal input handling logic.

        Receives: None

        Returns:
        - str: The current text value in the input field.
        """

        return self._handle.value( )

    # endregion