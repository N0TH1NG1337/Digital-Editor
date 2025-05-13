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
        Default constructor for the base file object.

        Receives:
        - path (str): The full path to the file.
        - name (str): The name of the file, including its extension.

        Returns:
        - c_base_file: The newly created c_base_file object.
        """

        self._path = path
        self._name = name


    def name( self ) -> str:
        """
        Returns the full name of the file (including the extension).

        Receives: None

        Returns:
        - str: The file's name.
        """

        return self._name


    def path( self ) -> str:
        """
        Returns the full path to the file.

        Receives: None

        Returns:
        - str: The file's path.
        """

        return self._path


    def file_path( self ) -> str:
        """
        Returns the complete file path, including the directory and the file name.

        Receives: None

        Returns:
        - str: The full file path.
        """

        return self._path + "\\" + self._name


    def information( self ) -> tuple:
        """
        Extracts and returns the file name (without extension) and its type (extension).

        Receives: None

        Returns:
        - tuple: A tuple containing the file name (str) and the file type (str). 
                 Returns (None, None) if the file name does not contain an extension.
        """

        try:

            name, file_type = self._name.rsplit( '.', 1 )
            return name, file_type

        except Exception as e:
            return None, None
    

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
        Default constructor for the base folder object.

        Receives:
        - prev (any): The parent folder object.
        - name (str): The name of the current folder.

        Returns:
        - c_base_folder: The newly created c_base_folder object.
        """
        
        self._prev = prev
        self._name = name

        self._folders = [ ]
        self._files = [ ]


    def previous( self ) -> any:
        """
        Returns the parent folder object.

        Receives: None

        Returns:
        - any: The parent c_base_folder object.
        """

        return self._prev
    

    def name( self ) -> str:
        """
        Returns the name of the current folder.

        Receives: None

        Returns:
        - str: The folder's name.
        """

        return self._name
    

    def folders( self ) -> list:
        """
        Returns a list of all sub-folders within the current folder.

        Receives: None

        Returns:
        - list: A list containing c_base_folder objects representing the sub-folders.
        """

        return self._folders
    
    
    def files( self ) -> list:
        """
        Returns a list of all files within the current folder.

        Receives: None

        Returns:
        - list: A list containing c_base_file objects representing the files.
        """

        return self._files
    

    def absolute_path( self ) -> str:
        """
        Constructs and returns the absolute path of the current folder.

        It traverses up the folder hierarchy using the `_prev` attribute until it reaches the root, 
        concatenating the names of the folders along the way.

        Receives: None

        Returns:
        - str: The absolute path of the folder.
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
        Scans the current folder for files and sub-folders and populates the internal lists.

        It uses `os.scandir` for efficient directory traversal. For each entry, it creates
        either a `c_base_file` object and adds it to the `_files` list, or a `c_base_folder`
        object (with the current folder as its parent) and adds it to the `_folders` list.

        Returns:
        - bool: True if the scan was successful.
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
        Removes all files and sub-folders from the current folder's internal lists.

        This method does not affect the actual file system; it only clears the
        references held by this `c_base_folder` object.

        Receives: None

        Returns: None
        """

        self._folders.clear( )
        self._files.clear( )


