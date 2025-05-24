"""
    project     : Digital Editor

    type:       : Host
    file        : Graphical icon_users Interface

    description : Host GUI class
"""

from host.business_logic        import *
from user_interface.application import *
from utilities.paths            import *
from utilities.debug            import *

import queue

LOADING_MIN_TIME = 1

DEFAULT_ICON_SIZE: vector = vector( 30, 30 )

class c_host_gui:
    
    # region : Privates attributes

    _application:               c_application
    _logic:                     c_host_business_logic

    _scene_loadup:              c_scene
    _scene_setup:               c_scene
    _scene_project:             c_scene

    _application_config:        application_config_t
    _scene_loadup_config:       scene_config_t
    _scene_setup_config:        scene_config_t
    _scene_project_config:      scene_config_t

    _temp:                      dict

    _entry_username:            c_text_input
    _entry_password:            c_text_input
    _entry_ip:                  c_text_input
    _entry_port:                c_text_input
    _path_select:               c_path_select
    _list_access_level:         c_side_list
    _list_original_scan_option: c_side_list
    _list_virtual_scan_option:  c_side_list
    _max_clients:               c_slider_int
    _button_prev_setup:         c_button
    _button_next_setup:         c_button

    _editor:                    c_editor
    _button_menu:               c_icon_button
    _button_files:              c_icon_button
    _button_admin:              c_icon_button

    _button_close:              c_icon_button
    _button_share:              c_button
    _button_users:              c_button
    _button_logs:               c_button

    _solution_explorer:         c_solution_explorer
    _button_dump_path:          c_button
    _button_add_file:           c_button

    _opened_what:               int

    _general_font:              c_font

    _logs:                      queue.Queue

    # endregion

    # region : Initialization

    def __init__( self, should_debug: bool = False ):
        """
        Default constructor for the host GUI class.

        Receive: 
        - should_debug (bool, optional): Should enable debug logging

        Returns: 
        - c_host_gui: Host Application object
        """

        if should_debug:
            c_debug.load_basic_debugging( "host_debug.log" )

        self._temp          = { }
        self._opened_what   = 0
        self._logs          = queue.Queue( )

        self.__initialize_application( )
        self.__initialize_logic( )


    def __initialize_application( self ):
        """
        Initialize the application object.

        Receive: None

        Returns: None
        """

        self._application_config = application_config_t( )

        self._application = c_application( self._application_config )

        self._application.initialize_window( "digital-editor host", vector( 50, 50 ), vector( 1300, 850 ), True )

        self.__initialize_resources( )

        self._application.initialize_events()

        self.__scene_loadup_initialize( )
        self.__scene_setup_initialize( )
        self.__scene_project_initialize( )

        self._application.set_event( "unload", self.__event_close_application, "Close Application", False )


    def __initialize_logic( self ):
        """
        Initialize the logic object.

        Receive: None

        Returns: None
        """

        self._logic = c_host_business_logic( )

        self.__initialize_logic_events( )


    def __initialize_logic_events( self ):
        """
        Initialize the logic's events callbacks.

        Receive:   None

        Returns:   None
        """

        self._logic.set_event( "on_files_refresh",  self.__event_update_files_list, "gui_update_files_list",    True )
        self._logic.set_event( "on_file_set",       self.__event_clear_editor,      "gui_clear_editor",         True )
        self._logic.set_event( "on_file_update",    self.__event_add_editor_line,   "gui_update_editor",        True )
        self._logic.set_event( "on_accept_line",    self.__event_accept_line,       "gui_editor_accept_line",   True )
        self._logic.set_event( "on_line_lock",      self.__event_lock_line,         "gui_editor_line_lock",     True )
        self._logic.set_event( "on_line_unlock",    self.__event_unlock_line,       "gui_editor_line_unlock",   True )
        self._logic.set_event( "on_line_update",    self.__event_change_lines,      "gui_editor_line_update",   True )
        self._logic.set_event( "on_line_delete",    self.__event_remove_line,       "gui_editor_line_remove",   True )
        self._logic.set_event( "on_added_log",      self.__event_add_log,           "gui_add_log",              True )

    
    def __initialize_resources( self ):
        """
        Initialize the resources for the application.

        Receive: None

        Returns: None
        """

        execution_directory = os.getcwd( )

        self._general_font = self._application.create_font( "general", FONT, 20 )

        self._application.create_image( "wallpaper_blurred",    execution_directory + PHOTO_WALLPAPER,      vector( 5784, 3254 ), [ IMAGE_FILTER_BLUR ] )
        self._application.create_image( "wallpaper",            execution_directory + PHOTO_WALLPAPER,      vector( 5784, 3254 ) )

        self._application.create_image( "icon_username",        execution_directory + ICON_USERNAME,        DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_password",        execution_directory + ICON_PASSWORD,        DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_next",            execution_directory + ICON_NEXT,            DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_previous",        execution_directory + ICON_PREV,            DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_folder",          execution_directory + ICON_FOLDER,          DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_file",            execution_directory + ICON_FILE,            DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_listen",          execution_directory + ICON_LISTEN,          DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_port",            execution_directory + ICON_PORT,            DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_share",           execution_directory + ICON_SHARE,           DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_users",           execution_directory + ICON_USERS,           DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_info",            execution_directory + ICON_INFO,            DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_copy",            execution_directory + ICON_COPY,            DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_lock",            execution_directory + ICON_LOCKED,          DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_visible",         execution_directory + ICON_VISIBLE,         DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_tune",            execution_directory + ICON_TUNE,            DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_check",           execution_directory + ICON_CHECK,           DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_addfile",         execution_directory + ICON_ADD_FILE,        DEFAULT_ICON_SIZE )
        self._application.create_image( "icon_refresh",         execution_directory + ICON_REFRESH,         DEFAULT_ICON_SIZE )

        self._application.create_image( "title_welcome",        execution_directory + TITLE_ICON_WELCOME,      vector( 700, 200 ) )
        self._application.create_image( "title_files",          execution_directory + TITLE_ICON_FILES,        vector( 500, 170 ) )
        self._application.create_image( "title_configure",      execution_directory + TITLE_ICON_CONFIGURE,    vector( 500, 170 ) )
        self._application.create_image( "title_connection",     execution_directory + TITLE_ICON_CONNECTION,   vector( 500, 170 ) )
        self._application.create_image( "title_loading",        execution_directory + TITLE_ICON_LOADING,      vector( 500, 170 ) )
        
        self._temp[ "setup_process" ] = 0
        
        self._application_config.wallpaper = self._application.image( "wallpaper_blurred" )

        window_icon = c_image( ).load_glfw( execution_directory + "\\resources\\window_icon.png" )
        self._application.set_window_icon( window_icon )
        
    # endregion

    # region : Scene Loadup

    def __scene_loadup_initialize( self ):
        """
        Initialize the Loadup Scene.

        Receive: None

        Returns: None
        """

        self._scene_loadup_config = scene_config_t( )
        self._scene_loadup_config.animate_movement = True

        self._scene_loadup = self._application.new_scene( self._scene_loadup_config )

        self._scene_loadup.set_event( "draw",           self.__scene_loadup_draw,    "gui_scene_loadup_draw_main", False )
        self._scene_loadup.set_event( "mouse_input",    self.__scene_loadup_update,     "gui_scene_loadup_update" )
        self._scene_loadup.set_event( "keyboard_input", self.__scene_loadup_update,     "gui_scene_loadup_update" )

    
    def __scene_loadup_draw( self ):
        """
        Main draw function for Loadup Scene.

        Receive: None

        Returns: None
        """

        img:            c_image         = self._application.image( "title_welcome" )
        img_size:       vector          = img.size( )

        fade:           float           = self._scene_loadup.animations( ).value( "Fade" )

        screen:         vector          = self._application.window_size( )
        image_pos:      vector          = ( screen - img_size ) / 2

        self._application.render( ).image( img, image_pos, color( ) * fade )


    def __scene_loadup_update( self, event ):
        """
        Update the Loadup Scene on any press.

        Receive: 
        - event (callable): Event information

        Returns: None
        """

        if event( "action" ) == glfw.PRESS:
            self._application.active_scene( self._scene_setup.index( ) )

    # endregion

    # region : Scene Setup

    def __scene_setup_initialize( self ):
        """
        Initialize the Setup Scene.

        Receive: None

        Returns: None
        """

        self._scene_setup_config = scene_config_t( )

        self._scene_setup_config.animate_movement   = True
        self._scene_setup_config.enable_stars       = True

        self._scene_setup = self._application.new_scene( self._scene_setup_config )

        self.__scene_setup_initialize_elements( )

        animations: c_animations = self._scene_setup.animations()
        animations.prepare( "title_files",          vector( ) )
        animations.prepare( "title_configure",      vector( ) )
        animations.prepare( "title_connection",     vector( ) )
        animations.prepare( "title_loading",        vector( ) )
        
        animations.prepare( "button_height",        250 )
        animations.prepare( "instructions_heights1", vector( ) )
        animations.prepare( "instructions_heights2", 0 )

        self._scene_setup.set_event( "draw",            self.__scene_setup_draw,               "gui_scene_setup_draw_main",         False )
        self._scene_setup.set_event( "draw",            self.__scene_setup_draw_instructions,  "gui_scene_setup_draw_instructions", False )
        self._scene_setup.set_event( "draw",            self.__scene_setup_adjust_elements,    "gui_scene_setup_adjust_elements",   False )
        self._scene_setup.set_event( "keyboard_input",  self.__scene_setup_control_steps,      "gui_scene_setup_control_elements",  False )

    
    def __scene_setup_initialize_elements( self ):
        """
        Setup the elements for the Setup Scene.

        Receive: None

        Returns: None
        """

        path_icons:     dict = {
            "back_icon":    self._application.image( "icon_previous" ), 
            "folder_icon":  self._application.image( "icon_folder" ), 
            "file_icon":    self._application.image( "icon_file" )
        }
        
        username_icon:  c_image = self._application.image( "icon_username" )
        password_icon:  c_image = self._application.image( "icon_password" )
        next_icon:      c_image = self._application.image( "icon_next" )
        prev_icon:      c_image = self._application.image( "icon_previous" )

        ip_icon:        c_image = self._application.image( "icon_listen" )
        port_icon:      c_image = self._application.image( "icon_port" )

        text_input_config = text_input_config_t( )
        text_input_config.color_background.a = 0
        text_input_config.color_shadow = color( 29, 29, 29, 0 )

        buttons_config = button_config_t( )
        buttons_config.back_color = color( 29, 29, 29 )

        path_config = path_select_config_t( )
        path_config.back_color = color( 29, 29, 29, 0 )

        list_config = list_config_t( )
        list_config.back_color = color( 29, 29, 29, 0 )

        # First the path select
        self._path_select       = c_path_select( self._scene_setup, self._general_font, vector( 50, 120 ), vector( 500, 560 ), path_icons, path_config )

        # Second we need the settings
        #self._list_scan_options = c_side_list( self._scene_setup, vector( 50, 750 ), 500, self._general_font, list_config )
        self._list_access_level         = c_side_list( self._scene_setup, vector( 50, 50 ), 500, self._general_font, list_config )

        self._list_original_scan_option = c_side_list( self._scene_setup, vector( 50, 50 ), 500, self._general_font, list_config )
        self._list_virtual_scan_option  = c_side_list( self._scene_setup, vector( 50, 50 ), 500, self._general_font, list_config )
        self._max_clients               = c_slider_int( self._scene_setup, vector( 50, 50 ), 300, self._general_font, 0, 20, 10 )

        # Third the connection details
        self._entry_ip          = c_text_input( self._scene_setup, vector( 50, 120 ), 40, vector( 200, 30 ), self._general_font, ip_icon, "ip", "0.0.0.0", False, text_input_config )
        self._entry_port        = c_text_input( self._scene_setup, vector( 50, 180 ), 40, vector( 200, 30 ), self._general_font, port_icon, "port", "9978", False, text_input_config )

        self._entry_username    = c_text_input( self._scene_setup, vector( 50, 120 ), 40, vector( 200, 30 ), self._general_font, username_icon, "username", "", False, text_input_config )
        self._entry_password    = c_text_input( self._scene_setup, vector( 50, 180 ), 40, vector( 200, 30 ), self._general_font, password_icon, "password", "", True, text_input_config )

        # Buttons to navigate
        self._button_prev_setup = c_button( self._scene_setup, vector( 50, 250 ), 40, self._general_font, prev_icon,   "Previous", self.__scene_setup_previous_step, buttons_config )
        self._button_next_setup = c_button( self._scene_setup, vector( 100, 250 ), 40, self._general_font, next_icon,  "Next",     self.__scene_setup_next_step, buttons_config )

        # Update the items visiblity
        self.__scene_setup_update( )

        # Configure the default path selection
        self._path_select.parse_path( os.getcwd( ) )

        # Configure access level list
        self._list_access_level.add_item( "Hidden", self._application.image( "icon_lock" ),      None )
        self._list_access_level.add_item( "Limit",  self._application.image( "icon_visible" ),   None )
        self._list_access_level.add_item( "Edit",   self._application.image( "icon_tune" ),      None )

        self._list_access_level.set_value( "Hidden" )

        #self._list_scan_options.set_value( "Both" )
        self._list_original_scan_option.add_item( "Disable",    None )
        self._list_original_scan_option.add_item( "Create",     None )
        self._list_original_scan_option.add_item( "Overwrite",  None )

        self._list_virtual_scan_option.add_item( "Disable",    None )
        self._list_virtual_scan_option.add_item( "Include",    None )

        self._list_original_scan_option.set_value( "Create" )
        self._list_virtual_scan_option.set_value( "Include" )
        

    def __scene_setup_draw( self ):
        """
        Main draw function for Setup Scene.

        Receive: None

        Returns: None
        """

        wallpaper:  c_image         = self._application.image( "wallpaper" )
        screen:     vector          = self._application.window_size( )

        box_size    = screen * 0.8
        start_box   = screen * 0.1
        end_box     = start_box + box_size

        render:     c_renderer      = self._application.render( )
        animations: c_animations    = self._scene_setup.animations( )

        fade:       float           = animations.value( "Fade" )
        speed:      int             = self._scene_setup_config.speed

        render.shadow( start_box, end_box, color( 207, 210, 215 ), fade, 18, 10 )
        render.shadow( start_box, end_box, color( 0, 0, 0 ), fade, 10, 10 )

        # Render the Image
        render.push_clip_rect( vector( ), vector( screen.x / 2, screen.y ), True )
        render.image( wallpaper, start_box, color( ) * fade, box_size, 10 )
        render.pop_clip_rect( )

        # Render the background
        render.push_clip_rect( vector( screen.x / 2, 0 ), screen, True )
        render.rect( start_box, end_box, color( 29, 29, 29, 200 ) * fade, 10 )
        render.pop_clip_rect( )

        steps = {
            0: "title_files",
            1: "title_configure",
            2: "title_connection",
            3: "title_loading"
        }

        selected: int = self._temp[ "setup_process" ]
        
        for index in steps:
            step: str = steps[ index ]

            image:      c_image = self._application.image( step )
            alpha_step: float   = ( selected == index and 1 or 0 ) * fade
                
            wanted_value:   vector  = vector( ( 1 - alpha_step ) * 50, alpha_step )
            values:         vector  = animations.perform( step, wanted_value, speed )

            image_size: vector = image.size( )
            render.image( image, vector( screen.x * 0.3 - image_size.x / 2 - values.x, start_box.y + 10 ), color( ) * values.y )

    
    def __scene_setup_draw_instructions( self ):
        """
        Draw instructions for the user in the setup scene.

        Receive: None

        Returns: None
        """

        screen:     vector          = self._application.window_size( )

        start_x = screen.x * 0.5 + 20
        start_y = screen.y * 0.1 + 20

        render:     c_renderer      = self._application.render( )
        animations: c_animations    = self._scene_setup.animations( )

        fade:       float           = animations.value( "Fade" ) * animations.value( "title_configure" ).y

        allowed_wraped_width = screen.x * 0.4 - 40

        first_wrapped_text:     str = render.wrap_text( self._general_font, "Select the default access level for new users",        allowed_wraped_width )
        second_wrapped_text:    str = render.wrap_text( self._general_font, "Select scan mode for original project files",          allowed_wraped_width )
        third_wrapped_text:     str = render.wrap_text( self._general_font, "Select scan mode for scanned project files",           allowed_wraped_width )
        forth_wrapped_text:     str = render.wrap_text( self._general_font, "Select max clients amount that can join this session", allowed_wraped_width )

        first_size:     vector = render.measure_text( self._general_font, first_wrapped_text )
        second_size:    vector = render.measure_text( self._general_font, second_wrapped_text )
        third_size:     vector = render.measure_text( self._general_font, third_wrapped_text )
        forth_size:     vector = render.measure_text( self._general_font, forth_wrapped_text )

        position = vector( start_x, start_y )

        render.text( self._general_font, position, color( ) * fade, first_wrapped_text )
        position.y += 80 + first_size.y

        render.text( self._general_font, position, color( ) * fade, second_wrapped_text )
        position.y += 80 + second_size.y

        render.text( self._general_font, position, color( ) * fade, third_wrapped_text )
        position.y += 80 + third_size.y

        render.text( self._general_font, position, color( ) * fade, forth_wrapped_text )

        # We use animations handle since I dont want to add millions of data just for this class...
        animations.value( "instructions_heights1", vector( first_size.y + 20, second_size.y + 20, third_size.y + 20 ) )
        animations.value( "instructions_heights2", forth_size.y )


    def __scene_setup_adjust_elements( self ):
        """
        Adjust the scene elements positions.

        Receive: None

        Returns: None
        """

        animations: c_animations    = self._scene_setup.animations( )
        screen:     vector          = self._application.window_size( )

        speed:      int             = self._scene_setup_config.speed

        instructions_heights1: vector = animations.value( "instructions_heights1" )
        
        button_next_drop: float = animations.perform( "button_height", screen.y * 0.9 - 20 - 40, speed )
        
        start_buttons_x = screen.x * 0.5 + 20
        start_widgets_y = screen.y * 0.1 + 20

        self._button_prev_setup.position( vector( start_buttons_x, button_next_drop ) )
        self._button_next_setup.position( vector( screen.x * 0.9 - 20 - self._button_next_setup.size( ).x, button_next_drop ) )

        self._entry_ip.position( vector( start_buttons_x, start_widgets_y ) )
        self._entry_port.position( vector( start_buttons_x, start_widgets_y + 60 ) )

        self._entry_username.position( vector( start_buttons_x, start_widgets_y + 140 ) )
        self._entry_password.position( vector( start_buttons_x, start_widgets_y + 200 ) )

        self._path_select.position( vector( start_buttons_x, start_widgets_y ) )
        self._path_select.size( vector( screen.x * 0.4 - 40, button_next_drop - self._path_select.position( ).y - 10 ) )

        start_widgets_y += instructions_heights1.x
        width = self._path_select.size( ).x

        self._list_access_level.position( vector( start_buttons_x, start_widgets_y ) )
        self._list_access_level.width( width )

        start_widgets_y += instructions_heights1.y + 60

        self._list_original_scan_option.position( vector( start_buttons_x, start_widgets_y ) )
        self._list_original_scan_option.width( width )

        start_widgets_y += instructions_heights1.z + 60

        self._list_virtual_scan_option.position( vector( start_buttons_x, start_widgets_y ) )
        self._list_virtual_scan_option.width( width )

        start_widgets_y += animations.value( "instructions_heights2" ) + 60

        self._max_clients.position( vector( start_buttons_x, start_widgets_y ) )
        self._max_clients.width( width )

    
    def __scene_setup_control_steps( self ):
        """
        Control each step of the setup progress.

        Receive: None

        Returns: None
        """

        progress_index: int = self._temp[ "setup_process" ]
        if progress_index == 2:
            # Registration

            is_username_valid, reason = c_registration.validate_username( self._entry_username.get( ) )
            is_password_valid, reason = c_registration.validate_password( self._entry_password.get( ) )

            # I want to avoid updating each frame...
            new_value: bool = is_username_valid and is_password_valid
            if self._button_next_setup.visible( ) != new_value:
                self._button_next_setup.visible( new_value )
    

    def __scene_setup_next_step( self ):
        """
        Next setup step.

        Receive:   None

        Returns:   None
        """

        self._temp[ "setup_process" ] = math.clamp( self._temp[ "setup_process" ] + 1, 0, 3 ) 

        self.__scene_setup_update( )

        if self._temp[ "setup_process" ] == 3:
            return self.__project_start( )
    

    def __scene_setup_previous_step( self ):
        """
        Previous setup step.

        Receive:   None

        Returns:   None
        """

        self._temp[ "setup_process" ] = math.clamp( self._temp[ "setup_process" ] - 1, 0, 3 ) 

        self.__scene_setup_update( )

    
    @safe_call( c_debug.log_error )
    def __scene_setup_update( self ):
        """
        Update setup scene elements visibility.

        Receive: None

        Returns: None
        """

        process_index = self._temp[ "setup_process" ]

        changes = {
            0: [ True, False, False ],
            1: [ False, True, False ],
            2: [ False, False, True ],
            3: [ False, False, False ]
        }

        if process_index not in changes:
            return
        
        current_changes = changes[ process_index ]

        self._path_select.visible( current_changes[ 0 ] )

        self._list_access_level.visible( current_changes[ 1 ] )
        self._list_original_scan_option.visible( current_changes[ 1 ] )
        self._list_virtual_scan_option.visible( current_changes[ 1 ] )
        self._max_clients.visible( current_changes[ 1 ] )

        self._entry_ip.visible( current_changes[ 2 ] )
        self._entry_port.visible( current_changes[ 2 ] )

        self._entry_username.visible( current_changes[ 2 ] )
        self._entry_password.visible( current_changes[ 2 ] )

        self._button_prev_setup.visible( not current_changes[ 0 ] and process_index != 3 )
        self._button_next_setup.visible( process_index != 3 and process_index != 2 )
        
    # endregion

    # region : Scene Project

    @standalone_execute
    def __project_start( self ):
        """
        Start the hosting program.

        Receive: None

        Returns: None
        """

        time.sleep( LOADING_MIN_TIME )

        success, error = self.__project_load_platform( )
        if not success:
            return self.__project_fast_close( error )

        self.__project_load_base( )
        
        success, error = self.__project_connect( )
        if not success:
            return self.__project_fast_close( error )
        
        self._logic.complete_setup_files( )

        self._logic.start( )

        time.sleep( LOADING_MIN_TIME )

        self._application.active_scene( self._scene_project.index( ) )

        self._application.maximize_window( )

    
    def __project_fast_close( self, error: str ):
        """
        Operation to fast close the host operations.

        Receive:
        - error (str): Reason to stop operations

        Returns: None
        """

        self._temp[ "setup_process" ] = 2
        self.__scene_setup_update( )

        # Show window
        self.__show_error_message( error, self._scene_setup )


    def __project_load_platform( self ) -> tuple:
        """
        Load platform for the host operations by setup business logic.

        Receive: None

        Returns:
        - tuple: Result of the setup and error log on fail
        """

        @safe_call( None )
        def get_connections_values( ) -> tuple:
            
            ip_value:   str = self._entry_ip.get( )
            port_value: int = int( self._entry_port.get( ) )

            return ( ip_value, port_value )
        
        values = get_connections_values( )
        if not values:
            return False, f"Failed to cast port value { self._entry_port.get( ) }"

        username_value:     str = self._entry_username.get( )
        max_clients_value:  int = self._max_clients.get( )

        self._logic.setup( values[ 0 ], values[ 1 ], username_value, max_clients_value )

        return self._logic( "success" ), self._logic( "last_error" )
    

    def __project_load_base( self ) -> None:
        """
        Load and initialize default values for the logic.

        Receive: None

        Returns: None
        """

        different_access_levels = {
            "Hidden":   FILE_ACCESS_LEVEL_HIDDEN,
            "Edit":     FILE_ACCESS_LEVEL_EDIT,
            "Limit":    FILE_ACCESS_LEVEL_LIMIT
        }

        scan_type_original_files = {
            "Disable":      ENUM_SCAN_DISABLE,
            "Create":       ENUM_SCAN_CREATE_NEW,
            "Overwrite":    ENUM_SCAN_OVERWRITE
        }
        
        path_value:     str     = self._path_select.get_path( )
        access_value:   int     = different_access_levels[ self._list_access_level.get( ) ]
        scan_value:     int     = scan_type_original_files[ self._list_original_scan_option.get( ) ]
        scan_virtuals:  bool    = self._list_virtual_scan_option.get( ) == "Include"

        self._logic.initialize_base_values( path_value, access_value, scan_value, scan_virtuals )

    
    def __project_connect( self ) -> tuple:
        """
        Connect to the database of the host.

        Receive: None

        Returns:
        - tuple: Result and error log on fail
        """

        password: str = self._entry_password.get( )

        result: bool = self._logic.connect_to_database( password )
        
        return result, self._logic( "last_error" )
         

    def __scene_project_initialize( self ):
        """
        Initialize the Project Scene.

        Receive: None

        Returns: None
        """

        self._scene_project_config = scene_config_t( )
        self._scene_project_config.enable_stars = False

        self._scene_project = self._application.new_scene( self._scene_project_config )

        self.__scene_project_initialize_elements( )

        animations: c_animations = self._scene_project.animations( )
        animations.prepare( "OpenMenu", 0 )

        self._scene_project.set_event( "draw", self.__scene_project_animate_tabs, "Scene Project Animate Tabs", False )
        self._scene_project.set_event( "draw", self.__scene_project_adjust_elements, "Scene Project Adjust Elements", False )

    
    def __scene_project_initialize_elements( self ):
        """
        Setup the elements for the Project Scene.

        Receive: None

        Returns: None
        """

        file_icon:      c_image = self._application.image( "icon_folder" )
        admin_icon:     c_image = self._application.image( "icon_users" )
        close_icon:     c_image = self._application.image( "icon_previous" )

        share_icon:     c_image = self._application.image( "icon_share" )
        user_icon:      c_image = self._application.image( "icon_users" )
        info_icon:      c_image = self._application.image( "icon_info" )
        add_file_icon:  c_image = self._application.image( "icon_addfile" )
        refresh_icon:   c_image = self._application.image( "icon_refresh" )

        solution_config = solution_explorer_config_t( )
        solution_config.folder_icon = self._application.image( "icon_folder" )
        solution_config.item_icon   = self._application.image( "icon_file" )

        top_bar_config = list_config_t( )
        top_bar_config.disable_pressed = True

        self._editor            = c_editor( self._scene_project, vector( 50, 140 ), vector( 1000, 760 ), self._general_font )
        self._buttons_bar       = c_side_list( self._scene_project, vector( 50, 50 ), 400, self._general_font, top_bar_config )
        self._solution_explorer = c_solution_explorer( self._scene_project, vector( 50, 140 ), vector( 250, 500 ), self._general_font, solution_config )
        self._button_dump_path  = c_button( self._scene_project, vector( 50, 660 ), 40, self._general_font, refresh_icon, "Refresh path", self.__callback_on_press_refresh_path )
        self._button_add_file   = c_button( self._scene_project, vector( 50, 720 ), 40, self._general_font, add_file_icon, "Add file", self.__callback_on_press_new_file )

        self._button_share  = c_button( self._scene_project, vector( 50, 140 ), 40, self._general_font, share_icon, "Share", self.__callback_on_press_share )
        self._button_users  = c_button( self._scene_project, vector( 50, 200 ), 40, self._general_font, user_icon, "Users", self.__callback_on_press_users )
        self._button_logs   = c_button( self._scene_project, vector( 50, 260 ), 40, self._general_font, info_icon, "Logs", self.__callback_on_press_logs )

        # Utilities
        self._editor.open_file( "Welcome" )
        welcome_messages = [ "Welcome to the Digital Editor.", "", "Current version : 1.0 preview.", "Please select a file to start editing."]
        for msg in welcome_messages:
            self._editor.add_line( msg )

        self._editor.read_only( True )

        self._buttons_bar.add_item( "Files", file_icon,  self.__callback_on_press_files )
        self._buttons_bar.add_item( "Admin", admin_icon, self.__callback_on_press_admin )
        self._buttons_bar.add_item( "Exit",  close_icon, self.__callback_on_press_close )
        
        self._editor.set_event( "request_line", self.__event_editor_request_line,   "gui_editor_request_line" )
        self._editor.set_event( "discard_line", self.__event_discard_line,          "gui_editor_discard_line" ) 
        self._editor.set_event( "update_line",  self.__event_update_line,           "gui_editor_update_line" ) 
        self._editor.set_event( "delete_line",  self.__event_delete_line,           "gui_editor_delete_line" )
        
        self.__update_sidebar_elements( )
    

    def __scene_project_animate_tabs( self ):
        """
        Main draw function for Project Scene.

        Receive: None

        Returns: None
        """

        animations: c_animations    = self._scene_project.animations( )
        speed:     int              = self._scene_project_config.speed

        animations.perform( "OpenMenu", self._opened_what != 0 and 300 or 0, speed, 1 )

    
    def __scene_project_adjust_elements( self ):
        """
            Adjust the scene elements positions.

            Receive: None

            Returns: None
        """

        screen:     vector          = self._application.window_size( )
        animations: c_animations    = self._scene_project.animations( )

        opened_tab = animations.value( "OpenMenu" )

        self._editor.position( vector( 50 + opened_tab, 140 ) )
        self._editor.size( vector( screen.x - 100 - opened_tab, screen.y - 190 ) )

    # endregion

    # region : Callbacks
    
    def __callback_on_press_files( self, _ ):
        """
        Callback for the files button.

        Receive: None

        Returns: None
        """

        if self._opened_what == 1:
            self._opened_what = 0
        else:
            self._opened_what = 1

        self.__update_sidebar_elements( )

    
    def __callback_on_press_admin( self, _ ):
        """
        Callback for the admin button.

        Receive: None

        Returns: None
        """

        if self._opened_what == 2:
            self._opened_what = 0
        else:
            self._opened_what = 2

        self.__update_sidebar_elements( )

    
    def __update_sidebar_elements( self ):
        """
        Update the sidebar elements.

        Receive: None

        Returns: None
        """

        elements_visible = {
            0: [ False, False ],
            1: [ True, False ],
            2: [ False, True ]
        }

        current = elements_visible[ self._opened_what ]

        self._solution_explorer.visible(    current[ 0 ] )
        self._button_dump_path.visible(     current[ 0 ] )
        self._button_add_file.visible(      current[ 0 ] )
        
        self._button_share.visible(         current[ 1 ] )
        self._button_users.visible(         current[ 1 ] )
        self._button_logs.visible(          current[ 1 ] )
    

    def __callback_on_press_close( self, _ ):
        """
        Callback for the close button.

        Receive: None

        Returns: None
        """

        self._editor.discard_action( )
        self._editor.clear( )

        self._logic.terminate( )

        self._button_next_setup.visible( True )
        self._button_prev_setup.visible( True )
        self._application.active_scene( self._scene_setup.index( ) )

        self._temp[ "setup_process" ] = 0
        self.__scene_setup_update( )
        
        self._solution_explorer.clear( )


    def __callback_on_press_share( self ):
        """
        Callback for the share button.

        Receive: None

        Returns: None
        """

        window_config = window_config_t( )
        window_config.show_bar      = True
        window_config.bar_title     = "Share connection"
        window_config.title_font    = self._general_font

        new_window = self._scene_project.create_window( vector( 300, 160 ), vector( 400, 170 ), window_config )
        
        c_button( new_window, vector( 10, 10 ), 40, self._general_font, self._application.image( "icon_copy" ), "Copy Code", lambda: glfw.set_clipboard_string( None, self._logic.generate_code( ) ) )

        render: c_renderer  = self._application.render( )
        font:   c_font      = self._general_font

        def draw_code( ):

            fade:   float       = new_window.animations( ).value( "Fade" )
            code:   str         = self._logic.generate_code( )

            text:       str     = render.wrap_text( self._general_font, f"Or you can manually copy this code and share it with others:", 380 )
            text_size:  vector  = render.measure_text( self._general_font, text )

            render.text( font, vector( 10, 70 ), color( 255, 255, 255, 255 ) * fade, text )
            render.text( font, vector( 10, 90 + text_size.y ), color( 255, 255, 255, 255 ) * fade, code )

        new_window.set_event( "draw", draw_code, "Draw Code", False )


    def __callback_on_press_users( self ):
        """
        Callback for the users button.

        Receive: None

        Returns: None
        """

        window_config = window_config_t( )
        window_config.show_bar      = True
        window_config.bar_title     = "Users panel"
        window_config.title_font    = self._general_font

        new_window = self._scene_project.create_window( vector( 300, 160 ), vector( 430, 380 ), window_config )

        list_config = list_config_t( )
        list_config.slots_count = 7
        list_config.back_color = list_config.back_color * 0

        users_list:     c_list = c_list( new_window, vector( 220, 10 ), 200, self._general_font, list_config )
        clients_list: c_list = c_list( new_window, vector( 10, 10 ), 200, self._general_font, list_config )

        active_clients: list = [ ]

        for client in self._logic.clients( ):
            client: c_client_handle = client
            username = client( "username" )

            active_clients.append( username )

            clients_list.add_item( username, self._application.image( "icon_username" ), self.__callback_on_client_click )


        for username in self._logic.host_registered_users( ):
            
            if username not in active_clients:
                users_list.add_item( username, self._application.image( "icon_username" ), self.__callback_on_user_click )


    def __callback_on_client_click( self, username: str ):
        """
        Callback for pressing on a client.

        Receive: 
        - username (str): Client username

        Returns: None
        """

        icon:   c_image     = self._application.image( "icon_previous" )
        render: c_renderer  = self._application.render( )
        
        client: c_client_handle = self._logic.find_client( username )
        if client is None:
            return
            
        # Client window configuration
        client_window_config = window_config_t( )
        client_window_config.show_bar       = True
        client_window_config.bar_title      = username
        client_window_config.title_font     = self._general_font
            
        client_info_window: c_window        = self._scene_project.create_window( vector( 400, 200 ), vector( 800, 390 ), client_window_config )
        animations:         c_animations    = client_info_window.animations( )

        def kick_user( ):
            client.disconnect( )
            client_info_window.show( False )


        def update_trust_factor( event ):
            new_value: int = event( "new_value" )
            client.trust_factor( new_value )


        trust_factor_slider = c_slider_int( client_info_window, vector( 10, 130 ), 300, self._general_font, 0, DEFAULT_TRUST_FACTOR, client.trust_factor( ) )
        trust_factor_slider.set_callback( update_trust_factor )

        c_button( client_info_window, vector( 10, 170 ), 40, self._general_font, icon, "Disconnect", kick_user )

        files_list_config = list_config_t( )
        files_list_config.slots_count   = 7
        files_list_config.back_color    = files_list_config.back_color * 0

        files_list: c_list = c_list( client_info_window, vector( 400, 10 ), 380, self._general_font, files_list_config)
        files:      list = client.files_list( )

        for file_name in files:
            files_list.add_item( file_name, self._application.image( "icon_file" ), self.__callback_on_file_click( client ) )

        def draw_client( ):
            fade = animations.value( "Fade" )
            render.text( self._general_font, vector( 10, 10 ), color( ) * fade,     f"user\t{ username }" )
            render.text( self._general_font, vector( 10, 40 ), color( ) * fade,     f"file\t{ client.selected_file( ) }" )
            render.text( self._general_font, vector( 10, 70 ), color( ) * fade,     f"line\t{ client.selected_line( ) }" )
            render.text( self._general_font, vector( 10, 100 ), color( ) * fade,    f"trust" )

        client_info_window.set_event( "draw", draw_client, "render", False )


    def __callback_on_user_click( self, username ):
        """
        Callback for pressing on a registered user.

        Receive: 
        - username (str): Client username

        Returns: None
        """

        render: c_renderer  = self._application.render( )
        
        user: dict = self._logic.find_client( username, True )
        if user is None:
            return
            
        # User window configuration
        user_window_config = window_config_t( )
        user_window_config.show_bar       = True
        user_window_config.bar_title      = username
        user_window_config.title_font     = self._general_font
            
        user_info_window: c_window        = self._scene_project.create_window( vector( 400, 200 ), vector( 800, 390 ), user_window_config )
        animations:         c_animations  = user_info_window.animations( )

        def update_trust_factor( event ):

            new_value: int = event( "new_value" )
            self._logic.update_registered_user( username, [ "trust_factor" ], new_value )

        trust_factor_slider = c_slider_int( user_info_window, vector( 10, 100 ), 300, self._general_font, 0, DEFAULT_TRUST_FACTOR, user[ "trust_factor" ] )
        trust_factor_slider.set_callback( update_trust_factor )

        files_list_config = list_config_t( )
        files_list_config.slots_count   = 7
        files_list_config.back_color    = files_list_config.back_color * 0

        files_list: c_list = c_list( user_info_window, vector( 400, 10 ), 380, self._general_font, files_list_config)
        files:      list = user[ "files" ]

        for file_name in files:
            files_list.add_item( file_name, self._application.image( "icon_file" ), self.__callback_on_user_file_click( username, file_name ) )

        def draw_client( ):
            fade = animations.value( "Fade" )
            render.text( self._general_font, vector( 10, 10 ), color( ) * fade,     f"user\t{ username }" )
            render.text( self._general_font, vector( 10, 40 ), color( ) * fade,     f"date\t{ user[ '__Creation_Date' ] }" )
            render.text( self._general_font, vector( 10, 70 ), color( ) * fade,     f"trust " )

        user_info_window.set_event( "draw", draw_client, "render", False )


    def __callback_on_file_click( self, client: c_client_handle ):
        """
        Callback for pressing on a file.

        Receive:   
        - client (c_client_handle): Client handle that the file click is refered to

        Returns:
        - function: Callback to init a window to display file information
        """

        def click_fn( file_name: str ):

            file_data:      list    = client.get_file( file_name )
            access_level:   int     = file_data[ 1 ]

            # icon_file window configuration
            file_window_config = window_config_t( )
            file_window_config.show_bar       = True
            file_window_config.bar_title      = file_name
            file_window_config.title_font     = self._general_font
            
            file_window: c_window       = self._scene_project.create_window( vector( 400, 300 ), vector( 400, 200 ), file_window_config )

            list_config = list_config_t( )
            list_config.slots_count = 3
            list_config.back_color  = list_config.back_color * 0
            list_config.check_mark  = self._application.image( "icon_check" )

            access_level_list: c_list = c_list( file_window, vector( 10, 10 ), 380, self._general_font, list_config )

            # FILE_ACCESS_LEVEL_HIDDEN    = 0     # This file should be hidden ( used only for host )
            # FILE_ACCESS_LEVEL_EDIT      = 1     # This file can be edited
            # FILE_ACCESS_LEVEL_LIMIT     = 2     # This file cannot be edited

            access_level_string = {
                0: "Hidden",
                1: "Edit",
                2: "Limit"
            }

            access_level_list.add_item( "Hidden",   self._application.image( "icon_lock" ),      lambda x: client.change_access_level( file_data[ 0 ], FILE_ACCESS_LEVEL_HIDDEN ) )
            access_level_list.add_item( "Edit",     self._application.image( "icon_tune" ),      lambda x: client.change_access_level( file_data[ 0 ], FILE_ACCESS_LEVEL_EDIT ) )
            access_level_list.add_item( "Limit",    self._application.image( "icon_visible" ),   lambda x: client.change_access_level( file_data[ 0 ], FILE_ACCESS_LEVEL_LIMIT ) )

            access_level_list.set_value( access_level_string[ access_level ] )

        return click_fn


    @static_arguments
    def __callback_on_user_file_click( self, username: str, file_index: str ):
        """
        Callback for pressing on a file in a registered user panel.

        Receive:   
        - username (str): Client username that the file refers to
        - file_index (str): File index that was pressed

        Returns: None
        """

        # We should update it everytime we open this window
        user: dict = self._logic.find_client( username, True )
        default_access_level = user[ "files" ][ file_index ]
        del user

        # icon_file window configuration
        file_window_config = window_config_t( )
        file_window_config.show_bar       = True
        file_window_config.bar_title      = file_index
        file_window_config.title_font     = self._general_font
            
        file_window: c_window       = self._scene_project.create_window( vector( 400, 300 ), vector( 400, 200 ), file_window_config )

        list_config = list_config_t( )
        list_config.slots_count = 3
        list_config.back_color  = list_config.back_color * 0
        list_config.check_mark  = self._application.image( "icon_check" )

        access_level_list: c_list = c_list( file_window, vector( 10, 10 ), 380, self._general_font, list_config )

        access_level_string = {
            0: "Hidden",
            1: "Edit",
            2: "Limit"
        }

        access_level_list.add_item( "Hidden",   self._application.image( "icon_lock" ),      lambda x: self._logic.update_registered_user( username, [ "files", file_index ], FILE_ACCESS_LEVEL_HIDDEN ) )
        access_level_list.add_item( "Edit",     self._application.image( "icon_tune" ),      lambda x: self._logic.update_registered_user( username, [ "files", file_index ], FILE_ACCESS_LEVEL_EDIT ) )
        access_level_list.add_item( "Limit",    self._application.image( "icon_visible" ),   lambda x: self._logic.update_registered_user( username, [ "files", file_index ], FILE_ACCESS_LEVEL_LIMIT ) )

        access_level_list.set_value( access_level_string[ default_access_level ] )


    def __callback_on_press_logs( self ):
        """
        Callback for the logs button.

        Receive: None

        Returns: None
        """

        window_config = window_config_t( )
        window_config.show_bar      = True
        window_config.bar_title     = "System logs"
        window_config.title_font    = self._general_font
        
        window_size: vector = vector( 1200, 800 )

        new_window = self._scene_project.create_window( vector( 300, 160 ), window_size, window_config )
        c_multiline_label( new_window, vector( 0, 0 ), window_size, self._general_font, self._logs )


    def __callback_on_press_refresh_path( self ):
        """
        Callback to refresh the registered files.

        Receive: None

        Returns: None
        """

        self._solution_explorer.clear( )

        self._logic.complete_setup_files( )

    
    def __callback_on_press_new_file( self ):
        """
        Callback to init a new file creation window.

        Receive: None

        Returns: None
        """

        window_config = window_config_t( )
        window_config.show_bar      = True

        list_config = list_config_t( )
        list_config.slots_count = 3
        list_config.check_mark  = self._application.image( "icon_check" )

        path_icons:     dict = {
            "back_icon":    self._application.image( "icon_previous" ), 
            "folder_icon":  self._application.image( "icon_folder" ), 
            "file_icon":    self._application.image( "icon_file" )
        }

        types: list = [ "py - Python", "cpp - C++", "hpp - C++", "c - C", "h - C", "cs - C#", "txt - Text" ]
        access_levels = {
            "Edit": ( FILE_ACCESS_LEVEL_EDIT, self._application.image( "icon_tune" ) ),
            "View": ( FILE_ACCESS_LEVEL_LIMIT, self._application.image( "icon_visible" ) ),
            "Hide": ( FILE_ACCESS_LEVEL_HIDDEN, self._application.image( "icon_lock" ) )
        }

        new_window = self._scene_project.create_window( vector( 300, 160 ), vector( 950, 600 ), window_config )

        path: c_path_select = c_path_select( new_window, self._general_font, vector( 10, 10 ), vector( 500, 580 ), path_icons )
        path.parse_path( self._logic( "normal_path" ) )

        name_input:     c_text_input    = c_text_input( new_window, vector( 520, 10 ), 40, vector( 180, 30 ), self._general_font, self._application.image( "icon_file" ), "File name", "__name__" )
        file_type:      c_list          = c_list( new_window, vector( 520, 70 ), 410, self._general_font, list_config )
        access_list:    c_side_list     = c_side_list( new_window, vector( 520, 240 ), 410, self._general_font, list_config )

        for any_type in types:
            any_type: str = any_type

            file_type.add_item( any_type, self._application.image( "icon_port" ) )
        
        for access_type in access_levels:
            values: tuple = access_levels[ access_type ]
            access_list.add_item( access_type, values[ 1 ] )

        file_type.set_value( "py - Python" )
        access_list.set_value( "Hide" )

        @safe_call( c_debug.log_error )
        def callback_on_complete_file( ):
            normalized_name = name_input.get( ) + "." + file_type.get( ).split( " - " )[ 0 ]

            self._solution_explorer.clear( )
            self._logic.create_empty_file( path.get_path( ), normalized_name, access_levels[ access_list.get( ) ][ 0 ] )
            self._logic.complete_setup_files( )

            new_window.show( False )

        c_button( new_window, vector( 520, 550 ), 40, self._general_font, self._application.image( "icon_check" ), "Create File", callback_on_complete_file )


    @static_arguments
    def __callback_show_file_details( self, file_index: str ):
        """
        Callback to init a window to show file information.

        Receive:
        - file_index (str): File name

        Returns: None
        """

        # Create window
        window_config = window_config_t( )
        window_config.show_bar = True
        window_config.title_font = self._general_font

        # TODO ! Limit the chars amount
        window_config.bar_title = f"{ file_index } details"

        new_window: c_window = self._scene_project.create_window( vector( 400, 400 ), vector( 500, 300 ), window_config )

        success, information = self._logic.find_file_information( file_index )

        if not success:
            return
        
        list_config = list_config_t( )
        list_config.check_mark = self._application.image( "icon_check" )
        list_config.slots_count = 3

        file_name:      c_text_input    = c_text_input( new_window, vector( 10, 10 ), 40, vector( 200, 30 ), self._general_font, self._application.image( "icon_file" ), "icon_file name", information[ 0 ] )
        file_type:      c_list          = c_list( new_window, vector( 10, 60 ), 235, self._general_font, list_config )
        file_access:    c_list          = c_list( new_window, vector( 255, 60 ), 235, self._general_font, list_config )

        types: list = [ "py - Python", "cpp - C++", "hpp - C++", "c - C", "h - C", "cs - C#", "txt - Text" ]
        for any_type in types:
            any_type: str = any_type

            file_type.add_item( any_type, self._application.image( "icon_port" ) )

            if any_type.startswith( information[ 1 ] ):
                file_type.set_value( any_type )

        access_levels = {
            "Edit": ( FILE_ACCESS_LEVEL_EDIT, self._application.image( "icon_tune" ) ),
            "View": ( FILE_ACCESS_LEVEL_LIMIT, self._application.image( "icon_visible" ) ),
            "Hide": ( FILE_ACCESS_LEVEL_HIDDEN, self._application.image( "icon_lock" ) )
        }

        for access_type in access_levels:
            values: tuple = access_levels[ access_type ]

            file_access.add_item( access_type, values[ 1 ] )

            if information[ 3 ] == values[ 0 ]:
                file_access.set_value( access_type )
        
        def callback_on_file_details_update( ):

            normalized_old_name = information[ 0 ] + "." + information[ 1 ]
            normalized_new_name = file_name.get( ) + "." + ( file_type.get( ).split( " - " )[ 0 ] )
            
            self._logic.update_file_details( file_index, file_index.replace( normalized_old_name, normalized_new_name ), access_levels[ file_access.get( ) ][ 0 ] )

            self._solution_explorer.remove_item( normalized_old_name )
            self._solution_explorer.add_item( normalized_new_name, self._logic.request_file( normalized_new_name ), self.__callback_show_file_details( normalized_new_name ) )

            new_window.show( False )

        c_button( new_window, vector( 10, 250 ), 40, self._general_font, self._application.image( "icon_check" ), "Update File details", callback_on_file_details_update )

    # endregion

    # region : Events

    def __event_close_application( self ):
        """
        Event callback when the application is closed.

        Receive: None

        Returns: None
        """
        
        self._logic.terminate( )


    def __event_update_files_list( self, event ):
        """
        Event callback to update files list.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        files: list = event( "files" )

        def add_file( file: str ):
            # I AM ACTUALLY GOING INSANE
            self._solution_explorer.add_item( file, self._logic.request_file( file ), self.__callback_show_file_details( file ) )

        for file in files:

            add_file( file )

            # YOU CANNOT CALL THE FUNCTION DIRECTLY 
            # BECAUSE IT WILL BREAK AND ADD THE SAME CALLBACK TO ALL FILES
            # self._solution_explorer.add_item( file, lambda: print( f"Left clicked on { file }" ) )
    

    def __event_clear_editor( self, event ):
        """
        Event callback for clearing the editor.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file:       str     = event( "file" )

        self._editor.clear( )
        self._editor.read_only( False )
        self._editor.open_file( file )


    def __event_add_editor_line( self, event ):
        """
        Event callback for adding new line.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        line_text:  str     = event( "line_text" )
        self._editor.add_line( line_text )

    
    def __event_editor_request_line( self, event ):
        """
        Client requests line from the server.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        self._logic.request_line( file, line )


    def __event_accept_line( self, event ):
        """
        If line is locked by host user.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        self._editor.accept_line( file, line, True )

    
    def __event_lock_line( self, event ): 
        """
        Response to lock a line.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file_name:  str     = event( "file")
        line:       int     = event( "line" )
        user:       str     = event( "user" )

        self._editor.lock_line( line, user )

    
    def __event_unlock_line( self, event ):
        """
        Response from host to client in order to unlock a line.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file_name:  str     = event( "file")
        line:       int     = event( "line" )

        self._editor.unlock_line( line )

    
    def __event_discard_line( self, event ):
        """
        Message to the host in order to discard line changes.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file_name:  str = event( "file" )
        line:       int = event( "line" )

        self._logic.discard_line( file_name, line )


    def __event_change_lines( self, event ):
        """
        Response from host to client in order to change lines.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file_name:  str     = event( "file" )
        line:       int     = event( "line" )
        new_lines:  list    = event( "new_lines" )

        self._editor.change_lines( file_name, line, new_lines )

    
    def __event_remove_line( self, event ):
        """
        Response from host to client in order to delete line.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file_name:  str     = event( "file" )
        line:       int     = event( "line" )

        self._editor.delete_line( file_name, line )

    
    def __event_update_line( self, event ):
        """
        Message to the host in order to commit changes.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        lines:  list    = event( "lines" )

        self._logic.update_line( file, line, lines )

    
    def __event_delete_line( self, event ):
        """
        Message to server in order to delete a line.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        self._logic.delete_line( file, line )
    
    
    @safe_call( None )
    def __event_add_log( self, event ):
        """
        Add new log in the application to display it.

        Receive :
        - event (callable): Event information

        Returns: None
        """

        message:    str = event( "message" )
        user:       str = event( "user" )
        time:       str = event( "time" )
        log_type:   int = event( "type" )

        result: str = f"- { time } "
        if log_type == ENUM_LOG_ERROR:
            result += "- error "
        else:
            result += "- info  "

        result += f" - { user } - { message }"

        self._logs.put_nowait( result )

    # endregion

    # region : Utilities

    def __show_error_message( self, message: str, scene: c_scene ):
        """
        Create and attach error message to a scene.

        Receive:
        - message (str): Error message
        - scene (c_scene) Scene to attach the error screen

        Returns: None
        """

        size:   vector = vector( 500, 250 )
        screen: vector = self._application.window_size( ) / 2

        error_window_config = window_config_t( )
        error_window_config.show_bar = True

        new_window = scene.create_window( screen - ( size / 2 ), size, error_window_config )

        render: c_renderer  = self._application.render( )

        icon_copy:  c_image     = self._application.image( "icon_copy" )

        c_icon_button( new_window, vector( 430, 10 ), icon_copy, lambda: glfw.set_clipboard_string( None, message ) )

        def draw( event ):

            fade:   float       = new_window.animations( ).value( "Fade" )

            render.push_clip_rect( vector( ), vector( 500, 300 ) )
            render.text( self._general_font, vector( 10, 10 ), color( ) * fade, "Error occurred" )
            render.text( self._general_font, vector( 10, 80 ), color( 180, 180, 180 ) * fade, render.wrap_text( self._general_font, message, 480 ) )
            render.pop_clip_rect( )

        new_window.set_event( "draw", draw, "draw_error_window" )

    # endregion

    def execute( self ):
        """
        Execute the application.

        Receive: None

        Returns: None
        """

        self._application.run( )