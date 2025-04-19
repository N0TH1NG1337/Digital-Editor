"""
    project     : Digital Editor

    type:       : User
    file        : Graphical User Interface

    description : User GUI class
"""

from user.business_logic        import *
from user_interface.application import *
from utilities.paths            import *
from utilities.debug            import *

LOADING_MIN_TIME = 2

class c_user_gui:

    # region : Privates attributes

    _application:           c_application
    _logic:                 c_user_business_logic

    _scene_loadup:          c_scene
    _scene_setup:           c_scene
    _scene_project:         c_scene

    _application_config:    application_config_t
    _scene_loadup_config:   scene_config_t
    _scene_setup_config:    scene_config_t
    _scene_project_config:  scene_config_t

    _entry_project_code:    c_text_input

    _registration_type:     c_side_list
    _entry_username:        c_text_input
    _entry_password:        c_text_input
    
    _button_next_setup:     c_button

    _editor:                c_editor
    _buttons_bar:           c_side_list

    _solution_explorer:     c_solution_explorer

    _opened_what:           int
    _temp:                  dict

    _general_font:          c_font

    # endregion

    # region : Initialization

    def __init__( self, should_debug: bool = False ):
        """
            Default constructor for the user interface.

            Receive :   
            - should_debug [optional] - Should enable debug logging

            Returns :   User GUI object
        """

        if should_debug:
            c_debug.load_basic_debugging( "user_debug.log" )

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

        self._application.initialize_window( "digital-editor user", vector( 50, 50 ), vector( 1300, 850 ), True )

        self.__initialize_resources( )

        self._application.initialize_events()

        self.__scene_loadup_initialize( )
        self.__scene_setup_initialize( )
        self.__scene_project_initialize( )


    def __initialize_logic( self ):
        """
            Initialize the logic object.

            Receive : None

            Returns : None
        """

        self._logic = c_user_business_logic( )

        self.__initialize_logic_callbacks( )

    
    def __initialize_logic_callbacks( self ):
        """
            Initialize user business logic callbacks.

            Receive :   None

            Returns :   None
        """

        self._logic.set_event( "on_post_disconnect",    self.__event_post_disconnect,       "gui_post_disconnect",      False )
        self._logic.set_event( "on_register_files",     self.__event_register_files,        "gui_files_register",       False )
        self._logic.set_event( "on_file_set",           self.__event_clear_editor,          "gui_clear_editor",         True )
        self._logic.set_event( "on_file_update",        self.__event_add_editor_line,       "gui_update_editor",        True )
        self._logic.set_event( "on_accept_line",        self.__event_accept_line,           "gui_editor_accept_line",   True )
        self._logic.set_event( "on_line_lock",          self.__event_lock_line,             "gui_editor_line_lock",     True )
        self._logic.set_event( "on_line_unlock",        self.__event_unlock_line,           "gui_editor_line_unlock",   True )
        self._logic.set_event( "on_line_update",        self.__event_change_lines,          "gui_editor_line_update",   True )
        self._logic.set_event( "on_line_delete",        self.__event_remove_line,           "gui_editor_line_remove",   True )
        self._logic.set_event( "on_file_register",      self.__event_file_register,         "gui_file_register",        True )
        self._logic.set_event( "on_file_rename",        self.__event_file_rename,           "gui_file_rename",          True )

        self._application.set_event( "unload",          self.__disconnect_on_window_close,  "gui_fast_unload",          False )

    
    def __initialize_resources( self ):
        """
            Initialize the resources for the application.

            Receive : None

            Returns : None
        """

        execution_directory = os.getcwd( )

        self._general_font = self._application.create_font( "general", FONT, 20 )

        self._application.create_image( "WallpaperBlur",    execution_directory + PHOTO_WALLPAPER,      vector( 5784, 3254 ), [IMAGE_FILTER_BLUR] )
        self._application.create_image( "Wallpaper",        execution_directory + PHOTO_WALLPAPER,      vector( 5784, 3254 ) )

        self._application.create_image( "Username",         execution_directory + ICON_USERNAME,        vector( 30, 30 ) )
        self._application.create_image( "Password",         execution_directory + ICON_PASSWORD,        vector( 30, 30 ) )
        self._application.create_image( "Next",             execution_directory + ICON_NEXT,            vector( 30, 30 ) )
        self._application.create_image( "Prev",             execution_directory + ICON_PREV,            vector( 30, 30 ) )

        self._application.create_image( "Folder",           execution_directory + ICON_FOLDER,          vector( 30, 30 ) )
        self._application.create_image( "File",             execution_directory + ICON_FILE,            vector( 30, 30 ) )

        self._application.create_image( "Code",             execution_directory + ICON_PORT,            vector( 30, 30 ) )
        self._application.create_image( "Copy",             execution_directory + ICON_COPY,            vector( 30, 30 ) )

        self._application.create_image( "TitleWelcome",     execution_directory + TITLE_ICON_WELCOME,   vector( 700, 200 ) )

        self._application.create_image( "TitleConnection",  execution_directory + TITLE_ICON_CONNECTION,vector( 500, 170 ) )
        self._application.create_image( "TitleLoading",     execution_directory + TITLE_ICON_LOADING,   vector( 500, 170 ) )

        self._temp[ "setup_process" ]  = 0
        
        self._application_config.wallpaper = self._application.image( "WallpaperBlur" )

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

        self._scene_loadup.set_event( "draw",           self.__scene_loadup_draw,   "Scene Loadup Draw Main", False )
        self._scene_loadup.set_event( "mouse_input",    self.__scene_loadup_update, "Scene Loadup Update", True )
        self._scene_loadup.set_event( "keyboard_input", self.__scene_loadup_update, "Scene Loadup Update", True )

    
    def __scene_loadup_draw( self ):
        """
            Main draw function for Loadup Scene.

            Receive : Event object

            Returns : None
        """

        render:         c_renderer      = self._application.render( )
        animations:     c_animations    = self._scene_loadup.animations( )

        fade:           float           = animations.value( "Fade" )
        screen:         vector          = self._application.window_size( )

        img:            c_image         = self._application.image( "TitleWelcome" )
        img_size:       vector          = img.size( )

        image_pos:      vector  = ( screen - img_size ) / 2

        render.image( img, image_pos, color( ) * fade )


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
        animations.prepare( "TitleConnection",  vector( ) )
        animations.prepare( "TitleLoading",     vector( ) )

        animations.prepare( "ButtonNext",   250 )
        animations.prepare( "InstructionsHeight", 0 )

        self._scene_setup.set_event( "draw",            self.__scene_setup_draw,                "Scene Setup Draw Main",            False )
        self._scene_setup.set_event( "draw",            self.__scene_setup_draw_instructions,   "Scene Setup Draw Instructions",    False )
        self._scene_setup.set_event( "draw",            self.__scene_setup_adjust_elements,     "Scene Setup Adjust Elements",      False )
        self._scene_setup.set_event( "keyboard_input",  self.__scene_setup_control_steps,       "Scene Setup Control Elements",     False )

    
    def __scene_setup_initialize_elements( self ):
        """
            Setup the elements for the Setup Scene.

            Receive : None

            Returns : None
        """

        username_icon:      c_image = self._application.image( "Username" )
        password_icon:      c_image = self._application.image( "Password" )
        code_icon:          c_image = self._application.image( "Code" )
        next_icon:          c_image = self._application.image( "Next" )

        text_input_config                       = text_input_config_t( )
        text_input_config.color_background.a    = 0
        text_input_config.color_shadow          = color( 29, 29, 29, 0 )

        buttons_config              = button_config_t( )
        buttons_config.back_color   = color( 29, 29, 29 )

        list_config             = list_config_t( )
        list_config.back_color  = color( 29, 29, 29, 0 )

        self._entry_project_code = c_text_input( self._scene_setup, vector( 50, 120 ), 40, vector( 200, 30 ), self._general_font, code_icon, "project code", "", False, text_input_config )

        self._registration_type  = c_side_list( self._scene_setup, vector( 50, 120 ), 400, self._general_font, list_config )
        self._entry_username     = c_text_input( self._scene_setup, vector( 50, 180 ), 40, vector( 200, 30 ), self._general_font, username_icon, "username", "", False, text_input_config )
        self._entry_password     = c_text_input( self._scene_setup, vector( 50, 240 ), 40, vector( 200, 30 ), self._general_font, password_icon, "password", "", True, text_input_config )

        self._button_next_setup  = c_button( self._scene_setup, vector( 100, 250 ),  40, self._general_font, next_icon, "Next", self.__scene_setup_next_step, buttons_config )

        self.__scene_setup_update( )

        self._registration_type.add_item( "Register",   None, None )
        self._registration_type.add_item( "Login",      None, None )
        self._registration_type.set_value( "Register" )


    def __scene_setup_draw( self ):
        """
            Main draw function for Setup Scene.

            Receive : Event object

            Returns : None
        """

        wallpaper:  c_image         = self._application.image( "Wallpaper" )
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
            0: "TitleConnection",
            1: "TitleLoading"
        }

        selected:           int = self._temp[ "setup_process" ]
        
        for index in steps:
            step: str = steps[ index ]

            image:      c_image = self._application.image( step )
            alpha_step: float   = ( selected == index and 1 or 0 ) * fade
                
            wanted_value:   vector  = vector( ( 1 - alpha_step ) * 50, alpha_step )
            values:         vector  = animations.perform( step, wanted_value, speed )

            image_size: vector = image.size( )
            render.image( image, vector( screen.x * 0.3 - image_size.x / 2 - values.x, start_box.y + 10 ), color( ) * values.y )

    
    def __scene_setup_draw_instructions( self ):

        screen:     vector          = self._application.window_size( )

        start_buttons_x = screen.x * 0.5 + 20
        start_widgets_y = screen.y * 0.1 + 20

        render:     c_renderer      = self._application.render( )
        animations: c_animations    = self._scene_setup.animations( )

        fade:       float           = animations.value( "Fade" ) * animations.value( "TitleConnection" ).y

        # Render the instructions here
        wrapped_text: str = render.wrap_text( self._general_font, "Enter the project code that you received from a host", screen.x * 0.4 - 40 )
        render.text( self._general_font, vector( start_buttons_x, start_widgets_y ), color( ) * fade, wrapped_text )

        # By the way update the height of the instructions
        animations.value( "InstructionsHeight", render.measure_text( self._general_font, wrapped_text ).y + 40 )


    def __scene_setup_adjust_elements( self ):
        """
            Adjust the scene elements positions.

            Receive : Event object

            Returns : None
        """

        animations: c_animations    = self._scene_setup.animations( )
        screen:     vector          = self._application.window_size( )

        speed:      int             = self._scene_setup_config.speed
        
        button_next_drop: float = animations.perform( "ButtonNext", screen.y * 0.9 - 20 - 40, speed )

        start_buttons_x = screen.x * 0.5 + 20
        start_widgets_y = screen.y * 0.1 + animations.value( "InstructionsHeight" )

        self._button_next_setup.position( vector( screen.x * 0.9 - 20 - self._button_next_setup.size( ).x, button_next_drop ) )

        self._entry_project_code.position( vector( start_buttons_x, start_widgets_y ) )

        self._entry_username.position( vector( start_buttons_x, start_widgets_y + 180 ) )
        self._entry_password.position( vector( start_buttons_x, start_widgets_y + 240 ) )

        self._registration_type.position( vector( start_buttons_x, start_widgets_y + 120 ) )
        self._registration_type.width( screen.x * 0.4 - 40 )


    def __scene_setup_control_steps( self ):

        progress_index: int = self._temp[ "setup_process" ]
        if progress_index == 0:
            # Connections

            if self._entry_project_code.get( ) != "":
                self._entry_username.visible( True )
                self._entry_password.visible( True )
                self._registration_type.visible( True )

            is_username_valid, reason = c_registration.validate_username( self._entry_username.get( ) )
            is_password_valid, reason = c_registration.validate_password( self._entry_password.get( ) )

            # I want to avoid updating each frame...
            new_value: bool = is_username_valid and is_password_valid
            if self._button_next_setup.visible( ) != new_value:
                self._button_next_setup.visible( new_value )
    

    def __scene_setup_next_step( self ):
        """
            Next setup step.

            Receive :   None

            Returns :   None
        """

        self._temp[ "setup_process" ] = math.clamp( self._temp[ "setup_process" ] + 1, 0, 1 )

        self.__scene_setup_update( )

        if self._temp[ "setup_process" ] == 1:
            return self.__project_start( )

    
    @safe_call( c_debug.log_error )
    def __scene_setup_update( self ):
        
        process_index = self._temp[ "setup_process" ]

        changes = {
            0: True,
            1: False
        }

        if process_index not in changes:
            return
        
        current_changes = changes[ process_index ]

        self._entry_project_code.visible(   current_changes )

        self._button_next_setup.visible(    False )
        self._registration_type.visible(    False )
        self._entry_username.visible(       False )
        self._entry_password.visible(       False )
        
    # endregion

    # region : Scene Project

    @standalone_execute
    def __project_start( self ):
        """
            Start the hosting program.

            Receive : None

            Returns : None
        """

        time.sleep( LOADING_MIN_TIME )

        result: bool = self._logic.connect( 
            self._entry_project_code.get( ),
            self._entry_username.get( ),
            self._entry_password.get( ),
            self._registration_type.get( )
        )
    
        if result:
            time.sleep( LOADING_MIN_TIME )
            self._application.active_scene( self._scene_project.index( ) )

            self._application.maximize_window( )
        else:
            self.__show_error_message( self._logic( "last_error" ), self._scene_setup )
            self._temp[ "setup_process" ] = 0
            
            self.__scene_setup_control_steps( )
        

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

        self._scene_project.set_event( "draw", self.__scene_project_animate_tabs,       "Scene Project Animate Tabs",       False )
        self._scene_project.set_event( "draw", self.__scene_project_adjust_elements,    "Scene Project Adjust Elements",    False )


    def __scene_project_initialize_elements( self ):
        """
            Setup the elements for the Project Scene.

            Receive : None

            Returns : None
        """

        file_icon:      c_image = self._application.image( "Folder" )
        close_icon:     c_image = self._application.image( "Prev" )

        solution_config             = solution_explorer_config_t( )
        solution_config.folder_icon = self._application.image( "Folder" )
        solution_config.item_icon   = self._application.image( "File" )

        top_bar_config                  = list_config_t( )
        top_bar_config.disable_pressed  = True

        self._editor            = c_editor( self._scene_project, vector( 50, 100 ), vector( 1000, 760 ), self._general_font )
        self._buttons_bar       = c_side_list( self._scene_project, vector( 50, 50 ), 300, self._general_font, top_bar_config )
        self._solution_explorer = c_solution_explorer( self._scene_project, vector( 50, 140 ), vector( 250, 400 ), self._general_font, solution_config )

        # Utilities
        self._editor.clear( )
        self._editor.open_file( "Welcome" )
        welcome_messages = [ "Welcome to the Digital Editor.", "", "Current version : 1.0 preview.", "Please select a file to start editing." ]
        for msg in welcome_messages:
            self._editor.add_line( msg )

        self._editor.read_only( True )

        self._buttons_bar.add_item( "Files", file_icon,  self.__callback_on_press_files )
        self._buttons_bar.add_item( "Exit",  close_icon, self.__callback_on_press_close )

        self._editor.set_event( "request_line",     self.__event_editor_request_line,   "gui_editor_request_line" )
        self._editor.set_event( "discard_line",     self.__event_discard_line,          "gui_editor_discard_line" ) 
        self._editor.set_event( "update_line",      self.__event_update_line,           "gui_editor_update_line" ) 
        self._editor.set_event( "delete_line",      self.__event_delete_line,           "gui_editor_delete_line" )
        self._editor.set_event( "correct_offset",   self.__event_verify_offset,         "gui_editor_correct_offset" )
        
        self.__update_sidebar_elements( )
    

    def __scene_project_animate_tabs( self ):
        """
            Main draw function for Project Scene.

            Receive : Event object

            Returns : None
        """

        animations: c_animations    = self._scene_project.animations( )
        speed:      int             = self._scene_project_config.speed

        animations.perform( "OpenMenu", self._opened_what != 0 and 300 or 0, speed, 1 )

    
    def __scene_project_adjust_elements( self ):
        """
            Adjust the scene elements positions.

            Receive : Event object

            Returns : None
        """

        screen:     vector          = self._application.window_size( )
        animations: c_animations    = self._scene_project.animations( )

        opened_tab: float           = animations.value( "OpenMenu" )

        self._editor.position( vector( 50 + opened_tab, 140 ) )
        self._editor.size( vector( screen.x - 100 - opened_tab, screen.y - 190 ) )

    # endregion

    # region : Callbacks
    
    def __update_sidebar_elements( self ):
        """
            Update the sidebar elements.

            Receive : None

            Returns : None
        """

        elements_visible = {
            0: [ False ],
            1: [ True ],

        }

        current = elements_visible[ self._opened_what ]

        self._solution_explorer.visible( current[ 0 ] )
    

    def __callback_on_press_files( self, _ ):
        """
            Callback for the files button.

            Receive : None

            Returns : None
        """

        if self._opened_what == 1:
            self._opened_what = 0
        else:
            self._opened_what = 1

        self.__update_sidebar_elements( )
       

    def __callback_on_press_close( self, _ ):
        """
            Callback for the close button.

            Receive : None

            Returns : None
        """

        self._logic.disconnect( )
        
    # endregion

    # region : Events

    def __event_post_disconnect( self ):
        """
            After client successfully disconnect.

            Receive :   
            - event - Event information

            Returns :   None
        """

        self._editor.discard_action( )

        self._solution_explorer.clear( )
        self._editor.clear( )

        self._application.active_scene( self._scene_setup.index( ) )

        self._temp[ "setup_process" ] = 0
        self.__scene_setup_update( )

    
    def __event_register_files( self ):
        """
            After client successfully register new files.

            Receive :   
            - event - Event information

            Returns :   None
        """

        self._solution_explorer.clear( )

    
    def __event_clear_editor( self, event ):
        """
            Event callback for clearing the editor.

            Receive :   None

            Returns :   None
        """

        file:           str     = event( "file" )
        read_only:      bool     = event( "read_only" )

        self._editor.discard_action( )
        self._editor.clear( )
        self._editor.open_file( file )
        self._editor.read_only( read_only )


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
            Response from the host if the line can be used by us.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )
        accept: bool    = event( "accept" )

        self._editor.accept_line( file, line, accept )

    
    def __event_lock_line( self, event ): 
        """
            Response from host to client in order to lock a line.

            Receive : 
            - event - Event information

            Returns :   None
        """

        line:       int     = event( "line" )
        user:       str     = event( "user" )

        self._editor.lock_line( line, user )

    
    def __event_unlock_line( self, event ):
        """
            Response from host to client in order to unlock a line.

            Receive : 
            - event - Event information

            Returns :   None
        """

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

        lines.clear( )

    
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

    
    def __event_verify_offset( self, event ):
        """
            Response to host, after a line offset change.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:   str = event( "file" )
        offset: int = event( "offset" )

        self._logic.accept_offset( file, offset )
    

    def __event_file_register( self, event ):
        """
            Update the access level of a file.

            Receive :
            - event - Event information

            Returns :   None
        """

        file_name:      str = event( "file" )
        access_level:   int = event( "access_level" )

        if access_level == FILE_ACCESS_LEVEL_HIDDEN:

            # We need to check a few things, first the editor...
            if self._editor.open_file( ) == file_name:
                # Stop any actions from the user
                self._editor.discard_action( )

                # Clear editor
                self._editor.clear( )

            # Now delete the file from the solution explorer
            return self._solution_explorer.remove_item( file_name )

        # If the file is not in the solution explorer, add it
        if not self._solution_explorer.has_item( file_name ):
            self._solution_explorer.add_item( file_name, lambda: self._logic.request_file( file_name ) )

        if access_level == FILE_ACCESS_LEVEL_LIMIT:

            if self._editor.open_file( ) == file_name:
                # Stop any actions from the user
                self._editor.discard_action( )
                self._editor.read_only( True )
            
            return
            
        if access_level == FILE_ACCESS_LEVEL_EDIT:

            if self._editor.open_file( ) == file_name:
                self._editor.read_only( False )

    
    def __event_file_rename( self, event ):
        
        old_index: str = event( "old_index" )
        new_index: str = event( "new_index" )

        if not self._solution_explorer.has_item( old_index ):
            return
        
        self._solution_explorer.remove_item( old_index )
        self._solution_explorer.add_item( new_index )

        self._editor.open_file( new_index )

        self._logic.accept_file_rename( old_index, new_index )

    # endregion

    # region : Utilities

    def __show_error_message( self, message: str, scene: c_scene ):
        """
            Create and attach error message to a scene.

            Receive :
            - message - Error message
            - scene_index - Scene index to attach the error screen

            Returns :   None
        """

        size:   vector = vector( 500, 250 )
        screen: vector = self._application.window_size( ) / 2

        error_window_config = window_config_t( )
        error_window_config.show_bar = True

        new_window = scene.create_window( screen - ( size / 2 ), size, error_window_config )

        render: c_renderer  = self._application.render( )

        icon_copy:  c_image     = self._application.image( "Copy" )

        c_icon_button( new_window, vector( 430, 10 ), icon_copy, lambda: glfw.set_clipboard_string( None, message ) )

        def draw( event ):

            fade:   float       = new_window.animations( ).value( "Fade" )

            render.push_clip_rect( vector( ), vector( 500, 300 ) )
            render.text( self._general_font, vector( 10, 10 ), color( ) * fade, "Error occurred" )
            render.text( self._general_font, vector( 10, 80 ), color( 180, 180, 180 ) * fade, render.wrap_text( self._general_font, message, 480 ) )
            render.pop_clip_rect( )

        new_window.set_event( "draw", draw, "ErrorMessageDraw" )


    def __disconnect_on_window_close( self ):

        if self._logic( "is_connected" ):
            self._logic.disconnect( )

    # endregion

    def execute( self ):
        self._application.run( )
        