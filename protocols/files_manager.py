"""
    project     : Digital Editor

    type:       : Protocol
    file        : Files Manager

    description : Files Manager Protocol class
"""

from utilities.wrappers import safe_call
from utilities.debug    import *

import shutil
import base64
import json
import time
import os

FILES_MANAGER_HEADER = "FL_UNK"

FILES_COMMAND_REQ_FILES = "ReqFiles"
FILES_COMMAND_RES_FILES = "ResFiles"

FILES_COMMAND_GET_FILE = "GetFileCont"
FILES_COMMAND_SET_FILE = "SetFileCont"

FILES_COMMAND_PREPARE_UPDATE    = "PrepUpdateLine"
FILES_COMMAND_PREPARE_RESPONSE  = "ResPrepUpdate"
FILES_COMMAND_UPDATE_LINE       = "UpdateLine"
FILES_COMMAND_DELETE_LINE       = "DelLine"
FILES_COMMAND_DISCARD_UPDATE    = "DisUpdateLine"
FILES_COMMAND_UPDATE_FILE       = "UpdateFile"   # Use this command to update file access level and register new files
FILES_COMMAND_UPDATE_FILE_NAME  = "ChangeFileName"

# This command is extremely important.
# FILES_COMMAND_APPLY_UPDATE - Update_ENUM - Update details
FILES_COMMAND_APPLY_UPDATE      = "ApplyUpdateLine"

FILE_ACCESS_LEVEL_HIDDEN    = 0     # This file should be hidden ( used only for host )
FILE_ACCESS_LEVEL_EDIT      = 1     # This file can be edited
FILE_ACCESS_LEVEL_LIMIT     = 2     # This file cannot be edited

FILE_UPDATE_CONTENT = 0
FILE_UPDATE_NAME    = 1


