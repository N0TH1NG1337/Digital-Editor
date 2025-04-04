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
    _scene_wait:            c_scene
    _scene_project:         c_scene

    _application_config:    application_config_t
    _scene_loadup_config:   scene_config_t
    _scene_setup_config:    scene_config_t
    _scene_project_config:  scene_config_t

    _entry_project_code:    c_text_input
    # _entry_ip:              c_text_input
    # _entry_port:            c_text_input

    _registration_type:     c_side_list
    _entry_username:        c_text_input
    _entry_password:        c_text_input
    
    _button_prev_setup:     c_button
    _button_next_setup:     c_button

    _editor:                c_editor
    _buttons_bar:           c_side_list
    _button_placehoder1:    c_button

    _solution_explorer:     c_solution_explorer

    _opened_what:           int
    _temp:                  dict

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

        self._application.initialize_window( "User", vector( 50, 50 ), vector( 1300, 850 ), False )

        self.__initialize_resources( )

        self._application.initialize_events()

        self.__scene_loadup_initialize( )
        self.__scene_setup_initialize( )
        self.__scene_wait_initialize( )
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

        self._logic.set_event( "on_post_disconnect",    self.__event_post_disconnect,   "gui_post_disconnect",      False )
        self._logic.set_event( "on_register_file",      self.__event_register_file,     "gui_file_register",        True )
        self._logic.set_event( "on_file_set",           self.__event_clear_editor,      "gui_clear_editor",         True )
        self._logic.set_event( "on_file_update",        self.__event_add_editor_line,   "gui_update_editor",        True )
        self._logic.set_event( "on_accept_line",        self.__event_accept_line,       "gui_editor_accept_line",   True )
        self._logic.set_event( "on_line_lock",          self.__event_lock_line,         "gui_editor_line_lock",     True )
        self._logic.set_event( "on_line_unlock",        self.__event_unlock_line,       "gui_editor_line_unlock",   True )
        self._logic.set_event( "on_line_update",        self.__event_change_lines,      "gui_editor_line_update",   True )
        self._logic.set_event( "on_line_delete",        self.__event_remove_line,       "gui_editor_line_remove",   True )
        self._logic.set_event( "on_level_update",       self.__event_update_level,      "gui_level_update",         True )

    
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

        self._application.create_image( "Wallpaper",    execution_directory + PHOTO_WALLPAPER,      vector( 5784, 3254 ) )
        #self._application.create_image( "City",         execution_directory + PHOTO_CITY,         vector( 3150, 1816 ) )

        self._application.create_image( "Username",     execution_directory + ICON_USERNAME,        vector( 30, 30 ) )
        self._application.create_image( "Password",     execution_directory + ICON_PASSWORD,        vector( 30, 30 ) )
        self._application.create_image( "Next",         execution_directory + ICON_NEXT,            vector( 30, 30 ) )
        self._application.create_image( "Prev",         execution_directory + ICON_PREV,            vector( 30, 30 ) )

        self._application.create_image( "Folder",       execution_directory + ICON_FOLDER,          vector( 30, 30 ) )
        self._application.create_image( "File",         execution_directory + ICON_FILE,            vector( 30, 30 ) )

        self._application.create_image( "Code",         execution_directory + ICON_PORT,            vector( 30, 30 ) )
        self._application.create_image( "Copy",         execution_directory + ICON_COPY,            vector( 30, 30 ) )

        self._application.create_image( "Menu",         execution_directory + ICON_MENU,            vector( 40, 40 ) )
        self._application.create_image( "Files",        execution_directory + ICON_FILES,           vector( 40, 40 ) )
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
        version:        str             = "User"

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
        animations.prepare( "Connection",   vector( ) )
        animations.prepare( "Registration", vector( ) )
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

        text_font:      c_font  = self._application.font( "TextInput" )
        button_font:    c_font  = self._application.font( "Button" )
        list_font:      c_font  = self._application.font( "List" )

        username_icon:      c_image = self._application.image( "Username" )
        password_icon:      c_image = self._application.image( "Password" )
        code_icon:          c_image = self._application.image( "Code" )

        next_icon:      c_image = self._application.image( "Next" )
        prev:           c_image = self._application.image( "Prev" )

        self._entry_project_code = c_text_input( self._scene_setup, vector( 50, 120 ), 40, vector( 200, 30 ), text_font, code_icon, "project code" )

        self._registration_type  = c_side_list( self._scene_setup, vector( 50, 120 ), 400, list_font )
        self._entry_username     = c_text_input( self._scene_setup, vector( 50, 180 ), 40, vector( 200, 30 ), text_font, username_icon, "username" )
        self._entry_password     = c_text_input( self._scene_setup, vector( 50, 240 ), 40, vector( 200, 30 ), text_font, password_icon, "password" )

        self._button_prev_setup = c_button( self._scene_setup, vector( 50, 250 ),   40, button_font, prev,      "Previous", self.__scene_setup_previous_step )
        self._button_next_setup = c_button( self._scene_setup, vector( 100, 250 ),  40, button_font, next_icon, "Next",     self.__scene_setup_next_step )

        self._entry_username.visible( False )
        self._entry_password.visible( False )
        self._registration_type.visible( False )

        self._registration_type.add_item( "Register",   None, None )
        self._registration_type.add_item( "Login",      None, None )
        self._registration_type.set_value( "Register" )


    @safe_call( c_debug.log_error )
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
        pad:        int             = 30

        steps = {
            0: "Connection",
            1: "Registration"
        }

        width:      float = pad
        for index in steps:
            size: vector = render.measure_text( steps_font, steps[ index ] )
            width += size.x + pad

        render.shadow( vector( 50, 50 ), vector( 50 + width, 100 ), color( 0, 0, 0, 100 ), fade, 20, 10 )
        render.rect( vector( 50, 50 ), vector( 50 + width, 100 ), color( 0, 0, 0, 100 * fade ), 10 )

        offset:     float = pad
        progress:   float = 0

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
            current_color = color( ).linear( color( 216, 208, 215, 255 ), values.y ) * values.x

            render.text( steps_font, vector( 50 + offset, 60 ), current_color, step )

            offset += step_size.x + pad

        render.shadow( vector( 80, 90 ), vector( 50 + progress, 90 ), color( 216, 208, 215, 255 ), fade, 25 )
        render.line( vector( 80, 90 ), vector( 50 + progress, 90 ), color( 216, 208, 215, 255 ) * fade )


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

        self._temp[ "setup_proccess" ] = math.clamp( self._temp[ "setup_proccess" ] + 1, 0, 2 ) 

        if self._temp[ "setup_proccess" ] == 1 and self._entry_project_code.get( ) == "":
            self._temp[ "setup_proccess" ] = 0
            # Show warning
            return

        self.__scene_setup_update( )

        if self._temp[ "setup_proccess" ] == 2:
            self.__project_start( )
            return
    

    def __scene_setup_previous_step( self ):
        """
            Previous setup step.

            Receive :   None

            Returns :   None
        """

        self._temp[ "setup_proccess" ] = math.clamp( self._temp[ "setup_proccess" ] - 1, 0, 2 ) 

        self.__scene_setup_update( )

    
    @safe_call( c_debug.log_error )
    def __scene_setup_update( self ):
        
        process_index = self._temp[ "setup_proccess" ]

        changes = {
            0: [ True, False  ],
            1: [ False, True ],
            2: [ False, False ]
        }

        if process_index not in changes:
            return
        
        current_changes = changes[ process_index ]

        self._entry_project_code.visible( current_changes[ 0 ] )
        self._entry_username.visible( current_changes[ 1 ] )
        self._entry_password.visible( current_changes[ 1 ] )
        self._registration_type.visible( current_changes[ 1 ] )
        
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

        result: bool = self._logic.connect( 
            self._entry_project_code.get( ),
            self._entry_username.get( ),
            self._entry_password.get( ),
            self._registration_type.get( )
        )
    
        if result:
            time.sleep( LOADING_MIN_TIME )
            self._application.active_scene( self._scene_project.index( ) )

        else:

            self.__show_error_message( self._logic( "last_error" ), self._scene_setup )
            time.sleep( LOADING_MIN_TIME )
            self._application.active_scene( self._scene_setup.index( ) )
        

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
        list_font:      c_font  = self._application.font( "List" )

        file_icon:      c_image = self._application.image( "Folder" )
        close_icon:     c_image = self._application.image( "Prev" )

        solution_config = solution_explorer_config_t( )
        solution_config.folder_icon = self._application.image( "Folder" )
        solution_config.item_icon   = self._application.image( "File" )

        top_bar_config = list_config_t( )
        top_bar_config.disable_pressed = True

        self._editor            = c_editor( self._scene_project, vector( 50, 100 ), vector( 1000, 760 ), editor_font )
        self._buttons_bar       = c_side_list( self._scene_project, vector( 50, 50 ), 300, list_font, top_bar_config )
        self._solution_explorer = c_solution_explorer( self._scene_project, vector( 50, 160 ), vector( 250, 400 ), button_font, solution_config )

        # Utilites
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

        animations:         c_animations    = self._scene_project.animations( )

        opened_tab = animations.value( "OpenMenu" ) * 300

        self._editor.position( vector( 50 + opened_tab, 150 ) )
        self._editor.size( vector( screen.x - 100 - opened_tab, screen.y - 200 ) )

    # endregion

    # region : Callbacks
    
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
            After client successfuly disconnect.

            Receive :   
            - event - Event information

            Returns :   None
        """

        self._application.active_scene( self._scene_setup.index( ) )

        self._temp[ "setup_proccess" ] = 0
        self._solution_explorer.clear( )
        self._editor.clear( )
        self._editor.discard_action( )
        self.__scene_setup_update( )

    
    def __event_register_file( self, event ):
        """
            After client successfuly register.

            Receive :   
            - event - Event information

            Returns :   None
        """

        file_name:      str = event( "file_name" )

        self._solution_explorer.add_item( file_name, lambda: self._logic.request_file( file_name ) )

    
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
    

    def __event_update_level( self, event ):
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

        big_font:   c_font      = self._application.font( "SubTitle" )
        font:       c_font      = self._application.font( "TextInput" )

        icon_copy:  c_image     = self._application.image( "Copy" )

        c_icon_button( new_window, vector( 430, 10 ), icon_copy, lambda: glfw.set_clipboard_string( None, message ) )

        def draw( event ):

            fade:   float       = new_window.animations( ).value( "Fade" )

            render.push_clip_rect( vector( ), vector( 500, 300 ) )
            render.text( big_font, vector( 10, 10 ), color( ) * fade, "Error occured" )
            render.text( font, vector( 10, 80 ), color( 180, 180, 180 ) * fade, render.wrap_text( font, message, 480 ) )
            render.pop_clip_rect( )

        new_window.set_event( "draw", draw, "ErrorMessageDraw" )

    # endregion

    def execute( self ):
        self._application.run( )
        