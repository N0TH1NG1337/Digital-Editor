"""
    project     : Digital Editor

    type:       : Client
    file        : Graphical User Interface

    description : Client GUI class
"""

from client.business_logic      import c_client_business_logic
from user_interface.application import *
from utilities.paths            import *

class c_client_gui:

    _application:       c_application
    _logic:             c_client_business_logic

    _scene_connect:     c_scene
    _scene_project:     c_scene

    _elements:          dict    

    # region : Initialize Client GUI Object

    def __init__( self ):
        """
            Default constructor for Client Graphical User Interface.

            Receive :   None

            Returns :   Server GUI Object
        """

        self.__initialize_application( )

        self.__initialize_logic( )
        

    def __initialize_application( self ):
        """
            Load application and setup it.

            Receive :   None

            Returns :   None
        """

        self._application = c_application( )

        self._application.initialize_window( "Client", vector( 100, 100 ), vector( 1300, 850 ) )

        self.__initialize_assets( )

        self._application.initialize_events( )

        self.__initialize_scenes( )

    
    def __initialize_assets( self ):
        """
            Load application resources like Images and Fonts.

            Receive :   None

            Returns :   None
        """

        execution_directory = os.getcwd( )

        self._application.create_font( "Title",     FONT, 100 )

        self._application.create_font( "Button",    FONT, 20 )
        self._application.create_font( "TextInput", FONT, 20 )
        self._application.create_font( "Path",      FONT, 20 )
        self._application.create_font( "List",      FONT, 20 )
        self._application.create_font( "Editor",    FONT_THIN, 20 )

        self._application.create_image( "Cloud",        execution_directory + ICON_CLOUD,         vector( 200, 200 ) )
        self._application.create_image( "Folders",      execution_directory + ICON_FOLDERS,       vector( 200, 200 ) )
        self._application.create_image( "Connection",   execution_directory + ICON_CONNECTION,    vector( 200, 200 ) )

        self._application.create_image( "City",         execution_directory + PHOTO_CITY,         vector( 3150, 1816 ) )

        self._application.create_image( "User",         execution_directory + ICON_USER,          vector( 40, 40 ) )
        self._application.create_image( "Next",         execution_directory + ICON_NEXT,          vector( 40, 40 ) )
        self._application.create_image( "Check",        execution_directory + ICON_CHECK,         vector( 40, 40 ) )
        self._application.create_image( "Edit",         execution_directory + ICON_EDIT,          vector( 40, 40 ) )
        self._application.create_image( "Visible",      execution_directory + ICON_VISIBLE,       vector( 40, 40 ) )
        self._application.create_image( "Close",        execution_directory + ICON_CLOSE,         vector( 40, 40 ) )
        self._application.create_image( "Listen",       execution_directory + ICON_LISTEN,        vector( 40, 40 ) )
        self._application.create_image( "NetMan",       execution_directory + ICON_NET_MAN,       vector( 40, 40 ) )

        self._application.create_image( "Back",         execution_directory + ICON_BACK,          vector( 40, 40 ) )
        self._application.create_image( "Folder",       execution_directory + ICON_FOLDER,        vector( 40, 40 ) )
        self._application.create_image( "File",         execution_directory + ICON_FILE,          vector( 40, 40 ) )


    def __initialize_scenes( self ):
        """
            Load and setup the application scenes.

            Receive :   None

            Returns :   None
        """

        scene_config = scene_config_t( )

        scene_config.animate_entrance   = True
        scene_config.animate_movement   = True
        scene_config.enable_background  = True
        scene_config.background_image   = self._application.image( "City" )
        scene_config.background_descale = 1.4
        scene_config.background_color   = self._application.config( ).back_color_4.copy( )

        self._scene_connect     = self._application.new_scene( scene_config )
        self._scene_project     = self._application.new_scene( scene_config )

        self.__attach_scenes_events( )
        self.__attach_scenes_elements( )

    
    def __attach_scenes_events( self ):
        """
            Attach to the scenes events.

            Receive :   None

            Returns :   None
        """

        self._scene_connect.set_event( "draw",  self.__scene_connection_draw,   "Scene Connection Draw" )
        self._scene_project.set_event( "draw",  self.__scene_project_draw,      "Scene Project Draw" )

    
    def __attach_scenes_elements( self ):
        """
            Attach to the scenes their elements.

            Receive :   None

            Returns :   None
        """

        self._elements = { }

        self.__scene_connection_elements( )
        
        self.__scene_project_elements( )


    def __initialize_logic( self ):
        """
            Initialize Client Logic.

            Receive :   None

            Returns :   None
        """

        self._logic = c_client_business_logic( )

        self.__initialize_logic_events( )
    

    def __initialize_logic_events( self ):
        """
            Set logic event callbacks.

            Receive :   None

            Returns :   None
        """

        self._logic.set_event( "post_disconnect",   self.__logic_post_disconnect,   "DisconnectEvent" )
        self._logic.set_event( "register_file",     self.__event_register_file,     "GUI_SetList" )
        self._logic.set_event( "set_file",          self.__event_clear_editor,      "GUI_ClearEditor" )
        self._logic.set_event( "update_file",       self.__event_add_editor_line,   "GUI_AddLine" )
        self._logic.set_event( "accept_line",       self.__event_response_line,     "GUI_Accept_Line" )
        self._logic.set_event( "lock_line",         self.__event_lock_line,         "GUI_LockLine")
        self._logic.set_event( "unlock_line",       self.__event_unlock_line,       "GUI_UnlockLine" ) 

    # endregion

    # region : Connection

    def __scene_connection_elements( self ):
        """
            Setup elements for scene connection.

            Receive :   None

            Returns :   None
        """

        text_font:      c_font  = self._application.font( "TextInput" )
        button_font:    c_font  = self._application.font( "Button" )

        user_icon:      c_image = self._application.image( "User" )
        edit_icon:      c_image = self._application.image( "Edit" )
        next_icon:      c_image = self._application.image( "Next" )

        self._elements[ "UsernameEntry" ]   = c_text_input( self._scene_connect, vector( 50, 50 ), 40, vector( 200, 30 ), user_icon, text_font, "Username" )
        self._elements[ "ProjectEntry" ]    = c_text_input( self._scene_connect, vector( 50, 100 ), 40, vector( 200, 30 ), edit_icon, text_font, "Project code" )
        self._elements[ "NextToProject" ]   = c_button( self._scene_connect, vector( 50, 150 ), 40, button_font, next_icon, "Continiue", self.__scene_connection_complete )

        #self._elements[ "ThemeColor" ]      = c_color_picker( self._scene_connect, vector( 500, 500 ), vector( 230 + 44, 230 + 44 ), color( 150, 150, 255 ) )


    def __scene_connection_draw( self, event ):
        """
            Scene Connection draw function.

            Receive : 
            - event - Event information

            Returns :   None
        """

        title_font:         c_font          = self._application.font( "Title" )
        cloud_icon:         c_image         = self._application.image( "Cloud" )
        screen:             vector          = self._application.window_size( )
        
        render:             c_renderer      = self._scene_connect.render( )
        animations:         c_animations    = self._scene_connect.animations( )

        fade:               float           = animations.value( "Fade" )
        text_size:          vector          = render.measure_text( title_font, "Client" )
        connection_size:    vector          = cloud_icon.size( )

        render.text( title_font, vector( 50 + 3,    screen.y - text_size.y - 50 - 3 ),  color( 200, 200, 255, 100 ) * fade, "Client" )
        render.text( title_font, vector( 50,        screen.y - text_size.y - 50 ),      color( ) * fade,                    "Client" )

        render.image( cloud_icon, vector( screen.x - 50 - connection_size.x, 50 ), color( ) * fade )

        self.__adjust_scene_connection_elements( )


    def __adjust_scene_connection_elements( self ):
        """
            Adjust the position of the Scene connection elements.

            Receive :   None

            Returns :   None
        """

        username_input: c_text_input    = self._elements[ "UsernameEntry" ]
        project_input:  c_text_input    = self._elements[ "ProjectEntry" ]
        next_button:    c_button        = self._elements[ "NextToProject" ]

        pad:            int             = 20

        screen          = self._application.window_size( )
        username_size   = username_input.size( )
        project_size    = project_input.size( )
        button_size     = next_button.size( )

        fixed   = screen.y - ( username_size.y + pad * 2 + project_size.y + button_size.y )
        fixed   = fixed / 2

        username_input.position( vector( 50, fixed ) )
        project_input.position( vector( 50, fixed + pad + username_size.y ) )
        next_button.position( vector( 50, fixed + pad * 2 + username_size.y + project_size.y ) )


    def __scene_connection_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        project_code_input: c_text_input = self._elements[ "ProjectEntry" ]
        username_input:     c_text_input = self._elements[ "UsernameEntry" ]
        
        self._logic.connect( project_code_input.get( ), username_input.get( ) ) 

        if self._logic( "is_connected" ):
            self._application.active_scene( self._scene_project.index( ) )
            self._application.maximize_window( )

        # TODO LOGIC

    # endregion

    # region : Project

    def __scene_project_elements( self ):
        """
            Setup elements for scene project.

            Receive :   None

            Returns :   None
        """

        button_font:    c_font  = self._application.font( "Button" )
        list_font:      c_font  = self._application.font( "List" )
        editor_font:    c_font  = self._application.font( "Editor" )

        close_icon:     c_image = self._application.image( "Close" )

        files_list_config = list_config_t( )
        files_list_config.check_mark = self._application.image( "Check" )
        files_list_config.slots_count = 8

        self._elements[ "StopClient" ]      = c_button( self._scene_project, vector( 50, 50 ), 40, button_font, close_icon, "Disconnect", self.__scene_project_complete )
        self._elements[ "FilesList" ]       = c_list( self._scene_project, vector( 50, 100 ), 300, list_font, files_list_config )

        self._elements[ "Editor" ]          = c_editor( self._scene_project, vector( 50, 100 ), vector( 1000, 760 ), editor_font )

        self._elements[ "Editor" ].set_event( "request_line", self.__event_request_line, "GUI_ReqLine" )
        self._elements[ "Editor" ].set_event( "discard_line", self.__event_discard_line, "Gui_DisLine" )


    def __scene_project_draw( self, event ):
        """
            Scene Project draw function.

            Receive : 
            - event - Event information

            Returns :   None
        """

        title_font:         c_font          = self._application.font( "Title" )
        screen:             vector          = self._application.window_size( )
        
        render:             c_renderer      = self._scene_project.render( )
        animations:         c_animations    = self._scene_project.animations( )

        fade:               float           = animations.value( "Fade" )
        text_size:          vector          = render.measure_text( title_font, "Project" )

        render.text( title_font, vector( 50 + 3,    screen.y - text_size.y - 50 - 3 ),  color( 200, 200, 255, 100 ) * fade, "Project" )
        render.text( title_font, vector( 50,        screen.y - text_size.y - 50 ),      color( ) * fade,                    "Project" )

        self.__adjust_scene_project_elements( )
    

    def __adjust_scene_project_elements( self ):
        """
            Adjust the position of the Scene project elements.

            Receive :   None

            Returns :   None
        """

        screen: vector = self._application.window_size( )

        files_list: c_list = self._elements[ "FilesList" ]
        files_list.position( vector( screen.x - 350, 100 ) )


    def __scene_project_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        self._logic.disconnect( )
        self._elements[ "FilesList" ].clear( )
        self._application.active_scene( self._scene_connect.index( ) )

    
    def __logic_post_disconnect( self, event ):
        """
            After client successfuly disconnect.

            Receive :   
            - event - Event information

            Returns :   None
        """

        self._application.active_scene( self._scene_connect.index( ) )

    # endregion

    # region : Events for client

    def __event_register_file( self, event ):
        """
            Event callback for file register from server.

            Receive :
            - event - Event information

            Returns :   None
        """

        file_name:  str     = event( "file_name" )
        file_icon:  c_image = self._application.image( "File" )

        files_list: c_list = self._elements[ "FilesList" ]
        files_list.add_item( file_name, file_icon, self._logic.request_file )

    
    def __event_clear_editor( self, event ):
        """
            Event callback for clearing the editor.

            Receive :
            - event - Event information

            Returns :   None
        """

        editor: c_editor = self._elements[ "Editor" ]
        editor.clear( )

    
    def __event_add_editor_line( self, event ):
        """
            Event callback for adding new line.

            Receive :
            - event - Event information

            Returns :   None
        """

        editor: c_editor = self._elements[ "Editor" ]

        file:           str     = event( "file" )
        line_text:      str     = event( "line_text" )

        editor.set_file( file )
        editor.add_line( line_text )


    def __event_request_line( self, event ):
        """
            Client requests line from the server.

            Receive :
            - event - Event information

            Returns :   None
        """

        file:   str     = event( "file" )
        line:   int     = event( "line" )

        self._logic.request_line( file, line )

    
    def __event_response_line( self, event ):
        """
            Response from the server if the line can be used by us.

            Receive :
            - event - Event information

            Returns :   None
        """

        editor: c_editor = self._elements[ "Editor" ]

        file_name:  str     = event( "file")
        line:       int     = event( "line" )
        accept:     bool    = event( "accept" )

        editor.accept_line( file_name, line, accept )

    
    def __event_lock_line( self, event ):
        """
            Response from server to client in order to lock a line.

            Receive : 
            - event - Event information

            Returns :   None
        """

        editor: c_editor = self._elements[ "Editor" ]

        file_name:  str     = event( "file")
        line:       int     = event( "line" )

        editor.lock_line( line )

    
    def __event_unlock_line( self, event ):
        """
            Response from server to client in order to unlock a line.

            Receive : 
            - event - Event information

            Returns :   None
        """

        editor: c_editor = self._elements[ "Editor" ]

        file_name:  str     = event( "file")
        line:       int     = event( "line" )
        
        editor.unlock_line( line )

    
    def __event_discard_line( self, event ):
        """
            Message to server in order to discard line changes.

            Receive :   
            - event - Event information

            Returns :   None
        """

        file_name:  str = event( "file" )
        line:       int = event( "line" )

        self._logic.discard_line( file_name, line )

    # endregion

    # region : Execute

    def execute( self ):

        self._application.run( )

    # endregion