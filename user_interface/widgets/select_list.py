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

    seperate_color: color       = color( 150, 150, 255 )

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
    
    # region : Initialize list

    def __init__( self, parent: any, position: vector, width: int, font: c_font, items: dict, config: list_config_t = None ):
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

        self.__initialize_animations( )
        self.__initialize_items( items )
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

    
    def __initialize_items( self, items: dict ):
        """
            Initialize items in the list.

            Receive : 
            - items - Item name and its image

            Returns :   None
        """
        
        self._items = [ ]

        for item in items:
            new_item = c_list_item( )

            new_item.text = item
            new_item.icon = items[ item ]

            new_item.is_enable      = False
            new_item.is_hovered     = False

            new_item.position       = vector( )

            self._animations.prepare( f"Item_{ item }_hover",   0 )
            self._animations.prepare( f"Item_{ item }_enable",  0 )

            self._items.append( new_item )


    def __initialize_animations( self ):
        """
            Initialize button animations values

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

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

        self.__draw_items( fade )


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

        check_mark: c_image = self._config.check_mark
        check_size: vector  = check_mark.size( )
        add_to_check: vector = vector( 0, ( height - check_size.y ) / 2 )

        enable_pad: float   = self._animations.value( "AddOnEnable" )

        drop = 0

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

        self.__hover_items( )

    
    def __event_mouse_input( self, event ) -> None:
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
            item.is_hovered = self._mouse_position.is_in_bounds( position, self._width, self._config.slot_height )


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

    # endregion
