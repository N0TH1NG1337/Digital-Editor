# User Interface. Widget -> File dialog / Folder selector .py

# Will be used only once, in the server, the user will need to select a path to copy the files from it.
# In this file, will be included, sub_file_clas, sub_folder_class that will be used only for the file dialog widget

import glfw
import os

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
from user_interface.text_input  import c_signle_input_logic


class c_base_file:
    # File class

    _path:  str     # Full path to file
    _name:  str     # Files name (including type)

    def __init__( self, path: str, name: str ):
        
        self._path = path
        self._name = name


    def name( self ) -> str:
        return self._name


    def path( self ) -> str:
        return self._path


    def file_path( self ) -> str:

        return self._path + "\\" + self._name


    def get_type( self ) -> str | None:

        try:

            name, file_type = self._name.rsplit( '.', 1 )
            return file_type

        except Exception as e:
            return None
        

    def get_file_content( self ) -> list:

        lines = [ ]

        with open( self.file_path( ), "r" ) as file:
            for line in file:
                #line_data = line.strip()
                lines.append( line )

        return lines
    

    def get_file_bytes( self ) -> bytes:

        with open( self.file_path( ), "rb" ) as file:
            return file.read( ) 
    

class c_base_folder:
    # Specific folder.
    # contains prev folder that points to this folder.
    # contains content of current folder.

    _prev:      any
    _name:      str

    _folders:   list
    _files:     list

    def __init__( self, prev: any, name: str ):
        
        self._prev = prev
        self._name = name

        self._folders = [ ]
        self._files = [ ]

    def previous( self ) -> any:

        return self._prev
    
    def name( self ) -> str:

        return self._name
    
    def folders( self ) -> list:

        return self._folders
    
    def files( self ) -> list:

        return self._files
    
    def absolute_path( self ) -> str:

        result = self.name( )

        pos = self._prev
        while pos is not None:

            result = f"{ pos.name( ) }\\{ result }"
            pos = pos.previous( )

        return result
    
    def dump( self ) -> bool:
        # Scans current folder for data

        full_path = self.absolute_path( )

        # TODO ! Maybe clear folders and files contenct?

        with os.scandir( full_path ) as entries:

            for entry in entries:

                if entry.is_file( ):
                    # Is File

                    new_file = c_base_file( full_path, entry.name )
                    self._files.append( new_file )
                
                elif entry.is_dir( ):
                    # Is Folder

                    new_folder = c_base_folder( self, entry.name )
                    self._folders.append( new_folder )

    def clear( self ) -> None:

        self._folders.clear( )
        self._files.clear( )


