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

        Receive: None

        Returns:    
        - c_user_business_logic: User business logic object
        """

        self.__initialize_protocols( )

        self.__initialize_events( )

        self.__initialize_information( )

    
    def __initialize_protocols( self ):
        """
        Initialize protocols for host business logic.

        Receive: None

        Returns: None
        """

        self._files         = c_files_manager_protocol( )

        self._registration  = c_registration( )
        
        self._security      = c_security( )

        self._network       = c_network_protocol( )
    

    def __initialize_events( self ):
        """
        Initialize events for user business logic.

        Receive: None

        Returns: None
        """

        self._events = {

            "on_connect":           c_event( ),

            "on_pre_disconnect":    c_event( ),
            "on_post_disconnect":   c_event( ),

            # Complex events 
            "on_refresh_files":     c_event( ), # Called when user request to refresh files list
            "on_register_files":    c_event( ), # ?

            "on_file_set":          c_event( ), # Called whenever the host is going to send the user specific file content.
            "on_file_update":       c_event( ), # ?

            "on_accept_line":       c_event( ), # Called when the host response with the line lock request.
            "on_line_lock":         c_event( ), # Called when the host forces the user to lock a specific line. ( Used for other users locked lines )
            "on_line_unlock":       c_event( ), # Called when the host unlocks a specific line for this user.

            "on_line_update":       c_event( ), # Called when the host updates line / lines. 
            "on_line_delete":       c_event( ), # Called when the host deletes a specific line. ( Line removal is other process than update )

            "on_file_register":     c_event( ), # Called when the host updates a access level to a specific file,
            "on_file_rename":       c_event( )  # Called when the host updates a file's name
        }

    
    def __initialize_information( self ):
        """
        Initialize information for user business logic.

        Receive: None

        Returns: None
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

            FILES_COMMAND_PREPARE_RESPONSE: self.__command_response_line_lock,

            FILES_COMMAND_PREPARE_UPDATE:   self.__command_line_lock,
            FILES_COMMAND_DISCARD_UPDATE:   self.__command_line_unlock,

            FILES_COMMAND_UPDATE_LINE:      self.__command_line_update,
            FILES_COMMAND_DELETE_LINE:      self.__command_line_delete,

            FILES_COMMAND_UPDATE_FILE:      self.__command_file_register,
            FILES_COMMAND_UPDATE_FILE_NAME: self.__command_update_file_name
        }

    # endregion

    # region : Connection

    def connect( self, project_code: str, username: str, password: str, register_type: str ) -> bool:
        """
        Establish connection with the host.

        Receive:
        - project_code (str): Project code received from host
        - username (str): Current username
        - password (str): Current password

        Receive:   
        - bool: Result of the connection process
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
            
        Receive:
        - project_code (str): Project code to connect to

        Returns: 
        - tuple: A tuple containing ip and port
        """

        result = base64.b64decode( project_code ).decode( )

        data = result.split( ":" )

        return data[0], int( data[1] )
    

    def __try_to_connect( self, ip: str, port: int ) -> bool:
        """
        Try to establish connection with the server.

        Receive: 
        - ip (str): Server IP
        - port (int): Server Port

        Returns:   
        - bool: Result of initialize connection
        """
        result = self._network.start_connection( CONNECTION_TYPE_CLIENT, ip, port, 5 ) is True
        
        # Or just idle. 
        self._information[ "last_error" ] = "The server might be full or offline."

        return result

    
    def __preform_safety_registration( self ) -> bool:
        """
        Initialize and establish safety for the communication.

        Receive:   None

        Returns:   
        - bool: Result of process
        """
        
        # Send public key and signature
        public_key, signature = self._security.share( ENUM_COMPLEX_KEY )
        self._network.send_bytes( signature )
        self._network.send_bytes( public_key )

        # Receive server's public key and signature
        server_signature    = self._network.receive_chunk( )
        server_public_key   = self._network.receive_chunk( )
        if not self._security.share( ENUM_COMPLEX_KEY, ( server_public_key, server_signature ) ):
            return False
        
        encrypted_nonce         = self._network.receive_chunk( )
        ephemeral_public_key    = self._network.receive_chunk( )

        nonce_signature = self._security.respond_to_challenge( encrypted_nonce, ephemeral_public_key )
        if not nonce_signature:
            return False
        
        self._network.send_bytes( nonce_signature )

        # Challenge the server (mutual authentication)
        client_enc_nonce, client_nonce, client_ephemeral_pub_key = self._security.initiate_challenge( )
        self._network.send_bytes( client_enc_nonce )
        self._network.send_bytes( client_ephemeral_pub_key )

        server_nonce_signature = self._network.receive_chunk( )
        if not self._security.verify_challenge( client_nonce, server_nonce_signature ):
            return False
        
        inner_layer_key = self._network.receive_chunk( )
        outer_layer_key = self._network.receive_chunk( )
        self._security.share( ENUM_INNER_LAYER_KEY, inner_layer_key )
        self._security.share( ENUM_OUTER_LAYER_KEY, outer_layer_key )

        self._security.sync_outer_level_keys( )

        return True

    
    def __preform_registration( self, username: str, password: str, register_type: str ) -> bool:
        """
        Preform a registration process for this user.

        Receive:
        - username (str): Current user username
        - password (str): Current user password
        - register_type (str): Type of registration operation

        Returns:   
        - bool: Result if success
        """
        
        register_command = {
            "Register":     REGISTRATION_COMMAND_REG,
            "Login":        REGISTRATION_COMMAND_LOG
        }

        message: str = self._registration.format_message( register_command[ register_type ], [ username, password ] )

        value: bytes = self._security.complex_protection( message.encode( ) )
        if not value:
            # This can happen only if the length is more than 190 bytes.
            # This mean that the username + password are ( 190 - 16 ) 174 bytes
            return False

        self.__send_quick_bytes( value )
        #self._network.send_bytes( value )

        # Preform the checks here...
        received_value: bytes = self.__receive( )
        if not received_value:
            return False

        command, arguments = self._registration.parse_message( received_value.decode( ) )
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

        Receive: None

        Returns: None
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
        Forcedly end connection with server, without notifying it.

        Receive: None

        Returns: None
        """

        self._network.end_connection( )

        self._security.reset_input_sequence_number( )
        self._security.reset_output_sequence_number( )

        # Invoke post_disconnect event
        # After we done with the connection, in some cases we will just need to clean up somethings.
        self.__event_post_disconnect( )

    # endregion

    # region : Process

    def __attach_process( self ):
        """
        Attach different processes into threads.

        Receive: None

        Returns: None
        """

        self._information[ "messages_thread" ] = self.__process_handle_messages( )

    
    @standalone_execute
    def __process_handle_messages( self ):
        """
        Process function to receive messages from server.

        Receive: None

        Returns: None
        """

        while self._network.is_valid( ):

            # Receive the message
            message: bytes = self.__receive( )
            if not message:
                continue

            self.__handle_receive( message.decode( ) )

    # endregion

    # region : Messages handle

    def __receive( self ) -> bytes:
        """
        Wrap the receive and the security part.

        Receive:   None

        Returns:   
        - bytes: Received information from server
        """

        result: bytes = b''

        has_next: bool = True
        while has_next:

            # Receive from network the data
            chunk: bytes = self._network.receive_chunk( TIMEOUT_MESSAGE )

            if not chunk:
                return None
            
            # Update the seq number
            self._security.increase_input_sequence_number( )

            # Remove protection
            chunk = self._security.dual_unprotect( chunk )
            if not chunk:
                return None
            
            # Parse data
            has_next    = chunk[ :1 ] == b'1'
            chunk       = chunk[ 1: ]

            result += chunk

        return result


    def __handle_receive( self, receive: str ):
        """
        Handles messages received from the host.

        Receive:
        - receive (str): Message content

        Returns:   None
        """

        if receive == DISCONNECT_MSG:
            return self.__end_connection( )
        
        if receive == COMMAND_ROTATE_KEY:
            return self.__handle_security_rotation( )
        
        if receive.startswith( self._files.get_header( ) ):
            return self.__handle_files_message( receive )

    
    def __handle_files_message( self, message: str ):
        """
        Handle file's protocol message.

        Receive:
        - message (str): Message from server

        Returns: None
        """

        command, arguments = self._files.parse_message( message )

        if command in self._commands:
            return self._commands[ command ]( arguments )
        
    
    def __handle_security_rotation( self ):
        """
        Perform the security key rotation operation.

        Receive: None

        Returns: None
        """

        # Get key
        new_key = self._network.receive_chunk( )

        # Send notification
        self.__send_quick_message( COMMAND_ROTATE_KEY )

        # Load new key
        self._security.share( ENUM_OUTER_LAYER_KEY, new_key )

        # Sync outer layer keys
        self._security.sync_outer_level_keys( )

        # Reset seq numbers
        self._security.reset_input_sequence_number( )
        self._security.reset_output_sequence_number( )

    # endregion

    # region : Commands

    @safe_call( c_debug.log_error )
    def __command_received_files( self, arguments: list ):
        """
        Command method for receiving files.

        Receive:
        - arguments (str): List containing files details

        Returns: None
        """

        self.__event_register_files( )

    
    @safe_call( c_debug.log_error )
    def __command_set_file( self, arguments: list ):
        """
        Command method for setting file content.

        Receive:
        - arguments (str): List containing files details

        Returns: None
        """

        file_name: str = arguments[ 0 ]
        file_size: int = int( arguments[ 1 ] )
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            raise Exception( f"Failed to find file { file_name }" )
        

        data = b''
        has_next: bool = True

        while has_next:
            chunk: bytes = self._network.receive_chunk( )
            #if not chunk:
            #    return None
            
            self._security.increase_input_sequence_number( )

            chunk = self._security.dual_unprotect( chunk )
            if not chunk:
                return
            
            has_next    = chunk[ :1 ] == b'1'
            chunk       = chunk[ 1: ]

            data += chunk

        if len( data ) != file_size:
            raise Exception( f"Failed to receive normally file { file_name }" )
        
        if data.endswith( b'\n' ):
            data = data + b'\r'

        lines: list = data.decode( ).splitlines( )
        del data

        self.__event_file_set( file )

        for line in lines:
            file.add_content_line( line )

        lines.clear( )

        self.__event_file_update( file )

        file.clear_content( )


    @safe_call( c_debug.log_error )
    def __command_response_line_lock( self, arguments: list ):
        """
        Command method for getting line lock response.

        Receive:
        - arguments (str): List containing files details

        Returns: None
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

        Receive:
        - arguments (str): List containing files details

        Returns: None
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

        Receive:
        - arguments (str): List containing files details

        Returns: None
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

        Receive:
        - arguments (str): List containing files details

        Returns: None
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

            # Maybe better approach will be to add '\n' for each line...
            if fixed_line == "\n":
                fixed_line = ""
            
            new_lines.append( fixed_line )

        self.__event_line_update( file.name( ), line, new_lines )


    @safe_call( c_debug.log_error )
    def __command_line_delete( self, arguments: list ):
        """
        Command method for line delete.

        Receive:
        - arguments (str): List containing files details

        Returns: None
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
    def __command_file_register( self, arguments: list ):
        """
        Command method for updating access level to a file.

        Receive:
        - arguments (str): List containing files details

        Returns: None
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
            
            return self.__event_file_register( file.name( ), file.access_level( ) )

        if not file:
            raise Exception( f"Failed to find file { file_name }" )

        if access_level == FILE_ACCESS_LEVEL_HIDDEN:
            # Remove
            self._files.remove_file( file_name )

        else:
            # Change to new access level
            file.access_level( access_level )

        self.__event_file_register( file_name, access_level )


    @safe_call( c_debug.log_error )
    def __command_update_file_name( self, arguments: list ):
        """
        Command method for updating file name.

        Receive:
        - arguments (str): List containing files details

        Returns: None
        """

        old_index: str = arguments[ 0 ]
        new_index: str = arguments[ 1 ]

        file: c_virtual_file = self._files.search_file( old_index )
        if not file:
            return
        
        self._files.update_name( old_index, new_index )

        self.__event_file_rename( old_index, new_index )

    # endregion

    # region : Communication

    def __send_quick_message( self, message: str ):
        """
        Send a quick message to the host.

        Receive:
        - message (str): String message to send to host

        Returns: None
        """

        self.__send_quick_bytes( message.encode( ) )

    
    def __send_quick_bytes( self, data: bytes ):
        """
        Send a quick bytes to the host.

        Receive:
        - data (bytes): Bytes of information to send to host

        Returns:   None
        """

        config = self._network.get_raw_details( len( data ) )

        for info in config:
            start       = info[ 0 ]
            end         = info[ 1 ]
            has_next    = info[ 2 ] and b'1' or b'0'

            chunk: bytes = has_next + data[ start:end ]
            
            self._security.increase_output_sequence_number( )
            chunk = self._security.dual_protect( chunk )

            result = self._network.send_bytes( chunk )
            if not result:
                return self.__end_connection( )


    def request_files( self ):
        """
        Request files from the host.

        Receive: None

        Returns: None
        """

        if not self._network.is_valid( False ):
            return

        message: str = self._files.format_message( FILES_COMMAND_REQ_FILES, ["unk"] )

        self.__send_quick_message( message )

    
    def request_file( self, file_name: str ):
        """
        Request specific file from the host.

        Receive:
        - file_name (str): File name

        Returns: None
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

        Receive: 
        - file_name (str): File name
        - line (int): Line number

        Returns: None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_PREPARE_UPDATE, [ file_name, str( line ) ] )
        self.__send_quick_message( message )


    def discard_line( self, file_name: str, line: int ):
        """
        Message of discard changes.

        Receive: 
        - file_name (str): File name
        - line (int): Line number

        Returns: None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_DISCARD_UPDATE, [ file_name, str( line ) ] )
        self.__send_quick_message( message )

    
    def update_line( self, file_name: str, line: int, lines: list ):
        """
        Message of updated lines.

        Receive: 
        - file_name (str): File name
        - line (int): Line number
        - lines (list): List of new lines

        Returns: None
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

        Receive: 
        - file_name (str): File name
        - line (int): Line number

        Returns: None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_DELETE_LINE, [ file.name( ), str( line ) ] )
        self.__send_quick_message( message )

    
    def accept_offset( self, file_name: str, offset: int ):
        """
        Message to correct offset.

        Receive: 
        - file_name (str): File name
        - offset (int): Offset value to verify

        Returns: None
        """

        # Without this, we will have problems
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_APPLY_UPDATE, [ str( FILE_UPDATE_CONTENT ), file.name( ), str( offset ) ] )
        self.__send_quick_message( message )


    def accept_file_rename( self, old_index: str, new_index: str ):
        """
        Message to accept new file name.

        Receive: 
        - old_index (str): Old file name
        - new_index (str): New file name

        Returns: None
        """

        file: c_virtual_file = self._files.search_file( new_index )
        if not file:
            return
        
        message: str = self._files.format_message( FILES_COMMAND_APPLY_UPDATE, [ str( FILE_UPDATE_NAME ), old_index, new_index ] )
        self.__send_quick_message( message )

    # endregion

    # region : Events

    def __event_connect( self, ip: str, port: int ):
        """
        Event callback when the user connects to the host.

        Receive:
        - ip (str): Host IP
        - port (int): Port to connect

        Returns:   None
        """

        event: c_event = self._events[ "on_connect" ]

        event.attach( "ip",         ip )
        event.attach( "port",       port )
        event.attach( "success",    self._information[ "is_connected" ] )

        event.invoke( )

    
    def __event_pre_disconnect( self ):
        """
        Event callback before disconnect process.

        Receive: None

        Returns: None
        """

        event: c_event = self._events[ "on_pre_disconnect" ]

        event.invoke( )

    
    def __event_post_disconnect( self ):
        """
        Event callback after disconnect process.

        Receive: None

        Returns: None
        """

        event: c_event = self._events[ "on_post_disconnect" ]

        event.invoke( )

    
    def __event_register_files( self ):
        """
        Event callback when the user registers a new file.

        Receive: None

        Returns: None
        """

        #self._files.create_new_file( file_name, access_level, False )

        event: c_event = self._events[ "on_register_files" ]

        event.invoke( )


    def __event_file_set( self, file: c_virtual_file ):
        """
        Event when the the host user request file.

        Receive:
        - file (c_virtual_file): File pointer to update

        Returns: None
        """

        event: c_event = self._events[ "on_file_set" ]

        event.attach( "file",           file.name( ) )
        event.attach( "read_only",      file.access_level( ) == FILE_ACCESS_LEVEL_LIMIT )

        event.invoke( )

    
    def __event_file_update( self, file: c_virtual_file ):
        """
        Event callback for updating a file

        Receive:
        - file (c_virtual_file): File pointer to update

        Returns: None
        """

        event: c_event = self._events[ "on_file_update" ]

        for line in file.read_file_content( ):
            event.attach( "line_text", line )
            event.invoke( )


    def __event_accept_line( self, file: str, line: int, accept: bool ):
        """
        Event callback for updating a file

        Receive:
        - file (str): File's name
        - line (int): Line number
        - accept (bool): Did host accept

        Returns: None
        """

        event: c_event = self._events[ "on_accept_line" ]

        event.attach( "file",   file )
        event.attach( "line",   line )
        event.attach( "accept", accept )

        event.invoke( )


    def __event_line_lock( self, file: str, line: int, locked_by: str ):
        """
        Event callback for locking a line.

        Receive:
        - file (str): File's name
        - line (int): Line number

        Returns: None
        """

        event: c_event = self._events[ "on_line_lock" ]

        event.attach( "file", file )
        event.attach( "line", line )
        event.attach( "user", locked_by )

        event.invoke( )


    def __event_line_unlock( self, file: str, line: int ):
        """
        Event callback for unlocking a line.

        Receive:
        - file (str): File's name
        - line (int): Line number

        Returns: None
        """

        event: c_event = self._events[ "on_line_unlock" ]

        event.attach( "file", file )
        event.attach( "line", line )

        event.invoke( )

    
    def __event_line_update( self, file: str, line: int, new_lines: list ):
        """
            Event callback for updating line/lines.

        Receive:
        - file (str): File's name
        - line (int): Line number
        - new_lines(list): New lines to add

        Returns: None
        """

        event: c_event = self._events[ "on_line_update" ]

        event.attach( "file",       file )
        event.attach( "line",       line )
        event.attach( "new_lines",  new_lines )

        event.invoke( )

    
    def __event_line_delete( self, file: str, line: int ):
        """
        Event callback for deleting line.

        Receive:
        - file (str): File's name
        - line (int): Line number

        Returns: None
        """

        event: c_event = self._events[ "on_line_delete" ]

        event.attach( "file",       file )
        event.attach( "line",       line )

        event.invoke( )


    def __event_file_register( self, file: str, access_level: int ):
        """
        Event callback for updating file's access level.

        Receive:
        - file (str): File's name
        - access_level (int): Access level to register for a file

        Returns: None
        """

        event: c_event = self._events[ "on_file_register" ]

        event.attach( "file", file )
        event.attach( "access_level", access_level )

        event.invoke( )


    def __event_file_rename( self, old_index: str, new_index: str ):
        """
        Event callback for updating file's access level.

        Receive:
        - old_index (str): Old file name
        - new_index (str): New file name

        Returns: None
        """

        event: c_event = self._events[ "on_file_rename" ]

        event.attach( "old_index", old_index )
        event.attach( "new_index", new_index )

        event.invoke( )


    def set_event( self, event_type: str, callback: any, index: str, allow_arguments: bool = True ):
        """
        Add function to be called on specific event.

        Receive:
        - event_type (str): Event name
        - callback (function): Function to execute
        - index (str): Function index

        Returns: None
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

        Receive: 
        - index (str): Information index

        Returns: 
        - any: Information value
        """

        if index in self._information:
            return self._information[ index ]
        
        return None
    

    def check_username( self, username: str ) -> tuple:
        """
        Check if the username is valid.

        Receive:
        - username (str): Username string
            
        Returns:   
        - bool: A tuple with result True/False and reason
        """ 

        return self._registration.validate_username( username )

    # endregion
