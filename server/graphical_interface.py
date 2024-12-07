"""
    project     : Digital Editor

    type:       : Server
    file        : Graphical User Interface

    description : Server GUI class
"""

from server.business_logic      import c_server_business_logic, c_client_handle
from user_interface.application import *
from utilities.paths            import *

class c_server_gui:

    _application:   c_application
    _logic:         c_server_business_logic

    _scene_start:   c_scene
    _scene_files:   c_scene
    _scene_connect: c_scene
    _scene_project: c_scene
    _scene_admin:   c_scene

    _elements:      dict

    # region : Initialize Server GUI Object

    def __init__( self ):
        """
            Default constructor for Server Graphical User Interface.

            Receive :   None

            Returns :   Server GUI Object
        """

        self.__initialize_application( )

        self._logic = c_server_business_logic( )

    
    def __initialize_application( self ):
        """
            Load application and setup it.

            Receive :   None

            Returns :   None
        """

        self._application = c_application( )

        self._application.initialize_window( "Server", vector( 100, 100 ), vector( 1300, 850 ), False )

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
        self._application.create_image( "Copy",         execution_directory + ICON_COPY,          vector( 40, 40 ) )

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
        scene_config.background_descale = 1.3
        scene_config.background_color   = self._application.config( ).back_color_4.copy( )

        self._scene_start   = self._application.new_scene( scene_config )
        self._scene_files   = self._application.new_scene( scene_config )
        self._scene_connect = self._application.new_scene( scene_config )
        self._scene_project = self._application.new_scene( scene_config )
        self._scene_admin   = self._application.new_scene( scene_config )

        self.__attach_scenes_events( )
        self.__attach_scenes_elements( )

    
    def __attach_scenes_events( self ):
        """
            Attach to the scenes events.

            Receive :   None

            Returns :   None
        """

        self._scene_start.set_event(    "draw",     self.__scene_start_draw,        "Scene Start Draw" )
        self._scene_files.set_event(    "draw",     self.__scene_files_draw,        "Scene Files Draw" )
        self._scene_connect.set_event(  "draw",     self.__scene_connection_draw,   "Scene Connection Draw" )
        self._scene_project.set_event(  "draw",     self.__scene_project_draw,      "Scene Project Draw" )
        self._scene_admin.set_event(    "draw",     self.__scene_admin_draw,        "Scene Admin Draw" )

    
    def __attach_scenes_elements( self ):
        """
            Attach to the scenes their elements.

            Receive :   None

            Returns :   None
        """

        self._elements = { }

        self.__scene_start_elements( )
        self.__scene_files_elements( )
        self.__scene_connection_elements( )
        self.__scene_project_elements( )
        self.__scene_admin_elements()
        
    # endregion

    # region : Start Scene

    def __scene_start_elements( self ):
        """
            Create elements for scene start.

            Receive :   None

            Returns :   None
        """

        button_font:    c_font  = self._application.font( "Button" )
        text_font:      c_font  = self._application.font( "TextInput" )

        user_icon:      c_image = self._application.image( "User" )
        next_icon:      c_image = self._application.image( "Next" )

        self._elements[ "Username" ]    = c_text_input( self._scene_start, vector( 50, 50 ), 40, vector( 200, 30 ), user_icon, text_font, "Username" )
        self._elements[ "NextToFiles" ] = c_button( self._scene_start, vector( 50, 100 ), 40, button_font, next_icon, "Continiue", self.__scene_start_complete )


    def __scene_start_draw( self, event ):
        """
            Scene Start draw function.

            Receive : 
            - event - Event information

            Returns :   None
        """

        title_font: c_font          = self._application.font( "Title" )
        cloud_icon: c_image         = self._application.image( "Cloud" )
        screen:     vector          = self._application.window_size( )
        
        render:     c_renderer      = self._scene_start.render( )
        animations: c_animations    = self._scene_start.animations( )

        fade:       float           = animations.value( "Fade" )
        text_size:  vector          = render.measure_text( title_font, "Server" )
        cloud_size: vector          = cloud_icon.size( )

        render.text( title_font, vector( 50 + 3,    screen.y - text_size.y - 50 - 3 ),  color( 200, 200, 255, 100 ) * fade, "Server" )
        render.text( title_font, vector( 50,        screen.y - text_size.y - 50 ),      color( ) * fade,                    "Server" )
        
        render.image( cloud_icon, vector( screen.x - 50 - cloud_size.x, 50 ), color( 150, 150, 255, 100 ) * fade )

        self.__adjust_scene_start_elements( )

    
    def __adjust_scene_start_elements( self ):
        """
            Adjust the position of the Scene Start elements.

            Receive :   None

            Returns :   None
        """

        username_input: c_text_input    = self._elements[ "Username" ]
        next_button:    c_button        = self._elements[ "NextToFiles" ]
        pad:            int             = 20

        screen          = self._application.window_size( )
        text_input_size = username_input.size( )
        button_size     = next_button.size( )

        fixed   = screen.y - ( button_size.y + pad + text_input_size.y )
        fixed   = fixed / 2

        username_input.position( vector( 50, fixed ) )
        next_button.position( vector( 50, fixed + pad + text_input_size.y ) )

    
    def __scene_start_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        self._application.active_scene( self._scene_files.index( ) )

    # endregion

    # region : Files

    def __scene_files_elements( self ):
        """
            Create elements for scene files.

            Receive :   None

            Returns :   None
        """

        path_font:      c_font  = self._application.font( "Path" )
        button_font:    c_font  = self._application.font( "Button" )
        list_font:      c_font  = self._application.font( "List" )

        path_icons:     dict = {
            "back_icon":    self._application.image( "Back" ), 
            "folder_icon":  self._application.image( "Folder" ), 
            "file_icon":    self._application.image( "File" )
        }

        next_icon:      c_image = self._application.image( "Next" )

        file_type_list_config = list_config_t( )
        file_type_list_config.check_mark = self._application.image( "Check" )

        self._elements[ "PathSelect" ]          = c_path_select( self._scene_files,path_font, vector( 50, 50 ), vector( 500, 600 ), path_icons )
        self._elements[ "NextToConnection" ]    = c_button( self._scene_files, vector( 50, 600 + 50 ), 40, button_font, next_icon, "Continiue", self.__scene_files_complete )
        self._elements[ "SelectFileType" ]      = c_list( self._scene_files, vector( 600, 50 ), 200, list_font, file_type_list_config  )

        self._elements[ "PathSelect" ].parse_path( os.getcwd( ) )

        self._elements[ "SelectFileType" ].add_item( "Edit",        self._application.image( "Edit" ) )
        self._elements[ "SelectFileType" ].add_item( "Read only",   self._application.image( "Visible" ) )
        self._elements[ "SelectFileType" ].add_item( "Hidden",      self._application.image( "Close" ) )


    def __scene_files_draw( self, event ):
        """
            Scene Files draw function.

            Receive : 
            - event - Event information

            Returns :   None
        """

        title_font:     c_font          = self._application.font( "Title" )
        folder_icon:    c_image         = self._application.image( "Folders" )
        screen:         vector          = self._application.window_size( )
        
        render:         c_renderer      = self._scene_files.render( )
        animations:     c_animations    = self._scene_files.animations( )

        fade:           float           = animations.value( "Fade" )
        text_size:      vector          = render.measure_text( title_font, "Files" )
        folders_size:   vector          = folder_icon.size( )

        render.text( title_font, vector( 50 + 3,    screen.y - text_size.y - 50 - 3 ),  color( 200, 200, 255, 100 ) * fade, "Files" )
        render.text( title_font, vector( 50,        screen.y - text_size.y - 50 ),      color( ) * fade,                    "Files" )

        render.image( folder_icon, vector( screen.x - 50 - folders_size.x, 50 ), color( ) * fade )
    

    def __scene_files_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        path_select: c_path_select = self._elements[ "PathSelect" ]
        self._logic.initialize_path( path_select.get_path( ) )

        self._application.active_scene( self._scene_connect.index( ) )

    # endregion

    # region : Connection

    def __scene_connection_elements( self ):
        """
            Create elements for scene connection.

            Receive :   None

            Returns :   None
        """

        text_font:      c_font  = self._application.font( "TextInput" )
        button_font:    c_font  = self._application.font( "Button" )

        ip_icon:        c_image = self._application.image( "Listen" )
        port_icon:      c_image = self._application.image( "NetMan" )
        next_icon:      c_image = self._application.image( "Next" )

        self._elements[ "IpEntry" ]         = c_text_input( self._scene_connect, vector( 50, 50 ), 40, vector( 200, 30 ), ip_icon, text_font, "IP", False, "0.0.0.0" )
        self._elements[ "PortEntry" ]       = c_text_input( self._scene_connect, vector( 50, 100 ), 40, vector( 200, 30 ), port_icon, text_font, "Port" )
        self._elements[ "NextToProject" ]   = c_button( self._scene_connect, vector( 50, 150 ), 40, button_font, next_icon, "Continiue", self.__scene_connection_complete )


    def __scene_connection_draw( self, event ):
        """
            Scene Connection draw function.

            Receive : 
            - event - Event information

            Returns :   None
        """

        title_font:         c_font          = self._application.font( "Title" )
        connection_icon:    c_image         = self._application.image( "Connection" )
        screen:             vector          = self._application.window_size( )
        
        render:             c_renderer      = self._scene_connect.render( )
        animations:         c_animations    = self._scene_connect.animations( )

        fade:               float           = animations.value( "Fade" )
        text_size:          vector          = render.measure_text( title_font, "Connection" )
        connection_size:    vector          = connection_icon.size( )

        render.text( title_font, vector( 50 + 3,    screen.y - text_size.y - 50 - 3 ),  color( 200, 200, 255, 100 ) * fade, "Connection" )
        render.text( title_font, vector( 50,        screen.y - text_size.y - 50 ),      color( ) * fade,                    "Connection" )

        render.image( connection_icon, vector( screen.x - 50 - connection_size.x, 50 ), color( ) * fade )

        self.__adjust_scene_connection_elements( )


    def __adjust_scene_connection_elements( self ):
        """
            Adjust the position of the Scene connection elements.

            Receive :   None

            Returns :   None
        """

        ip_input:       c_text_input    = self._elements[ "IpEntry" ]
        port_input:     c_text_input    = self._elements[ "PortEntry" ]
        next_button:    c_button        = self._elements[ "NextToProject" ]

        pad:            int             = 20

        screen          = self._application.window_size( )
        ip_size         = ip_input.size( )
        port_size       = port_input.size( )
        button_size     = next_button.size( )

        fixed   = screen.y - ( ip_size.y + pad * 2 + port_size.y + button_size.y )
        fixed   = fixed / 2

        ip_input.position( vector( 50, fixed ) )
        port_input.position( vector( 50, fixed + pad + ip_size.y ) )
        next_button.position( vector( 50, fixed + pad * 2 + ip_size.y + port_size.y ) )


    def __scene_connection_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        self._application.active_scene( self._scene_project.index( ) )
        self._application.maximize_window( )

        ip_input:       c_text_input    = self._elements[ "IpEntry" ]
        port_input:     c_text_input    = self._elements[ "PortEntry" ]

        self._logic.setup( ip_input.get(), int( port_input.get( ) ) )
        self._logic.start( )

        #code = self._logic.generate_code( )
        #print( code )

    # endregion

    # region : Project

    def __scene_project_elements( self ):
        """
            Create elements for scene project.

            Receive :   None

            Returns :   None
        """
        
        button_font:    c_font  = self._application.font( "Button" )

        file_icon:      c_image = self._application.image( "File" )
        admin_icon:     c_image = self._application.image( "User" )

        self._elements[ "Bar_Connection" ]  = c_button( self._scene_project, vector( 50, 50 ), 40, button_font, file_icon, "Connection", self.__scene_project_bar_connection )
        self._elements[ "Bar_Admin" ]       = c_button( self._scene_project, vector( 100, 50 ), 40, button_font, admin_icon, "Admin", self.__scene_project_bar_admin )


    def __scene_project_bar_connection( self ):
        """
            Open File option on bar.

            Receive :   None

            Returns :   None
        """

        window_config = window_config_t( )
        window_config.show_bar = True

        button_font:    c_font  = self._application.font( "Button" )
        copy_icon:      c_image = self._application.image( "Copy" )
        close_icon:     c_image = self._application.image( "Close" )

        file_button:    c_button = self._elements[ "Bar_Connection" ]
        file_position:  vector = file_button.position( ) + vector( 0, file_button.size( ).y + 20 )

        new_window = self._scene_project.create_window( vector( 100, 100 ), vector( 250, 200 ), window_config )

        copy_button = c_button( new_window, vector( 10, 10 ), 40, button_font, copy_icon, "Project Code", lambda: self.__copy_to_clipboard( self._logic.generate_code( ) ) )
        stop_button = c_button( new_window, vector( 10, 60 ), 40, button_font, close_icon, "Stop Server", self.__scene_project_complete )


    def __scene_project_bar_admin( self ):
        """
            Button callback to open Admin panel.

            Receive :   None

            Returns :   None
        """

        self._application.active_scene( self._scene_admin.index( ) )


    def __scene_project_draw( self, event ):
        """
            Scene Project draw function.

            Receive : 
            - event - Event information

            Returns :   None
        """

        title_font:         c_font          = self._application.font( "Title" )
        text_font:          c_font          = self._application.font( "TextInput" )
        screen:             vector          = self._application.window_size( )
        
        render:             c_renderer      = self._scene_project.render( )
        animations:         c_animations    = self._scene_project.animations( )

        fade:               float           = animations.value( "Fade" )
        text_size:          vector          = render.measure_text( title_font, "Project" )

        render.text( title_font, vector( 50 + 3,    screen.y - text_size.y - 50 - 3 ),  color( 200, 200, 255, 100 ) * fade, "Project" )
        render.text( title_font, vector( 50,        screen.y - text_size.y - 50 ),      color( ) * fade,                    "Project" )

        self.__adjust_scene_project_bar_elements( )


    def __adjust_scene_project_bar_elements( self ):
        """
            Adjust the position of the Scene project bar elements.

            Receive :   None

            Returns :   None
        """

        connection_button:  c_button    = self._elements[ "Bar_Connection" ]
        admin_button:       c_button    = self._elements[ "Bar_Admin" ]

        connection_size = connection_button.size( )

        connection_button.position( vector( 50, 50 ) )
        admin_button.position( vector( 100 + connection_size.x, 50 ) )


    def __scene_project_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        self._logic.terminate( )
        self._application.active_scene( self._scene_start.index( ) )

    # endregion

    # region : Admin

    def __scene_admin_elements( self ):
        """
            Create elements for scene admin.

            Receive :   None

            Returns :   None
        """
        
        button_font:    c_font  = self._application.font( "Button" )

        exit_icon:      c_image = self._application.image( "Close" )

        self._elements[ "FromAdmin" ]  = c_button( self._scene_admin, vector( 50, 50 ), 40, button_font, exit_icon, "Back", self.__scene_admin_complete )


    def __scene_admin_draw( self, event ):
        """
            Scene Admin draw function.

            Receive : 
            - event - Event information

            Returns :   None
        """

        title_font:         c_font          = self._application.font( "Title" )
        text_font:          c_font          = self._application.font( "TextInput" )
        screen:             vector          = self._application.window_size( )
        
        render:             c_renderer      = self._scene_admin.render( )
        animations:         c_animations    = self._scene_admin.animations( )

        fade:               float           = animations.value( "Fade" )
        text_size:          vector          = render.measure_text( title_font, "Admin Panel" )

        render.text( title_font, vector( 50 + 3,    screen.y - text_size.y - 50 - 3 ),  color( 200, 200, 255, 100 ) * fade, "Admin Panel" )
        render.text( title_font, vector( 50,        screen.y - text_size.y - 50 ),      color( ) * fade,                    "Admin Panel" )

        logs: list = self._logic.get_logs( )

        start   = vector( screen.x / 2, screen.y - 150 )
        drop    = 0

        render.push_clip_rect( vector( 50, 100 ), start )

        for log in reversed( logs ):
            text_size = render.measure_text( text_font, log )

            render.text( text_font, vector( 60, start.y - text_size.y - drop ), color( 200, 200, 200, 255 ) * fade, log )

            drop = drop + text_size.y + 10

        render.pop_clip_rect( )

        clients: list = self._logic.clients( )

        start   = vector( screen.x, screen.y - 150 )
        drop    = 0

        render.push_clip_rect( vector( screen.x / 2, 100 ), start )

        for client in clients:
            client: c_client_handle = client

            address = client.network( ).get_address( True )
            name = client( "username" )
            file_name = client.get_file_name( )

            text = f" { address } - { name } -> { file_name } "

            text_size = render.measure_text( text_font, text )

            render.text( text_font, vector( screen.x / 2 + 10, 100 + drop ), color( 200, 200, 200, 255 ) * fade, text )

            drop = drop + text_size.y + 10

        render.pop_clip_rect( )


    def __scene_admin_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        self._application.active_scene( self._scene_project.index( ) )

    # endregion

    # region Utilities

    def __copy_to_clipboard( self, text: str ):
        """
            Copy text into users clipboard.

            Receive :
            - text - String to copy

            Returns :   None
        """

        glfw.set_clipboard_string( None, text )

    # endregion

    # region : Execute

    def execute( self ):

        self._application.run( )

    # endregion