class c_virtual_file:

    # NOTE ! Virtual files can be reference to a real file or just empty name without content

    _name:                  str     # File's name. Including the type.
    _log_changes:           bool    # Should log changes of the file

    _original_path:         str     # Original file. DO NOT TOUCH
    _normal_path:           str     # Project new folder path

    _access_level:          int     # File's access level
    _locked_lines:          list    # File's locked lines

    _content:               list    # File's content

    # region : Initialize

    def __init__( self, name: str, access_level: int = 0, log_changes: bool = True ):
        """
        Default constructor for virtual file object.

        Receive:
        - name (str) File's name
        - log_changes (bool, optional) Enable logging for any file changes.

        Returns: 
        - c_virtual_file: Virtual file object.
        """

        self._name          = name
        self._log_changes   = log_changes

        self._access_level  = access_level

        self._original_path = None
        self._normal_path   = None

        self._content       = [ ]
        self._locked_lines  = [ ]


    def __create_logging_file( self ):
        """
        Create a file to log each change for this file.

        Receive:  None

        Returns:  None
        """

        if not self._log_changes:
            return
        
        file_name, file_type = self.name( True )
        
        file_name = f"{ file_name }_changes.txt"
        file_path = f"{ self._normal_path }\\{ file_name }"

        if os.path.exists( file_path ):
            return

        with open( file_path, "w" ) as f:
            json.dump( 
                { 
                    "original_file":    self._name,
                    "file_type":        file_type
                }, 
            f )

    # endregion

    # region : Creation and referencing

    def create( self, path: str, message: str = "\n" ):
        """
        Create new empty file.

        Receive:  
        - path (str) Path for that new file
        - message (str, optional): Default value to add to an empty file

        Returns:  
        - any: None or string on fail
        """

        file_path = f"{ path }\\{ self._name }"

        try:
            os.makedirs( os.path.dirname( file_path ), exist_ok=True )

            with open( file_path, 'w' ) as f:
                f.write( message + "\n" )
                f.write( "\n" )

            self._normal_path = path

            self.__create_logging_file( )

            return None
        
        except Exception as e:
            return str( e )
    

    def copy( self, path_from: str, path_to: str ):
        """
        Copy existing file into new file.

        Receive :
        - path_from (str): Path to an original file
        - path_to (str): New path for the new file

        Returns:  
        - any: None or string on fail
        """

        file_path_from: str = f"{ path_from }\\{ self._name }"
        file_path_to:   str = f"{ path_to }\\{ self._name }"

        if not os.path.exists( file_path_from ):
            return f"Failed to find original file { file_path_from }"
        
        try:
            os.makedirs( os.path.dirname( file_path_to ), exist_ok=True )

            shutil.copy( file_path_from, file_path_to )

            self._normal_path = path_to

            self.__create_logging_file( )

        except Exception as e:
            return str( e )
    

    def attach( self, path: str ):
        """
        Unlike .copy( ) or .create( ), here we know that we have file
        that previously was a c_virtual_file, and now we just need to attach
        it for the object.

        Receive:
        - path (str): File's path

        Returns: None 
        """

        self._normal_path = path

        self.__create_logging_file( )

    
    def copy_instance( self, original: any ):
        """
        Copy one virtual_file information into this instance.

        Receive :
        - original (c_virtual_file) Original instance of the virtual file

        Returns:  
        - c_virtual_file: This object
        """

        # The funny thing that unlike other programing lng,
        # This works becuase in python there is no private/protected attr types
        self._original_path = original._original_path
        self._normal_path   = original._normal_path
        self._locked_lines  = original._locked_lines
        
        return self 

   # endregion

    # region : File information

    @safe_call( c_debug.log_error )
    def name( self, should_parse: bool = False ) -> any:
        """
        Returns the file's name.
        Can return ( file_name, file_type ) or full file name.

        Receive :
        - should_parse (bool, optional): Should the returns value will be the name parsed into name and type

        Returns:  
        - any: str on full name or tuple on split
        """

        if not should_parse:
            return self._name
        
        information = self._name.rsplit( ".", 1 )

        return information[ 0 ], information[ 1 ]
    

    @safe_call( c_debug.log_error )
    def update_name( self, new_name: str, should_operate: bool = False ) -> bool:
        """
        Update name for the virutal file.

        Receive:
        - new_name (str): New name for the file. Including type
        - should_operate (bool, optional): Should perform .raname call

        Returns:
        - bool: True on success or None of fail
        """

        file_path: str = f"{ self._normal_path }\\{ self._name }"
        name_path: str = f"{ self._normal_path }\\{ new_name }"

        if should_operate:
            os.rename( file_path, name_path )

        if should_operate and self._log_changes:
            file_name, file_type = self.name( True )

            file_path = f"{ self._normal_path }\\{ file_name }_changes.txt"
            name_path = f"{ self._normal_path }\\{ new_name.rsplit( '.', 1 )[ 0 ] }_changes.txt"

            os.rename( file_path, name_path )
        
        self._name = new_name

        return True
    

    def access_level( self, new_value: int = None ) -> int:
        """
        Get/Set virtual file's access level.

        Receive:  
        - new_value (int, optional): New access level for virtual_file

        Returns:  
        - int: Current access level
        """

        if new_value is None:
            return self._access_level

        self._access_level = new_value
        return self._access_level


    def size( self, virtual_content: bool = False ) -> int:
        """
        Get virtual file's content size.

        Receive:  
        - virtual_content (bool, optional): Count the virtual content and not the real file

        Returns:  
        - int: File's size
        """

        if virtual_content:
            size: int = 0

            for line in self._content:
                size += len( line )

            return size

        if self._normal_path is None:
            raise Exception( "Invalid file path" )
        
        file_path:  str = f"{ self._normal_path }\\{ self._name }"
        if not os.path.exists( file_path ):
            return -1
        
        size:       int = os.path.getsize( file_path )

        return size

    # endregion

    # region : File content

    def read( self, start: int, end: int ) -> any:
        """
        Read specific chunk from the file.

        Receive :
        - start (int): Start byte of the chunk
        - end (int): End file of the chunk

        Returns:  
        - bytes: A specific content from the real file
        """

        if self._normal_path is None:
            return None
        
        file_path   = f"{ self._normal_path }\\{ self._name }"
        data        = b''

        with open( file_path, 'rb' ) as f:
            f.seek( start )
            data = f.read( end - start )

        return data
    

    def read_lines( self ) -> list:
        """
        Reads file's data and converts into Lines.

        Receive: None

        Returns:  
        - list: List of string that represents the file content lines
        """

        if self._normal_path is None:
            return None
        
        file_path   = f"{ self._normal_path }\\{ self._name }"
        data        = b''

        with open( file_path, 'rb' ) as f:
            data = f.read( )

        if data.endswith( b'\n' ):
            data = data + b'\r'

        return data.decode( ).splitlines( )
    

    def add_content_line( self, line: str ):
        """
        Add line for the file.

        Receive :
        - line (str): Text of a specific line

        Returns: None
        """
        
        self._content.append( line )

    
    def clear_content( self ):
        """
        Clear file's content.

        Receive: None

        Returns: None
        """

        self._content.clear( )
    

    def read_file_content( self ) -> list:
        """
        Read from file's content.

        Receive: None

        Returns: 
        - list: Virtual file content
        """

        return self._content
    
    # endregion

    # region : File actions

    @safe_call( c_debug.log_error )
    def change_line( self, line: int, new_lines: list, change_log: dict ) -> bool:
        """
        Preform change in files lines.

        Receive :
        - line (int): Line to change
        - new_lines (list) New lines to add
        - change_log (dict): Ready to add change log

        Returns: 
        - bool: Result if success or fail

        Note ! This function removes the [line] and adds the new_lines[0] instead.
        """

        if self._normal_path is None:
            return False
        
        file_path   = f"{ self._normal_path }\\{ self._name }"

        # never use .readlines( ). 
        # This trash actually breaks everything
        # It has incorrect encoding and more

        data = b''
        with open( file_path, "rb" ) as f:
            data = f.read( )

        if data.endswith( b'\n' ):
            data = data + b'\r'

        lines: list = data.decode( ).splitlines( )
        del data

        line -= 1
        removed_line = lines.pop( line )

        for new_line in new_lines:
            new_line: str = new_line
            lines.insert( line, new_line )

            line += 1

        with open( file_path, "wb" ) as f:
            f.write( os.linesep.join( lines ).encode( ) )
        
        lines.clear( )

        if not self._log_changes:
            return True
        
        file_name, file_type = self.name( True )
        
        file_name = f"{ file_name }_changes.txt"
        file_path = f"{ self._normal_path }\\{ file_name }"

        changes: dict
        with open( file_path, "r" ) as f:
            changes = json.load( f )

        cur_time = time.strftime( "%y-%m-%d %H:%M:%S", time.localtime( ) )

        change_log[ "line" ]    = line - len( new_lines ) + 1
        change_log[ "removed" ] = removed_line
        change_log[ "added" ]   = new_lines

        changes[ cur_time ] = change_log

        with open( file_path, "w" ) as f:
            json.dump( changes, f )

        return True

    
    @safe_call( c_debug.log_error )
    def remove_line( self, line: int, change_log: dict ) -> bool:
        """
        Remove a specific line from the file.

        Receive :
        - line (int): Line to remove
        - change_log (dict): Ready to add change log

        Returns: 
        - bool: Result if success or fail
        """

        if self._normal_path is None:
            return False
        
        file_path   = f"{ self._normal_path }\\{ self._name }"

        data = b''
        with open( file_path, "rb" ) as f:
            data = f.read( )

        if data.endswith( b'\n' ):
            data = data + b'\r'

        lines: list = data.decode( ).splitlines( )
        del data

        removed_line: str = lines.pop( line - 1 )

        with open( file_path, "wb" ) as f:
            f.write( os.linesep.join( lines ).encode( ) )

        lines.clear( )

        if not self._log_changes:
            return True
        
        file_name, file_type = self.name( True )
        
        file_name = f"{ file_name }_changes.txt"
        file_path = f"{ self._normal_path }\\{ file_name }"

        changes: dict
        with open( file_path, "r" ) as f:
            changes = json.load( f )

        cur_time = time.strftime( "%y-%m-%d %H:%M:%S", time.localtime( ) )

        change_log[ "line" ]    = line
        change_log[ "removed" ] = removed_line

        changes[ cur_time ] = change_log

        with open( file_path, "w" ) as f:
            json.dump( changes, f )

        return True

    # endregion

    # region : File lines

    def is_line_locked( self, line: int) -> bool:
        """
        Check if a specific line is locked.

        Receive :
        - line (int): Line number

        Returns:  
        - bool: Result
        """

        # I dont want to use .index and catch Exception...

        for item in self._locked_lines:
            if item == line:
                return True
            
        return False
    

    def lock_line( self, line: int ):
        """
        Lock specific line.

        Receive :
        - line (int): Line number

        Returns: None
        """

        self._locked_lines.append( line )


    def unlock_line( self, line: int ):
        """
        Unlock specific line.

        Receive:
        - line (int): Line number

        Returns: None
        """

        #if not self.is_line_locked( line ):
        #    return
        
        self._locked_lines.remove( line )


    def locked_lines( self ) -> list:
        """
        Get the locked lines of the file.

        Receive: None

        Returns: 
        - list: List of locked lines
        """ 

        return self._locked_lines
    
    # endregion
    

