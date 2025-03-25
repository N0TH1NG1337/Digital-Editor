"""
    project     : Digital Editor

    type:       : User
    file        : Business Logic

    description : User Business Logic class
"""

from protocols.network          import *
from protocols.files_manager    import *
from protocols.registration     import *
from protocols.security         import *
from utilities.event            import c_event
from utilities.math             import math
from utilities.wrappers         import safe_call, standalone_execute

import threading
import base64
import queue
import time
import os

TIMEOUT_MESSAGE = 0.5

class c_user_business_logic:

    # region : Private Attributes

    _network:       c_network_protocol
    _files:         c_files_manager_protocol
    _registration:  c_registration
    _security:      c_security

    _information:   dict
    _events:        dict
    _commands:      dict

    # endregion

    # region : Initialization user business logic

    def __init__( self ):
        """
            Default constructor for user business logic.

            Receive:    None

            Returns:    None
        """

        self.__initialize_protocols( )

        self.__initialize_events( )

        self.__initialize_information( )

    
    def __initialize_protocols( self ):
        """
            Initialize protocols for host business logic.

            Receive:    None

            Returns:    None
        """

        self._network       = c_network_protocol( )

        self._files         = c_files_manager_protocol( )

        self._registration  = c_registration( )
        
        self._security      = c_security( )
    

    def __initialize_events( self ):
        """
            Initialize events for user business logic.

            Receive:    None

            Returns:    None
        """

        self._events = {

            "on_connect":           c_event( ),

            "on_pre_disconnect":    c_event( ),
            "on_post_disconnect":   c_event( ),

            # Complex events 
            "on_refresh_files":     c_event( ), # Called when user request to refresh files list
            "on_register_file":     c_event( ), # ?

            "on_file_set":          c_event( ), # Called whenever the host is going to send the user specific file content.
            "on_file_update":       c_event( ), # ?

            "on_accept_line":       c_event( ), # Called when the host response with the line lock request.
            "on_line_lock":         c_event( ), # Called when the host forces the user to lock a specific line. ( Used for other users locked lines )
            "on_line_unlock":       c_event( ), # Called when the host unlocks a specific line for this user.

            "on_line_update":       c_event( ), # Called when the host updates line / lines. 
            "on_line_delete":       c_event( ), # Called when the host deletes a specific line. ( Line removal is other process than update )

            "on_level_update":      c_event( )  # Called when the host updates a access level to a specific file
        }

    
    def __initialize_information( self ):
        """
            Initialize information for user business logic.

            Receive:    None

            Returns:    None
        """

        self._information = {
            "is_connected":     False,  # Is the user connected
            "last_error":       "",     # Last error message

            "access_levels":    {
                FILE_ACCESS_LEVEL_HIDDEN:   "Hidden",
                FILE_ACCESS_LEVEL_EDIT:     "Edit",
                FILE_ACCESS_LEVEL_LIMIT:    "Limit"
            }
        }

        self._commands = {
            FILES_COMMAND_RES_FILES:        self.__command_received_files,
            FILES_COMMAND_SET_FILE:         self.__command_set_file,

            FILES_COMMAND_PREPARE_RESPONSE: self.__commad_response_line_lock,

            FILES_COMMAND_PREPARE_UPDATE:   self.__command_line_lock,
            FILES_COMMAND_DISCARD_UPDATE:   self.__command_line_unlock,

            FILES_COMMAND_UPDATE_LINE:      self.__command_line_update,
            FILES_COMMAND_DELETE_LINE:      self.__command_line_delete,

            FILES_COMMAND_CHANGE_LEVEL:     self.__command_update_level
        }

    # endregion

    # region : Connection

    def connect( self, project_code: str, username: str, password: str, register_type: str ) -> bool:
        """
            Establish connection with the host.

            Receive :
            - project_code  - Project code received from host
            - username      - Current username
            - password      - Current password

            Receive :   Result
        """

        # We receive code that need to be resolved into ip and port
        ip, port = self.__resolve_code( project_code )

        if not self.__try_to_connect( ip, port ):
            return False
        
        if not self.__preform_safety_registration( ):
            self.__end_connection( )
            return False

        if not self.__preform_registration( username, password, register_type ):
            self.__end_connection( )
            return False

        self.__attach_process( )

        self.__event_connect( ip, port )

        self.request_files( )

        self._information[ "is_connected" ] = True

        return True

    
    def __resolve_code( self, project_code: str ):
        """
            Convert the code into information. 
            
            Receive :
            - project_code - String value

            Returns : Tuple ( ip, port )
        """

        result = base64.b64decode( project_code ).decode( )

        data = result.split( ":" )

        return data[0], int( data[1] )
    

    def __try_to_connect( self, ip: str, port: int ) -> bool:
        """
            Try to establish connection with the server.

            Receive : 
            - ip    - Server IP
            - port  - Server Port

            Returns :   Result
        """

        try:
            self._network.start_connection( CONNECTION_TYPE_CLIENT, ip, port )
            
            return True
        except Exception as e:

            # TODO ! ADD DEBUG OPTIONS LATER
            return False
        
    
    def __preform_safety_registration( self ) -> bool:
        """
            Initialize and establish safety for the communication.

            Receive :   None

            Returns :   None
        """

        # Quick 3 hand shake thing :P

        # Share this client public key
        self._network.send_bytes( self._security.share( SHARE_TYPE_LONG_PART ) )
        
        # Receive host's public key
        self._security.share( SHARE_TYPE_LONG_PART, self._network.receive( ) )

        # Receive the quick key
        self._security.share( SHARE_TYPE_QUICK_PART, self._network.receive( ) )

        # TODO ! Add check if everything is fine.

        return True

    
    def __preform_registration( self, username: str, password: str, register_type: str ) -> bool:
        """
            Preform a registration process for this user.

            Receive :
            - username  - Current user username
            - password  - Current user password

            Returns :   Result if success
        """
        
        register_command = {
            "Register":     REGISTRATION_COMMAND_REG,
            "Login":        REGISTRATION_COMMAND_LOG
        }

        message: str = self._registration.format_message( register_command[ register_type ], [ username, password ] )

        value: bytes = self._security.strong_protect( message.encode( ) )
        if not value:
            # This can happen only if the length is more than 190 bytes.
            # This mean that the username + password are ( 190 - 16 ) 174 bytes
            return False
        
        self._network.send_bytes( value )

        # Preform the checks here...
        command, arguments = self._registration.parse_message( self.__receive( ).decode( ) )
        if command != REGISTRATION_RESPONSE:
            return False
        
        success:    bool    = arguments[ 0 ] == "1"

        if not success:
            self._information[ "last_error" ] = arguments[ 1 ]
            return False
        
        return True

    
    def disconnect( self ):
        """
            Disconnect from the server.

            Receive :   None

            Returns :   None
        """

        if not self._information[ "is_connected" ]:
            raise Exception( "Cannot disconnect if you are not connected" )
        
        # Before we disconnect, in somecases, we would like to do some more operations,
        # Like send some information to server so it will save it.
        # Therefore, we can use the pre_disconnect event to send all unsaved information
        # or do this kinds of operations
        self.__event_pre_disconnect( )

        # Notify the server we disconnect
        self.__send_quick_message( DISCONNECT_MSG )

        # In general words, we just notify the server we are going to disconnect from it,
        # and if the server tries to send more information, it will be just lost.
        self.__end_connection( )


    def __end_connection( self ):
        """
            Forcely end connection with server, without notifing it.

            Receive :   None

            Returns :   None
        """

        self._network.end_connection( )

        # Invoke post_disconnect event
        # After we done with the connection, in some cases we will just need to clean up somethings.
        self.__event_post_disconnect( )

    # endregion

    # region : Process

    def __attach_process( self ):
        """
            Attach different processes into threads.

            Receive :   None

            Returns :   None
        """

        self._information[ "messages_thread" ] = self.__process_handle_messages( )

    
    @standalone_execute
    def __process_handle_messages( self ):
        """
            Process function to receive messages from server.

            Receive :   None

            Returns :   None
        """

        while self._network.is_valid( ):

            # Receive the key and remove the protection
            message: bytes = self.__receive( )
            if not message:
                continue

            self.__handle_receive( message.decode( ) )

    # endregion

    # region : Messages handle

    def __receive( self ) -> bytes:
        """
            Wrap the receive and the security part.

            Receive :   None

            Returns :   Received Bytes
        """

        # Receive the key and remove the protection
        key: bytes = self._security.remove_strong_protection( self._network.receive( TIMEOUT_MESSAGE ) )
        if not key:
            return None
                
        # Receive the message
        message: bytes = self._network.receive( TIMEOUT_MESSAGE )

        # If there is no message, continue
        if message is None:
            return None

        # Remove shuffle and protection
        return self._security.remove_quick_protection( self._security.unshuffle( key, message ) )


    def __handle_receive( self, receive: str ):
        """
            Handles messages received from the host.

            Receive :
            - receive - Message content

            Returns :   None
        """

        if receive == DISCONNECT_MSG:
            return self.__end_connection( )
        
        if receive.startswith( self._files.get_header( ) ):
            return self.__handle_files_message( receive )

    
    def __handle_files_message( self, message: str ):
        """
            Handle file's protocol message.

            Receive :   None
            - message - Message from server

            Returns :   None
        """

        command, arguments = self._files.parse_message( message )

        if command in self._commands:
            return self._commands[ command ]( arguments )

    # endregion

    # region : Commands

    @safe_call( c_debug.log_error )
    def __command_received_files( self, arguments: list ):
        """
            Command method for receiving files.

            Receive :
            - arguments - List containing files details

            Returns : None
        """

        length = len( arguments )

        if length == 1 and arguments[ 0 ] == "":
            return

        if length % 2 != 0:
            raise Exception( f"Invalid arguments list. Number of arguments must be even.\nReceived : { arguments }" )
            
        for i in range( 0, length, 2 ):

            name:           str = arguments[ i ] 
            access_level:   int = int( arguments[ i + 1 ] ) 

            self.__event_register_file( name, access_level )

    
    @safe_call( c_debug.log_error )
    def __command_set_file( self, arguments: list ):
        """
            Command method for setting file content.

            Receive :
            - arguments - List containing file details

            Returns :   None
        """

        file_name: str = arguments[ 0 ]
        file_size: int = int( arguments[ 1 ] )

        key: bytes = self._security.remove_strong_protection( self._network.receive( ) )
        if not key:
            return
                
        message: list = self._network.receive( -1, True )
        if message is None:
            return
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            raise Exception( f"Failed to find file { file_name }" )

        data = b''
        for chunk in message:
            data += self._security.remove_quick_protection( self._security.unshuffle( key, chunk ) )

        # Clear list with information to avoid filling the memory
        message.clear( )

        if len( data ) != file_size:
            raise Exception( f"Failed to receive normally file { file_name }" )

        lines: list = data.decode( ).splitlines( )
        del data

        self.__event_file_set( file )

        for line in lines:
            file.add_content_line( line )

        lines.clear( )

        self.__event_file_update( file )

        file.clear_content( )


    @safe_call( c_debug.log_error )
    def __commad_response_line_lock( self, arguments: list ):
        """
            Command method for geting line lock response.

            Receive :
            - arguments - List containing file details

            Returns :   None
        """

        file_name:  str = arguments[ 0 ]
        line:       int = math.cast_to_number( arguments[ 1 ] )
        accept:     bool = arguments[ 2 ] == "0"

        if line is None:
            return
        
        self.__event_accept_line( file_name, line, accept )


    @safe_call( c_debug.log_error )
    def __command_line_lock( self, arguments: list ):
        """
            Command method for line lock.

            Receive :
            - arguments - List containing file details

            Returns :   None
        """

        file_name:  str = arguments[ 0 ]
        line:       int = math.cast_to_number( arguments[ 1 ] )
        user:       str = len( arguments ) == 3 and arguments[ 2 ] or "Unk"

        if line is None:
            return
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        # Maybe lock the line here ? for later checks ?
        
        self.__event_line_lock( file.name( ), line, user )

    
    @safe_call( c_debug.log_error )
    def __command_line_unlock( self, arguments: list ):
        """
            Command method for line unlock.

            Receive :
            - arguments - List containing file details

            Returns :   None
        """

        file_name:  str = arguments[ 0 ]
        line:       int = math.cast_to_number( arguments[ 1 ] )

        if line is None:
            return
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        # TODO ! Check if the line is locked
        
        self.__event_line_unlock( file.name( ), line )

    
    @safe_call( c_debug.log_error )
    def __command_line_update( self, arguments: list ):
        """
            Command method for line update.

            Receive :
            - arguments - List containing file details

            Returns :   None
        """

        file_name:      str = arguments[ 0 ]
        line:           int = math.cast_to_number( arguments[ 1 ] )
        lines_count:    int = math.cast_to_number( arguments[ 2 ] )

        if line is None or lines_count is None:
            return
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        new_lines: list = [ ]
        for i in range( lines_count ):

            received_line: bytes = self.__receive( )
            if not received_line:
                # Failed to do something
                continue

            fixed_line: str = base64.b64decode( received_line ).decode( )
            del received_line

            # Maybe better approuch will be to add '\n' for each line...
            if fixed_line == "\n":
                fixed_line = ""
            
            new_lines.append( fixed_line )

        self.__event_line_update( file.name( ), line, new_lines )


    @safe_call( c_debug.log_error )
    def __command_line_delete( self, arguments: list ):
        """
            Command method for line delete.

            Receive :
            - arguments - List containing file details

            Returns :   None
        """

        file_name:      str = arguments[ 0 ]
        line:           int = math.cast_to_number( arguments[ 1 ] )

        if line is None:
            return
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        self.__event_line_delete( file.name( ), line )

    
    @safe_call( c_debug.log_error )
    def __command_update_level( self, arguments: list ):
        """
            Command method for updating access level to a file.

            Receive :
            - arguments - List containing file details

            Returns :   None
        """

        file_name:      str = arguments[ 0 ]
        access_level:   int = math.cast_to_number( arguments[ 1 ] )

        if access_level is None:
            return
        
        if not access_level in self._information[ "access_levels" ]:
            return

        file: c_virtual_file = self._files.search_file( file_name )
        if not file and access_level != FILE_ACCESS_LEVEL_HIDDEN:
            # Create new one
            file = self._files.create_new_file( file_name, access_level, False )
            
            return self.__event_level_update( file.name( ), file.access_level( ) )

        if not file:
            raise Exception( f"Failed to find file { file_name }" )

        if access_level == FILE_ACCESS_LEVEL_HIDDEN:
            # Remove
            self._files.remove_file( file_name )

        else:
            # Change to new access level
            file.access_level( access_level )

        self.__event_level_update( file_name, access_level )


    # endregion

    # region : Communication

    def __send_quick_message( self, message: str ):
        """
            Send a quick message to the host.

            Receive :
            - message - Message to send

            Returns :   None
        """

        key: bytes = self._security.generate_shaffled_key( )
        
        self._network.send_bytes( self._security.strong_protect( key ) )
        self._network.send_bytes( self._security.shuffle( key, self._security.quick_protect( message.encode( ) ) ) )

    
    def __send_quick_bytes( self, data: bytes ):
        """
            Send a quick bytes to the host.

            Receive :
            - message - Message to send

            Returns :   None
        """

        key: bytes = self._security.generate_shaffled_key( )
        
        self._network.send_bytes( self._security.strong_protect( key ) )
        self._network.send_bytes( self._security.shuffle( key, self._security.quick_protect( data ) ) )


    def request_files( self ):
        """
            Request files from the host.

            Receive :   None

            Returns :   None
        """

        if not self._network.is_valid( False ):
            return

        message: str = self._files.format_message( FILES_COMMAND_REQ_FILES, ["unk"] )

        self.__send_quick_message( message )

    
    def request_file( self, file_name: str ):
        """
            Request specific file from the host.

            Receive :
            - file_name - File name

            Returns :   None
        """

        if not self._network.is_valid( False ):
            return

        file: c_virtual_file = self._files.search_file( file_name )
        if file is None:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_GET_FILE, [ file_name ] )
        self.__send_quick_message( message )

    
    def request_line( self, file_name: str, line: int ):
        """
            Request specific line.

            Receive : 
            - file_name - File name
            - line      - Line number

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_PREPARE_UPDATE, [ file_name, str( line ) ] )
        self.__send_quick_message( message )


    def discard_line( self, file_name: str, line: int ):
        """
            Message of discard changes.

            Receive : 
            - file_name - File name
            - line      - Line number

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_DISCARD_UPDATE, [ file_name, str( line ) ] )
        self.__send_quick_message( message )

    
    def update_line( self, file_name: str, line: int, lines: list ):
        """
            Message of updated lines.

            Receive :
            - file_name - File name
            - line      - Line number
            - lines     - List of changed lines

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        # We have notified the host about the update
        message: str = self._files.format_message( FILES_COMMAND_UPDATE_LINE, [ file.name( ), str( line ), str( len( lines ) ) ] )
        self.__send_quick_message( message )

        for line_str in lines:
            line_str: str = line_str
            if line_str == "":
                line_str = "\n"
            
            self.__send_quick_bytes( base64.b64encode( line_str.encode( ) ) )

    
    def delete_line( self, file_name: str, line: int ):
        """
            Message of delete line.

            Receive :
            - file_name - File name
            - line      - Line number

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_DELETE_LINE, [ file.name( ), str( line ) ] )
        self.__send_quick_message( message )

    
    def accept_offset( self, file_name: str, offset: int ):
        """
            Message to correct offset.

            Receive :
            - file_name - File name
            - offset    - Offset value

            Returns :   None
        """

        # Without this, we will have problems

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_APPLY_UPDATE, [ file.name( ), str( offset) ] )
        self.__send_quick_message( message )

    # endregion

    # region : Events

    def __event_connect( self, ip: str, port: int ):
        """
            Event callback when the user connects to the host.

            Receive :
            - ip    - Host IP
            - port  - Port to connect

            Returns :   None
        """

        event: c_event = self._events[ "on_connect" ]

        event.attach( "ip",         ip )
        event.attach( "port",       port )
        event.attach( "success",    self._information[ "is_connected" ] )

        event.invoke( )

    
    def __event_pre_disconnect( self ):
        """
            Event callback before disconnect process.

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "on_pre_disconnect" ]

        event.invoke( )

    
    def __event_post_disconnect( self ):
        """
            Event callback after disconnect process.

            Receive :   None

            Returns :   None
        """

        event: c_event = self._events[ "on_post_disconnect" ]

        event.invoke( )

    
    def __event_register_file( self, file_name: str, access_level: int ):
        """
            Event callback when the user registers a new file.

            Receive :
            - file_name     - File name
            - access_level  - File access level

            Returns :   None
        """

        self._files.create_new_file( file_name, access_level, False )

        event: c_event = self._events[ "on_register_file" ]

        event.attach( "file_name", file_name )
        event.attach( "access_level", access_level )

        event.invoke( )


    def __event_file_set( self, file: c_virtual_file ):
        """
            Event when the the host user request file.

            Receive :
            - file - Line Text

            Returns :   None
        """

        event: c_event = self._events[ "on_file_set" ]

        event.attach( "file",           file.name( ) )
        event.attach( "read_only",      file.access_level( ) == FILE_ACCESS_LEVEL_LIMIT )

        event.invoke( )

    
    def __event_file_update( self, file: c_virtual_file ):
        """
            Event callback for updating a file

            Receive :
            - file - Line Text

            Returns :   None
        """

        event: c_event = self._events[ "on_file_update" ]

        for line in file.read_file_content( ):
            event.attach( "line_text", line )
            event.invoke( )


    def __event_accept_line( self, file: str, line: int, accept: bool ):
        """
            Event callback for updating a file

            Receive :
            - file      - File's name
            - line      - Line number
            - accept    - Did host accept

            Returns :   None
        """

        event: c_event = self._events[ "on_accept_line" ]

        event.attach( "file",   file )
        event.attach( "line",   line )
        event.attach( "accept", accept )

        event.invoke( )


    def __event_line_lock( self, file: str, line: int, locked_by: str ):
        """
            Event callback for locking a line.

            Receive :
            - file      - File's name
            - line      - Line number

            Returns :   None
        """

        event: c_event = self._events[ "on_line_lock" ]

        event.attach( "file", file )
        event.attach( "line", line )
        event.attach( "user", locked_by )

        event.invoke( )


    def __event_line_unlock( self, file: str, line: int ):
        """
            Event callback for unlocking a line.

            Receive :
            - file      - File's name
            - line      - Line number

            Returns :   None
        """

        event: c_event = self._events[ "on_line_unlock" ]

        event.attach( "file", file )
        event.attach( "line", line )

        event.invoke( )

    
    def __event_line_update( self, file: str, line: int, new_lines: list ):
        """
            Event callback for updating line/lines.

            Receive :
            - file      - File's name
            - line      - Line number
            - new_lines - New lines

            Returns :   None
        """

        event: c_event = self._events[ "on_line_update" ]

        event.attach( "file",       file )
        event.attach( "line",       line )
        event.attach( "new_lines",  new_lines )

        event.invoke( )

    
    def __event_line_delete( self, file: str, line: int ):
        """
            Event callback for deleting line.

            Receive :
            - file      - File's name
            - line      - Line number

            Returns :   None
        """

        event: c_event = self._events[ "on_line_delete" ]

        event.attach( "file",       file )
        event.attach( "line",       line )

        event.invoke( )


    def __event_level_update( self, file: str, access_level: int ):
        """
            Event callback for updating file's access level.

            Receive :
            - file          - File's name
            - access_level  - New access level value

            Returns :   None
        """

        event: c_event = self._events[ "on_level_update" ]

        event.attach( "file", file )
        event.attach( "access_level", access_level )

        event.invoke( )


    def set_event( self, event_type: str, callback: any, index: str, allow_arguments: bool = True ):
        """
            Add function to be called on specific event.

            Receive :
            - event_type    - Event name
            - callback      - Function to execute
            - index         - Function index
        """

        if not event_type in self._events:
            raise Exception( "Invalid event type to attach" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, allow_arguments )

    # endregion

    # region : Access

    def __call__( self, index ):
        """
            Access sepcific information from the user bl.

            Receive : 
            - index - Information index

            Returns : Any ( based on value type )
        """

        if index in self._information:
            return self._information[ index ]
        
        return None
    

    def check_username( self, username: str ) -> tuple:
        """
            Check if the username is valid.

            Receive :
            - username - Username string
            
            Returns :   Result ( True/False, Reason )
        """ 

        return self._registration.validate_username( username )

    # endregion
