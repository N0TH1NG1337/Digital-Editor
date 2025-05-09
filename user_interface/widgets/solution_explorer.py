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
            Default constructor for item.

            Receive :   None

            Returns :   None
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
            Default constructor for holder.

            Receive :   None

            Returns :   None
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
            Add item to holder.

            Receive :   
            - item - Item to add

            Returns :   None
        """

        self._items.append( item )

    
    def get_items( self ) -> list:
        """
            Get items in holder.

            Receive :   None

            Returns :   List of items
        """

        return self._items

    
    def add_holder( self, holder: any ):
        """
            Add holder to holder.

            Receive :   
            - holder - Holder to add

            Returns :   None
        """

        self._other_holders.append( holder )

    
    def get_holders( self ) -> list:
        """
            Get holders in holder.

            Receive :   None

            Returns :   List of holders
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

            Receive :   None

            Returns :   None
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
            Initialize parent for solution explorer.

            Receive :   
            - parent - Parent object

            Returns :   None
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
            Initialize animations for solution explorer.

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Fade",           0 )
        self._animations.prepare( "FadeContent",    0 )
        self._animations.prepare( "Scroll",         0 )

    
    def __initialize_values( self ):
        """
            Initialize values for solution explorer.

            Receive :   None

            Returns :   None
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
            Draw solution explorer.

            Receive :   
            - fade - Fade value

            Returns :   None
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
            Preforms all the behind the scenes small calculations.

            Receive :   None

            Returns :   None
        """

        pad:                int     = self._config.pad
        seperate:           int     = self._config.seperate

        parent_position         = self._parent.relative_position( )
        self._relative_position = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

    
    def __animate( self, fade: float ):
        """
            Animate solution explorer.

            Receive :   None

            Returns :   None
        """

        speed:      int     = self._config.speed

        self._animations.update( )

        self._animations.perform( "Fade", self._is_visible and 1 or 0, speed )
        self._animations.perform( "FadeContent", fade == 1 and 1 or 0, speed )
        self._animations.perform( "Scroll", self._offset, speed, 1 )

    
    def __draw_back( self, fade: float ):
        """
            Draw back of solution explorer.

            Receive :   
            - fade - Fade value

            Returns :   None
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
            Draw folder of solution explorer.

            Receive :   
            - fade - Fade value

            Returns :   None
        """

        pad: int = self._config.pad

        self._drop = 0

        self._render.push_clip_rect( self._position, self._position + self._size )

        self.__draw_folder( fade, self._folder, pad )
        self.__draw_scrollbar( fade )

        self._render.pop_clip_rect( )

    
    def __draw_folder( self, fade: float, folder: c_holder, add_to_x: int ):
        """
            Draw folder of solution explorer.

            Receive :   
            - fade - Fade value
            - folder - Folder to draw

            Returns :   None
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
            Draw scroll bar.

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """

        seperate:       int     = self._config.seperate
        seperate_color: color   = self._config.seperate_color
        
        start_position: vector  = vector( self._position.x + self._size.x - seperate, self._position.y )
        
        window_delta    = self._size.y

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
            Mouse position change callback.

            Receive :   
            - event - Event information

            Returns :   None
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
            Mouse buttons input callback.

            Receive :   
            - event - Event information

            Returns :   None
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
            Mouse scroll input callback.

            Receive :   
            - event - Event information

            Returns :   None
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
            Handle if the user hover one of the items.

            Receive :   None

            Returns :   None
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

    
    def __handle_items( self, folder: c_holder, button: any ):
        """
            Handle if the user click one of the items.

            Receive :   None

            Returns :   None
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
            Add item to solution explorer.

            Receive :   
            - value - Value to add

            Returns :   None
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
            Remove item from solution explorer.

            Receive :   
            - item_name - Name of the item to remove

            Returns :   None
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
            Check if item exists in solution explorer.

            Receive :   
            - file_name - Name of the file

            Returns :   Bool
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
            Clear solution explorer.

            Receive :   None

            Returns :   None
        """

        del self._folder
        
        self._folder = c_holder( "Solution Explorer" )
        self._offset = 0



    def visible( self, new_value: bool = None ) -> bool:
        """
            Access / Update buttons visibility.

            Receive :
            - new_value - New button visibility

            Returns : Bool or None
        """

        if new_value is None:
            return self._is_visible
        
        self._is_visible = new_value
        return self._is_visible
    

    def position( self, new_value: vector = None ) -> vector:
        """
            Access / Update position.

            Receive :
            - new_value - New position in the parent

            Returns : Vector or None
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y
        return new_value
    

    def size( self, new_value: vector = None ) -> vector:
        """
            Access / Update size.

            Receive :
            - new_value - New size

            Returns : Vector or None
        """

        if new_value is None:
            return self._size
        
        self._size.x = new_value.x
        self._size.y = new_value.y
        return new_value

    # endregion
