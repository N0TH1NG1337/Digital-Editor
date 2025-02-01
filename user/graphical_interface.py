"""
    project     : Digital Editor

    type:       : User
    file        : Graphical User Interface

    description : User GUI class
"""

from user.business_logic        import *
from user_interface.application import *
from utilities.paths            import *

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
    _button_menu:           c_icon_button
    _button_files:          c_icon_button

    _button_close:          c_icon_button
    _button_placehoder1:    c_button

    _solution_explorer:     c_solution_explorer

    _opened_what:           int
    _temp:                  dict

    # endregion

    # region : Initialization

    def __init__( self ):
        """
            Default constructor for the user interface.

            Receive :   None

            Returns :   User GUI object
        """

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

        self._logic.set_event( "on_post_disconnect",    self.__event_post_disconnect,   "gui_post_disconnect",  False )
        self._logic.set_event( "on_register_file",      self.__event_register_file,     "gui_file_register",    True )
        self._logic.set_event( "on_file_set",           self.__event_clear_editor,      "gui_clear_editor",     False )
        self._logic.set_event( "on_file_update",        self.__event_add_editor_line,   "gui_update_editor",    True )

    
    def __initialize_resources( self ):
        """
            Initialize the resources for the application.

            Receive : None

            Returns : None
        """

        execution_directory = os.getcwd( )
        self._application.create_font( "Title",     FONT, 100 )
        self._application.create_font( "SubTitle",  FONT, 50 )
        self._application.create_font( "Steps",     FONT, 20 )
        self._application.create_font( "Button",    FONT, 20 )
        self._application.create_font( "TextInput", FONT, 20 )
        self._application.create_font( "Path",      FONT, 20 )
        self._application.create_font( "List",      FONT, 20 )
        self._application.create_font( "Editor",    FONT_THIN, 20 )

        self._application.create_image( "Wallpaper",    execution_directory + PHOTO_WALLPAPER,    vector( 3840, 2160 ) )
        self._application.create_image( "City",         execution_directory + PHOTO_CITY,         vector( 3150, 1816 ) )

        self._application.create_image( "Cloud",        execution_directory + ICON_CLOUD,         vector( 200, 200 ) )
        self._application.create_image( "Folders",      execution_directory + ICON_FOLDERS,       vector( 200, 200 ) )
        self._application.create_image( "Connection",   execution_directory + ICON_CONNECTION,    vector( 200, 200 ) )
        self._application.create_image( "User",         execution_directory + ICON_USER,          vector( 40, 40 ) )
        self._application.create_image( "Next",         execution_directory + ICON_NEXT,          vector( 40, 40 ) )
        self._application.create_image( "Check",        execution_directory + ICON_CHECK,         vector( 40, 40 ) )
        self._application.create_image( "Edit",         execution_directory + ICON_EDIT,          vector( 40, 40 ) )
        self._application.create_image( "Visible",      execution_directory + ICON_VISIBLE,       vector( 40, 40 ) )
        self._application.create_image( "Close",        execution_directory + ICON_CLOSE,         vector( 40, 40 ) )
        self._application.create_image( "Listen",       execution_directory + ICON_LISTEN,        vector( 40, 40 ) )
        self._application.create_image( "NetMan",       execution_directory + ICON_NET_MAN,       vector( 40, 40 ) )
        self._application.create_image( "Copy",         execution_directory + ICON_COPY,          vector( 40, 40 ) )
        self._application.create_image( "Back",         execution_directory + ICON_BACK,          vector( 40, 40 ) )
        self._application.create_image( "Folder",       execution_directory + ICON_FOLDER,        vector( 40, 40 ) )
        self._application.create_image( "File",         execution_directory + ICON_FILE,          vector( 40, 40 ) )
        self._application.create_image( "Menu",         execution_directory + ICON_MENU,          vector( 40, 40 ) )

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

        self._scene_loadup = self._application.new_scene( self._scene_loadup_config )

        self._scene_loadup.set_event( "draw",           self.__scene_loadup_draw,   "Scene Loadup Draw Main" )
        self._scene_loadup.set_event( "mouse_input",    self.__scene_loadup_update, "Scene Loadup Update" )

    
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

        if event( "action" ) == glfw.PRESS and event( "button" ) == glfw.MOUSE_BUTTON_LEFT:
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

        user_icon:      c_image = self._application.image( "User" )
        next_icon:      c_image = self._application.image( "Next" )
        close_icon:     c_image = self._application.image( "Close" )

        self._entry_project_code = c_text_input( self._scene_setup, vector( 50, 100 ), 40, vector( 200, 30 ), user_icon, text_font, "project code" )

        self._registration_type  = c_side_list( self._scene_setup, vector( 50, 100 ), 400, list_font )
        self._entry_username     = c_text_input( self._scene_setup, vector( 50, 160 ), 40, vector( 200, 30 ), user_icon, text_font, "username" )
        self._entry_password     = c_text_input( self._scene_setup, vector( 50, 220 ), 40, vector( 200, 30 ), user_icon, text_font, "password", True )

        self._button_prev_setup = c_button( self._scene_setup, vector( 50, 250 ),   40, button_font, close_icon, "Previous", self.__scene_setup_previous_step )
        self._button_next_setup = c_button( self._scene_setup, vector( 100, 250 ),  40, button_font, next_icon,  "Next",     self.__scene_setup_next_step )

        self._entry_username.visible( False )
        self._entry_password.visible( False )
        self._registration_type.visible( False )

        self._registration_type.add_item( "Register",   None, None )
        self._registration_type.add_item( "Login",      None, None )
        self._registration_type.set_value( "Register" )


    @safe_call( print )
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
            0: "Connection",
            1: "Registration"
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

    
    @safe_call( print )
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

        # TODO ! Start the user program
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

        menu_icon:      c_image = self._application.image( "Menu" )
        file_icon:      c_image = self._application.image( "File" )
        admin_icon:     c_image = self._application.image( "User" )
        close_icon:     c_image = self._application.image( "Close" )
        copy_icon:      c_image = self._application.image( "Copy" )

        solution_config = solution_explorer_config_t( )

        solution_config.folder_icon = self._application.image( "Folder" )
        solution_config.item_icon   = self._application.image( "File" )

        self._editor        = c_editor( self._scene_project, vector( 50, 100 ), vector( 1000, 760 ), editor_font )

        self._button_menu   = c_icon_button( self._scene_project, vector( 50, 50 ), menu_icon, self.__callback_on_press_menu )
        self._button_files  = c_icon_button( self._scene_project, vector( 100, 50 ), file_icon, self.__callback_on_press_files )

        self._button_close  = c_icon_button( self._scene_project, vector( 50, 1000 ), close_icon, self.__callback_on_press_close )

        self._button_placehoder1 = c_button( self._scene_project, vector( 50, 160 ), 40, button_font, menu_icon, "Placeholder 1", None )
        #self._button_placehoder2 = c_button( self._scene_project, vector( 50, 160 ), 40, button_font, menu_icon, "Placeholder 2", None )

        self._solution_explorer = c_solution_explorer( self._scene_project, vector( 50, 160 ), vector( 250, 600 ), button_font, solution_config )

        # Utilites
        self._editor.add_line( "Welcome to the Digital Editor" )
        self._editor.set_event( "request_line", self.__event_editor_request_line, "gui_editor_request_line" )
        
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

        opened_tab = animations.value( "OpenMenu" ) * 300

        self._editor.position( vector( 50 + opened_tab, 100 + button_menu_size.y ) )
        self._editor.size( vector( screen.x - 100 - opened_tab, screen.y - 150 - button_menu_size.y ) )

        self._button_close.position( vector( 50, screen.y - 50 - self._button_close.size( ).y ) )

    # endregion

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

    
    def __update_sidebar_elements( self ):
        """
            Update the sidebar elements.

            Receive : None

            Returns : None
        """

        elements_visible = {
            0: [ False, False ],
            1: [ True, False ],
            2: [ False, True ],
        }

        current = elements_visible[ self._opened_what ]

        self._button_placehoder1.visible(   current[ 0 ] )
        self._button_close.visible(         current[ 0 ] )
        self._solution_explorer.visible(    current[ 1 ] )
       

    def __callback_on_press_close( self ):
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
        self.__scene_setup_update( )

    
    def __event_register_file( self, event ):
        """
            After client successfuly register.

            Receive :   
            - event - Event information

            Returns :   None
        """

        file_name:      str = event( "file_name" )
        access_level:   int = event( "access_level" )

        self._solution_explorer.add_item( file_name, lambda: self._logic.request_file( file_name ) )

    
    def __event_clear_editor( self ):
        """
            Event callback for clearing the editor.

            Receive :   None

            Returns :   None
        """

        self._editor.clear( )


    def __event_add_editor_line( self, event ):
        """
            Event callback for adding new line.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:       str     = event( "file" )
        line_text:  str     = event( "line_text" )

        self._editor.set_file( file )
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

        print( f"Line request { file } -> { line }" )
        
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
        