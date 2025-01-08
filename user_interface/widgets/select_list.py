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
    speed:          int         = 7
    pad:            int         = 10
    seperate:       int         = 4
    roundness:      int         = 10

    seperate_color: color       = color( 216, 208, 215 )
    back_color:     color       = color( 0, 0, 0, 100 )

    slots_count:    int         = 6
    slot_height:    int         = 40

    is_mutliselect: bool        = False

    check_mark:     c_image     = None



class c_list_item:

    text:       str
    icon:       c_image

    is_hovered: bool
    is_enable:  bool

    position:   vector

    callback:   any


class c_list:

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

    _offset:                float
    _someone_enabled:       bool
    _rect:                  list
    _is_hovered:            bool
    
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
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,      this_id )


    def __initialize_animations( self ):
        """
            Initialize button animations values

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Scroll", 0 )
        self._animations.prepare( "AddOnEnable", 0 )


    def __initialize_values( self ):
        """
            Initialize defaule button values

            Receive :   None

            Returns :   None
        """

        self._mouse_position        = vector( )
        self._relative_position     = self._position.copy( )

        self._offset                = 0 
        self._someone_enabled       = False
        self._is_hovered            = False
        self._rect                  = [ vector( ), vector( ) ]

    
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

        self.__draw_back( fade )
        self.__draw_items( fade )
        self.__draw_scrollbar( fade )


    def __preform( self ):
        """
            Preforms all the behind the scenes small calculations.

            Receive :   None

            Returns :   None
        """

        pad:                int     = self._config.pad
        seperate:           int     = self._config.seperate

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
        pad:        int     = self._config.pad
        size:       vector  = self._config.check_mark.size( )

        self._animations.preform( "AddOnEnable", self._someone_enabled and size.x + pad or 0, speed )
        self._animations.preform( "Scroll", self._offset, speed, 1 )

    
    def __draw_back( self, fade: float ):
        """
            Draw the backgound.

            Receive :
            - fade - Fade factor of the parent

            Returns :   None
        """

        roundness:  int     = self._config.roundness
        back_color: color   = self._config.back_color

        self._render.gradiant(
            self._position,
            self._position + self._rect[ 1 ],
            back_color * fade,
            back_color * fade,
            back_color * 0,
            back_color * 0,
            roundness
        )

        self._render.shadow(
            self._position,
            self._position + self._rect[ 1 ],
            back_color,
            fade,
            20,
            roundness
        )


    def __draw_items( self, fade: float ):
        """
            Draw the items.

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """

        speed:      int     = self._config.speed
        pad:        int     = self._config.pad
        seperate:   int     = self._config.seperate
        height:     int     = self._config.slot_height
        amount:     int     = self._config.slots_count

        check_mark: c_image = self._config.check_mark
        check_size: vector  = check_mark.size( )
        add_to_check: vector = vector( pad, ( height - check_size.y ) / 2 )

        enable_pad: float   = self._animations.value( "AddOnEnable" )
        scroll:     float   = self._animations.value( "Scroll" )

        self._rect[ 0 ] = self._position.copy( )
        self._rect[ 1 ] = vector( self._width, amount * ( height + pad * 2 ) )

        self._render.push_clip_rect( self._rect[ 0 ], self._rect[ 0 ] + self._rect[ 1 ] )

        drop = pad + scroll

        self._someone_enabled = False

        for item in self._items:
            item: c_list_item = item

            self._someone_enabled = self._someone_enabled or item.is_enable

            icon_size:      vector      = item.icon.size( )
            text_size:      vector      = self._render.measure_text( self._font, item.text )

            hover:          float       = self._animations.preform( f"Item_{ item }_hover", item.is_hovered and 0.7 or 0.3, speed ) * fade
            enable:         float       = self._animations.preform( f"Item_{ item }_enable", item.is_enable and 1 or 0, speed ) * fade

            position:       vector      = vector( self._position.x, self._position.y + drop )
            icon_position:  vector      = vector( position.x + enable_pad, position.y + ( height - icon_size.y ) / 2 )
            text_position:  vector      = vector( position.x + icon_size.x + pad * 2 + seperate + enable_pad, position.y + ( height - text_size.y ) / 2 )

            self._render.image( check_mark, position + add_to_check, color( ) * enable )

            self._render.image( item.icon, icon_position, color( ) * hover )
            self._render.text( self._font, text_position, color( ) * hover, item.text )

            item.position = vector( 0, drop )

            drop = drop + height + pad * 2

        self._render.pop_clip_rect( )


    def __draw_scrollbar( self, fade: float ):
        """
            Draw scroll bar.

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """

        seperate:       int     = self._config.seperate
        pad:            int     = self._config.pad
        height:         int     = self._config.slot_height

        seperate_color: color   = self._config.seperate_color
        
        start_position: vector  = vector( self._position.x + self._width - seperate, self._position.y )
        
        amount_max      = self._config.slots_count
        amount_items    = len( self._items )

        window_delta    = amount_max * ( height + pad * 2 )
        drop            = amount_items * ( height + pad * 2 )

        if drop <= window_delta:
            return

        scroll = self._animations.value( "Scroll" )

        scroll_delta = window_delta / drop

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

        self._mouse_position.x  = event( "x" )
        self._mouse_position.y  = event( "y" )
        

        if self._mouse_position.is_in_bounds( self._relative_position, self._rect[ 1 ].x, self._rect[ 1 ].y ):
            
            # Check if we hovered and can have the handle. Also register self object
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:

            # Release if we hold the handle
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False


        self.__hover_items( self._is_hovered )

    
    def __event_mouse_input( self, event ) -> None:
        """
            Mouse buttons input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_hovered:
            return

        button = event( "button" )
        action = event( "action" )

        if not button == glfw.MOUSE_BUTTON_LEFT or not action == glfw.PRESS:
            return
        
        self.__handle_items( )

    
    def __event_mouse_scroll( self, event ) -> None:
        """
            Mouse scroll input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_hovered:
            return

        x_offset = event( "x_offset" )
        y_offset = event( "y_offset" )

        amount_items    = len( self._items )
        amount_max      = self._config.slots_count
        pad             = self._config.pad
        height          = self._config.slot_height

        drop        = amount_items *    ( height + pad * 2 )
        fixed_drop  = amount_max *      ( height + pad * 2 )

        if drop > fixed_drop:
            drop_min    = fixed_drop - drop
        else:
            drop_min = 0

        self._offset = math.clamp( self._offset + y_offset * 20, drop_min, 0 )


    def __hover_items( self, is_hovered_rect: bool ):
        """
            Handle if the user hover one of the items.

            Receive :   None

            Returns :   None
        """

        for item in self._items:
            item: c_list_item = item

            position = item.position + self._relative_position

            if is_hovered_rect:
                item.is_hovered = self._mouse_position.is_in_bounds( position, self._width, self._config.slot_height )
            else:
                item.is_hovered = False


    def __handle_items( self ):
        """
            Handle the press on the items. 

            Receive :   None

            Returns :   None
        """

        is_multi: bool = self._config.is_mutliselect

        for item in self._items:
            item: c_list_item = item

            if item.is_hovered:

                if is_multi:
                    item.is_enable = not item.is_enable

                else:

                    if not item.is_enable:
                        item.is_enable = True

                        self.__new_values( False, item )

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


    def set_value( self, item_name: str, value: bool = None ):
        """
            Set a new value for specific item.

            Receive : 
            - item_name         - Item text
            - value [optional]  - New value for multi select

            Returns :   None
        """

        is_multi: bool = self._config.is_mutliselect

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

    def get( self, index: str = None ) -> any: #str | bool:
        """
            Get value from list.

            Receive :
            - index [optional] - Index in multi select

            Returns :   String index or Boolean
        """

        is_multiselect = self._config.is_mutliselect

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
        seperate:           int     = self._config.seperate

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

        self._animations.preform( "Fade", self._is_visible and 1 or 0, speed )

    
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

        seperate:       int = self._config.seperate
        seperate_color: color = self._config.seperate_color

        offset: float = 0

        for item in self._items:
            item: c_list_item = item

            icon_size:          vector      = item.icon is None and vector( ) or ( item.icon.size( ) + vector( pad, 0 ) )
            text_size:          vector      = self._render.measure_text( self._font, item.text )

            hover:              float       = self._animations.preform( f"Item_{ item }_hover", item.is_hovered and 0.7 or 0.3, speed ) * fade
            enable:             float       = self._animations.preform( f"Item_{ item }_enable", item.is_enable and 1 or 0, speed ) * fade
            up:                 float       = self._animations.preform( f"Item_{ item }_up", item.is_enable and 5 or 0, speed * 2, 0.1 ) * fade

            reversed_hover:     float       = abs( enable - 1 )

            item_size:          vector      = vector( icon_size.x + text_size.x, 0 )
            position:           vector      = vector( self._position.x + offset + ( self._block_size - item_size.x ) / 2, self._position.y - up )
            
            select_position:    vector      = vector( position.x + ( item_size.x / 2 ) * reversed_hover, position.y + height - seperate )
            select_size:        vector      = vector( item_size.x * enable, seperate )
            icon_position:      vector      = vector( position.x, position.y + ( height - icon_size.y ) / 2 )
            text_position:      vector      = vector( position.x + icon_size.x, position.y + ( height - text_size.y ) / 2 )

            if enable > 0:
                self._render.shadow(
                    select_position,
                    select_position + select_size,
                    seperate_color,
                    enable,
                    25,
                    seperate / 2
                )

                self._render.rect(
                    select_position,
                    select_position + select_size,
                    color( ).lieaner( seperate_color, enable ) * enable,
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

        is_multi: bool = self._config.is_mutliselect

        for item in self._items:
            item: c_list_item = item

            if item.is_hovered:

                if is_multi:
                    item.is_enable = not item.is_enable

                else:

                    if not item.is_enable:
                        item.is_enable = True

                        self.__new_values( False, item )

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

        is_multi: bool = self._config.is_mutliselect

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


    def get( self, index: str = None ) -> any: #str | bool:
        """
            Get value from list.

            Receive :
            - index [optional] - Index in multi select

            Returns :   String index or Boolean
        """

        is_multiselect = self._config.is_mutliselect

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