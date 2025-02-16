"""
    project     : Digital Editor

    type:       : User Interface - Widget
    file        : Path selector

    description : Path selector classes

    NOTE ! Like file dialog but only for folders select.
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

from user_interface.widgets.text_input import c_single_input_logic, text_input_config_t


class c_base_file:
    # File class

    _path:  str     # Full path to file
    _name:  str     # Files name (including type)

    def __init__( self, path: str, name: str ):
        """
            Default constructor for base file object.

            Receive : 
            - path - Path to the file
            - name - Name of the file (including .type)

            Returns :   Base file object
        """

        self._path = path
        self._name = name


    def name( self ) -> str:
        """
            Get file full name.

            Receive :   None

            Returns :   String value
        """

        return self._name


    def path( self ) -> str:
        """
            Get file path.

            Receive :   None

            Returns :   String value
        """

        return self._path


    def file_path( self ) -> str:
        """
            Get file full path, including its name.

            Receive :   None

            Returns :   String value
        """

        return self._path + "\\" + self._name


    def information( self ) -> tuple:
        """
            Get file type and name.

            Receive :   None
            
            Returns :   Tuple value ( name, type )
        """

        try:

            name, file_type = self._name.rsplit( '.', 1 )
            return name, file_type

        except Exception as e:
            return None, None
        

    #def get_file_content( self ) -> list:
    #    lines = [ ]
    #    with open( self.file_path( ), "r" ) as file:
    #        for line in file:
    #            lines.append( line )
    #    return lines
    

    #def get_file_bytes( self ) -> bytes:
    #    with open( self.file_path( ), "rb" ) as file:
    #        return file.read( ) 
    

class c_base_folder:
    # Specific folder.
    # contains prev folder that points to this folder.
    # contains content of current folder.

    _prev:      any
    _name:      str

    _folders:   list
    _files:     list

    def __init__( self, prev: any, name: str ):
        """
            Default constructor for base folder object.

            Receive :   
            - prev - Previous folder
            - name - Name of the folder

            Returns :   Base folder object
        """
        
        self._prev = prev
        self._name = name

        self._folders = [ ]
        self._files = [ ]


    def previous( self ) -> any:
        """
            Get previous folder.

            Receive :   None

            Returns :   Base folder object
        """

        return self._prev
    

    def name( self ) -> str:
        """
            Get folder name.

            Receive :   None

            Returns :   String value
        """

        return self._name
    

    def folders( self ) -> list:
        """
            Get all the folders inside this folder.

            Receive :   None

            Returns :   List of base folder objects
        """

        return self._folders
    
    
    def files( self ) -> list:
        """
            Get all the files inside this folder.

            Receive :   None

            Returns :   List of base file objects
        """

        return self._files
    

    def absolute_path( self ) -> str:
        """
            Get absolute path of this folder.

            Receive :   None

            Returns :   String value
        """

        result = self.name( )

        pos = self._prev
        while pos is not None:

            result = f"{ pos.name( ) }\\{ result }"
            pos = pos.previous( )

        return result
    

    @safe_call( None )
    def dump( self ) -> bool:
        """
            Scans current folder for files and other folders.

            Receive :   None

            Returns :   Result
        """

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

        return True


    def clear( self ) -> None:
        """
            Clear this folder content.

            Receive :   None

            Returns :   None
        """

        self._folders.clear( )
        self._files.clear( )


class path_select_config_t:
    speed:              int     = 10
    pad:                int     = 10
    seperate:           int     = 4
    roundness:          int     = 10

    seperate_color:     color   = color( 216, 208, 215 )
    path_text_color:    color   = color( )
    back_color:         color   = color( 0, 0, 0, 100 )


class c_path_select:
    # NOTE ! This is not fully correct to call this widget, but collection of widgets

    _parent:                any     # c_scene / c_window
    _index:                 int     # Button index

    _position:              vector  # Position in parent
    _relative_position:     vector  # Relative position on screen
    _size:                  vector
    _window_size:           vector

    _font:                  c_font
    _back_icon:             c_image
    _folder_icon:           c_image
    _file_icon:             c_image

    _render:                c_renderer
    _animations:            c_animations

    _config:                path_select_config_t

    _active_folder:         c_base_folder

    _is_visible:            bool
    _is_hovered:            bool
    _is_hovered_back:       bool
    _is_hovered_path:       bool
    _input_path:            c_single_input_logic

    _offset:                float
    _drop:                  float

    _mouse_position:        vector
    _files_information:     dict

    # region : Initialize widget

    def __init__( self, parent: any, font: c_font, position: vector, size: vector, images: dict, config: path_select_config_t = None ):
        """
            Default constructor for path select object.

            Receive : 
            - parent                - Parent object to attach
            - font                  - Font for text
            - position              - Position in the parent
            - size                  - Size of the whole path selector
            - images                - 3 Images. { back_icon, folder_icon, file_icon }
            - config [ optinal ]    - Config for path selector

            Returns :   Path select object
        """

        self._parent    = parent

        self._position  = position.copy( )
        self._size      = size.copy( )

        self._font      = font

        self._back_icon:    c_image = images[ "back_icon" ]
        self._folder_icon:  c_image = images[ "folder_icon" ]
        self._file_icon:    c_image = images[ "file_icon" ]

        self._config = config is None and path_select_config_t( ) or config

        self.__initialize_parent( )
        self.__initialize_path_input( )
        self.__initialize_animations( )
        self.__initialize_values( )

    
    def __initialize_parent( self ):
        """
            Initialize parent attach.

            Receive :   None

            Returns :   None
        """
        
        self._render = self._parent.render( )

        self._index = self._parent.attach_element( self )

        this_id = f"PathSelect::{ self._index }"
        self._parent.set_event( "mouse_position",   self.__event_mouse_position,    this_id )
        self._parent.set_event( "mouse_input",      self.__event_mouse_input,       this_id )
        self._parent.set_event( "mouse_scroll",     self.__event_mouse_scroll,      this_id )
        self._parent.set_event( "char_input",       self.__event_char_input,        this_id )
        self._parent.set_event( "keyboard_input",   self.__event_keyboard_input,    this_id )

    
    def __initialize_path_input( self ):
        """
            Initialize the input field it self.

            Receive :   None

            Returns :   None
        """

        pad:            int     = self._config.pad
        seperate:       int     = self._config.seperate
        back_button:    int     = pad * 3 + self._back_icon.size( ).x + seperate
        position:       vector  = vector( self._position.x + back_button, self._position.y )
        size:           vector  = vector( self._size.x - back_button - pad * 2, self._back_icon.size( ).y )

        config = text_input_config_t( )

        config.pad          = pad
        config.speed        = self._config.speed
        config.input_color  = self._config.path_text_color.copy( )

        self._input_path = c_single_input_logic( self._parent, position, self._font, size, False, "", config )


    def __initialize_animations( self ):
        """
            Initialize animations.

            Receive :   None

            Returns :   None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Back",   0.5 )
        self._animations.prepare( "Scroll", 0 )
        self._animations.prepare( "Fade",   0 )

    
    def __initialize_values( self ):
        """
            Initialize default values.

            Receive :   None

            Returns :   None
        """

        self._active_folder     = None

        self._is_hovered        = False
        self._is_visible        = True
        self._is_hovered_back   = False
        self._is_hovered_path   = False

        self._offset            = 0
        self._drop              = 0

        self._relative_position = self._position.copy( )
        self._window_size       = self._size.copy( )
        self._mouse_position    = vector( )

        self._files_information = { }

    # endregion

    # region : Draw

    def draw( self, fade: float ):
        """
            Draw the path selector.

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """ 

        self.__preform( )
        self.__animate( )

        fade = fade * self._animations.value( "Fade" )
        if fade == 0:
            return
        
        self.__draw_back( fade )
        self.__draw_top_bar( fade )
        self.__draw_content( fade )
        self.__draw_scrollbar( fade )


    def __preform( self ):
        """
            Preforms all the behind the scenes small calculations.

            Receive :   None

            Returns :   None
        """

        pad:                        int     = self._config.pad

        self._window_size.y                 = self._size.y - self._input_path.correct_size( ).y

        parent_position:            vector  = self._parent.relative_position( )
        self._relative_position:    vector  = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )
    

    def __animate( self ):
        """
            Animate the animations.

            Receive :   None

            Returns :   None
        """

        self._animations.update( )

        speed: int = self._config.speed

        fade: float = self._animations.preform( "Fade", self._is_visible and 1 or 0, speed )
        if fade == 0:
            return

        self._animations.preform( "Back", self._is_hovered_back and 1 or 0.3, speed )
        self._animations.preform( "Scroll", self._offset, speed, 1 )


    def __draw_back( self, fade: float ):
        """
            Draw the backgorund

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """

        roundness:  int     = self._config.roundness
        back_color: color   = self._config.back_color

        self._render.gradiant(
            self._position,
            self._position + self._size, 
            back_color * fade,
            back_color * fade,
            back_color * fade,
            back_color * fade,
            roundness
        )

        self._render.shadow(
            self._position,
            self._position + self._size, 
            back_color,
            fade,
            25,
            roundness
        )


    def __draw_top_bar( self, fade: float ):
        """
            Draw the top bar of the path select. 
            Including back button, path and more.

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """
        
        pad:                int     = self._config.pad
        seperate:           int     = self._config.seperate
        seperate_color:     color   = self._config.seperate_color
        back_icon_size:     vector  = self._back_icon.size( )
        path_size:          vector  = self._input_path.correct_size( )
        seperate_position:  vector  = vector( self._position.x + pad * 2 + back_icon_size.x, self._position.y + pad )

        hover_back:         float   = self._animations.value( "Back" ) * fade

        self._render.image( self._back_icon, self._position + vector( pad, pad ), color( ) * hover_back )

        self._render.shadow( seperate_position, seperate_position + vector( seperate, path_size.y - pad * 2 ), seperate_color, fade, 25, seperate / 2)
        self._render.rect( seperate_position, seperate_position + vector( seperate, path_size.y - pad * 2 ), seperate_color * fade, seperate / 2 )

        self._input_path.draw( fade )

    
    def __draw_content( self, fade: float ):
        """
            Draw the content of the active folder.

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """

        speed:          int     = self._config.speed
        pad:            int     = self._config.pad
        seperate:       int     = self._config.seperate
        seperate_color: color   = self._config.seperate_color
        
        end_position:   vector  = self._position + self._size
        start_position: vector  = end_position - self._window_size

        if self._active_folder is None:
            return
        
        drop                = 0
        
        self._render.push_clip_rect( start_position, end_position, True )

        start_position.y    = start_position.y + self._animations.value( "Scroll" )

        folders:    list    = self._active_folder.folders( )
        files:      list    = self._active_folder.files( )

        # Folders
        for folder in folders:
            folder: c_base_folder = folder
            name = folder.name( )

            if not name in self._files_information:
                self._files_information[ name ] = { }

                self._files_information[ name ][ "folder" ]     = folder
                self._files_information[ name ][ "is_hovered" ] = False

            name_size   = self._render.measure_text( self._font, name )
            info        = self._files_information[ name ]
            icon_size   = self._folder_icon.size( )
            
            show            = self._animations.preform( f"Folder_{ name }_show",        info[ "is_hovered" ] and 1 or 0.5, speed / 3 ) * fade
            show_seperate   = self._animations.preform( f"Folder_{ name }_seperate",    info[ "is_hovered" ] and 1 or 0, speed ) * fade
            hover_add       = self._animations.preform( f"Folder_{ name }_hover_add",   info[ "is_hovered" ] and pad * 2 + seperate or 0, speed, 1 )

            icon_position = vector( start_position.x + pad, start_position.y + drop )
            text_position = vector( start_position.x + icon_size.x + pad * 2 + hover_add, start_position.y + drop + ( icon_size.y - name_size.y ) / 2 )
            seperate_position = vector( start_position.x + icon_size.x + pad * 2, start_position.y + drop )

            self._render.image( self._folder_icon, icon_position, color( ) * show )

            self._render.rect( seperate_position, seperate_position + vector( seperate, icon_size.y * show_seperate ), seperate_color * show_seperate, seperate / 2 )

            self._render.text( self._font, text_position, color( ) * show, name )

            drop = drop + pad + icon_size.y

            info[ "position" ] = icon_position
            info[ "size" ]      = vector( self._window_size.x, icon_size.y )

        # Files 
        for file in files:
            file: c_base_file = file
            name = file.name( )

            name_size   = self._render.measure_text( self._font, name )
            icon_size   = self._file_icon.size( )

            show = 0.3 * fade

            icon_position = vector( start_position.x + pad, start_position.y + drop )
            text_position = vector( start_position.x + icon_size.x + pad * 2, start_position.y + drop + ( icon_size.y - name_size.y ) / 2 )

            self._render.image( self._file_icon, icon_position, color( ) * show )

            self._render.text( self._font, text_position, color( ) * show, name )

            drop = drop + pad + icon_size.y

        self._drop = drop

        self._render.pop_clip_rect( )
        

    def __draw_scrollbar( self, fade: float ):
        """
            Draw scroll bar.

            Receive : 
            - fade - Fade factor of the parent

            Returns :   None
        """

        seperate:       int     = self._config.seperate
        seperate_color: color   = self._config.seperate_color
        
        end_position:   vector  = self._position + self._size
        start_position: vector  = end_position - self._window_size

        if self._active_folder is None:
            return
        
        if self._drop <= self._window_size.y:
            return

        scroll = self._animations.value( "Scroll" )

        window_delta = self._window_size.y
        scroll_delta = window_delta / self._drop

        fixed = self._window_size.y * scroll_delta
        value = abs( scroll ) * scroll_delta

        position        = vector( start_position.x + self._window_size.x - seperate, start_position.y + value )
        end_position    = vector( start_position.x + self._window_size.x, start_position.y + value + fixed )

        self._render.shadow( position, end_position, seperate_color, fade, 25, seperate / 2)
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

        self._is_hovered = self._mouse_position.is_in_bounds( self._position, self._size.x, self._size.y )

        self.__hover_back_button( )
        if self._is_hovered_back:
            return

        self.__hover_folders( )

    def __event_mouse_input( self, event ) -> None:
        """
            Mouse buttons input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_visible:
            return

        button = event( "button" )
        action = event( "action" )

        if not button == glfw.MOUSE_BUTTON_LEFT or not action == glfw.PRESS:
            return
        
        if self.__handle_back_button( ):
            return
        
        self.__handle_folders( )

    
    def __event_mouse_scroll( self, event ) -> None:
        """
            Mouse scroll input callback.

            Receive :   
            - event - Event information

            Returns :   None
        """

        if not self._is_visible:
            return

        y_offset = event( "y_offset" )

        if not y_offset:
            return
        
        if not self._is_hovered:
            return

        if self._drop > self._window_size.y:
            drop_min    = self._window_size.y - self._drop
        else:
            drop_min = 0

        self._offset = math.clamp( self._offset + y_offset * 20, drop_min, 0 )


    def __event_char_input( self, event ) -> None:
        
        pass


    def __event_keyboard_input( self, event ) -> None:
        
        pass


    def __hover_back_button( self ):
        """
            Handle if the user hover the back button.

            Receive :   None

            Returns :   None
        """

        position = self._relative_position + vector( self._config.pad, self._config.pad )
        size = self._back_icon.size( )

        self._is_hovered_back = self._mouse_position.is_in_bounds( position, size.x, size.y )


    def __handle_back_button( self ) -> bool:
        """
            Handle back button action.

            Receive :   None

            Returns :   Should stop other actions
        """

        if not self._is_hovered_back:
            return False
        
        if self._active_folder.previous( ) is None:
            return False
        
        self._active_folder.clear( )
        self._animations.clear( )

        self._active_folder: c_base_folder = self._active_folder.previous( )
        
        self._active_folder.dump( )

        self.__prepare_animations( )
        self.__set_new_folder( self._active_folder )

        return True
    

    def __hover_folders( self ):
        """
            Handle if the user hover one of the folders.

            Receive :   None

            Returns :   None
        """

        if self._active_folder is None:
            return
        
        for folder in self._files_information:

            info                = self._files_information[ folder ]
            position:   vector  = info[ "position" ] + self._relative_position - self._position
            size:       vector  = info[ "size" ]

            info[ "is_hovered" ] = self._mouse_position.is_in_bounds( position, size.x, size.y )

    
    def __handle_folders( self ):
        """
            Handle folder press actions.

            Receive :   None

            Returns :   None
        """

        if self._active_folder is None:
            return
        
        end_position    = self._relative_position + self._size
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

    # endregion

    # region : Utilities

    def parse_path( self, path: str ) -> c_base_folder:
        """
            Get absolute path to a specific folder.
            Create folders chain.

            Receive : 
            - path - Path value

            Returns :   Active folder
        """

        data = path.split( os.sep )

        for folder in data:

            # Fix for disks paths...
            if folder.endswith( ":" ):
                folder = f"{folder}\\"

            self._active_folder = c_base_folder( self._active_folder, folder )

        self._active_folder.dump( )
        
        self.__prepare_animations( )

        self._input_path.set( self._active_folder.absolute_path( ) )

        return self._active_folder
    

    def __set_new_folder( self, new_folder: c_base_folder ):
        """
            Set new active folder, and reset some other things.

            Receive : 
            - new_folder - New base folder object

            Returns :   None
        """

        self._input_path.set( new_folder.absolute_path( ) )
        self._active_folder = new_folder

        self._offset = 0

    
    def __prepare_animations( self ):
        """
            Prepare animations for active folder content. 

            Receive :   None

            Returns :   None
        """

        if self._active_folder is None:
            return
        
        folders: list = self._active_folder.folders( )

        for folder in folders:
            folder: c_base_folder = folder
            name = folder.name( )

            self._animations.prepare( f"Folder_{ name }_show",      0 )
            self._animations.prepare( f"Folder_{ name }_seperate",  0 )
            self._animations.prepare( f"Folder_{ name }_hover",     0 )
    

    def position( self, new_value: vector = None ) -> vector:
        """
            Access / Update position.

            Receive :
            - new_value - New position in the parent

            Returns : Vector
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

    
    def get_path( self ) -> str:
        """
            Get selected path.

            Receive :   None

            Returns :   String value
        """
        
        return self._active_folder.absolute_path( )

    # endregion