class c_files_manager_protocol:

    _last_error:    str
    _files:         dict

    # region : Initialize protocol

    def __init__( self ):
        """
        Default constructor for Files protocol.

        Receive: None

        Returns: 
        - c_files_manager_protocol: Protocol object
        """

        self._last_error    = ""
        self._files         = { }

    # endregion

    # region : Shared

    def get_files( self ) -> dict:
        """
        Get all registered files.

        Receive: None

        Returns: 
        - dict: A dict with virtual files refs.
        """

        return self._files

    
    def share_files( self ) -> str:
        """
        Share files names.

        Receive: None

        Returns: 
        - list: List of files indexes
        """

        files_list = [ ]

        for file in self._files:
            file: c_virtual_file = self._files[ file ]

            access_level: int = file.access_level( )

            if access_level == FILE_ACCESS_LEVEL_HIDDEN:
                continue

            files_list.append( file.name( ) )
            files_list.append( str( access_level ) )

        return self.format_message( FILES_COMMAND_RES_FILES, files_list )

    
    def format_message( self, message: str, arguments: list ):
        """
        Format message for Files Protocol.

        Receive :
        - message (str): Command to send
        - arguments (list): Arguments to follow it

        Returns:  
        - str: Formated string value
        """

        message: str = base64.b64encode( message.encode( ) ).decode( )

        for index in range( 0, len( arguments ) ):
            arguments[ index ] = base64.b64encode( str( arguments[ index ] ).encode( ) ).decode( )

        return f"{ FILES_MANAGER_HEADER }::{ message }->{ '->'.join( arguments ) }"


    def parse_message( self, message: str ):
        """
        Parse information from Files Protocol message.

        Receive :
        - message - String value to parse

        Returns:
        - tuple: Command and list of arguments
        """

        first_parse = message.split( "::" )
        
        information = first_parse[ 1 ].split( "->" )
        for index in range( 0, len( information ) ):
            information[ index ] = base64.b64decode( information[ index ].encode( ) ).decode( )

        command = information[ 0 ]

        # Remove command from arguments
        information.pop( 0 )

        return command, information

    # endregion

    # region : Register

    def create_new_file( self, name: str, access_level: int = 0, log_changes: bool = True ) -> c_virtual_file:
        """
        Create new virtual file instance.

        Receive :
        - name (str) File name
        - access_level (int, optional): Access level of the file
        - log_changes (bool, optional): Should log changes

        Returns:
        - c_virtual_file: Virtual File object
        """

        new_file = c_virtual_file( name, access_level, log_changes )
        self._files[ name ] = new_file

        return new_file

    
    def copy( self, virtual_file: c_virtual_file ) -> c_virtual_file:
        """
        Copy virtual files content into a new instance in this handle.

        Receive :
        - virtual_file (c_virtual_file): Original copy of the virtual file instance

        Returns:  
        - c_virtual_file: New instance of virtual file
        """

        new_file = c_virtual_file( virtual_file.name( ), virtual_file.access_level( ), True )
        new_file.copy_instance( virtual_file )

        self._files[ new_file.name( ) ] = new_file

        return new_file

    # endregion

    # region : Utilities

    def search_file( self, name: str ) -> c_virtual_file:
        """
        Search a virtual file based on name.

        Receive :
        - name (str): File's name

        Returns:  
        - c_virtual_file: File object or None on fail
        """

        if name in self._files:
            return self._files[ name ]
        
        return None
    

    def clear_all( self ):
        """
        Clears all the files content.

        Receive: None

        Returns: None
        """

        for file_name in self._files:
            file: c_virtual_file = self._files[ file_name ]
            file.clear_content( )


    def remove_file( self, name: str ):
        """
        Unregister a specific file from the files protocol.

        Receive :
        - name (str): File's name

        Returns: None
        """

        del self._files[ name ]

    
    def update_name( self, old_index: str, new_index: str, should_operate: bool = False ) -> c_virtual_file:
        """
        Update a virtual file name.

        Receive: 
        - old_index (str): Old file name
        - new_index (str): New file name
        - should_operate (bool, optional): Should use .rename operation

        Returns:
        - c_virtual_file: Updated file ref
        """

        file: c_virtual_file = self.search_file( old_index )
        if not file:
            return None
        
        file.update_name( new_index, should_operate )
        
        self._files[ new_index ] = file
        del self._files[ old_index ]
        
        return file


    def get_header( self ) -> str:
        """
        Get protocol's header.

        Receive: None

        Returns:
        - str: Files protocol message header
        """

        return FILES_MANAGER_HEADER
    

    def get_last_error( self ):
        """
        Get last error that occured in the protocol.

        Receive: None

        Returns:
        - str: Error message
        """
        
        return self._last_error

    # endregion