class path_select_config_t:
    speed:              int
    pad:                int
    separate:           int
    roundness:          int

    separate_color:     color
    path_text_color:    color
    back_color:         color

    def __init__( self ):

        self.speed:              int     = 10
        self.pad:                int     = 10
        self.separate:           int     = 4
        self.roundness:          int     = 10

        self.separate_color:     color   = color( 207, 210, 215 )
        self.path_text_color:    color   = color( )
        self.back_color:         color   = color( 0, 0, 0, 150 )


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
        Default constructor for the path select object.

        Receives:
        - parent (any): The parent object to which this path selector will be attached.
        - font (c_font): The font object used for displaying text.
        - position (vector): The initial position (x, y) of the path selector within its parent.
        - size (vector): The dimensions (width, height) of the path selector.
        - images (dict): A dictionary containing three `c_image` objects with keys: "back_icon", "folder_icon", and "file_icon".
        - config (path_select_config_t, optional): Configuration settings for the path selector. Defaults to None.

        Returns:
        - c_path_select: The newly created c_path_select object.
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
        Initializes the attachment of the path selector to its parent and registers event handlers.

        Receives: None

        Returns: None
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
        Initializes the single-line text input field for displaying and editing the path.

        Receives: None

        Returns: None
        """

        pad:            int     = self._config.pad
        seperate:       int     = self._config.separate
        back_button:    int     = pad * 3 + self._back_icon.size( ).x + seperate
        position:       vector  = vector( self._position.x + back_button, self._position.y )
        size:           vector  = vector( self._size.x - back_button - pad * 2, self._back_icon.size( ).y + pad * 2 )

        config = text_input_config_t( )

        config.pad          = pad
        config.speed        = self._config.speed
        config.input_color  = self._config.path_text_color.copy( )

        self._input_path = c_single_input_logic( self._parent, position, size, self._font, "", False, config )


    def __initialize_animations( self ):
        """
        Initializes the animation values for the path selector.

        Receives: None

        Returns: None
        """

        self._animations = c_animations( )

        self._animations.prepare( "Back",   0.5 )
        self._animations.prepare( "Scroll", 0 )
        self._animations.prepare( "Fade",   0 )

    
    def __initialize_values( self ):
        """
        Initializes the default state and values for the path selector.

        Receives: None

        Returns: None
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
        Draws the path selector and its components.

        Receives:
        - fade (float): The fade factor inherited from the parent.

        Returns: None
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
        Performs background calculations for the path selector.

        Calculates the available size for the content area based on the total size and the input field's height.
        Updates the absolute screen position of the path selector.
        Adjusts the position and size of the internal path input field.

        Receives: None

        Returns: None
        """

        pad:                        int     = self._config.pad
        seperate:                   int     = self._config.separate
        back_button:                int     = pad * 3 + self._back_icon.size( ).x + seperate

        self._window_size.y                 = self._size.y - self._input_path.fixed_size( ).y
        self._window_size.x                 = self._size.x

        parent_position:            vector  = self._parent.relative_position( )
        self._relative_position:    vector  = vector( parent_position.x + self._position.x, parent_position.y + self._position.y )

        
        self._input_path.position( vector( self._position.x + back_button, self._position.y ) )
        self._input_path.size( vector( self._size.x - back_button - pad * 2, self._input_path.size( ).y ) )
    

    def __animate( self ):
        """
        Updates and performs animations for the path selector.

        Receives: None

        Returns: None
        """

        self._animations.update( )

        speed: int = self._config.speed

        fade: float = self._animations.perform( "Fade", self._is_visible and 1 or 0, speed )
        if fade == 0:
            return

        self._animations.perform( "Back", self._is_hovered_back and 1 or 0.3, speed )
        self._animations.perform( "Scroll", self._offset, speed, 1 )


    def __draw_back( self, fade: float ):
        """
        Draws the background of the path selector.

        Receives:
        - fade (float): The fade factor inherited from the parent.

        Returns: None
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
            back_color.alpha_override( 255 ),
            fade,
            20,
            roundness
        )


    def __draw_top_bar( self, fade: float ):
        """
        Draws the top bar of the path selector, including the back button, separator, and the path input field.

        Receives:
        - fade (float): The fade factor inherited from the parent.

        Returns: None
        """
        
        pad:                int     = self._config.pad
        seperate:           int     = self._config.separate
        seperate_color:     color   = self._config.separate_color
        back_icon_size:     vector  = self._back_icon.size( )
        path_size:          vector  = self._input_path.fixed_size( )
        seperate_position:  vector  = vector( self._position.x + pad * 2 + back_icon_size.x, self._position.y + pad )

        hover_back:         float   = self._animations.value( "Back" ) * fade

        self._render.image( self._back_icon, self._position + vector( pad, pad ), color( ) * hover_back )

        self._render.neon( seperate_position, seperate_position + vector( seperate, path_size.y - pad * 2 ), seperate_color * fade, 18, seperate / 2 )

        self._input_path.draw( fade )

    
    def __draw_content( self, fade: float ):
        """
        Draws the list of folders and files within the currently active folder.

        Receives:
        - fade (float): The fade factor inherited from the parent.

        Returns: None
        """

        speed:          int     = self._config.speed
        pad:            int     = self._config.pad
        seperate:       int     = self._config.separate
        seperate_color: color   = self._config.separate_color
        
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
            
            show            = self._animations.perform( f"Folder_{ name }_show",        info[ "is_hovered" ] and 1 or 0.5, speed / 3 ) * fade
            show_seperate   = self._animations.perform( f"Folder_{ name }_seperate",    info[ "is_hovered" ] and 1 or 0, speed ) * fade
            hover_add       = self._animations.perform( f"Folder_{ name }_hover_add",   info[ "is_hovered" ] and pad * 2 + seperate or 0, speed, 1 )

            icon_position = vector( start_position.x + pad, start_position.y + drop )
            text_position = vector( start_position.x + icon_size.x + pad * 2 + hover_add, start_position.y + drop + ( icon_size.y - name_size.y ) / 2 )
            seperate_position = vector( start_position.x + icon_size.x + pad * 2, start_position.y + drop )

            self._render.image( self._folder_icon, icon_position, color( ) * show )

            self._render.neon( seperate_position, seperate_position + vector( seperate, icon_size.y * show_seperate ), seperate_color * show_seperate, 18, seperate / 2 )

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
        Draws the vertical scrollbar for the content area, if necessary.

        Receives:
        - fade (float): The fade factor inherited from the parent.

        Returns: None
        """

        seperate:       int     = self._config.separate
        seperate_color: color   = self._config.separate_color
        
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

        self._render.neon( position, end_position, seperate_color * fade, 18, seperate / 2 )

    # endregion

    # region : Input

    def __event_mouse_position( self, event ) -> None:
        """
        Handles mouse position change events for the path selector.

        Receives:
        - event (callable): Event information containing mouse coordinates.

        Returns: None
        """

        if not self._is_visible:
            return

        self._mouse_position.x  = event( "x" )
        self._mouse_position.y  = event( "y" )

        self._is_hovered = self._mouse_position.is_in_bounds( self._relative_position, self._size.x, self._size.y )

        self.__hover_back_button( )
        if self._is_hovered_back:
            return

        self.__hover_folders( )


    def __event_mouse_input( self, event ) -> None:
        """
        Handles mouse button input events for the path selector.

        Receives:
        - event (callable): Event information containing button and action.

        Returns: None
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
        Handles mouse scroll input events for the path selector's content area.

        If the mouse is hovering over the path selector and the content overflows the visible area,
        it updates the vertical scroll offset based on the scroll direction.

        Receives:
        - event (callable): Event information containing the vertical scroll offset.

        Returns: None
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
        
        pass    # Like actually todo


    def __event_keyboard_input( self, event ) -> None:
        
        pass


    def __hover_back_button( self ):
        """
        Checks if the mouse cursor is currently hovering over the back button area.

        Updates the `_is_hovered_back` flag accordingly.

        Receives: None

        Returns: None
        """
        position = self._relative_position + vector( self._config.pad, self._config.pad )
        size = self._back_icon.size( )

        self._is_hovered_back = self._mouse_position.is_in_bounds( position, size.x, size.y )


    def __handle_back_button( self ) -> bool:
        """
        Handles the action when the back button is clicked.

        If the back button is hovered and there is a previous folder, it clears the current folder's content and animations,
        moves to the previous folder, re-scans its content, prepares new animations, and updates the displayed path.

        Receives: None

        Returns:
        - bool: True if the back button action was handled, False otherwise.
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
        Checks if the mouse cursor is currently hovering over any of the displayed folders or files.

        It iterates through the `_files_information` dictionary, which stores the position and size of each item,
        and updates the "is_hovered" status accordingly.

        Receives: None

        Returns: None
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
        Handles the action when a folder within the content area is clicked.

        It checks if the click occurred within the visible content area. If so, it iterates through the displayed folders
        and, if a hovered folder is found, it clears the current folder's content and animations, sets the clicked folder
        as the new active folder, scans its content, prepares new animations, and updates the displayed path.

        Receives: None

        Returns: None
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
        Parses a given path string, creates a chain of `c_base_folder` objects representing the directory structure,
        and sets the last folder in the chain as the active folder.

        Receives:
        - path (str): The absolute or relative path to parse.

        Returns:
        - c_base_folder: The last folder in the created chain, representing the target directory.
        """

        data:           list    = path.split( os.sep )
        folders_count:  int     = len( data )

        for i, folder in enumerate( data ):
            if not folder:
                continue

            is_drive_letter = ( len( folder ) == 2 and folder.endswith( ":" ) )

            if i == 0 and is_drive_letter:
                folder = f"{folder}{os.sep}"

            self._active_folder = c_base_folder( self._active_folder, folder )

        self._active_folder.dump( )
        self.__prepare_animations( )
        self._input_path.value( self._active_folder.absolute_path( ) )

        return self._active_folder
    

    def __set_new_folder( self, new_folder: c_base_folder ):
        """
        Sets a new active folder, updates the path input field, and resets the scroll offset.

        Receives:
        - new_folder (c_base_folder): The new folder to set as active.

        Returns: None
        """

        self._input_path.value( new_folder.absolute_path( ) )
        self._active_folder = new_folder

        self._offset = 0

    
    def __prepare_animations( self ):
        """
        Prepares animation values for each folder within the currently active folder.

        For each folder, it creates animation tracks for its appearance ("_show"), a separator line ("_seperate"),
        and a hover effect ("_hover").

        Receives: None

        Returns: None
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
        Accesses or updates the position of the path selector.

        Receives:
        - new_value (vector, optional): The new position (x, y). If None, returns the current position. Defaults to None.

        Returns:
        - vector: The current position.
        """

        if new_value is None:
            return self._position
        
        self._position.x = new_value.x
        self._position.y = new_value.y

        return new_value


    def size( self, new_value: vector = None ) -> vector:
        """
        Accesses or updates the size of the path selector.

        Receives:
        - new_value (vector, optional): The new size (width, height). If None, returns the current size. Defaults to None.

        Returns:
        - vector: The current size.
        """

        if new_value is None:
            return self._size
        
        self._size.x = new_value.x
        self._size.y = new_value.y

        return new_value
    

    def visible( self, new_value: bool = None ) -> bool:
        """
        Access or update the visibility state of a text input.

        Receives:
        - new_value (bool, optional): The new visibility value to set. 
                                      If None, the current visibility state is returned. Defaults to None.

        Returns:
        - bool: The current visibility.
        """

        if new_value is None:
            return self._is_visible
        
        self._is_visible = new_value

        return new_value

    
    def get_path( self ) -> str:
        """
        Get the absolute path of the selected folder.

        Receives: None

        Returns:
        - str: The absolute path of the active folder as a string.
        """
        
        return self._active_folder.absolute_path( )

    # endregion