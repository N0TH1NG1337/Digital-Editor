# Client - Graphical User Interface .py

from protocols.network              import *

from user_interface.application     import *
from client.client_bl               import c_client_business_logic

from utilities.base64               import base64

FONT_BOLD_PATH  = "C:\\Windows\\Fonts\\arialbd.ttf"
FONT_PATH       = "C:\\Windows\\Fonts\\arial.ttf"

ICON            = "C:\Users\mishs\Downloads\check.png"

class c_client_gui:

    _network:       c_network_protocol
    _application:   c_application
    _logic:         c_client_business_logic

    _scene_connect: c_scene
    _scene_show:    c_scene

    _elements:      dict

    def __init__( self ):
        
        self.__init_application( )
        self.__init_logic( )

    # region : Initialize Application

    def __init_application( self ):
        self._application = c_application( )

        self._application.initialize( "Client", vector( 50, 50 ), vector( 1050, 700 ) )

        self.__init_assets( )
        self._application.initialize_events( )

        self.__init_scenes( )

    def __init_assets( self ):
        self._application.create_font( "Title",     FONT_BOLD_PATH, 50 )

        self._application.create_font( "Button",    FONT_BOLD_PATH, 20 )
        self._application.create_font( "TextInput", FONT_PATH, 20 )

        self._application.create_image( "Check",    ICON, vector( 40, 40 ) )

    def __init_scenes( self ):

        self._scene_connect = self._application.new_scene( )
        self._scene_show    = self._application.new_scene( )

        self.__attach_scene_events( )
        self.__attach_elements( )

    def __attach_scene_events( self ):

        self._scene_connect.set_event(  "draw",     self.__scene_connect_draw,  "Connect Scene Draw" )
        self._scene_show.set_event(     "draw",     self.__scene_show_draw,     "Show Scene Draw" )

    def __attach_elements( self ):
        self._elements = { }

        self._elements[ "Username" ]    = c_text_input( self._scene_connect, vector( 50, 150 ), 60, vector( 200, 30 ), False, self._application.image( "Check" ), self._application.font( "TextInput" ), "Username" )
        self._elements[ "ProjectCode" ] = c_text_input( self._scene_connect, vector( 50, 220 ), 60, vector( 200, 30 ), False, self._application.image( "Check" ), self._application.font( "TextInput" ), "Project Code" )

        self._elements[ "ExitButton" ] = c_button_dynamic( self._scene_connect, vector( 50, 300 ), 60, self._application.font( "Button" ), self._application.image( "Check" ), "Exit", self._application.exit )
        self._elements[ "NextButton" ] = c_button_dynamic( self._scene_connect, vector( 120, 300 ), 60, self._application.font( "Button" ), self._application.image( "Check" ), "Next", self.__connect )

        self._elements[ "DisconnectButton" ] = c_button_dynamic( self._scene_show, vector( 50, 150 ), 60, self._application.font( "Button" ), self._application.image( "Check" ), "Disconnect", self.__disconnect )

    def __scene_connect_draw( self, event ):

        scene:          c_scene     = event( "scene" )
        title_font:     c_font      = self._application.font( "Title" )
        title2_font:    c_font      = self._application.font( "Title2" )
        screen_size:    vector      = self._application.get_window_size( )

        fade:       float       = scene.animations( ).value( "Fade" )

        self._application.render( ).text( title_font, vector( 50, 50 ), color( 156, 140, 182 ) * fade, "Client" )

        exit_button: c_button_dynamic = self._elements[ "ExitButton" ]
        next_button: c_button_dynamic = self._elements[ "NextButton" ]

        exit_button.position( vector( 50, screen_size.y - 110 ) )
        next_button.position( vector( 60 + exit_button.size( ).x, screen_size.y - 110 ) )

    def __scene_show_draw( self, event ):

        scene:      c_scene     = event( "scene" )
        title_font: c_font      = self._application.font( "Title" )

        fade:       float       = scene.animations( ).value( "Fade" )

        self._application.render( ).text( title_font, vector( 50, 50 ), color( 156, 140, 182 ) * fade, "Connected" )

    # endregion

    # region : Initialize Client Logic

    def __init_logic( self ):

        self._logic = c_client_business_logic( )

    def __connect( self ):

        project_code_input: c_text_input = self._elements[ "ProjectCode" ]
        #self._logic.connect( project_code_input.get( ) ) 

        #if self._logic( "is_connected" ):
        #    self._application.next_scene( )
    
    def __disconnect( self ):

        # self._logic.disconnect( )
        self._application.previous_scene( )

    # endregion

    def execute( self ):
        self._application.run( )