"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Solution explorer

    description : Solution explorer classes

    TODO ! FIX INPUT... THIS IS COMPLETE CANCER
"""

import glfw
import os

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


class solution_explorer_config_t:
    speed:          int         = 7
    pad:            int         = 10
    seperate:       int         = 4
    roundness:      int         = 10

    seperate_color: color       = color( 207, 210, 215 )
    back_color:     color       = color( 0, 0, 0, 150 )

    folder_color:   color       = color( 255, 255, 255 )
    item_color:     color       = color( 255, 255, 255 )

    slot_height:    int         = 40

    folder_icon:    c_image     = None
    item_icon:      c_image     = None


class c_item:
    
    name:                   str

    position:               vector

    left_click_callback:    any
    right_click_callback:   any

    is_hovered:             bool
    fade:                   float

    def __init__( self, name: str = "" ):
        """
        Initializes a new c_item instance.

        Receives:
        - name (str, optional): The name of the item. Defaults to "".

        Returns:
        - c_item - Item in solution explorer.
        """

        self.name = name

        self.left_click_callback    = None
        self.right_click_callback   = None
        
        self.position   = vector( )

        self.is_hovered = False
        self.fade       = 0


class c_holder:
    # Use to store data about items in hold.
    
    _other_holders:     list
    _items:             list

    name:               str

    fade:              float
    opened:            float

    position:          vector

    is_hovered:        bool
    is_opened:         bool

    show_slide:        bool

    def __init__( self, name: str = "" ):
        """
        Initializes a new c_holder instance.

        Receives:
        - name (str, optional): The name of the holder. Defaults to "".

        Returns: 
        - c_holder - Holder object. Like a folder.
        """

        self.name           = name

        self._other_holders = []
        self._items         = []

        self.position       = vector( )
        self.is_hovered     = False
        self.is_opened      = True
        self.show_slide     = True

        self.fade           = 0
        self.opened         = 1

    
    def add_item( self, item: c_item ):
        """
        Adds an item to this holder's list of items.

        Receives:
        - item (c_item): The item to be added to the holder.

        Returns: None
        """

        self._items.append( item )

    
    def get_items( self ) -> list:
        """
        Retrieves the list of items currently held by this holder.

        Receives: None

        Returns:
        - list: A list containing the c_item objects within this holder.
        """

        return self._items

    
    def add_holder( self, holder: any ):
        """
        Add holder to holder.

        Receives:
        - holder (c_holder): Holder to add

        Returns: None
        """

        self._other_holders.append( holder )

    
    def get_holders( self ) -> list:
        """
        Get holders in holder.

        Receives: None

        Returns:
        - list: List of holders
        """

        return self._other_holders
    


class c_solution_explorer:

    _parent:                any     # c_scene / c_window
    _index:                 int     # Index

    _position:              vector  # Position in parent
    _relative_position:     vector  # Relative position on screen
    _size:                  vector

    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _folder:                c_holder

    _mouse_position:        vector

    _config:                solution_explorer_config_t

    _is_visible:            bool
    _drop:                  float
    _offset:                float
    _is_hovered:            bool

    # region : Initialization

    def __init__( self, parent: any, position: vector, size: vector, font: c_font, config: solution_explorer_config_t = None ):
        """
        Default constructor for solution explorer.

        Receives:
        - parent (any): The parent object or container for this solution explorer.
        - position (vector): The initial position (x, y) of the solution explorer.
        - size (vector): The initial size (width, height) of the solution explorer.
        - font (c_font): The font object to use for rendering text.
        - config (solution_explorer_config_t, optional): Configuration settings for the solution explorer. Defaults to None.

        Returns:
        - c_solution_explorer: The newly created c_solution_explorer object.
        """

        self._config = config is None and solution_explorer_config_t( ) or config

        self.__initialize_parent( parent )

        self._position  = position.copy( )
        self._size      = size.copy( )

        self._font = font

        self.__initialize_animations( )
        self.__initialize_values( )
    

    def __initialize_parent( self, parent: any ):
        """
        Initialize the parent object for the solution explorer.

        Receives:
        - parent (any): The parent object to which the solution explorer belongs.

        Returns: None
        """

        self._parent    = parent

        self._render    = self._parent.render( )
        self._index     = self._parent.attach_element( self )

        this_id = f"SolutionExplorer::{ self._index }"

        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,      this_id )


    def __initialize_animations( self ):
        """
        Sets up the animation manager and pre-configures fade and scroll animations.

        Receives: None

        Returns: None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Fade",           0 )
        self._animations.prepare( "FadeContent",    0 )
        self._animations.prepare( "Scroll",         0 )

    
    def __initialize_values( self ):
        """
        Initialize values for the solution explorer.

        Receives: None

        Returns: None
        """

        self._mouse_position    = vector( )
        self._relative_position = self._position.copy( )

        self._offset            = 0
        self._is_hovered        = False
        self._is_visible        = True

        self._folder            = c_holder( "Solution Explorer" )
        self._folder.show_slide = False

    # endregion

    # region : Draw 

    def draw( self, fade: float ):
        """
        Draw the solution explorer.

        Receives:
        - fade (float): The fade value to apply during drawing.

        Returns: None
        """

        self.__preform( )
        self.__animate( fade )

        fade = fade * self._animations.value( "Fade" )
        if fade == 0:
            return
        
        self.__draw_back( fade )
        self.__draw_content( fade * self._animations.value( "FadeContent" ) )


    def __preform( self ):
        """
        Performs behind-the-scenes calculations.

        Receives: None

        Returns: None
        """

        pad:                int     = self._config.pad
        seperate:           int     = self._config.seperate

        parent_position         = self._parent.relative_position( )
        self._relative_position = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

    
    def __animate( self, fade: float ):
        """
        Animates the solution explorer.

        Receives:
        - fade (float): The current fade value used to control content animation.

        Returns: None
        """

        speed:      int     = self._config.speed

        self._animations.update( )

        self._animations.perform( "Fade", self._is_visible and 1 or 0, speed )
        self._animations.perform( "FadeContent", fade == 1 and 1 or 0, speed )
        self._animations.perform( "Scroll", self._offset, speed, 1 )

    
    def __draw_back( self, fade: float ):
        """
        Draws the background of the solution explorer.

        Receives:
        - fade (float): The fade value to apply to the background color.

        Returns: None
        """

        roundness:  int     = self._config.roundness
        back_color: color   = self._config.back_color

        self._render.shadow(
            self._position,
            self._position + self._size,
            back_color,
            fade,
            20,
            roundness
        )

        self._render.rect(
            self._position,
            self._position + self._size,
            back_color * fade,
            roundness
        )
    

    def __draw_content( self, fade: float ):
        """
        Draws the content folder of the solution explorer.

        Receives:
        - fade (float): The fade value to apply to the content.

        Returns: None
        """

        pad: int = self._config.pad

        self._drop = 0

        self._render.push_clip_rect( self._position, self._position + self._size )

        self.__draw_folder( fade, self._folder, pad )
        self.__draw_scrollbar( fade )

        self._render.pop_clip_rect( )

    
    def __draw_folder( self, fade: float, folder: c_holder, add_to_x: int ):
        """
        Draws a folder and its contents recursively.

        Receives:
        - fade (float): The fade value to apply to the folder and its items.
        - folder (c_holder): The folder object to draw.
        - add_to_x (int): An additional horizontal offset for the folder's position.

        Returns: None
        """

        if fade == 0:
            return

        pad:            int = self._config.pad
        speed:          int = self._config.speed
        slot_height:    int = self._config.slot_height
        seperate:       int = self._config.seperate

        folder_color:   color = self._config.folder_color
        item_color:     color = self._config.item_color
        seperate_color: color = self._config.seperate_color

        folder_icon:    c_image = self._config.folder_icon
        item_icon:      c_image = self._config.item_icon

        scroll_offset:  float   = self._animations.value( "Scroll" )

        position = self._position + vector( add_to_x, scroll_offset )
        start_drop = self._drop

        font_size: int = self._font.size( )

        folders: list = folder.get_holders( )
        for sub_folder in folders:
            sub_folder: c_holder = sub_folder

            current_folder_position:  vector  = position + vector( 0, self._drop + ( slot_height / 2 ) )
            current_folder_size:      vector  = self._render.measure_text( self._font, sub_folder.name )

            sub_folder.fade                 = self._animations.fast_perform( sub_folder.fade,   sub_folder.is_hovered and 1 or 0.5, speed )
            sub_folder.opened               = self._animations.fast_perform( sub_folder.opened, sub_folder.is_opened and 1 or 0, speed )

            current_color:          color   = folder_color * fade * sub_folder.fade

            # Draw the name here
            self._render.image( folder_icon, current_folder_position + vector( 0, -font_size / 2 ), folder_color * fade, vector( font_size, font_size ) )
            self._render.text( self._font, current_folder_position + vector( pad + font_size, -current_folder_size.y / 2 ), current_color, sub_folder.name )
            
            sub_folder.position = vector( 0, self._drop + scroll_offset )

            self._drop += slot_height * folder.opened
            
            self.__draw_folder( fade * sub_folder.opened, sub_folder, add_to_x + pad * 2 )


        items: list = folder.get_items( )
        for item in items:
            item: c_item = item
            
            current_item_position:  vector  = position + vector( 0, self._drop + ( slot_height / 2 ) )
            current_item_size:      vector  = self._render.measure_text( self._font, item.name )

            item.fade = self._animations.fast_perform( item.fade, item.is_hovered and 1 or 0.3, speed ) * fade
            current_color:          color   = item_color * item.fade

            # Here draw the item
            self._render.image( item_icon, current_item_position + vector( 0, -font_size / 2 ), item_color * fade, vector( font_size, font_size ) )
            self._render.text( self._font, current_item_position + vector( pad + font_size, -current_item_size.y / 2 ), current_color, item.name )

            item.position = vector( 0, self._drop + scroll_offset )

            self._drop += slot_height * fade 
        

        if folder.show_slide:
            position.x = position.x - pad

            delta_drop = self._drop - start_drop

            start_slide = position + vector( -pad, start_drop )
            end_slide   = position + vector( seperate - pad, start_drop + delta_drop * fade )

            self._render.shadow(
                start_slide,
                end_slide,
                seperate_color,
                fade,
                25,
                seperate / 2
            )

            self._render.rect(
                start_slide,
                end_slide,
                seperate_color * fade,  
                seperate / 2
            )

    
    def __draw_scrollbar( self, fade: float ):
        """
        Draws the vertical scroll bar.

        Receives:
        - fade (float): The fade factor inherited from the parent.

        Returns: None
        """

        seperate:       int     = self._config.seperate
        roundness:      int     = self._config.roundness
        seperate_color: color   = self._config.seperate_color
        
        start_position: vector  = vector( self._position.x + self._size.x - seperate, self._position.y + roundness )
        
        window_delta    = self._size.y - roundness

        if self._drop == 0:
            return

        if self._drop <= window_delta:
            return

        scroll = self._animations.value( "Scroll" )

        scroll_delta = window_delta / self._drop

        fixed = window_delta * scroll_delta
        value = abs( scroll ) * scroll_delta

        position        = vector( start_position.x, start_position.y + value )
        end_position    = vector( start_position.x + seperate, position.y + fixed )

        self._render.shadow( position, end_position, seperate_color, fade, 15, seperate / 2)
        self._render.rect( position, end_position, seperate_color * fade, seperate / 2 )

    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        """
        Handles mouse position change events.

        Receives:
        - event (callable): Event information.

        Returns: None
        """

        if not self._is_visible:
            return

        self._mouse_position.x  = event( "x" )
        self._mouse_position.y  = event( "y" )
        
        if self._mouse_position.is_in_bounds( self._relative_position, self._size.x, self._size.y ):
            
            # Check if we hovered and can have the handle. Also register self object
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:

            # Release if we hold the handle
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False

        self.__hover_items( self._folder )
    

    def __event_mouse_input( self, event ) -> None:
        """
        Handles mouse button input events.

        Receives:
        - event (callable): Event information.

        Returns: None
        """

        if not self._is_visible:
            return

        if not self._is_hovered:
            return

        button = event( "button" )
        action = event( "action" )

        if not action == glfw.PRESS:
            return
        
        self.__handle_items( self._folder, button )


    def __event_mouse_scroll( self, event ) -> None:
        """
        Handles mouse scroll input events.

        Receives:
        - event (callable): Event information.

        Returns: None
        """

        if not self._is_visible:
            return

        if not self._is_hovered:
            return

        #x_offset = event( "x_offset" )
        y_offset = event( "y_offset" )

        if self._drop > self._size.y:
            drop_min    = self._size.y - self._drop
        else:
            drop_min = 0

        self._offset = math.clamp( self._offset + y_offset * 20, drop_min, 0 )


    def __hover_items( self, folder: c_holder ):
        """
        Checks and handles hover events for items within a folder.

        Receives:
        - folder (c_holder): The folder to check for hovered items.

        Returns: None
        """

        slot_height: int = self._config.slot_height
        width:       int = self._size.x

        folders: list = folder.get_holders( )
        for current_folder in folders:
            current_folder: c_holder = current_folder

            position = self._relative_position + current_folder.position

            if self._is_hovered:
                current_folder.is_hovered = self._mouse_position.is_in_bounds( position, width, slot_height )
            else:
                current_folder.is_hovered = False

            self.__hover_items( current_folder )

        
        items: list = folder.get_items( )
        for item in items:
            item: c_item = item

            position = self._relative_position + item.position

            if self._is_hovered and folder.is_opened:
                item.is_hovered = self._mouse_position.is_in_bounds( position, width, slot_height )
            else:
                item.is_hovered = False

    
    def __handle_items( self, folder: c_holder, button: int ):
        """
        Handles click events for items within a folder and its subfolders.

        Receives:
        - folder (c_holder): The folder to check for clicked items.
        - button (int): The mouse button that was pressed.

        Returns: None
        """

        folders: list = folder.get_holders( )
        for current_folder in folders:
            current_folder: c_holder = current_folder

            if current_folder.is_hovered and button == glfw.MOUSE_BUTTON_LEFT:
                current_folder.is_opened = not current_folder.is_opened
                return True
                
            if current_folder.is_opened and self.__handle_items( current_folder, button ):
                return True

        
        items: list = folder.get_items( )
        for item in items:
            item: c_item = item

            if item.is_hovered and item.fade > 0:

                if button == glfw.MOUSE_BUTTON_LEFT and item.left_click_callback is not None:
                    item.left_click_callback( )
                    return True

                if button == glfw.MOUSE_BUTTON_RIGHT and item.right_click_callback is not None:
                    item.right_click_callback( )
                    return True
                
        return False

    # endregion

    # region : Utilities

    def add_item( self, value: str, left_click_callback: any = None, right_click_callback: any = None ):
        """
        Adds a new item to the solution explorer.

        Receives:
        - value (str): The path-like string representing the item to add. 
                       Folders are created based on path components.
        - left_click_callback (any, optional): A callback function to execute on left-click. 
                                               Defaults to None.
        - right_click_callback (any, optional): A callback function to execute on right-click. 
                                                Defaults to None.

        Returns: None
        """

        parse_item = value.split( os.sep )
        
        index = 0
        last_folder = self._folder
        while index < len( parse_item ) - 1:

            folder = parse_item[ index ]

            folders: list = last_folder.get_holders( )

            for sub_folder in folders:
                if sub_folder.name == folder:
                    last_folder = sub_folder
                    break
            else:
                new_folder = c_holder( folder )
                last_folder.add_holder( new_folder )
                last_folder = new_folder

            index += 1

        new_item = c_item( parse_item[ -1 ] )

        new_item.left_click_callback    = left_click_callback
        new_item.right_click_callback   = right_click_callback

        last_folder.add_item( new_item )

    
    def remove_item( self, item_name: str ):
        """
        Removes an item from the solution explorer.

        Receives:
        - item_name (str): The path-like string representing the item to remove. 
                          Folders in the path must exist for the item to be found.

        Returns: None
        """

        parse_item = item_name.split( os.sep )
        
        index = 0
        last_folder = self._folder
        while index < len( parse_item ) - 1:

            folder = parse_item[ index ]

            folders: list = last_folder.get_holders( )

            for sub_folder in folders:
                if sub_folder.name == folder:
                    last_folder = sub_folder
                    break
            else:
                return

            index += 1

        items: list = last_folder.get_items( )

        for item in items:
            if item.name == parse_item[ -1 ]:
                items.remove( item )
                break
        

    def has_item( self, file_name: str ):
        """
        Checks if an item exists in the solution explorer.

        Receives:
        - file_name (str): The path-like string representing the item to check for.
                           Folders in the path must exist for the item to be found.

        Returns:
        - bool: True if the item exists, False otherwise.
        """

        parse_item = file_name.split( os.sep )
        
        index = 0
        last_folder = self._folder
        while index < len( parse_item ) - 1:

            folder = parse_item[ index ]

            folders: list = last_folder.get_holders( )

            for sub_folder in folders:
                if sub_folder.name == folder:
                    last_folder = sub_folder
                    break
            else:
                return False

            index += 1

        items: list = last_folder.get_items( )

        for item in items:
            if item.name == parse_item[ -1 ]:
                return True

        return False


    def clear( self ):
        """
        Clears all items and folders from the solution explorer.

        Receives: None

        Returns: None
        """

        del self._folder
        
        self._folder = c_holder( "Solution Explorer" )
        self._offset = 0


    def visible( self, new_value: bool = None ) -> bool:
        """
        Access or update the visibility of the solution explorer.

        Receives:
        - new_value (bool, optional): The new visibility value to set. 
                                      If None, the current visibility is returned. Defaults to None.

        Returns:
        - bool: Returns the current visibility.
        """

        if new_value is None:
            return self._is_visible
        
        self._is_visible = new_value
        return self._is_visible
    

    def position( self, new_value: vector = None ) -> vector:
        """
        Access or update the position of the solution explorer.

        Receives:
        - new_value (vector, optional): The new position (x, y) relative to the parent. 
                                      If None, the current position is returned. Defaults to None.

        Returns:
        - vector: Returns the current position.
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y
        return new_value
    

    def size( self, new_value: vector = None ) -> vector:
        """
        Access or update the size of the solution explorer.

        Receives:
        - new_value (vector, optional): The new size (width, height). 
                                        If None, the current size is returned. Defaults to None.

        Returns:
        - vector: The current size.
        """

        if new_value is None:
            return self._size
        
        self._size.x = new_value.x
        self._size.y = new_value.y
        return new_value

    # endregion
