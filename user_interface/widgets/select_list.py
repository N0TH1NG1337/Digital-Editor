"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Selectable List

    description : Selectable List classes
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


class list_config_t:
    speed:              int
    pad:                int
    separate:           int
    roundness:          int

    separate_color:     color
    back_color:         color

    slots_count:        int
    slot_height:        int

    is_multiselect:     bool
    disable_pressed:    bool

    check_mark:         c_image

    def __init__( self ):
        self.speed:              int         = 7
        self.pad:                int         = 10
        self.separate:           int         = 4
        self.roundness:          int         = 10

        self.separate_color:     color       = color( 207, 210, 215 )
        self.back_color:         color       = color( 0, 0, 0, 150 )

        self.slots_count:        int         = 6
        self.slot_height:        int         = 40

        self.is_multiselect:     bool        = False
        self.disable_pressed:    bool        = False

        self.check_mark:         c_image     = None



class c_list_item:

    text:           str
    icon:           c_image

    is_hovered:     bool
    is_enable:      bool

    position:       vector

    fade_hover:     float
    fade_enable:    float

    callback:       any

    def __init__( self ):
        self.text:           str         = ""
        self.icon:           c_image     = None

        self.is_hovered:     bool        = False
        self.is_enable:      bool        = False

        self.position:       vector      = vector( )

        self.fade_hover:     float       = 0
        self.fade_enable:    float       = 0

        self.callback:       any         = None


