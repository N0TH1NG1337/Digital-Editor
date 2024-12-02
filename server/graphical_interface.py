"""
    project     : Digital Editor

    type:       : Server
    file        : Graphical User Interface

    description : Server GUI class
"""

from user_interface.application import *
from utilities.paths            import *

class c_server_gui:

    _application:   c_application

    _scene_start:   c_scene
    _scene_files:   c_scene
    _scene_connect: c_scene
    _scene_project: c_scene

    _elements:      dict

    # region : Initialize Server GUI Object

    def __init__( self ):
        """
            Default constructor for Server Graphical User Interface.

            Receive :   None

            Returns :   Server GUI Object
        """

        self.__initialize_application( )

    
    def __initialize_application( self ):
        """
            Load application and setup it.

            Receive :   None

            Returns :   None
        """

        self._application = c_application( )

        self._application.initialize_window( "Server", vector( 100, 100 ), vector( 1300, 850 ) )

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

        self._application.create_image( "Cloud",        execution_directory + ICON_CLOUD,         vector( 200, 200 ) )
        self._application.create_image( "Folders",      execution_directory + ICON_FOLDERS,       vector( 200, 200 ) )
        self._application.create_image( "Connection",   execution_directory + ICON_CONNECTION,    vector( 200, 200 ) )

        self._application.create_image( "City",         execution_directory + PHOTO_CITY,         vector( 3150, 1816 ) )

        self._application.create_image( "User",         execution_directory + ICON_USER,          vector( 40, 40 ) )
        self._application.create_image( "Next",         execution_directory + ICON_NEXT,          vector( 40, 40 ) )

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

        self.__attach_scenes_events( )
        self.__attach_scenes_elements( )

    
    def __attach_scenes_events( self ):
        """
            Attach to the scenes events.

            Receive :   None

            Returns :   None
        """

        self._scene_start.set_event( "draw", self.__scene_start_draw, "Scene Start Draw" )
        self._scene_files.set_event( "draw", self.__scene_files_draw, "Scene Files Draw" )

    
    def __attach_scenes_elements( self ):
        """
            Attach to the scenes their elements.

            Receive :   None

            Returns :   None
        """

        self._elements = { }

        self._elements[ "Username" ]    = c_text_input( self._scene_start, vector( 50, 50 ), 40, vector( 200, 30 ), self._application.image( "User" ), self._application.font( "TextInput" ), "Username" )
        self._elements[ "NextToFiles" ] = c_button( self._scene_start, vector( 50, 100 ), 40, self._application.font( "Button" ), self._application.image( "Next" ), "Continiue", self.__scene_start_complete )

        self._elements[ "PathSelect" ]          = c_path_select( self._scene_files, self._application.font( "Path" ), vector( 50, 50 ), vector( 500, 600 ), {"back_icon": self._application.image( "Back" ), "folder_icon": self._application.image( "Folder" ), "file_icon": self._application.image( "File" ) } )
        self._elements[ "PathSelect" ].parse_path( os.getcwd( ) )
        self._elements[ "NextToConnection" ]    = c_button( self._scene_files, vector( 50, 600 + 50 ), 40, self._application.font( "Button" ), self._application.image( "Next" ), "Continiue", self.__scene_files_complete )

    # endregion

    # region : Start Scene

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

        render.image( cloud_icon, vector( screen.x - 50 - cloud_size.x, 50 ), color( ) * fade )

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
        text_size:      vector          = render.measure_text( title_font, "Server" )
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

        self._application.active_scene( self._scene_connect.index( ) )

    # endregion

    # region : Execute

    def execute( self ):

        self._application.run( )


    # endregion