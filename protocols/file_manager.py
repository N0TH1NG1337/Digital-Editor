# Protocols. File manager .py

from utilities.wrappers import safe_call

import shutil
import os

FILE_MANAGER_HEADER = "FL_UNK"

# There are some problems now with this protocol
# First, the client's one and the server's one are differnt.

# While the client should just have the content and the type access.
# The server should also contain much more information about the file
# Like what users use it, what their access and more.

# Besides... Need to decide if the client saves the files or no.

class c_file:
    # This class will have all the server files.

    # Data, Users, Changes and more.
    _name:              str     # File's name. Indcluding the type.

    _original_path:     str     # Original file. DO NOT TOUCH
    _normal_path:       str     # Project new folder path

    def __init__( self, name: str ):
        # Default constructor

        self._name              = name
        self._normal_path       = None

    def create_new( self, path: str ):
        # This will create new empty file
        
        file_path = f"{ path }\\{ self._name }"

        try:
            os.makedirs( os.path.dirname( file_path ), exist_ok=True )

            with open( file_path, 'w' ) as f:
                pass
            
            self._normal_path = path

            return None
        
        except Exception as e:
            return str( e )

    def copy_from( self, path_from: str, path_to: str ):
        # This will create new file and copy the content from other file
        
        file_path_from = f"{ path_from }\\{ self._name }"
        file_path_to = f"{ path_to }\\{ self._name }"

        if not os.path.exists( file_path_from ):
            return f"Failed to find original file { file_path_from }"
        
        try:
            shutil.copy( file_path_from, file_path_to )

            self._normal_path = path_to
        except Exception as e:
            return str( e )
        
        return None

    @safe_call( None )
    def parse_name( self ) -> tuple:
        # Convert the name with type into tuple

        information = self._name.rsplit( ".", 1 )

        return information[ 0 ], information[ 1 ]



class c_file_manager_protocol:

    _last_error:    str
    _files:         dict

    # region : Initialize protocol

    def __init__( self ):
        self._last_error = ""
        self._files = { }

    # endregion

    # region : Shared

    # endregion

    # region : Register

    def create_new_file( self, name: str ) -> c_file:
        # Create file handle

        new_file = c_file( name )
        self._files[ name ] = new_file

        return new_file

    # region : Utils

    def get_header( self ):
        return FILE_MANAGER_HEADER
    
    def get_last_error( self ):
        return self._last_error

    # endregion