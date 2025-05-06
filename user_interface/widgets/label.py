"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Label

    description : Label classes
"""

import glfw
import time
import math as omath

from queue import Queue as queue

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


class lable_config_t:
    speed:              int
    pad:                int

    text_color:         color

    def __init__( self ):
        self.speed:             int     = 7
        self.pad:               int     = 10

        self.text_color:       color   = color( 255, 255, 255 )



class c_multiline_label:

    _parent:                any    # c_scene / c_window
    _index:                 int

    _position:              vector
    _relative_position:     vector
    _size:                  vector

    _font:                  c_font

    _render:                c_renderer
    _animations:            c_animations

    _mouse_position:        vector

    _config:                lable_config_t

    _is_visible:            bool
    _is_hovered:            bool

    _items:                 queue
    _drop:                  float
    _offset:                vector

    # region : Initialize

    def __init__( self, parent: any, position: vector, size: vector, font: c_font, items: queue = None, config: lable_config_t = None ):
        
        # Set config
        self._config = config is None and lable_config_t( ) or config

        # Set parent 
        self._parent = parent

        # Set position and size
        self._position  = position.copy( )
        self._size      = size.copy( )

        # Set display information
        self._font = font

        # Set items default value
        self._items = items

        # Initialize attachment to parent
        self.__init_attachment( )

        # Initialize animations of the widget
        self.__init_animations( )

        # Initialize widget bones
        self.__init_bones( )


    def __init_attachment( self ):
        
        # Get renderer
        self._render = self._parent.render( )

        # Attach widget to parent
        self._index = self._parent.attach_element( self )

        # Attach this widget's events handlers to parent
        this_widget = f"multiline_label::{ self._index }"

        self._parent.set_event( "mouse_position",   self.__event_mouse_position,        this_widget )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,          this_widget )


    def __init_animations( self ):
        
        # Create standalone animations handler
        self._animation = c_animations( )

        self._animation.prepare( "scroll",  vector( ) )
        self._animation.prepare( "fade",    0 )

    
    def __init_bones( self ):

        self._relative_position = self._position.copy( )

        self._is_visible = True
        self._is_hovered = False

        self._drop  = 0

        self._mouse_position    = vector( )
        self._offset            = vector( )

        if not self._items:
            self._items = queue( )

    # endregion

    # region : Draw

    def draw( self, fade: float ):

        # Perform some calculations before drawing
        self.__perform_calculations( )
        self.__perform_animations( )

        fade = fade * self._animation.value( "fade" )
        if fade == 0:
            return

        self.__draw_items( fade )


    def __perform_calculations( self ):

        parent_position:            vector  = self._parent.relative_position( )
        self._relative_position:    vector  = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

        size_drop: float = self._size.y - self._config.pad

        if self._drop > size_drop:
            drop_min    = size_drop - self._drop
        else:
            drop_min = 0

        if self._offset.z > self._size.x:   
            sideways_min = self._size.x - self._offset.z
        else:
            sideways_min = 0

        self._offset.y = math.clamp( self._offset.y, drop_min, 0 )
        self._offset.x = math.clamp( self._offset.x, sideways_min, 0 )

        
    def __perform_animations( self ):

        self._animation.update( )
    
        speed: int = self._config.speed

        self._animation.perform( "fade", self._is_visible and 1 or 0, speed )
        self._animation.perform( "scroll", self._offset, speed, 1 )

    
    def __draw_items( self, fade: float ):
        
        if self._items.empty( ):
            return

        queue_size: int     = self._items.qsize( )
        pad:        int     = self._config.pad
        text_color: color   = self._config.text_color

        scroll:     vector  = self._animation.value( "scroll" )

        self._offset.z      = 0
        drop:       float   = 0
        position:   vector  = vector( self._position.x + pad + scroll.x, self._position.y + pad + self._drop + scroll.y )
        
        for index in range( queue_size ):

            # Place both of the function nearby to minimize issues later
            text = self._items.get_nowait( )
            self._items.put_nowait( text )

            # Calcualte the text and size
            wrapped_text = self._render.wrap_text( self._font, text, self._size.x )
            text_size = self._render.measure_text( self._font, wrapped_text )

            if text_size.x > self._offset.z:
                self._offset.z = text_size.x
            
            drop += text_size.y + pad

            # We have the value. display it
            self._render.text( self._font, vector( position.x, position.y - drop ), text_color * fade, wrapped_text )

        self._drop = drop

    # endregion

    # region : Events

    def __event_mouse_position( self, event ):
        
        if not self._is_visible:
            return
        
        self._mouse_position.x = event( "x" )
        self._mouse_position.y = event( "y" )

        if self._mouse_position.is_in_bounds( self._relative_position, self._size.x, self._size.y ):
            self._is_hovered = self._parent.try_to_get_handle( self._index )

        else:
            if self._parent.is_this_active( self._index ):
                self._parent.release_handle( self._index )

            self._is_hovered = False


    def __event_mouse_scroll( self, event ):
        
        if not self._is_hovered:
            return

        x_offset = event( "x_offset" )
        y_offset = event( "y_offset" )

        # We update here
        # But clamp it in the __perform_calculations function
        self._offset.y = self._offset.y + y_offset * 20
        self._offset.x = self._offset.x + x_offset * 30
        
    # endregion

    # region : Utilities

    def position( self, new_value: vector = None ) -> vector:

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y
        return new_value
    
    
    def size( self, new_value: vector = None ) -> vector:

        if new_value is None:
            return self._size
        
        self._size.x = new_value.x
        self._size.y = new_value.y
        return new_value


    def visible( self, new_value: bool = None ) -> bool:

        if new_value is None:
            return self._is_visible

        self._is_visible = new_value
        return new_value
    

    @safe_call( None )
    def add_item( self, message: str ):

        self._items.put_nowait( message ) 

    
    def clear( self, amount: int = -1, should_clear: int = -1 ):

        if self._items.empty( ):
            return

        if amount == -1 and should_clear == -1:
            amount = self._items.qsize( )

        if should_clear != -1:
            if amount > should_clear:
                amount = amount - should_clear
            else:
                return

        for index in range( amount ):
            self._items.get_nowait( )

    # endregion