class c_file_dialog:

    _parent:            c_scene
    _index:             int

    _position:          vector
    _size:              vector
    _window_size:       vector

    _font:              c_font

    _render:            c_renderer
    _animations:        c_animations

    _config:            dict

    _active_folder:     c_base_folder

    _mouse_position:    vector
    _files_information: vector

    _is_hovered_back:   bool
    _is_hovered_path:   bool
    _input_path:        c_signle_input_logic

    _offset:            float
    _drop:              float

    def __init__( self, parent: c_scene, font: c_font, position: vector, size: vector, height_of_path: int ):
        # Default constructor

        self._parent        = parent
        self._index         = -1

        self._position      = position.copy( )
        self._size          = size.copy( )
        self._window_size   = size.copy( )

        self._font          = font

        self._input_path    = c_signle_input_logic( font, vector( size.x - 60, height_of_path ), False, "", False )

        self.__init_parent( )
        self.__init_config( )
        self.__init_animations( )
        self.__init_attach( )

        self.__init( )

    def __init_parent( self ):
        self._render = self._parent.render( )

        self._input_path.setup( self, self._position + vector( 60, 0 ) )
        self._input_path.size( self._input_path.size() - self._input_path.config( "pad" ) * 2 )

    def __init_animations( self ):
        self._animations = c_animations( )

        self._animations.prepare( "Back", 1 )
        self._animations.prepare( "Scroll", 0 )

    def __init_attach( self ):

        self._index = self._parent.attach_element( self )

        this_id = f"FileDialog::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,      this_id )
        self._parent.set_event( "char_input",       self.__event_char_input,        this_id )
        self._parent.set_event( "keyboard_input",   self.__event_keyboard_input,    this_id )
        
    def __init_config( self ):

        # Receive config information
        first_parent = self._parent
        while str( type( first_parent ) ).find( "c_application" ) == -1:
            first_parent = first_parent.parent( )
        
        self._config = first_parent.config( "File Dialog" )

    def __init( self ):
        # Complete all the remaining things

        self._mouse_position    = vector( )
        self._active_folder     = None

        self._is_hovered_back   = False
        self._is_hovered_path   = False

        self._offset            = 0
        self._drop              = 0

        self._files_information = { }

    # region : Draw

    def draw( self, fade: float ):
        self.__calculate( )

        self.__draw_back_button( fade )
        self.__draw_path_input( fade )
        self.__draw_background( fade )

        self.__draw_folders( fade )

        self._render.pop_clip_rect( )

    def __draw_back_button( self, fade: float ):

        color_back      = self._config[ "color_back" ]
        color_button    = self._config[ "color_button" ]
        rounding        = self._config[ "rounding" ]

        size            = vector( 50, self._input_path.correct_size( ).y )

        back = self._animations.value( "Back" )

        self._render.rect( self._position, self._position + size, color_back * fade * back, rounding )

        self._render.triangle( 
            self._position + vector( 13, size.y / 2 ), 
            self._position + vector( 32, size.y / 2 - 7 ), 
            self._position + vector( 32, size.y / 2 + 7 ),
            color_button * fade
        )

    def __draw_path_input( self, fade: float ):
        
        color_back  = self._config[ "color_back" ]
        rounding    = self._config[ "rounding" ]

        position = self._input_path.position( )

        self._render.rect( position, position + self._input_path.correct_size( ), color_back * fade, rounding )
        self._input_path.draw( fade )

    def __draw_background( self, fade: float ):

        end_position    = self._position + self._size
        start_position  = end_position - self._window_size

        color_back  = self._config[ "color_back" ]
        rounding    = self._config[ "rounding" ]

        self._render.rect( start_position, end_position, color_back * fade, rounding )
        self._render.push_clip_rect( start_position, end_position )

    def __draw_folders( self, fade: float ):
        
        pad             = self._config[ "pad" ]
        color_folder    = self._config[ "color_folder" ]
        speed           = self._config[ "speed" ]

        end_position    = self._position + self._size
        start_position  = end_position - self._window_size + vector( pad, pad )
        end_position    = end_position - vector( pad, pad )

        delta = end_position.x - start_position.x

        start_position.y = start_position.y + self._animations.value( "Scroll" )

        drop = 0

        if self._active_folder is None:
            return
        
        folders: list = self._active_folder.folders( )

        for folder in folders:
            folder: c_base_folder = folder
            name = folder.name( )

            if not name in self._files_information:
                self._files_information[ name ] = { }

                self._files_information[ name ][ "folder" ] = folder
                self._files_information[ name ][ "is_hovered" ] = False

            name_size   = self._render.measure_text( self._font, name )
            info        = self._files_information[ name ]
            drop_add    = name_size.y + pad

            show        = self._animations.preform( f"Folder_{ name }_show", 1, speed / 3 )
            is_hovered  = self._animations.preform( f"Folder_{ name }_hover", info[ "is_hovered" ] and 20 or 0, speed, 1 )

            show_position   = start_position + vector( 0, drop )
            add_vector      = vector( is_hovered, 0 )

            self._render.text( self._font, show_position + add_vector, color_folder * fade * show, name )

            drop = drop + drop_add

            info[ "position" ]  = show_position
            info[ "size" ]      = vector( delta, name_size.y )

        self._drop = drop

    def __calculate( self ):
        self._animations.update( )

        correct_size        = self._input_path.correct_size( )
        self._window_size.y = self._size.y - correct_size.y - 10

        speed = self._config[ "speed" ]

        self._animations.preform( "Back", self._is_hovered_back and 0.5 or 1, speed )
        self._animations.preform( "Scroll", self._offset, speed, 0.5 )

    def position( self, new_value: vector = None ) -> vector | None:

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

    def size( self, new_value: vector = None ) -> vector | None:

        if new_value is None:
            return self._size
        
        self._size.x = new_value.x
        self._size.y = new_value.y

    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        # Mouse Position change callback

        self._input_path.event_mouse_position( event )

        x = event( "x" )
        y = event( "y" )

        self._mouse_position.x = x
        self._mouse_position.y = y

        size_of_path = self._input_path.correct_size( )

        self._is_hovered_back = self._mouse_position.is_in_bounds( self._position, 50, size_of_path.y )
        self._is_hovered_path = self._mouse_position.is_in_bounds( self._input_path.position( ), size_of_path.x, size_of_path.y )

        if self._active_folder is None:
            return

        for folder in self._files_information:

            info        = self._files_information[ folder ]
            position    = info[ "position" ]
            size        = info[ "size" ]

            info[ "is_hovered" ] = self._mouse_position.is_in_bounds( position, size.x, size.y )


    def __event_mouse_input( self, event ) -> None:
        
        self._input_path.event_mouse_input( event )

        button = event( "button" )
        action = event( "action" )

        if not button == glfw.MOUSE_BUTTON_LEFT or not action == glfw.PRESS:
            return
        
        if self._is_hovered_back and self._active_folder.previous( ) is not None:
            self._active_folder: c_base_folder = self._active_folder.previous( )
            self.__set_new_folder( self._active_folder )

            self._active_folder.dump( )
            self._animations.clear( )
            self.__prepare_animations( )
                

            return

        self._input_path.is_typing( self._is_hovered_path )

        if self._active_folder is None:
            return
        
        end_position    = self._position + self._size
        start_position  = end_position - self._window_size

        if not self._mouse_position.is_in_bounds( start_position, self._window_size.x, self._window_size.y ):
            return
        
        folders: list = self._active_folder.folders( )

        for folder in folders:
            folder: c_base_folder = folder
            name = folder.name( )

            info        = self._files_information[ name ]

            if info[ "is_hovered" ]:

                self._active_folder.clear( )
                self._animations.clear( )

                self._active_folder = folder

                self._active_folder.dump( )

                self.__prepare_animations( )
                self.__set_new_folder( self._active_folder )
                break

    
    def __event_mouse_scroll( self, event ) -> None:

        x_offset = event( "x_offset" )
        y_offset = event( "y_offset" )

        if self._drop > self._window_size.y:
            pad         = self._config[ "pad" ]
            drop_min    = self._window_size.y - self._drop - pad
        else:
            drop_min = 0

        self._offset = math.clamp( self._offset + y_offset * 20, drop_min, 0 )


    def __event_char_input( self, event ) -> None:
        
        self._input_path.event_char_input( event )


    def __event_keyboard_input( self, event ) -> None:
        
        self._input_path.event_keyboard_input( event )

    # endregion

    # region : Access

    def render( self ) -> c_renderer:

        return self._render
    
    def parent( self ) -> any:

        return self._parent
    
    def get_path( self ) -> str:

        return self._active_folder.absolute_path( )
    
    def get_files( self ) -> list:

        return self._active_folder.files( )
    
    def parse_path( self, path: str ) -> any:
        # Get absolute path to a specific folder.
        # Create folders chain

        data = path.split( os.sep )

        for folder in data:

            # Fix for discs paths...
            if folder.endswith( ":" ):
                folder = f"{folder}\\"

            self._active_folder = c_base_folder( self._active_folder, folder )

        self._active_folder.dump( )
        
        self.__prepare_animations( )

        self._input_path.set( self._active_folder.absolute_path( ) )

        return self._active_folder

    def __prepare_animations( self ):

        if self._active_folder is None:
            return
        
        folders: list = self._active_folder.folders( )

        for folder in folders:
            folder: c_base_folder = folder
            name = folder.name( )

            self._animations.prepare( f"Folder_{ name }_show", 0 )
            self._animations.prepare( f"Folder_{ name }_hover", 0 )

    def __set_new_folder( self, new_folder: c_base_folder ):
        
        self._input_path.set( new_folder.absolute_path( ) )
        self._active_folder = new_folder

        self._offset = 0

    # endregion