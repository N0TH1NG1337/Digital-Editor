# Server - Graphical User Interface .py

from protocols.network              import *

from user_interface.application     import *
from server.server_bl               import c_server_business_logic

FONT_BOLD_PATH  = "C:\\Windows\\Fonts\\arialbd.ttf"
FONT_PATH       = "C:\\Windows\\Fonts\\arial.ttf"

ICON            = "C:\Users\mishs\Downloads\check.png"
DEFAULT_PATH    = "C:\Users\mishs\Documents\Project"

class c_server_gui:

    _network:       c_network_protocol
    _application:   c_application
    _logic:         c_server_business_logic

    _scene_start:   c_scene
    _scene_files:   c_scene
    _scene_connect: c_scene
    _scene_project: c_scene

    _elements:      dict

    def __init__( self ):
        
        self.__init_application( )
        #self.__init_logic( )

    # region : Initialize Application

    def __init_application( self ):
        self._application = c_application( )

        self._application.initialize( "Server", vector( 50, 50 ), vector( 1050, 700 ) )

        self.__init_assets( )
        self._application.initialize_events( )

        self.__init_scenes( )

    def __init_assets( self ):
        self._application.create_font( "Title",     FONT_BOLD_PATH, 50 )

        self._application.create_font( "Button",    FONT_BOLD_PATH, 20 )
        self._application.create_font( "TextInput", FONT_BOLD_PATH, 20 )
        self._application.create_font( "Editor",    FONT_PATH, 20 )

        self._application.create_image( "Check",    ICON, vector( 40, 40 ) )

    def __init_config( self ):

        config_application = self._application.config( "Application" )[ "background_color" ]

        config_application[ 0 ] = color( 30, 30, 30 )
        config_application[ 1 ] = color( 30, 30, 30 )
        config_application[ 2 ] = color( 30, 30, 30 )
        config_application[ 3 ] = color( 30, 30, 30 )
    
    def __init_scenes( self ):

        self._scene_start   = self._application.new_scene( )
        self._scene_files   = self._application.new_scene( )
        self._scene_connect = self._application.new_scene( )
        self._scene_project = self._application.new_scene( )

        self.__attach_scene_events( )
        self.__attach_elements( )

    def __attach_scene_events( self ):

        self._scene_start.set_event(    "draw",     self.__scene_start_draw,    "Start Scene Draw" )
        self._scene_files.set_event(    "draw",     self.__scene_files_draw,    "Files Scene Draw" )
        self._scene_connect.set_event(  "draw",     self.__scene_connect_draw,  "Connection Scene Draw" )
        self._scene_project.set_event(  "draw",     self.__scene_project_draw,  "Project Scene Draw" ) 

    def __attach_elements( self ):
        self._elements = { }

        self._elements[ "Username" ] = c_text_input( self._scene_start, vector( 50, 150 ), 60, vector( 200, 30 ), False, self._application.image( "Check" ), self._application.font( "TextInput" ), "Username" )
        self._elements[ "MoveToFiles" ] = c_button_dynamic( self._scene_start, vector( 50, 300 ), 60, self._application.font( "Button" ), self._application.image( "Check" ), "Next", self.__complete_start_scene )

        self._elements[ "PathPicker" ] = c_file_dialog( self._scene_files, self._application.font( "Button" ), vector( 50, 150 ), vector( 500, 500 ), 40 )
        self._elements[ "PathPicker" ].parse_path( DEFAULT_PATH )
        self._elements[ "MoveToConnection" ] = c_button_dynamic( self._scene_files, vector( 600, 150 ), 60, self._application.font( "Button" ), self._application.image( "Check" ), "Next", self.__complete_files_scene )

        self._elements[ "IpToList" ] = c_text_input( self._scene_connect, vector( 50, 150 ), 60, vector( 200, 30 ), False, self._application.image( "Check" ), self._application.font( "TextInput" ), "IP" )
        self._elements[ "PortToList" ] = c_text_input( self._scene_connect, vector( 50, 220 ), 60, vector( 200, 30 ), False, self._application.image( "Check" ), self._application.font( "TextInput" ), "Port" )

        self._elements[ "MoveToProject" ] = c_button_dynamic( self._scene_connect, vector( 600, 150 ), 60, self._application.font( "Button" ), self._application.image( "Check" ), "Next", self.__complete_connection_scene )

        #self._elements[ "Editor" ] = c_editor( self._scene_project, vector( 0, 150 ), vector( 500, 500 ), self._application.font( "Editor" ) )
        #self._elements[ "Editor" ].insert_line( "" )

    def __scene_start_draw( self, event ):

        scene:          c_scene     = event( "scene" )
        title_font:     c_font      = self._application.font( "Title" )
        screen_size:    vector      = self._application.get_window_size( )

        fade:       float       = scene.animations( ).value( "Fade" )

        self._application.render( ).text( title_font, vector( 50, 50 ), color( 156, 140, 182 ) * fade, "Server" )

        button: c_button_dynamic = self._elements[ "MoveToFiles" ]
        button.position( vector( 50, screen_size.y - 110 ) )

    def __scene_files_draw( self, event ):

        scene:          c_scene     = event( "scene" )
        title_font:     c_font      = self._application.font( "Title" )
        screen_size:    vector      = self._application.get_window_size( )

        fade:       float       = scene.animations( ).value( "Fade" )

        self._application.render( ).text( title_font, vector( 50, 50 ), color( 156, 140, 182 ) * fade, "Select Path" )

    def __scene_connect_draw( self, event ):

        scene:          c_scene     = event( "scene" )
        title_font:     c_font      = self._application.font( "Title" )
        screen_size:    vector      = self._application.get_window_size( )

        fade:       float       = scene.animations( ).value( "Fade" )

        self._application.render( ).text( title_font, vector( 50, 50 ), color( 156, 140, 182 ) * fade, "Setup Connection" )

        button: c_button_dynamic = self._elements[ "MoveToProject" ]
        button.position( vector( 50, screen_size.y - 110 ) )
        

    def __scene_project_draw( self, event ):

        scene:          c_scene     = event( "scene" )
        title_font:     c_font      = self._application.font( "Title" )
        button_font:    c_font      = self._application.font( "Button" )
        screen_size:    vector      = self._application.get_window_size( )

        fade:       float       = scene.animations( ).value( "Fade" )

        self._application.render( ).text( title_font, vector( 50, 50 ), color( 156, 140, 182 ) * fade, "Project" )

        file_dialog: c_file_dialog = self._elements[ "PathPicker" ]
        path = file_dialog.get_path( )

        # Need to find files
        files = os.listdir( path )
        drop = 0

        for file in files:
            self._application.render( ).text( button_font, vector( 50, 150 + drop ), color( 156, 140, 182 ) * fade, file )
            drop += 24

    # endregion

    # region : Initialize Server Logic

    def __complete_start_scene( self ):

        self._application.active_scene( self._scene_files.index( ) )

    def __complete_files_scene( self ):

        self._application.active_scene( self._scene_connect.index( ) )

    def __complete_connection_scene( self ):

        self._application.active_scene( self._scene_project.index( ) )
        self._application.maximize_window( )

    # endregion

    def execute( self ):
        self._application.run( )