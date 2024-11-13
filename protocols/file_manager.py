# Protocols. File manager .py

from utilities.safe import safe_call

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
    # Base class for each file, the application will need to handle
    
    _name:  str
    _path:  str

    def __init__( self ):
        pass


class c_file_manager_protocol:

    _last_error:    str
    _files:         dict

    def __init__( self ):
        self._files = { }

    def register_file( self, file_name: str, file_path: str ):

        self._files[ file_name ] = file_path


    @safe_call( None )
    def create_folder( self, name: str, path: str ) -> str:
        
        fixed_name = f"{ path }\\{ name }"
        os.mkdir( fixed_name )

        return fixed_name
    
    @safe_call( None )
    def copy_file( self, path_from: str, path_to: str ) -> bool:
        
        if not os.path.exists( path_from ):
            self._last_error = f"Failed to fine {path_from}"
            raise Exception( self._last_error )
        
        shutil.copy( path_from, path_to )

        return True

    def get_header( self ):
        return FILE_MANAGER_HEADER
    
    def get_last_error( self ):
        return self._last_error