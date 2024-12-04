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

        self._logic = c_client_business_logic( )
        self._logic.set_event( "post_disconnect", self.__logic_post_disconnect, "DisconnectEvent" )

    
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
        scene_config.background_descale = 1.3
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

        self._elements[ "UsernameEntry" ]   = c_text_input( self._scene_connect, vector( 50, 50 ), 40, vector( 200, 30 ), self._application.image( "User" ), self._application.font( "TextInput" ), "Username" )
        self._elements[ "ProjectEntry" ]    = c_text_input( self._scene_connect, vector( 50, 100 ), 40, vector( 200, 30 ), self._application.image( "Edit" ), self._application.font( "TextInput" ), "Project code" )
        self._elements[ "NextToProject" ]   = c_button( self._scene_connect, vector( 50, 150 ), 40, self._application.font( "Button" ), self._application.image( "Next" ), "Continiue", self.__scene_connection_complete )
        
        self._elements[ "StopClient" ]      = c_button( self._scene_project, vector( 50, 50 ), 40, self._application.font( "Button" ), self._application.image( "Close" ), "Disconnect", self.__scene_project_complete )

    # endregion

    # region : Connection

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


    def __scene_project_complete( self ):
        """
            On Continiue button press callback.

            Receive :   None

            Returns :   None
        """

        # self._logic.terminate( )
        self._logic.disconnect( )
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

    # region : Execute

    def execute( self ):

        self._application.run( )

    # endregion