class c_list:

    _parent:                any    # c_scene / c_window
    _index:                 int

    _position:              vector
    _relative_position:     vector
    _size:                  vector  # .x - width ( declared by const value )

    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _items:                 list

    _mouse_position:        vector

    _config:                list_config_t

    _offset:                float
    _is_visible:            bool
    _is_anyone_enabled:     bool
    _is_hovered:            bool

    # region : Initialize

    def __init__( self, parent: any, position: vector, width: int, font: c_font, config: list_config_t = None ):
        
        self._config = config is None and None or config

        self.__initialize_parent( parent )

        self._position  = position.copy( )
        self._size      = vector( width, self._config.slots_count * ( self._config.slot_height + self._config.pad ) + self._config.pad )

        self._font  = font

        self._items = [ ]

        self.__initialize_animations( )
        self.__initialize_values( )

        
    def __initialize_parent( self, parent: any ):
        
        self._parent = parent

        self._render = self._parent.render( )

        self._index = self._parent.attach_element( self )

        this_id = f"list::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,      this_id )


    def __initialize_animations( self ):
        
        self._animations = c_animations( )

        self._animations.prepare( "fade",           0 )
        self._animations.prepare( "scroll",         0 )
        self._animations.prepare( "add_on_enable",  0 )


    def __initialize_values( self ):
        
        self._relative_position = self._position.copy( )
        self._mouse_position    = vector( )
        
        self._offset = 0

        self._is_visible        = True
        self._is_anyone_enabled = False
        self._is_hovered        = False

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        
        self.__perform_calculations( )
        self.__perform_animations( )

        fade = fade * self._animations.value( "fade" )
        if fade == 0:
            return

        self.__draw_background( fade )
        self.__draw_items( fade )
        self.__draw_scrollbar( fade )
    

    def __perform_calculations( self ):

        count:      int = len( self._items )
        count_max:  int = self._config.slots_count
        pad:        int = self._config.pad
        height:     int = self._config.slot_height + pad

        drop        = count * height
        fixed_drop  = count_max * height

        if drop > fixed_drop:
            drop_min = fixed_drop - drop
        else:
            drop_min = 0

        self._offset = math.clamp( self._offset, drop_min, 0 )
        
        relative: vector = self._parent.relative_position( )
        self._relative_position.x = relative.x + self._position.x
        self._relative_position.y = relative.y + self._position.y


    def __perform_animations( self ):
        
        self._animations.update( )

        speed:  int = self._config.speed
        pad:    int = self._config.pad
        width:  int =  pad

        fade: float = self._animations.perform( "fade", self._is_visible and 1 or 0, speed )
        if fade == 0:
            return

        if self._config.check_mark:
            width:  int = self._config.check_mark.size( ).x + width

        self._animations.perform( "scroll",         self._offset, speed, 1 )
        self._animations.perform( "add_on_enable",  self._is_anyone_enabled and width or 0, speed, 1 )

    
    def __draw_background( self, fade: float ):

        roundness:          int = self._config.roundness
        background_color:   color = self._config.back_color

        self._render.shadow( self._position, self._position + self._size, background_color, fade, 20, roundness )
        self._render.rect( self._position, self._position + self._size, background_color * fade, roundness )


    def __draw_items( self, fade: float ):
        
        speed:  int = self._config.speed
        pad:    int = self._config.pad
        height: int = self._config.slot_height

        check_mark:     c_image = self._config.check_mark
        check_size:     vector  = check_mark is None and vector( ) or check_mark.size( )
        add_to_check:   vector  = vector( 0, ( height - check_size.y ) / 2 )

        enabled_pad:    float = self._animations.value( "add_on_enable" )
        scroll:         float = self._animations.value( "scroll" )

        self._render.push_clip_rect( self._position, self._position + self._size, True )

        drop = pad + scroll
        self._is_anyone_enabled = False

        for item in self._items:
            item: c_list_item = item

            self._is_anyone_enabled = self._is_anyone_enabled or item.is_enable

            icon_size:  vector = item.icon.size( ) + vector( pad, 0 )
            text_size:  vector = self._render.measure_text( self._font, item.text )

            item.fade_hover     = self._animations.fast_perform( item.fade_hover, ( item.is_hovered or item.is_enable ) and 0.7 or 0.3, speed ) * fade
            item.fade_enable    = self._animations.fast_perform( item.fade_enable, item.is_enable and 1 or 0, speed ) * fade

            item.position.y = drop

            position:       vector = vector( self._position.x + pad, self._position.y + drop )
            icon_position:  vector = vector( position.x + enabled_pad, position.y + ( height - icon_size.y ) / 2 )
            text_position:  vector = vector( position.x + icon_size.x + enabled_pad, position.y + ( height - text_size.y ) / 2 )

            if check_mark:
                self._render.image( check_mark, position + add_to_check, color( ) * item.fade_enable )

            self._render.image( item.icon, icon_position, color( ) * item.fade_hover )
            self._render.text( self._font, text_position, color( ) * item.fade_hover, item.text )

            drop = drop + height + pad

        self._render.pop_clip_rect( )

    
    def __draw_scrollbar( self, fade: float ):

        pad:            int     = self._config.pad
        separate:       int     = self._config.separate
        separate_color: color   = self._config.separate_color
        slot_height:    int     = self._config.slot_height

        window_delta:   float   = self._size.y
        drop                    = len( self._items ) * ( slot_height + pad ) + pad

        if drop == 0:
            return
        
        if drop <= window_delta:
            return
        
        scroll_y        = self._animations.value( "scroll" )
        scroll_delta    = window_delta / drop

        fixed           = window_delta * scroll_delta
        value           = abs( scroll_y ) * scroll_delta

        position:       vector  = vector( self._position.x + self._size.x - separate, self._position.y )
        start_position: vector  = vector( position.x, position.y + value )
        end_position:   vector  = vector( position.x + separate, start_position.y + fixed )

        self._render.shadow( start_position, end_position, separate_color, fade, 15, separate / 2 )
        self._render.rect( start_position, end_position, separate_color * fade, separate / 2 )

    # endregion

    # region : Input

    def __event_mouse_position( self, event ):

        if not self._is_visible:
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False
            return
        
        self._mouse_position.x = event( "x" )
        self._mouse_position.y = event( "y" )

        if self._mouse_position.is_in_bounds( self._relative_position, self._size.x, self._size.y ):
            
            # Check if we hovered and can have the handle. Also register self object
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:

            # Release if hold the handle
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False

        self.__hover_items( )

    
    def __event_mouse_input( self, event ):

        if not self._is_hovered or not self._is_visible:
            return

        button = event( "button" )
        action = event( "action" )

        if not button == glfw.MOUSE_BUTTON_LEFT or not action == glfw.PRESS:
            return
        
        self.__handle_items( )

    
    def __event_mouse_scroll( self, event ):

        if not self._is_hovered or not self._is_visible:
            return

        y_offset = event( "y_offset" )

        self._offset += y_offset * 20


    def __hover_items( self ):

        for item in self._items:
            item: c_list_item = item

            position = vector( self._relative_position.x, self._relative_position.y + item.position.y )

            if self._is_hovered:
                item.is_hovered = self._mouse_position.is_in_bounds( position, self._size.x, self._config.slot_height )
            else:
                item.is_hovered = False

    
    def __handle_items( self ):
        
        is_multiselect: bool = self._config.is_multiselect

        for item in self._items:
            item: c_list_item = item

            if not item.is_hovered:
                continue

            if is_multiselect:
                item.is_enable = not item.is_enable
            
            else:
                if not item.is_enable:
                    item.is_enable = True
                    self.__set_values( False, item )

            if item.callback is not None:
                item.callback( item.text )

            return
    
    # endregion

    # region : Utilities

    def __set_values( self, new_value: bool, exception: c_list_item = None ):

        for item in self._items:
            item: c_list_item = item

            if item is not exception:
                item.is_enable = new_value


    def position( self, new_value: vector = None ) -> any:

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

        return new_value
    

    def set_value( self, item_name: str, value: bool = None ):

        is_multiselect: bool = self._config.is_multiselect

        for item in self._items:
            item: c_list_item = item

            if item.text != item_name:
                continue

            if is_multiselect:
                item.is_enable = value
            
            else:

                if not item.is_enable:
                    item.is_enable = True
                    self.__set_values( False, item )

            return

    
    def get( self, index: str = None ) -> any:

        is_multiselect: bool = self._config.is_multiselect

        for item in self._items:
            item: c_list_item = item

            if is_multiselect:
                if item.text == index:
                    return item.is_enable
            
            else:
                if item.is_enable:
                    return item.text
                
        return False


    def clear( self ):
        self._items.clear( )


    def add_item( self, index: str, icon: c_image, callback: any = None ):
        
        new_item = c_list_item( )

        new_item.text = index
        new_item.icon = icon

        new_item.callback = callback

        new_item.is_enable      = False
        new_item.is_hovered     = False

        new_item.position = vector( )

        new_item.fade_enable    = 0
        new_item.fade_hover     = 0

        self._items.append( new_item )

    
    def visible( self, new_value: bool = None ) -> bool:

        if new_value is None:
            return self._is_visible
        
        self._is_visible = new_value

        return self._is_visible

    # endregion


