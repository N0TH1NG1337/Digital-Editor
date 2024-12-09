"""
    project     : Digital Editor

    type:       : Protocol
    file        : Files Manager

    description : Files Manager Protocol class
"""

from utilities.wrappers import safe_call

import shutil
import os

FILES_MANAGER_HEADER = "FL_UNK"

FILES_COMMAND_REQ_FILES = "ReqFiles"
FILES_COMMAND_RES_FILES = "ResFiles"

FILES_COMMAND_GET_FILE = "GetFileCont"
FILES_COMMAND_SET_FILE = "SetFileCont"


FILES_COMMAND_PREPARE_UPDATE = "PrepUpdateLine"
FILES_COMMAND_PREPARE_RESPONSE = "ResPrepUpdate"
FILES_COMMAND_UPDATE_LINE = "UpdateLine"
FILES_COMMAND_DISCARD_UPDATE = "DisUpdateLine"

# There are some problems now with this protocol
# First, the client's one and the server's one are differnt.

# While the client should just have the content and the type access.
# The server should also contain much more information about the file
# Like what users use it, what their access and more. Most likely I will attach files to users.
# And not users to files...

# NOTE ! The Client doesnt save the file. Only raw memory data.

class c_virtual_file:

    _name:              str     # File's name. Indcluding the type.

    _original_path:     str     # Original file. DO NOT TOUCH
    _normal_path:       str     # Project new folder path

    _content:           list    # This will be used for client
    _lines_used:        list

    def __init__( self, name: str ):
        """
            Default constructor for virtual file.
            
            Receive : 
            - name - File name ( like test.py )

            Returns :   File object
        """

        self._name              = name
        self._normal_path       = None
        self._content           = [ ]
        self._lines_used        = [ ]

    
    def name( self ) -> str:
        """
            Get file name.

            Receive :   None

            Returns :   String value
        """

        return self._name
    

    def create_new( self, path: str ):
        """
            Create new empty file.

            Receive :   
            - path - Path for that new file

            Returns :   None
        """

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
        """
            Copy existing file into new file.

            Receive :
            - path_from - Path to a original file
            - path_to   - New path for new file

            Returns :   None
        """

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
        """
            Convert the name with type into tuple.

            Receive :   None

            Returns :   Tuple ( name, type )
        """

        information = self._name.rsplit( ".", 1 )

        return information[ 0 ], information[ 1 ]
    

    def get_file_size( self ) -> int | None:
        """
            Get file size.

            Receive :   None

            Returns :   File size
        """

        if self._normal_path is None:
            return
        
        file_path = f"{ self._normal_path }\\{ self._name }"
        
        size = os.path.getsize( file_path )

        return size


    def read_from_file( self, start: int, end: int ) -> bytes | None:
        """
            Read specific chunk from the file.

            Receive :
            - start - Start byte of the chunk
            - end   - End file of the chunk

            Returns :   Bytes
        """

        if self._normal_path is None:
            return
        
        file_path = f"{ self._normal_path }\\{ self._name }"

        data = b""

        with open( file_path, "rb" ) as file:
            file.seek( start )

            data = file.read( end - start )

        return data
    

    def clear_content( self ):
        """
            Clears file's content.

            Receive :   None

            Returns :   None
        """

        self._content.clear( )


    def add_file_content( self, line: str ):
        """
            Add line for the file.

            Receive :
            - line - Text of a specific line

            Returns :   None
        """
        
        self._content.append( line )

    
    def read_file_content( self ) -> list:
        """
            Read from file's content.

            Receive :   None

            Returns :   List with lines
        """

        return self._content.copy( )

    
    def lock_line( self, line: int ):
        """
            Lock line, aka set it as used.

            Receive :
            - line - Line number

            Returns :   None
        """

        #if line < 0 or line > len( self._content ):
        #    return
        
        self._lines_used.append( line )

    
    def unlock_line( self, line: int ):
        """
            Unlocks line.

            Receive :
            - line - Line number

            Returns :   None
        """

        #if line < 0 or line > len( self._content ):
        #    return
        
        self._lines_used.remove( line )

    
    def is_line_locked( self, line: int ) -> bool:
        """
            Is specific line locked.

            Receive :
            - line - Line number

            Returns :   Result
        """
        
        for _line in self._lines_used:
            if _line == line:
                return True
            
        return False
    

    def get_locked_lines( self ) -> list:
        """
            Get all the locked lines.

            Receive :   None

            Returns :   List
        """

        return self._lines_used.copy( )

    

class c_files_manager_protocol:

    _last_error:    str
    _files:         dict

    # region : Initialize protocol

    def __init__( self ):
        """
            Default constructor for Files protocol.

            Receive :   None

            Returns :   Protocl object
        """

        self._last_error    = ""
        self._files         = { }

    # endregion

    # region : Shared

    def get_files( self ) -> dict:
        """
            Get all registered files.

            Receive :   None

            Returns :   Dict with files
        """

        return self._files

    
    def share_files( self ) -> str:
        """
            Share files names.

            Receive :   None

            Returns :   List with files
        """

        files_list = [ ]

        for file in self._files:
            file: c_virtual_file = self._files[ file ]

            name = file.name( )
            if not name.endswith( "_changes.txt" ):
                files_list.append( name )

        return self.format_message( FILES_COMMAND_RES_FILES, files_list )

    
    def format_message( self, message: str, arguments: list ):
        """
            Format message for Files Protocol.

            Receive :
            - message   - Command to send
            - arguments - Arguments to follow it

            Returns :   String value
        """

        return f"{ FILES_MANAGER_HEADER }::{ message }->{ "->".join( arguments ) }"


    def parse_message( self, message: str ):
        """
            Parse information from Files Protocol message.

            Receive :
            - message - String value to parse

            Returns : Tuple ( cmd, list[arguments] )
        """

        first_parse = message.split( "::" )
        
        information = first_parse[ 1 ].split( "->" )
        command     = information[ 0 ]

        # Remove command from arguments
        information.pop( 0 )

        return command, information

    # endregion

    # region : Register

    def create_new_file( self, name: str ) -> c_virtual_file:
        """
            Create new virtual file instance.

            Receive :
            - name - File name

            Returns : Virtual File object
        """

        new_file = c_virtual_file( name )
        self._files[ name ] = new_file

        return new_file

    # endregion

    # region : Utilities

    def search_file( self, name: str ) -> c_virtual_file | None:
        """
            Search a virtual file based on name.

            Receive :
            - name - File's name

            Returns :   File object or None on fail
        """

        if name in self._files:
            return self._files[ name ]
        
        return None
    

    def clear_all( self ):
        """
            Clears all the files content.

            Receive :   None

            Returns :   None
        """

        for file_name in self._files:
            file: c_virtual_file = self._files[ file_name ]
            file.clear_content( )


    def get_header( self ) -> str:
        return "FL_UNK"
    
    def get_last_error( self ):
        return self._last_error

    # endregion