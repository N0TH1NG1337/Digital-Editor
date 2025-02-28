"""
    project     : Digital Editor

    type:       : Host
    file        : Graphical User Interface

    description : Host GUI class
"""

from host.business_logic        import *
from user_interface.application import *
from utilities.paths            import *
from utilities.debug            import *

LOADING_MIN_TIME = 2

class c_host_gui:
    
    # region : Privates attributes

    _application:           c_application
    _logic:                 c_host_business_logic

    _scene_loadup:          c_scene
    _scene_setup:           c_scene
    _scene_wait:            c_scene
    _scene_project:         c_scene


    _application_config:    application_config_t
    _scene_loadup_config:   scene_config_t
    _scene_setup_config:    scene_config_t
    _scene_project_config:  scene_config_t

    _temp:                  dict

    _entry_username:        c_text_input
    _entry_ip:              c_text_input
    _entry_port:            c_text_input
    _path_select:           c_path_select
    _list_access_level:     c_side_list
    _button_prev_setup:     c_button
    _button_next_setup:     c_button

    _editor:                c_editor
    _button_menu:           c_icon_button
    _button_files:          c_icon_button
    _button_admin:          c_icon_button

    _button_close:          c_icon_button
    _button_share:          c_button
    _button_users:          c_button
    _button_logs:           c_button

    _solution_explorer:     c_solution_explorer
    _button_placehoder1:    c_button
    _button_placehoder2:    c_button

    _opened_what:           int

    # endregion

    # region : Initialization

    def __init__( self, should_debug: bool = False ):
        """
            Default constructor for the host GUI class.

            Receive : 
            - should_debug [optional] - Should enable debug logging

            Returns : Host GUI object
        """

        if should_debug:
            c_debug.load_basic_debugging( "host_debug.log" )

        self._temp          = { }
        self._opened_what   = 0

        self.__initialize_application( )
        self.__initialize_logic( )


    def __initialize_application( self ):
        """
            Initialize the application object.

            Receive : None

            Returns : None
        """

        self._application_config = application_config_t( )

        self._application = c_application( self._application_config )

        self._application.initialize_window( "Host", vector( 50, 50 ), vector( 1300, 850 ), True )

        self.__initialize_resources( )

        self._application.initialize_events()

        self.__scene_loadup_initialize( )
        self.__scene_setup_initialize( )
        self.__scene_wait_initialize( )
        self.__scene_project_initialize( )

        self._application.set_event( "unload", self.__event_close_application, "Close Application" )


    def __initialize_logic( self ):
        """
            Initialize the logic object.

            Receive : None

            Returns : None
        """

        self._logic = c_host_business_logic( )

        self.__initialize_logic_events( )


    def __initialize_logic_events( self ):
        """
            Initialize the logic's events callbacks.

            Receive :   None

            Returns :   None
        """

        self._logic.set_event( "on_files_refresh",  self.__event_update_files_list, "gui_update_files_list",    True )
        self._logic.set_event( "on_file_set",       self.__event_clear_editor,      "gui_clear_editor",         True )
        self._logic.set_event( "on_file_update",    self.__event_add_editor_line,   "gui_update_editor",        True )
        self._logic.set_event( "on_accept_line",    self.__event_accept_line,       "gui_editor_accept_line",   True )
        self._logic.set_event( "on_line_lock",      self.__event_lock_line,         "gui_editor_line_lock",     True )
        self._logic.set_event( "on_line_unlock",    self.__event_unlock_line,       "gui_editor_line_unlock",   True )
        self._logic.set_event( "on_line_update",    self.__event_change_lines,      "gui_editor_line_update",   True )
        self._logic.set_event( "on_line_delete",    self.__event_remove_line,       "gui_editor_line_remove",   True )

    
    def __initialize_resources( self ):
        """
            Initialize the resources for the application.

            Receive : None

            Returns : None
        """

        execution_directory = os.getcwd( )
        self._application.create_font( "Title",     FONT_BOLD, 100 )
        self._application.create_font( "SubTitle",  FONT_BOLD, 50 )
        self._application.create_font( "Steps",     FONT, 20 )
        self._application.create_font( "Button",    FONT, 20 )
        self._application.create_font( "TextInput", FONT, 20 )
        self._application.create_font( "Path",      FONT, 20 )
        self._application.create_font( "List",      FONT, 20 )
        self._application.create_font( "Editor",    FONT, 20 )

        self._application.create_image( "Wallpaper",    execution_directory + PHOTO_WALLPAPER,      vector( 3840, 2160 ), [ IMAGE_FILTER_BLUR ] )

        self._application.create_image( "Username",     execution_directory + ICON_USERNAME,        vector( 30, 30 ) )
        self._application.create_image( "Next",         execution_directory + ICON_NEXT,            vector( 30, 30 ) )
        self._application.create_image( "Prev",         execution_directory + ICON_PREV,            vector( 30, 30 ) )

        self._application.create_image( "Folder",       execution_directory + ICON_FOLDER,          vector( 30, 30 ) )
        self._application.create_image( "File",         execution_directory + ICON_FILE,            vector( 30, 30 ) )

        self._application.create_image( "Listen",       execution_directory + ICON_LISTEN,          vector( 30, 30 ) )
        self._application.create_image( "Port",         execution_directory + ICON_PORT,            vector( 30, 30 ) )

        self._application.create_image( "Share",        execution_directory + ICON_SHARE,           vector( 30, 30 ) )
        self._application.create_image( "User",         execution_directory + ICON_USER,            vector( 30, 30 ) )
        self._application.create_image( "Info",         execution_directory + ICON_INFO,            vector( 30, 30 ) )

        self._application.create_image( "Copy",         execution_directory + ICON_COPY,            vector( 30, 30 ) )

        self._application.create_image( "Lock",         execution_directory + ICON_LOCKED,          vector( 30, 30 ) )
        self._application.create_image( "Visible",      execution_directory + ICON_VISIBLE,         vector( 30, 30 ) )
        self._application.create_image( "Tune",         execution_directory + ICON_TUNE,            vector( 30, 30 ) )

        self._application.create_image( "Check",        execution_directory + ICON_CHECK,           vector( 30, 30 ) )

        self._application.create_image( "Menu",         execution_directory + ICON_MENU,            vector( 40, 40 ) )
        self._application.create_image( "Files",        execution_directory + ICON_FILES,           vector( 40, 40 ) )
        self._application.create_image( "Admin",        execution_directory + ICON_ADMIN,           vector( 40, 40 ) )
        self._application.create_image( "Close",        execution_directory + ICON_CLOSE,           vector( 40, 40 ) )
        
        self._temp[ "setup_proccess" ]  = 0
        
        self._application_config.wallpaper = self._application.image( "Wallpaper" )
        
    # endregion

    # region : Scene Loadup

    def __scene_loadup_initialize( self ):
        """
            Initialize the Loadup Scene.

            Receive : None

            Returns : None
        """

        self._scene_loadup_config = scene_config_t( )
        self._scene_loadup_config.animate_movement = True

        self._scene_loadup = self._application.new_scene( self._scene_loadup_config )

        self._scene_loadup.set_event( "draw",           self.__scene_loadup_draw,   "Scene Loadup Draw Main" )
        self._scene_loadup.set_event( "mouse_input",    self.__scene_loadup_update, "Scene Loadup Update" )
        self._scene_loadup.set_event( "keyboard_input", self.__scene_loadup_update, "Scene Loadup Update" )

    
    def __scene_loadup_draw( self, event ):
        """
            Main draw function for Loadup Scene.

            Receive : Event object

            Returns : None
        """

        render:         c_renderer      = self._application.render( )
        animations:     c_animations    = self._scene_loadup.animations( )

        fade:           float           = animations.value( "Fade" )
        screen:         vector          = self._application.window_size( )

        title_font:     c_font          = self._application.font( "Title" )
        title:          str             = "Digital Editor"
        version:        str             = "Host"

        title_size:     vector  = render.measure_text( title_font, title )
        version_size:   vector  = render.measure_text( title_font, version )

        title_pos:      vector  = ( screen - title_size ) / 2
        version_pos:    vector  = ( screen - version_size ) / 2 + vector( 0, 100 )

        back_start  = title_pos - vector( 10, 10 )
        back_end    = title_pos + vector( title_size.x + 10, 200 + 10 )

        render.shadow(
            back_start,
            back_end,
            color( 216, 208, 215, 255 ),
            fade,
            25,
            10
        )

        render.rect(
            back_start,
            back_end,
            color( 0, 0, 0, 100 ) * fade,
            10
        )

        render.text( title_font, title_pos + vector( 3, -3 ), color( 216, 208, 215, 255 ) * fade, title )
        render.text( title_font, title_pos, color( 255, 255, 255, 255 ) * fade, title )

        render.text( title_font, version_pos + vector( 3, -3 ), color( 216, 208, 215, 255 ) * fade, version )
        render.text( title_font, version_pos, color( 255, 255, 255, 255 ) * fade, version )


    def __scene_loadup_update( self, event ):
        """
            Update the Loadup Scene on any press.

            Receive : Event object

            Returns : None
        """

        if event( "action" ) == glfw.PRESS:
            self._application.active_scene( self._scene_setup.index( ) )

    # endregion

    # region : Scene Setup

    def __scene_setup_initialize( self ):
        """
            Initialize the Setup Scene.

            Receive : None

            Returns : None
        """

        self._scene_setup_config = scene_config_t( )

        self._scene_setup_config.animate_movement   = True
        self._scene_setup_config.enable_stars       = True

        self._scene_setup = self._application.new_scene( self._scene_setup_config )

        self.__scene_setup_initialize_elements( )

        animations: c_animations = self._scene_setup.animations()
        animations.prepare( "Username",     vector( ) )
        animations.prepare( "Files",        vector( ) )
        animations.prepare( "Connection",   vector( ) )
        animations.prepare( "ButtonNext",   250 )
        animations.prepare( "ProgressBar",  0 )

        self._scene_setup.set_event( "draw", self.__scene_setup_draw,               "Scene Setup Draw Main" )
        self._scene_setup.set_event( "draw", self.__scene_setup_adjust_elements,    "Scene Setup Adjust Elements" )

    
    def __scene_setup_initialize_elements( self ):
        """
            Setup the elements for the Setup Scene.

            Receive : None

            Returns : None
        """

        path_font:      c_font  = self._application.font( "Path" )
        text_font:      c_font  = self._application.font( "TextInput" )
        button_font:    c_font  = self._application.font( "Button" )
        list_font:      c_font  = self._application.font( "List" )

        path_icons:     dict = {
            "back_icon":    self._application.image( "Prev" ), 
            "folder_icon":  self._application.image( "Folder" ), 
            "file_icon":    self._application.image( "File" )
        }
        
        username_icon:  c_image = self._application.image( "Username" )
        next_icon:      c_image = self._application.image( "Next" )
        prev_icon:      c_image = self._application.image( "Prev" )


        ip_icon:        c_image = self._application.image( "Listen" )
        port_icon:      c_image = self._application.image( "Port" )

        self._entry_username    = c_text_input( self._scene_setup, vector( 50, 100 ), 40, vector( 200, 30 ), username_icon, text_font, "username" )
        self._entry_ip          = c_text_input( self._scene_setup, vector( 50, 100 ), 40, vector( 200, 30 ), ip_icon,       text_font, "ip", False, "0.0.0.0" )
        self._entry_port        = c_text_input( self._scene_setup, vector( 50, 150 ), 40, vector( 200, 30 ), port_icon,     text_font, "port", False, "9978" )

        self._path_select       = c_path_select( self._scene_setup, path_font, vector( 50, 100 ), vector( 500, 580 ), path_icons )
        self._list_access_level = c_side_list( self._scene_setup, vector( 50, 700 ), 500, list_font )

        self._button_prev_setup = c_button( self._scene_setup, vector( 50, 250 ), 40, button_font, prev_icon,   "Previous", self.__scene_setup_previous_step )
        self._button_next_setup = c_button( self._scene_setup, vector( 100, 250 ), 40, button_font, next_icon,  "Next",     self.__scene_setup_next_step )

        self._path_select.visible( False )
        self._list_access_level.visible( False )
        self._entry_ip.visible( False )
        self._entry_port.visible( False )

        self._path_select.parse_path( os.getcwd( ) )
        self._list_access_level.add_item( "Hidden", None, None )
        self._list_access_level.add_item( "Limit",  None, None )
        self._list_access_level.add_item( "Edit",   None, None )

        self._list_access_level.set_value( "Hidden" )


    def __scene_setup_draw( self, event ):
        """
            Main draw function for Setup Scene.

            Receive : Event object

            Returns : None
        """

        steps_font: c_font          = self._application.font( "TextInput" )
        screen:     vector          = self._application.window_size( )

        render:     c_renderer      = self._application.render( )
        animations: c_animations    = self._scene_setup.animations( )

        fade:       float           = animations.value( "Fade" )
        speed:      int             = self._scene_setup_config.speed
        pad:        int             = 50

        steps = {
            0: "Username",
            1: "Files",
            2: "Connection"
        }

        offset      = 0
        progress    = 0

        selected    = self._temp[ "setup_proccess" ]
        
        for index in steps :
            step = steps[ index ]

            step_size:      vector  = render.measure_text( steps_font, step )

            alpha_step: float = 0
            if selected == index:
                progress    = animations.preform( "ProgressBar", offset + step_size.x, speed )
                alpha_step  = 1
            else:
                alpha_step  = 0
                
            wanted_value:   vector  = vector( max( alpha_step , 0.5 ), alpha_step )
            values:         vector  = animations.preform( step, wanted_value, speed )

            values.x *= fade
            current_color = color( ).lieaner( color( 216, 208, 215, 255 ), values.y ) * values.x

            render.text( steps_font, vector( 50 + offset, 50 ), current_color, step )

            offset += step_size.x + pad

        render.shadow( vector( 50, 80 ), vector( 50 + progress, 80 ), color( 216, 208, 215, 255 ), fade, 25 )
        render.line( vector( 50, 80 ), vector( 50 + progress, 80 ), color( 216, 208, 215, 255 ) * fade )


    def __scene_setup_adjust_elements( self, event ):
        """
            Adjust the scene elements positions.

            Receive : Event object

            Returns : None
        """

        animations: c_animations    = self._scene_setup.animations( )
        screen:     vector          = self._application.window_size( )

        speed:      int             = self._scene_setup_config.speed
        
        button_next_drop: float = animations.preform( "ButtonNext", screen.y - 50 - 40, speed )

        self._button_prev_setup.position( vector( 50, button_next_drop ) )
        self._button_next_setup.position( vector( 100 + self._button_prev_setup.size( ).x, button_next_drop ) )

    
    def __scene_setup_next_step( self ):
        """
            Next setup step.

            Receive :   None

            Returns :   None
        """

        self._temp[ "setup_proccess" ] = math.clamp( self._temp[ "setup_proccess" ] + 1, 0, 3 ) 

        self.__scene_setup_update( )

        if self._temp[ "setup_proccess" ] == 3:
            self.__project_start( )
            return
    

    def __scene_setup_previous_step( self ):
        """
            Previous setup step.

            Receive :   None

            Returns :   None
        """

        self._temp[ "setup_proccess" ] = math.clamp( self._temp[ "setup_proccess" ] - 1, 0, 3 ) 

        self.__scene_setup_update( )

    
    @safe_call( c_debug.log_error )
    def __scene_setup_update( self ):
        
        process_index = self._temp[ "setup_proccess" ]

        changes = {
            0: [ True, False, False ],
            1: [ False, True, False ],
            2: [ False, False, True ],
            3: [ False, False, False ]
        }

        if process_index not in changes:
            return
        
        current_changes = changes[ process_index ]

        self._entry_username.visible( current_changes[ 0 ] )
        self._path_select.visible( current_changes[ 1 ] )
        self._list_access_level.visible( current_changes[ 1 ] )
        self._entry_ip.visible( current_changes[ 2 ] )
        self._entry_port.visible( current_changes[ 2 ] )
        
    # endregion

    # region : Scene Wait
    # This scene is only a placeholder for the moment until the host is fully implemented

    def __scene_wait_initialize( self ):
        """
            Initialize the Wait Scene.

            Receive : None

            Returns : None
        """

        self._scene_wait = self._application.new_scene( )

    # endregion

    # region : Scene Project

    @standalone_execute
    def __project_start( self ):
        """
            Start the hosting program.

            Receive : None

            Returns : None
        """

        self._application.active_scene( self._scene_wait.index( ) )

        time.sleep( 1 )

        self._logic.initialize_path( self._path_select.get_path( ), self._list_access_level.get( ) )

        self._logic.setup( self._entry_ip.get( ), int( self._entry_port.get( ) ), self._entry_username.get( ) )
        self._logic.start( )

        time.sleep( LOADING_MIN_TIME )

        self._application.active_scene( self._scene_project.index( ) )
        

    def __scene_project_initialize( self ):
        """
            Initialize the Project Scene.

            Receive : None

            Returns : None
        """

        self._scene_project_config = scene_config_t( )

        self._scene_project = self._application.new_scene( self._scene_project_config )

        self.__scene_project_initialize_elements( )

        animations: c_animations = self._scene_project.animations( )
        animations.prepare( "OpenMenu", 0 )

        self._scene_project.set_event( "draw", self.__scene_project_animate_tabs, "Scene Project Animate Tabs" )
        self._scene_project.set_event( "draw", self.__scene_project_adjust_elements, "Scene Project Adjust Elements" )

    
    def __scene_project_initialize_elements( self ):
        """
            Setup the elements for the Project Scene.

            Receive : None

            Returns : None
        """

        editor_font:    c_font  = self._application.font( "Editor" )
        button_font:    c_font  = self._application.font( "Button" )

        menu_icon:      c_image = self._application.image( "Menu" )
        file_icon:      c_image = self._application.image( "Files" )
        admin_icon:     c_image = self._application.image( "Admin" )
        close_icon:     c_image = self._application.image( "Close" )

        #copy_icon:      c_image = self._application.image( "Copy" )
        share_icon:     c_image = self._application.image( "Share" )
        user_icon:      c_image = self._application.image( "User" )
        info_icon:      c_image = self._application.image( "Info" )

        solution_config = solution_explorer_config_t( )
        
        solution_config.folder_icon = self._application.image( "Folder" )
        solution_config.item_icon   = self._application.image( "File" )

        self._editor        = c_editor( self._scene_project, vector( 50, 100 ), vector( 1000, 760 ), editor_font )

        self._button_menu   = c_icon_button( self._scene_project, vector( 50, 50 ),     menu_icon,  self.__callback_on_press_menu )
        self._button_files  = c_icon_button( self._scene_project, vector( 100, 50 ),    file_icon,  self.__callback_on_press_files )
        self._button_admin  = c_icon_button( self._scene_project, vector( 500, 50 ),    admin_icon, self.__callback_on_press_admin )
        self._button_close  = c_icon_button( self._scene_project, vector( 50, 1000 ),   close_icon, self.__callback_on_press_close )

        self._solution_explorer = c_solution_explorer( self._scene_project, vector( 50, 160 ), vector( 250, 400 ), button_font, solution_config )

        self._button_placehoder1 = c_button( self._scene_project, vector( 50, 160 ), 40, button_font, menu_icon, "Placeholder 1", self.__callback_on_press_admin )
        # self._button_placehoder2 = c_button( self._scene_project, vector( 50, 160 ), 40, button_font, menu_icon, "Placeholder 2", self.__callback_on_press_admin )

        self._button_share  = c_button( self._scene_project, vector( 50, 160 ), 40, button_font, share_icon, "Share", self.__callback_on_press_share )
        self._button_users  = c_button( self._scene_project, vector( 50, 220 ), 40, button_font, user_icon, "Users", self.__callback_on_press_users )
        self._button_logs   = c_button( self._scene_project, vector( 50, 280 ), 40, button_font, info_icon, "Logs", self.__callback_on_press_logs )

        # Utilites
        welcome_messages = [ "Welcome to the Digital Editor.", "", "Current version : 1.0 preview.", "Please select a file to start editing." ]
        for msg in welcome_messages:
            self._editor.add_line( msg )
        
        self._editor.set_event( "request_line", self.__event_editor_request_line,   "gui_editor_request_line" )
        self._editor.set_event( "discard_line", self.__event_discard_line,          "gui_editor_discard_line" ) 
        self._editor.set_event( "update_line",  self.__event_update_line,           "gui_editor_update_line" ) 
        self._editor.set_event( "delete_line",  self.__event_delete_line,           "gui_editor_delete_line" )
        
        self.__update_sidebar_elements( )

        
    def __scene_project_animate_tabs( self, event ):
        """
            Main draw function for Project Scene.

            Receive : Event object

            Returns : None
        """

        animations: c_animations    = self._scene_project.animations( )
        speed:     int              = self._scene_project_config.speed

        animations.preform( "OpenMenu", self._opened_what != 0 and 1 or 0, speed )

    
    def __scene_project_adjust_elements( self, event ):
        """
            Adjust the scene elements positions.

            Receive : Event object

            Returns : None
        """

        screen:             vector      = self._application.window_size( )
        button_menu_size:   vector      = self._button_menu.size( )
        button_files_size:  vector      = self._button_files.size( )

        animations:         c_animations    = self._scene_project.animations( )

        self._button_files.position( vector( 100 + button_menu_size.x, 50 ) )
        self._button_admin.position( vector( 150 + button_menu_size.x + button_files_size.x, 50 ) )

        opened_tab = animations.value( "OpenMenu" ) * 300

        self._editor.position( vector( 50 + opened_tab, 100 + button_menu_size.y ) )
        self._editor.size( vector( screen.x - 100 - opened_tab, screen.y - 150 - button_menu_size.y ) )

        self._button_close.position( vector( 50, screen.y - 50 - self._button_close.size( ).y ) )

    # region : Callbacks

    def __callback_on_press_menu( self ):
        """
            Callback for the menu button.

            Receive : None

            Returns : None
        """

        if self._opened_what == 1:
            self._opened_what = 0
        else:
            self._opened_what = 1

        self.__update_sidebar_elements( )

    
    def __callback_on_press_files( self ):
        """
            Callback for the files button.

            Receive : None

            Returns : None
        """

        if self._opened_what == 2:
            self._opened_what = 0
        else:
            self._opened_what = 2

        self.__update_sidebar_elements( )

    
    def __callback_on_press_admin( self ):
        """
            Callback for the admin button.

            Receive : None

            Returns : None
        """

        if self._opened_what == 3:
            self._opened_what = 0
        else:
            self._opened_what = 3

        self.__update_sidebar_elements( )

    
    def __update_sidebar_elements( self ):
        """
            Update the sidebar elements.

            Receive : None

            Returns : None
        """

        elements_visible = {
            0: [ False, False, False ],
            1: [ True, False, False ],
            2: [ False, True, False ],
            3: [ False, False, True ]
        }

        current = elements_visible[ self._opened_what ]

        self._button_close.visible(         current[ 0 ] )
        self._button_placehoder1.visible(   current[ 0 ] )

        #self._button_placehoder2.visible(   current[ 1 ] )
        self._solution_explorer.visible(    current[ 1 ] )
        
        self._button_share.visible(         current[ 2 ] )
        self._button_users.visible(         current[ 2 ] )
        self._button_logs.visible(          current[ 2 ] )
    

    def __callback_on_press_close( self ):
        """
            Callback for the close button.

            Receive : None

            Returns : None
        """

        self._logic.terminate( )
        self._application.active_scene( self._scene_setup.index( ) )


        self._temp[ "setup_proccess" ] = 0
        self._entry_username.visible( True )


    def __callback_on_press_share( self ):
        """
            Callback for the share button.

            Receive : None

            Returns : None
        """

        window_config = window_config_t( )
        window_config.show_bar      = True
        window_config.bar_title     = "Share connection"
        window_config.title_font    = self._application.font( "Button" )

        new_window = self._scene_project.create_window( vector( 300, 160 ), vector( 400, 150 ), window_config )
        
        c_button( new_window, vector( 10, 10 ), 40, self._application.font( "Button" ), self._application.image( "Copy" ), "Copy Code", lambda: glfw.set_clipboard_string( None, self._logic.generate_code( ) ) )

        render: c_renderer  = self._application.render( )
        font:   c_font      = self._application.font( "TextInput" )

        def draw_code( ):

            fade:   float       = new_window.animations( ).value( "Fade" )
            code:   str         = self._logic.generate_code( )

            render.text( font, vector( 10, 70 ), color( 255, 255, 255, 255 ) * fade, code )

        new_window.set_event( "draw", draw_code, "Draw Code", False )


    def __callback_on_press_users( self ):
        """
            Callback for the users button.

            Receive : None

            Returns : None
        """

        window_config = window_config_t( )
        window_config.show_bar      = True
        window_config.back_wallpaper = self._application.image( "Wallpaper" )

        new_window = self._scene_project.create_window( vector( 300, 160 ), vector( 320, 340 ), window_config )

        button_font:    c_font  = self._application.font( "Button" )

        list_config = list_config_t( )
        list_config.slots_count = 8
        list_config.back_color = list_config.back_color * 0

        clients_list: c_list = c_list( new_window, vector( 10, 10 ), 300, button_font, list_config )

        clients: list = self._logic.clients( )

        for client in clients:
            client: c_client_handle = client

            clients_list.add_item( client( "username" ), self._application.image( "User" ), self.__callback_on_client_click( ) )


    def __callback_on_client_click( self ):
        """
            Callback for pressing on a client.

            Receive :   None

            Returns :   Click function
        """

        font:   c_font      = self._application.font( "List" )
        render: c_renderer  = self._application.render( )
        
        
        def click_fn( username: str ):
            client: c_client_handle = self._logic.find_client( username )
            if client is None:
                return
            
            # Client window configuration
            client_window_config = window_config_t( )
            client_window_config.show_bar       = True
            client_window_config.bar_title      = username
            client_window_config.title_font     = font
            client_window_config.back_wallpaper = self._application.image( "Wallpaper" )
            
            client_info_window: c_window        = self._scene_project.create_window( vector( 400, 200 ), vector( 400, 330 ), client_window_config )
            animations:         c_animations    = client_info_window.animations( )

            files_list_config = list_config_t( )
            files_list_config.slots_count   = 3
            files_list_config.back_color    = files_list_config.back_color * 0

            files_list: c_list = c_list( client_info_window, vector( 10, 140 ), 380, font, files_list_config)

            files: list = client.files_list( )

            for file_name in files:
                files_list.add_item( file_name, self._application.image( "File" ), self.__callback_on_file_click( client ) )

            def draw_client( ):
                fade = animations.value( "Fade" )
                render.text( font, vector( 10, 10 ), color( ) * fade,   f"user  | \t{ username }" )
                render.text( font, vector( 10, 40 ), color( ) * fade,   f"trust | \t{ client.get_trust_factor( ) }" )

                render.text( font, vector( 10, 80 ), color( ) * fade,   f"file  | \t{ client.selected_file( ) }" )
                render.text( font, vector( 10, 110 ), color( ) * fade,  f"line  | \t{ client.selected_line( ) }" )

            client_info_window.set_event( "draw", draw_client, "render", False )

        return click_fn


    def __callback_on_file_click( self, client: c_client_handle ):
        """
            Callback for pressing on a file.

            Receive :   None

            Returns :   Click function
        """

        font:   c_font      = self._application.font( "List" )
        render: c_renderer  = self._application.render( )

        def click_fn( file_name: str ):

            file_data:      list    = client.get_file( file_name )
            access_level:   int     = file_data[ 1 ]

            # File window configuration
            file_window_config = window_config_t( )
            file_window_config.show_bar       = True
            file_window_config.bar_title      = file_name
            file_window_config.title_font     = font
            file_window_config.back_wallpaper = self._application.image( "Wallpaper" )
            
            file_window: c_window       = self._scene_project.create_window( vector( 400, 300 ), vector( 400, 200 ), file_window_config )
            animations:  c_animations   = file_window.animations( )

            list_config = list_config_t( )
            list_config.slots_count = 3
            list_config.back_color = list_config.back_color * 0
            list_config.check_mark  = self._application.image( "Check" )

            access_level_list: c_list = c_list( file_window, vector( 10, 10 ), 380, font, list_config )

            # FILE_ACCESS_LEVEL_HIDDEN    = 0     # This file should be hidden ( used only for host )
            # FILE_ACCESS_LEVEL_EDIT      = 1     # This file can be edited
            # FILE_ACCESS_LEVEL_LIMIT     = 2     # This file cannot be edited

            access_level_string = {
                0: "Hidden",
                1: "Edit",
                2: "Limit"
            }

            access_level_list.add_item( "Hidden",   self._application.image( "Lock" ),      lambda x: client.change_access_level( file_data[ 0 ], FILE_ACCESS_LEVEL_HIDDEN ) )
            access_level_list.add_item( "Edit",     self._application.image( "Tune" ),      lambda x: client.change_access_level( file_data[ 0 ], FILE_ACCESS_LEVEL_EDIT ) )
            access_level_list.add_item( "Limit",    self._application.image( "Visible" ),   lambda x: client.change_access_level( file_data[ 0 ], FILE_ACCESS_LEVEL_LIMIT ) )

            access_level_list.set_value( access_level_string[ access_level ] )

        return click_fn


    def __callback_on_press_logs( self ):
        """
            Callback for the logs button.

            Receive : None

            Returns : None
        """

        window_config = window_config_t( )
        window_config.show_bar      = True

        new_window = self._scene_project.create_window( vector( 300, 160 ), vector( 700, 600 ), window_config )

    # endregion

    # region : Events

    def __event_close_application( self, event ):
        """
            Event callback when the application is closed.

            Receive :
            - event - Event information

            Returns :   None
        """
        
        self._logic.terminate( )


    def __event_update_files_list( self, event ):
        """
            Event callback to update files list.

            Receive :
            - event - Event information

            Returns :   None
        """

        files: list = event( "files" )

        def add_file( file: str ):
            # I AM ACTUALLY GOING INSANE
            self._solution_explorer.add_item( file, self._logic.request_file( file ) )

        for file in files:

            add_file( file )

            # YOU CANNOT CALL THE FUNCTION DIRECTLY 
            # BECAUSE IT WILL BREAK AND ADD THE SAME CALLBACK TO ALL FILES
            # self._solution_explorer.add_item( file, lambda: print( f"Left clicked on { file }" ) )
    

    def __event_clear_editor( self, event ):
        """
            Event callback for clearing the editor.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:       str     = event( "file" )

        self._editor.clear( )
        self._editor.set_file( file )


    def __event_add_editor_line( self, event ):
        """
            Event callback for adding new line.

            Receive :
            - event - Event information

            Returns :   None
        """

        line_text:  str     = event( "line_text" )
        self._editor.add_line( line_text )

    
    def __event_editor_request_line( self, event ):
        """
            Client requests line from the server.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        self._logic.request_line( file, line )


    def __event_accept_line( self, event ):
        """
            If line is locked by host user.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        self._editor.accept_line( file, line, True )

    
    def __event_lock_line( self, event ): 
        """
            Response to lock a line.

            Receive : 
            - event - Event information

            Returns :   None
        """

        file_name:  str     = event( "file")
        line:       int     = event( "line" )

        self._editor.lock_line( line )

    
    def __event_unlock_line( self, event ):
        """
            Response from host to client in order to unlock a line.

            Receive : 
            - event - Event information

            Returns :   None
        """

        file_name:  str     = event( "file")
        line:       int     = event( "line" )

        self._editor.unlock_line( line )

    
    def __event_discard_line( self, event ):
        """
            Message to the host in order to discard line changes.

            Receive :   
            - event - Event information

            Returns :   None
        """

        file_name:  str = event( "file" )
        line:       int = event( "line" )

        self._logic.discard_line( file_name, line )


    def __event_change_lines( self, event ):
        """
            Response from host to client in order to change lines.

            Receive : 
            - event - Event information

            Returns :   None
        """

        file_name:  str     = event( "file" )
        line:       int     = event( "line" )
        new_lines:  list    = event( "new_lines" )

        self._editor.change_lines( file_name, line, new_lines )

    
    def __event_remove_line( self, event ):
        """
            Response from host to client in order to delete line.

            Receive : 
            - event - Event information

            Returns :   None
        """

        file_name:  str     = event( "file" )
        line:       int     = event( "line" )

        self._editor.delete_line( file_name, line )

    
    def __event_update_line( self, event ):
        """
            Message to the host in order to commit changes.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        lines:  list    = event( "lines" )

        self._logic.update_line( file, line, lines )

    
    def __event_delete_line( self, event ):
        """
            Message to server in order to delete a line.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        self._logic.delete_line( file, line )
    
    # region : Utilities

    # endregion

    # endregion

    def execute( self ):
        self._application.run( )