class c_side_list:

    _parent:                any     # c_scene / c_window
    _index:                 int     # Button index

    _position:              vector  # Position in parent
    _relative_position:     vector  # Relative position on screen
    _width:                 int

    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _items:                 list

    _mouse_position:        vector

    _config:                list_config_t

    _is_visible:            bool
    _someone_enabled:       bool
    _is_hovered:            bool

    _block_size:            float

    # region : Initialize list

    def __init__( self, parent: any, position: vector, width: int, font: c_font, config: list_config_t = None ):
        """
            Default constructor for list object.

            Receive : 
            - parent            - List Box Parent
            - position          - Position in the parent
            - width             - List Box width
            - font              - Default font
            - items             - List items
            - config [optional] - Config for List Box

            Returns :   List object
        """

        self._config = config is None and list_config_t( ) or config

        self.__initialize_parent( parent )

        self._position  = position.copy( )
        self._width     = width
        self._font      = font

        self._items = [ ]

        self.__initialize_animations( )
        self.__initialize_values( )


    def __initialize_parent( self, parent: any ):
        """
            Initialize parent attach.

            Receive : 
            - parent - Parent object to attach to.

            Returns :   None
        """

        self._parent = parent

        self._render = self._parent.render( )

        self._index = self._parent.attach_element( self )

        this_id = f"List::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )


    def __initialize_animations( self ):
        """
            Initialize button animations values

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Fade", 0 )


    def __initialize_values( self ):
        """
            Initialize defaule button values

            Receive :   None

            Returns :   None
        """

        self._mouse_position        = vector( )
        self._relative_position     = self._position.copy( )

        self._block_size            = 0
        self._is_hovered            = False
        self._is_visible            = True

    
    def add_item( self, index: str, icon: c_image, callback: any = None ):
        """
            Add new item for list.

            Receive :
            - index                 - Value index
            - icon                  - Index icon
            - callback [optional]   - Callback to be called on item press

            Returns :   None
        """

        new_item = c_list_item( )

        new_item.text = index
        new_item.icon = icon

        new_item.callback = callback is None and None or callback

        new_item.is_enable      = False
        new_item.is_hovered     = False

        new_item.position       = vector( )

        self._animations.prepare( f"Item_{ index }_hover",   0 )
        self._animations.prepare( f"Item_{ index }_enable",  0 )
        self._animations.prepare( f"Item_{ index }_up",      0 )

        self._items.append( new_item )

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        """
            Draw function.

            Receive : 
            - fade - Parent fade factor

            Returns :   None
        """

        self.__preform( )
        self.__animate( )

        fade = fade * self._animations.value( "Fade" )
        if fade == 0:
            return

        self.__draw_back( fade )
        self.__draw_items( fade )

    
    def __preform( self ):
        """
            Preforms all the behind the scenes small calculations.

            Receive :   None

            Returns :   None
        """

        pad:                int     = self._config.pad
        seperate:           int     = self._config.separate

        self._block_size:   float   = self._width / len( self._items )

        # Do position staff.
        # I could use self._render.push_position, but I dont want.
        # I still need to calculate all the input relatives positions
        parent_position         = self._parent.relative_position( )
        self._relative_position = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )


    def __animate( self ):
        """
            Preform animations of the list.

            Receive :   None

            Returns :   None
        """

        self._animations.update( )

        speed:      int     = self._config.speed

        self._animations.perform( "Fade", self._is_visible and 1 or 0, speed )

    
    def __draw_back( self, fade: float ):
        """
            Draw background for side list.

            Receive :
            - fade - Fade factor

            Returns :   None
        """

        slot_height:    int     = self._config.slot_height
        roundness:      int     = self._config.roundness
        back_color:     color   = self._config.back_color

        size = vector( self._width, slot_height )

        self._render.rect(
            self._position,
            self._position + size, 
            back_color * fade,
            roundness
        )

        self._render.shadow(
            self._position,
            self._position + size, 
            back_color,
            fade,
            20,
            roundness
        )

    
    def __draw_items( self, fade: float ):
        """
            Draw the items for side list.

            Receive :
            - fade - Fade factor

            Returns :   None
        """

        speed:          int = self._config.speed
        pad:            int = self._config.pad
        height:         int = self._config.slot_height

        seperate:       int = self._config.separate
        seperate_color: color = self._config.separate_color

        offset: float = 0

        for item in self._items:
            item: c_list_item = item

            icon_size:          vector      = item.icon is None and vector( ) or ( item.icon.size( ) + vector( pad, 0 ) )
            text_size:          vector      = self._render.measure_text( self._font, item.text )

            hover:              float       = self._animations.perform( f"Item_{ item }_hover", item.is_hovered and 0.7 or 0.3, speed ) * fade
            enable:             float       = self._animations.perform( f"Item_{ item }_enable", item.is_enable and 1 or 0, speed ) * fade
            up:                 float       = self._animations.perform( f"Item_{ item }_up", item.is_enable and 5 or 0, speed * 2, 0.1 ) * fade

            reversed_hover:     float       = abs( enable - 1 )

            item_size:          vector      = vector( icon_size.x + text_size.x, 0 )
            position:           vector      = vector( self._position.x + offset + ( self._block_size - item_size.x ) / 2, self._position.y - up )
            
            select_position:    vector      = vector( position.x + ( item_size.x / 2 ) * reversed_hover, position.y + height - seperate )
            select_size:        vector      = vector( item_size.x * enable, seperate )
            icon_position:      vector      = vector( position.x, position.y + ( height - icon_size.y ) / 2 )
            text_position:      vector      = vector( position.x + icon_size.x, position.y + ( height - text_size.y ) / 2 )

            if enable > 0:
                self._render.neon(
                    select_position,
                    select_position + select_size,
                    color( ).linear( seperate_color, enable ) * enable,
                    18,
                    seperate / 2
                )

            if item.icon is not None:
                self._render.image( item.icon, icon_position, color( ) * hover )

            self._render.text( self._font, text_position, color( ) * max( hover, enable ), item.text )

            item.position = vector( offset, 0 )

            offset += self._block_size
    
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
        

        if self._mouse_position.is_in_bounds( self._relative_position, self._width, self._config.slot_height ):
            
            # Check if we hovered and can have the handle. Also register self object
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:

            # Release if we hold the handle
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False


        self.__hover_items( )

    
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

        if not button == glfw.MOUSE_BUTTON_LEFT or not action == glfw.PRESS:
            return
        
        self.__handle_items( )


    def __hover_items( self ):
        """
            Handle if the user hover one of the items.

            Receive :   None

            Returns :   None
        """

        for item in self._items:
            item: c_list_item = item

            position = item.position + self._relative_position

            if self._is_hovered:
                item.is_hovered = self._mouse_position.is_in_bounds( position, self._block_size, self._config.slot_height )
            else:
                item.is_hovered = False

    
    def __handle_items( self ):
        """
            Handle the press on the items. 

            Receive :   None

            Returns :   None
        """

        is_multi:           bool = self._config.is_multiselect
        disable_pressed:    bool = self._config.disable_pressed

        for item in self._items:
            item: c_list_item = item

            if item.is_hovered:

                if is_multi:
                    item.is_enable = not item.is_enable

                else:

                    if not item.is_enable:
                        item.is_enable = True

                        self.__new_values( False, item )
                    else:
                        
                        if disable_pressed:
                            item.is_enable = False

                if item.callback is not None:
                    item.callback( item.text )

                return

    # endregion

    # region : Utilities

    def __new_values( self, new_value: bool, exception: c_list_item = None ):
        """
            Set all the items a new value.

            Receive : 
            - new_value             - New bool value for every item
            - exception [optional]  - Exception item that should not include

            Returns :   None
        """

        for item in self._items:
            item: c_list_item = item

            if item != exception:
                item.is_enable = new_value
    

    def set_value( self, item_name: str, value: bool = None ):
        """
            Set a new value for specific item.

            Receive : 
            - item_name         - Item text
            - value [optional]  - New value for multi select

            Returns :   None
        """

        is_multi: bool = self._config.is_multiselect

        for item in self._items:
            item: c_list_item = item

            if item.text == item_name:

                if is_multi:
                    item.is_enable = value

                else:

                    if not item.is_enable:
                        item.is_enable = True

                        self.__new_values( False, item )

                return
            
    
    def position( self, new_value: vector = None ) -> any: #vector | None:
        """
            Access / Update list position.

            Receive :
            - new_value - New position in the parent

            Returns : Vector or None
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

        return new_value
    

    def width( self, new_value: int = None ) -> int:
        """
            Access / Update the width of the list.

            Receive :
            - new_value - New width

            Returns : Vector or None
        """

        if new_value is None:
            return self._width
        
        self._width = new_value

        return new_value


    def get( self, index: str = None ) -> any: #str | bool:
        """
            Get value from list.

            Receive :
            - index [optional] - Index in multi select

            Returns :   String index or Boolean
        """

        is_multiselect = self._config.is_multiselect

        for item in self._items:
            item: c_list_item = item

            if is_multiselect:

                if item.text == index:
                    return item.is_enable
            
            else:

                if item.is_enable:
                    return item.text
                
        return False
    

    def clear( self ) -> None:
        """
            Clears list items.

            Receive :   None

            Returns :   None
        """

        for item in self._items:
            item: c_list_item = item
            index = item.text

            self._animations.delete_value( f"Item_{ index }_hover" )
            self._animations.delete_value( f"Item_{ index }_enable" )

        self._items.clear( )


    def visible( self, new_value: bool = None ) -> bool:
        """
            Access / Update text input visibility.

            Receive :   
            - new_value [optional] - New visibility value

            Returns :   Result
        """

        if new_value is None:
            return self._is_visible
        
        self._is_visible = new_value

        return self._is_visible
    
    # endregion