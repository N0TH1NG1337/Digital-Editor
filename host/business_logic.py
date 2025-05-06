"""
    project     : Digital Editor

    type:       : Host
    file        : Business Logic

    description : Host Business Logic class
"""

from protocols.network          import *
from protocols.files_manager    import *
from protocols.registration     import *
from protocols.security         import *
from utilities.event            import c_event
from utilities.wrappers         import safe_call, standalone_execute, static_arguments
from utilities.math             import math

import base64
import queue
import time
import os

DEFAULT_FOLDER_NAME:    str     = ".digital_files"
DEFAULT_TRUST_FACTOR:   int     = 50

TIMEOUT_CONNECTION:     float   = 0.5
TIMEOUT_MSG:            float   = 0.5
TIMEOUT_COMMAND:        float   = 0.1
SLEEP_ON_IDLE:          float   = 2.0

ENUM_PROTOCOL_FILES:    int     = 1
ENUM_PROTOCOL_NETWORK:  int     = 2
ENUM_PROTOCOL_UNK:      int     = 0


ENUM_SCAN_DISABLE:      int = 1
ENUM_SCAN_CREATE_NEW:   int = 2
ENUM_SCAN_OVERWRITE:    int = 3

ENUM_LOG_INFO:          int = 1
ENUM_LOG_ERROR:         int = 2

class c_log:

    _type:      int # Log type
    _time:      str # Log timestamp

    _user:      str # Who registered this log
    _message:   str # Log meesage it self

    def __init__( self, message: str, log_type: int = ENUM_LOG_INFO, user: str = "system" ):
        
        self._type = log_type
        self._user = user

        self._message = message

        self._time = time.strftime( "%y-%m-%d %H:%M:%S", time.localtime( ) )

    
    def type( self ) -> int:
        return self._type
    
    def time( self ) -> str:
        return self._time
    
    def user( self ) -> str:
        return self._user
    
    def message( self ) -> str:
        return self._message


class c_command:

    _client:    any     # c_client_handle

    _protocol:  int
    _command:   str
    _arguments: list

    def __init__( self, client: any,protocol: int, command: str, arguments: list ):
        """
            Default constructor for command object.
            
            Receive :
            - client    - Client handle object
            - protocol  - Related protocol command
            - command   - Command itself
            - arguments - Arguments for command

            Returns :   Command object
        """

        self._client    = client
        self._protocol  = protocol
        self._command   = command
        self._arguments = arguments

    
    def client( self ) -> any:
        """
            Access the client.

            Receive :   None

            Returns :   Client handle object
        """

        return self._client
    

    def protocol( self ) -> int:
        """
            Access the protocol index.

            Receive :   None

            Returns :   Int - Protocol enum
        """

        return self._protocol
    

    def command( self ) -> str:
        """
            Access the command itself.

            Receive :   None

            Returns :   Command string
        """

        return self._command
    

    def arguments( self ) -> list:
        """
            Access the arguments list.

            Receive :   None

            Returns :   List
        """

        return self._arguments
    

    def clear_arguments( self ) -> None:
        """
            Clear the arguments list.

            Receive :   None

            Returns :   None
        """

        self._arguments.clear( )

    
    def add_arguments( self, value: any ) -> None:
        """
            Add to the arguments any value.

            Receive :
            - value - Value to add

            Returns :   None
        """ 

        self._arguments.append( value )


class c_client_handle:
    
    # region : Private Attributes

    _network:           c_network_protocol          # Clients handle network connection
    _files:             c_files_manager_protocol    # Clients handle files
    _registration:      c_registration              # Clients register process
    _security:          c_security                  # Clients security protocol

    _information:       dict                        # Clients information
    _events:            dict                        # Each client events

    _selected_file:     c_virtual_file              # Selected file
    _selected_line:     int                         # Selected line

    # We dont want modded client to spoof index change response.
    # As a result each change will be added to a list, and in general used as sum( ) for offset
    # And checks if one offset is responded, just remove from the list.
    _offsets:           list                        # Offsets for missed lines
    
    # This part will be used to keep track of the issues that the client created.
    # If the client created an issue, the trust factor will be lowered.
    # The trust factor will be between 50 - 0. If the trust factor is 0, the client will be disconnected and blacklisted.
    _trust_factor:      int                         # Trust factor for the client
    _is_modded:         bool                        # Is the client modded
    _issues:            list                        # Issues that the client created that lowered the trust factor
    
    _files_commands:    dict

    _start_rotation:    bool

    # endregion

    # region : Initialization client handle

    def __init__( self ):
        """
            Default constructor for client handle.

            Receive:    None

            Returns:    None
        """

        # Initialize client's events
        self.__initialize_events( )

        # Initialize client's information
        self.__initialize_information( )

    
    def __initialize_events( self ):
        """
            Initialize events for client handle.

            Receive:    None

            Returns:    None
        """

        self._events = {
            "on_client_connected":      c_event( ),
            "on_client_disconnected":   c_event( ),
            "on_client_command":        c_event( ),

            "on_client_log":            c_event( )
        }

    
    def __initialize_information( self ):
        """
            Initialize information for client handle.

            Receive:    None

            Returns:    None
        """

        self._network       = None
        self._files         = c_files_manager_protocol( )
        self._registration  = c_registration( )
        self._security      = c_security( )

        self._information = {
            "last_error":   "",
            "username":     "unknown"
        }

        self._selected_file     = None
        self._selected_line     = 0
        self._trust_factor      = DEFAULT_TRUST_FACTOR
        self._offsets           = [ ]
        self._issues            = [ ]

        self._start_rotation    = False

        self._files_commands = {
            FILES_COMMAND_REQ_FILES:        self.__share_files,

            FILES_COMMAND_GET_FILE:         self.__get_file,

            FILES_COMMAND_PREPARE_UPDATE:   self.__request_line,
            # FILES_COMMAND_PREPARE_RESPONSE: None, # No need since this is only for client

            FILES_COMMAND_DISCARD_UPDATE:   self.__discard_line,

            # These 3 commands are the most important
            FILES_COMMAND_UPDATE_LINE:      self.__update_line,
            FILES_COMMAND_DELETE_LINE:      self.__delete_line,
            FILES_COMMAND_APPLY_UPDATE:     self.__apply_update
        }

    # endregion

    # region : Connection

    def connect( self, socket_object: socket, address: tuple ) -> bool:
        """
            Connect the client to the server.

            Receive:    
            - socket_object     - Client socket object
            - address           - Client address

            Returns:    bool - Is the client connected successfully
        """

        self.__event_client_log( f"New connection. Ip - { address[ 0 ] } : Port - { address[ 1 ] }" )

        # Attach connection
        self.__attach_connection( socket_object, address )

        # Protect connection
        if not self.__secure_connection( ):
            return self.disconnect( False, True, False )

        # Register the connection
        if not self.__register_connection( ):
            return self.disconnect( False, True, False )

        self.__event_client_connected( address )

        # Attach processes
        self.__attach_processes( )

        return True
    

    def __attach_connection( self, socket_object: socket, address: tuple ):
        """
            Create new connection object and attach it in the network protocol.

            Receive :
            - socket_object - Client socket
            - address       - Client address

            Returns :   None
        """

        # Create connection
        new_connection = c_connection( )

        # Unlike the default .connect. Here we just give the information. 
        new_connection.attach( address[0], address[1], socket_object )

        # Create and attach the connection to the protocol
        self._network = c_network_protocol( new_connection )


    def __secure_connection( self ) -> bool:
        """
            Protect the communication between the host and the client.

            Receive :   None

            Returns :   None
        """

        # Send public key and signature
        public_key, signature = self._security.share( ENUM_COMPLEX_KEY )
        self._network.send_bytes( signature )
        self._network.send_bytes( public_key )

        # Receive client's public key and signature
        client_signature    = self._network.receive_chunk( )
        client_public_key   = self._network.receive_chunk( )
        
        # Register this information
        if not self._security.share( ENUM_COMPLEX_KEY, ( client_public_key, client_signature ) ):
            return False

        
        # Generate and send nonce challenge
        encrypted_nonce, nonce, ephemeral_pub_key = self._security.initiate_challenge( )
        
        # Send to client the information
        self._network.send_bytes( encrypted_nonce )
        self._network.send_bytes( ephemeral_pub_key )

        # Receive client's nonce response
        nonce_signature = self._network.receive_chunk( )
        if not self._security.verify_challenge( nonce, nonce_signature ):
            return False
        
        
        # Handle client's challenge (mutual authentication)
        client_encryped_nonce = self._network.receive_chunk( )
        client_ephemeral_pub_key = self._network.receive_chunk( )

        server_nonce_signature = self._security.respond_to_challenge( client_encryped_nonce, client_ephemeral_pub_key )
        if not server_nonce_signature:
            return False
        
        self._network.send_bytes( server_nonce_signature )

        # Now, after we done with the verification we can share the inner layer key
        self._security.generate_key( ENUM_INNER_LAYER_KEY )
        self._security.generate_key( ENUM_OUTER_LAYER_KEY )

        self._security.sync_outer_level_keys( )

        self._network.send_bytes( self._security.share( ENUM_INNER_LAYER_KEY ) )
        self._network.send_bytes( self._security.share( ENUM_OUTER_LAYER_KEY ) )

        self.__event_client_log( f"Secured connection with the client { self._network.get_address( )[ 0 ] }:{ self._network.get_address( )[ 1 ] }" )

        return True
    

    def __register_connection( self ) -> bool:
        """
            Register the connection to the server.

            Receive:    None

            Returns:    Result
        """

        raw_msg: str = self._security.complex_remove_protection( self.__receive( ) ).decode( )
        
        if not raw_msg.startswith( self._registration.header( ) ):
            self._information[ "last_error" ] = "Cannot receive normalized registration information about client"
            return self.disconnect( False, True, False )

        command, arguments = self._registration.parse_message( raw_msg )
        if not command or not arguments:
            self._information[ "last_error" ] = "Failed to parse message"
            return self.disconnect( False, True, False )
        
        success = False

        if command == REGISTRATION_COMMAND_REG:
            # Register
            
            success:    bool        = self._registration.register_user( arguments[ 0 ], arguments[ 1 ], { "files": { }, "trust_factor": DEFAULT_TRUST_FACTOR, "issues": [ ] } )
        
        elif command == REGISTRATION_COMMAND_LOG:
            # Login
            
            success:    bool        = self._registration.login_user( arguments[ 0 ], arguments[ 1 ] )


        response: str = self._registration.format_message( 
            REGISTRATION_RESPONSE, 
            [ 
                success and "1" or "0", 
                self._registration.last_error( ) 
            ] 
        )

        self.send_quick_message( response )
        
        if success:
            
            self.__event_client_log( f"Client with username ( { arguments[ 0 ] } ) completed registration" )

            self._information[ "username" ] = arguments[ 0 ]

            # Now since we have registered the user. Get the fields we need
            self._trust_factor = self._registration.get_field( "trust_factor" )
            self._issues       = self._registration.get_field( "issues" )

            if not self.check_trust_factor( ):
                return False

            # Now get the files access levels
            stored_access_levels = self._registration.get_field( "files" )

            for file_name, access_level in stored_access_levels.items( ):
                file: c_virtual_file = self._files.search_file( file_name )

                if file is None:
                    continue

                file.access_level( access_level )

            return True
        
        self.__event_client_log( f"Client with username ( { arguments[ 0 ] } ) failed registration" )

        # Here we have a problem
        return False
        

    def __attach_processes( self ):
        """
            Attach processes for the client handle.

            Receive:    None

            Returns:    None
        """

        # Start the receive process
        self.__receive_process( )


    def disconnect( self, notify_the_client: bool = True, remove_client_handle: bool = True, update_fields: bool = True ):
        """
            Disconnect the client from the server.

            Receive:    
            - notify_the_client  - Notify the client about the disconnection

            Returns:    None
        """

        # Potentially notify the client
        if notify_the_client:
            self.__event_client_log( f"Notifying client ( { self( 'username' ) } ) about disconnection" )
            self.send_quick_message( DISCONNECT_MSG )

        # End the connection
        self._network.end_connection( )

        # Clear if anything selected on the host side
        self.clear( )

        # Update the fields
        if update_fields:
            self._registration.set_field( "trust_factor", self._trust_factor )
            self._registration.set_field( "issues", self._issues )

            files_field = { }
            for file_name, file in self._files.get_files( ).items( ):
                file: c_virtual_file = file
                files_field[ file.name( ) ] = file.access_level( )
            
            self._registration.set_field( "files", files_field )

            self._registration.update_fields( )

        # Call the event
        self.__event_client_disconnected( notify_the_client, remove_client_handle )

        self.__event_client_log( f"client ( { self( 'username' ) } ) disconnected" )


    def clear( self ):
        # Clear the user activities, such as line lock or anything similar

        if self._selected_line == 0:
            return
        
        command: c_command = c_command( self, ENUM_PROTOCOL_FILES, FILES_COMMAND_DISCARD_UPDATE, [ self._selected_file.name( ), self._selected_line ] )
        self.__event_client_command( command )

        self.__event_client_log( f"Cleared client ( { self( 'username' ) } ) actions" )

    # endregion

    # region : Communication

    @standalone_execute
    def __receive_process( self ):
        """
            Process for receiving messages from the client.

            Receive:    None

            Returns:    None
        """

        # Run the process while the network is valid
        while self._network.is_valid( ):

            if not self.check_trust_factor( ):
                return self.disconnect( False )
            
            self.trust_factor_latency( )
            
            if not self._start_rotation and self._security.should_rotate( ):
                self.__start_security_rotation( )
                continue
            
            message: bytes = self.__receive( )

            if not message:
                continue
        
            self.__handle_message( message.decode( ) )


    def __receive( self ) -> bytes:
        """
            Wrap the receive and the security part.

            Receive :   None

            Returns :   Received Bytes
        """

        result:     bytes   = b''
        has_next:   bool    = True

        while has_next:
            chunk: bytes = self._network.receive_chunk( TIMEOUT_MSG )
            if not chunk:
                return None
            
            self._security.increase_input_sequence_number( )

            chunk = self._security.dual_unprotect( chunk )
            if not chunk:
                return self.lower_trust_factor( 10, "Failed to decrypt received message." )
            
            has_next    = chunk[ :1 ] == b'1'
            chunk       = chunk[ 1: ]

            result += chunk

        return result


    def __handle_message( self, message: str ):
        """
            Handle message from client.

            Receive :
            - message - Client's message

            Returns :   None
        """

        self.__event_client_log( f"Received from client ( { self( 'username' ) } ) -> { message }", False )

        # Manual checks
        if message == DISCONNECT_MSG:
            return self.disconnect( False, True )

        if message == PING_MSG:
            return self.__event_client_log( f"Client ( { self( 'username' ) } ) pinged", False )
        
        if message == COMMAND_ROTATE_KEY:
            return self.__complete_security_rotation( )

        # Try to parse the message and create new command object
        new_command = self.__parse_message( message )

        # Remove the message string it self
        del message

        if not self.__verify( new_command ):
            del new_command
            return

        # Each command has to be processed on the client handle first.
        # It will process all the verefications and only then pass to the main queue
        if new_command.protocol( ) == ENUM_PROTOCOL_FILES:

            callback = self._files_commands[ new_command.command( ) ]
            if callback is not None:
                return callback( new_command )

        # If it cannot, attach the command to the pool
        self.__event_client_command( new_command )

    
    def __parse_message( self, message: str ) -> c_command:
        """
            Parse message from the client.

            Receive :
            - message - Client's message

            Returns : Tuple ( Protocol, Command, Arguments )
        """

        if message.startswith( self._files.get_header( ) ):
            # Files protocol message
            command, arguments = self._files.parse_message( message )

            return c_command( self, ENUM_PROTOCOL_FILES, command, arguments )
        
        # If failed
        return c_command( self, ENUM_PROTOCOL_UNK, message, None )


    def __verify( self, cmd: c_command ) -> bool:
        """
            Verify if the command is valid.

            Receive :
            - command - Command object

            Returns :   Result 
        """

        protocol = cmd.protocol( )

        if protocol == ENUM_PROTOCOL_UNK:
            self.lower_trust_factor( 10, "Invalid command" )

            self.__event_client_log( f"Failed to find protocol for message from client ( { self( 'username' ) } ) \n{ cmd.command( ) }", True )
            return False

        if protocol == ENUM_PROTOCOL_FILES:
            return cmd.command( ) in self._files_commands

        return True


    def send_quick_message( self, message: str ):
        """
            Send a quick message to the host.

            Receive :
            - message - Message to send

            Returns :   None
        """

        self.send_quick_bytes( message.encode( ) )
    

    def send_quick_bytes( self, data: bytes ):
        """
            Send a quick bytes to the client.

            Receive :
            - message - Message to send

            Returns :   None
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
                return # self.disconnect( False, True, False )


    def __start_security_rotation( self ):
        
        self.__event_client_log( f"Started key rotation for client ( { self( 'username' ) } )" )

        self.send_quick_message( COMMAND_ROTATE_KEY )
        
        self._security.generate_key( ENUM_OUTER_LAYER_KEY )

        self._network.send_bytes( self._security.share( ENUM_OUTER_LAYER_KEY ) )

        self._security.reset_output_sequence_number( )

        self._start_rotation = True

    
    def __complete_security_rotation( self ):
        
        self._security.sync_outer_level_keys( )

        self._security.reset_input_sequence_number( )

        self._start_rotation = False

        self.__event_client_log( f"Completed key rotation for client ( { self( 'username' ) } )" )

    # endregion

    # region : Events

    def __event_client_connected( self, address: tuple ):
        """
            Event when the client connected to the server.

            Receive: 
            - address   - Client address

            Returns:    None
        """

        event: c_event = self._events[ "on_client_connected" ]
        event.attach( "ip",     address[ 0 ] )
        event.attach( "port",   address[ 1 ] )

        event.invoke( )


    def __event_client_disconnected( self, notify_the_client: bool, remove_client_handle: bool ):
        """
            Event when the client disconnected from the server.

            Receive:    
            - notify_the_client  - Notify the client about the disconnection

            Returns:    None
        """

        event: c_event = self._events[ "on_client_disconnected" ]
        event.attach( "client", self )
        event.attach( "notify", notify_the_client and "1" or "0" )
        event.attach( "remove", remove_client_handle and 1 or 0 )

        event.invoke( )

    
    def __event_client_command( self, command: c_command ):
        """
            Event when the client sent a command.

            Receive:    
            - command   - Command object

            Returns:    None
        """

        event: c_event = self._events[ "on_client_command" ]
        event.attach( "command", command )

        event.invoke( )
    

    def __event_client_log( self, message: str, save_in_app: bool = True, log_type: int = ENUM_LOG_INFO, user: str = "system" ):
        
        event: c_event = self._events[ "on_client_log" ]
        
        event.attach( "message",        message )
        event.attach( "save_in_app",    save_in_app )
        event.attach( "log_type",       log_type )
        event.attach( "user",           user )

        event.invoke( )


    def set_event( self, event_name: str, callback: any, index: str ):
        """
            Set an event for the client handle.

            Receive:    
            - event_name    - Event name
            - callback      - Callback function
            - index         - Index of the event

            Returns:    None
        """

        if not event_name in self._events:
            raise Exception( f"Event {event_name} is not valid." )
        
        event: c_event = self._events[ event_name ]
        event.set( callback, index, True )

    # endregion

    # region : File and line

    def load_files( self, files_protocol: c_files_manager_protocol ):
        """
            Initialize files for client.

            Receive :   
            - files - Files access

            Returns :   None
        """

        files: dict = files_protocol.get_files( )

        for index in files:
            file: c_virtual_file = files[ index ]

            self._files.copy( file )

    
    def load_database( self, database: c_database ):
        """
            Load path for database of registration protocol.

            This must be called before .connect( )

            Receive :
            - database  - Database object

            Returns :   None
        """

        self._registration.load_database( database )


    def __share_files( self, command: c_command ):
        """
            Share with client the allowed files.

            Receive :   
            - command - Original command

            Returns :   None
        """

        self.__event_client_log( "requested files list", user=f"client ( { self( 'username' ) } )" )

        files: dict = self._files.get_files( )

        self.send_quick_message( self._files.format_message( FILES_COMMAND_RES_FILES, [ str( len( files ) ) ] ) )

        for file in files:
            file: c_virtual_file = self._files.search_file( file )

            if not file:
                return
            
            access_level: int = file.access_level( )
            if access_level == FILE_ACCESS_LEVEL_HIDDEN:
                continue

            message: str = self._files.format_message( FILES_COMMAND_UPDATE_FILE, [ file.name( ), str( access_level ) ] )
            self.send_quick_message( message )

    
    def __get_file( self, command: c_command ):
        """
            Share the file with the client.

            Receive :   
            - command - Original command

            Returns :   None
        """

        file_name: str = command.arguments( )[ 0 ]

        self.__event_client_log( f"requested file { file_name }", user=f"client ( { self( 'username' ) } )" )

        file: c_virtual_file = self._files.search_file( file_name )
        if file is None:
            return self.lower_trust_factor( 5, "Invalid file name" ) 
        
        if file.access_level( ) == FILE_ACCESS_LEVEL_HIDDEN:
            return self.lower_trust_factor( 10, "Unauthorized request" )
        
        c_debug.log_information( f"Client ( { self( 'username' ) } ) - requested file { file.name( ) }" )

        self._selected_file = file

        file_size:  int     = file.size()
        config:     list    = self._network.get_raw_details( file_size )

        self.send_quick_message( self._files.format_message( FILES_COMMAND_SET_FILE, [ file.name( ), str( file_size ) ] ) )

        #key: bytes = self._security.generate_key( ENUM_OUTER_LAYER_KEY )
        #self._security.increase_output_sequence_number( )

        for info in config:
            start       = info[ 0 ]
            end         = info[ 1 ]
            has_next    = info[ 2 ] and b'1' or b'0'

            chunk: bytes = has_next + file.read( start, end )
            
            self._security.increase_output_sequence_number( )
            chunk = self._security.dual_protect( chunk )

            result = self._network.send_bytes( chunk )
            if not result:
                return # self.disconnect( False, True, False )
            
        self.__event_client_log( f"sent file { file_name } to client ( { self( 'username' ) } )" )

        # After we done with the file. need to notify the client with locked lines
        lines: list = file.locked_lines( )
        for line in lines:
            message: str = self._files.format_message( FILES_COMMAND_PREPARE_UPDATE, [ file.name( ), str( line ) ] )
            self.send_quick_message( message )


    def __request_line( self, command: c_command ):
        """
            Client's request to lock a line.

            Receive :   
            - command - Original command

            Returns :   None
        """

        # Here we just preform all the checks...
        arguments:      list    = command.arguments( )

        # Convert the arguments into real values
        file_name:      str     = arguments[ 0 ]
        line_number:    int     = math.cast_to_number( arguments[ 1 ] )

        self.__event_client_log( f"request line { line_number } in { file_name }", user=f"client ( { self( 'username' ) } )" )

        if line_number is None:
            return self.lower_trust_factor( 5, "Invalid line number" ) 

        if self._selected_line != 0:
            return self.lower_trust_factor( 10, "Cannot select new line while using other" ) 

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return self.lower_trust_factor( 5, "Invalid file name" ) 
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            return self.lower_trust_factor( 10, "Unauthorized request" )
        
        # In general the locked lines should show up for the client
        # and it doesn't need to request it if locked
        if file.is_line_locked( line_number ):
            # This can happen only in 1 cases.
            # 1. The client didn't have time to register line lock
            # 2. The client is modded

            # To be sure, will add more checks later
            self._is_modded = True  

        self.__event_client_log( f"response for line { line_number } in { file_name } completed" )

        # Change the command arguments into real values
        command.clear_arguments( )
        command.add_arguments( file_name )
        command.add_arguments( line_number )

        # In the end process the command in commands pool
        self.__event_client_command( command )


    def __discard_line( self, command: c_command ):
        """
            Client's message to discard a line.

            Receive :   
            - command - Original command

            Returns :   None
        """

        # Here we just preform all the checks...
        arguments:      list    = command.arguments( )

        # Convert the arguments into real values
        file_name:      str     = arguments[ 0 ]
        line_number:    int     = math.cast_to_number( arguments[ 1 ] )

        self.__event_client_log( f"request to discard line { line_number } in { file_name }", user=f"client ( { self( 'username' ) } )" )

        if line_number is None:
            return self.lower_trust_factor( 5, "Invalid line number" ) 

        if self._selected_line == 0:
            return self.lower_trust_factor( 10, "Cannot discard line when not locked one" ) 

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return self.lower_trust_factor( 5, "Invalid file name" ) 
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            return self.lower_trust_factor( 10, "Unauthorized request" )

        # Fix the client offset
        line_number += self.get_offset( )

        if line_number != self.selected_line( ):
            return self.lower_trust_factor( 5, "Incorrect line index" )
        
        self.__event_client_log( f"response to discard line { line_number } in { file_name } completed" )

        # Change the command arguments into real values
        command.clear_arguments( )
        command.add_arguments( file_name )
        command.add_arguments( line_number )

        # In the end process the command in commands pool
        self.__event_client_command( command )


    def __update_line( self, command: c_command ):
        """
            Client's message to update a line.

            Receive :   
            - command - Original command

            Returns :   None
        """

        # Here we just preform all the checks...
        arguments:      list    = command.arguments( )

        # Convert the arguments into real values
        file_name:      str     = arguments[ 0 ]
        line_number:    int     = math.cast_to_number( arguments[ 1 ] )
        lines_number:   int     = math.cast_to_number( arguments[ 2 ] )

        self.__event_client_log( f"request to update line { line_number } in { file_name } with { lines_number } new lines", user=f"client ( { self( 'username' ) } )" )

        if line_number is None or lines_number is None:
            return self.lower_trust_factor( 5, "Invalid line number" ) 

        if self._selected_line == 0:
            return self.lower_trust_factor( 10, "Cannot update line when not locked one" ) 
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return self.lower_trust_factor( 5, "Invalid file name" ) 
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            return self.lower_trust_factor( 10, "Unauthorized request" )
        
        # Fix the client offset
        line_number += self.get_offset( )

        if line_number != self.selected_line( ):
            return self.lower_trust_factor( 5, "Incorrect line index" )

        new_lines: list = [ ]
        for index in range( lines_number ):
            new_line: bytes = self.__receive( )

            if not new_line:
                raise Exception( f"Failed to get line on index { index + 1 }" )
            
            new_line: str = base64.b64decode( new_line ).decode( )
            if new_line == "\n":
                new_line = ""
            
            new_lines.append( new_line )

        self.__event_client_log( f"update for line { line_number } in { file_name } completed" )

        # Change the command arguments into real values
        command.clear_arguments( )
        command.add_arguments( file.name( ) )
        command.add_arguments( line_number )
        command.add_arguments( new_lines )

        # In the end process the command in commands pool
        self.__event_client_command( command )
    

    def __delete_line( self, command: c_command ):
        """
            Client's message to delete a line.

            Receive :   
            - command - Original command

            Returns :   None
        """

        # Here we just preform all the checks...
        arguments:      list    = command.arguments( )

        # Convert the arguments into real values
        file_name:      str     = arguments[ 0 ]
        line_number:    int     = math.cast_to_number( arguments[ 1 ] )

        self.__event_client_log( f"request to delete line { line_number } in { file_name }", user=f"client ( { self( 'username' ) } )" )

        if line_number is None:
            return self.lower_trust_factor( 5, "Invalid line number" ) 

        if self._selected_line == 0:
            return self.lower_trust_factor( 10, "Cannot delete line when not locked one" ) 

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return self.lower_trust_factor( 5, "Invalid file name" ) 
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            return self.lower_trust_factor( 10, "Unauthorized request" )
        
        # Fix the client offset
        line_number += self.get_offset( )

        if line_number != self.selected_line( ):
            return self.lower_trust_factor( 5, "Incorrect line index" )
        
        self.__event_client_log( f"delete line { line_number } in { file_name } was completed" )
        
        # Change the command arguments into real values
        command.clear_arguments( )
        command.add_arguments( file.name( ) )
        command.add_arguments( line_number )

        # In the end process the command in commands pool
        self.__event_client_command( command )


    def __apply_update( self, command: c_command ):
        """
            Client's message to apply an update received before.

            Receive :   
            - command - Original command

            Returns :   None
        """

        arguments:      list    = command.arguments( )

        # Convert the argument into real values
        update_type:    int     = math.cast_to_number( arguments[ 0 ] )

        self.__event_client_log( f"verified change type { update_type }", user=f"client ( { self( 'username' ) } )" )

        arguments.pop( 0 )
        self.__get_correct_update_callback( update_type, command )
    

    @standalone_execute
    def change_access_level( self, file_name: str, new_level: int ):
        """
            Change the access level of the file.

            Receive :   
            - file_name - File name
            - new_level - New access level

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        old_access_level: int = file.access_level( )
        
        self.__event_client_log( f"changed access level in file { file_name } to { new_level } from { old_access_level }", user=f"client ( { self( 'username' ) } )" )

        if old_access_level == FILE_ACCESS_LEVEL_EDIT and new_level != FILE_ACCESS_LEVEL_EDIT and ( self._selected_file is not None and self._selected_file.name( ) == file.name( ) ) and self._selected_line != 0:
            # Disable line lock
            command = c_command( self, ENUM_PROTOCOL_FILES, FILES_COMMAND_DISCARD_UPDATE, [ ] )
            command.add_arguments( file_name )
            command.add_arguments( self._selected_line )

            self.__event_client_command( command )

        file.access_level( new_level )

        # Prepare message for client
        message: str = self._files.format_message( FILES_COMMAND_UPDATE_FILE, [ file.name( ), str( new_level ) ] )
        self.send_quick_message( message )

    # endregion

    # region : Updates verifications

    def __get_correct_update_callback( self, update_type: int, command: c_command ):
        
        update_callbacks = {
            FILE_UPDATE_CONTENT:    self.__update_type_content,
            FILE_UPDATE_NAME:       self.__update_type_name
        }

        update_callbacks[ update_type ]( command ) 

    
    def __update_type_content( self, command: c_command ):
        arguments:      list    = command.arguments( )

        file_name:      str     = arguments[ 0 ]
        offset_number:  int     = math.cast_to_number( arguments[ 1 ] )

        if offset_number is None:
            return self.lower_trust_factor( 5, "Invalid offset value" ) 

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return self.lower_trust_factor( 5, "Invalid file name" ) 
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            return self.lower_trust_factor( 10, "Unauthorized request" )
        
        if not self.is_offset( offset_number ):
            return self.lower_trust_factor( 10, "Unknown offset" )
        
        command.clear_arguments( )
        command.add_arguments( FILE_UPDATE_CONTENT )
        command.add_arguments( offset_number )

        # In the end process the command in commands pool
        self.__event_client_command( command )


    def __update_type_name( self, command: c_command ):

        arguments:      list    = command.arguments( )

        old_index:      str     = arguments[ 0 ]
        new_index:      str     = arguments[ 1 ]

        file: c_virtual_file = self._files.search_file( old_index )
        if not file:
            return self.lower_trust_factor( 5, "Invalid file name" ) 
        
        if file.access_level( ) == FILE_ACCESS_LEVEL_HIDDEN:
            return self.lower_trust_factor( 10, "Unauthorized request" )

        command.clear_arguments( )
        command.add_arguments( FILE_UPDATE_CONTENT )
        command.add_arguments( old_index )
        command.add_arguments( new_index )

        # In the end process the command in commands pool
        self.__event_client_command( command )

    # endregion

    # region : Offsets

    def get_offset( self ) -> int:
        """
            Get the offset for the client.

            Receive:    None

            Returns:    int - Offset
        """

        return sum( self._offsets )
    

    def add_offset( self, offset: int ):
        """
            Add an offset to the client.

            Receive:    
            - offset    - Offset

            Returns:    None
        """

        self._offsets.append( offset )

    
    def is_offset( self, offset: int ) -> bool:
        """
            Check if the client has an offset.

            Receive:    
            - offset    - Offset

            Returns:    bool - Is the offset in the client
        """

        for item in self._offsets:
            if offset == item:
                return True
            
        return False
    

    def remove_offset( self, offset: int ) -> bool:
        """
            Remove an offset from the client.

            Receive:    
            - offset    - Offset

            Returns:    bool - Is the offset removed
        """

        if not self.is_offset( offset ):
            return False
        
        self._offsets.remove( offset )
        return True

    # endregion

    # region : Files and lines

    def selected_file( self, new_value: any = None ) -> str:
        """
            Get/Set active client's file.

            Receive :   
            - new_value [optional] - New value to set

            Returns :   String
        """

        if new_value is None:

            if self._selected_file is None:
                return "Unknown"
            
            return self._selected_file.name( )
        
        new_value_type = type( new_value )

        if new_value_type == str:
            self._selected_file = self._files.search_file( new_value )

        elif new_value_type == c_virtual_file:
            self._selected_file = new_value
        
        return self._selected_file
    
    
    def selected_line( self, new_value: int = None ) -> int:
        """
            Get/Set clients active line.

            Receive :   
            - new_value [optional] - New value to set

            Returns :   Line number. ( 0 - is None )
        """

        if new_value is None:

            if self._selected_file is None:
                return 0
            
            return self._selected_line
        
        self._selected_line = new_value
        return new_value


    def files_list( self ) -> list:
        """
            Returns a list of names of files for the client.

            Receive :   None

            Returns :   List
        """

        result = [ ]

        for file_index in self._files.get_files( ):
            file: c_virtual_file = self._files.search_file( file_index )

            if file:
                result.append( file.name( ) )

        return result


    def get_file( self, file_name: str ) -> list:
        """
            Get the file object by name.

            Receive :   
            - file_name - File name

            Returns :   List [ file_name, access_level ]
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return [ "Unknown", 0 ]

        return [ file.name( ), file.access_level( ) ]

    # endregion

    # region : Trust factor

    def lower_trust_factor( self, value: int, reason: str ):
        """
            Register lowering the trust factor of a client.

            Receive :
            - value     - How much to lower the trust factor
            - reason    - Reason for lowering

            Returns :   None
        """

        self._trust_factor = math.clamp( self._trust_factor - value, 0, 100 )
        self._issues.append( reason )

        self.__event_client_log( f"lower trust factor for { reason }", user=f"client ( { self( 'username' ) } )", log_type=ENUM_LOG_ERROR )

    
    def check_trust_factor( self ) -> bool:
        """
            Check if the current client trust factor is valid.

            Receive :   None

            Returns :   Result if valid
        """
        
        return self._trust_factor > 0
    

    def trust_factor_latency( self ):
        
        pure_value = DEFAULT_TRUST_FACTOR - self._trust_factor
        
        if pure_value == 0:
            return
        
        pure_value = pure_value / DEFAULT_TRUST_FACTOR
        time.sleep( pure_value * 4 )
    

    def trust_factor( self, value: int = None ) -> int:
        """
            Get/Set client's trust factor value.

            Receive :   None

            Returns :   Number value
        """

        if value is None:
            return self._trust_factor
        
        self._trust_factor = value
        return value

    # endregion

    # region : Utility

    def network( self ) -> c_network_protocol:
        """
            Get the network protocol.

            Receive :   None

            Returns :   c_network_protocol - Network protocol
        """

        return self._network
    

    def files( self ) -> c_files_manager_protocol:
        """
            Get the clients files protocol.

            Receive :   None

            Returns :   c_files_manager_protocol - Files protocol
        """

        return self._files
    

    def attach_files( self, value: c_files_manager_protocol ):
        """
            Attach file manager protocol instance.

            Receive :
            - value - New instance of files manager protocol

            Returns :   None
        """

        self._files = value

    
    def attach_network( self, value: c_network_protocol ):
        """
            Attach network protocol instance.

            Receive :
            - value - New instance of network protocol

            Returns :   None
        """

        self._network = value

    
    def attach_information( self, index: str, value: any ):
        """
            Attach new information or update for client handle.

            Receive :
            - index - Key for value
            - value - Actual value to attach

            Returns :   None
        """

        self._information[ index ] = value


    def __call__( self, index: str ):
        """
            Index clients information.

            Receive:    
            - index - Index of the information

            Returns:    Any - Information
        """

        if index in self._information:
            return self._information[ index ]
        
        return None
    

    def __eq__( self, other ) -> bool:
        """
            Check if the client handle is equal to another client handle.

            Receive:    
            - other - Other client handle

            Returns:    bool - Is the client handle equal to the other
        """

        current_address = self._network.get_address( )
        other_address   = other._network.get_address( )

        if current_address[ 0 ] != other_address[ 0 ]:
            return False
        
        if current_address[ 1 ] != other_address[ 1 ]:
            return False
        
        return True

    # endregion


class c_host_business_logic:
    
    # region : Private Attributes

    _network:               c_network_protocol
    _files:                 c_files_manager_protocol
    _database:              c_database

    _information:           dict
    _events:                dict
    
    _command_pool:          queue.Queue

    _clients:               list

    _host_client:           c_client_handle     # For the host user should be also client that contains the information about file and line...
    # It is easier to control the host user with client handle

    # endregion 

    # region : Initialization host business logic

    def __init__( self ):
        """
            Default constructor for host business logic.

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

        self._network   = c_network_protocol( )
        self._files     = c_files_manager_protocol( )
        self._database  = c_database( )

    
    def __initialize_events( self ):
        """
            Initialize events for host business logic.

            Receive:    None

            Returns:    None
        """

        self._events = {
            "on_server_start":          c_event( ),
            "on_server_stop":           c_event( ),

            "on_client_connected":      c_event( ),
            "on_client_disconnected":   c_event( ),
            "on_client_command":        c_event( ),

            "on_files_refresh":         c_event( ),

            # Host user actions events
            "on_file_set":              c_event( ),
            "on_file_update":           c_event( ),

            "on_accept_line":           c_event( ),

            "on_line_lock":             c_event( ),
            "on_line_unlock":           c_event( ),

            "on_line_update":           c_event( ),
            "on_line_delete":           c_event( ),

            "on_added_log":             c_event( )
        }


    def __initialize_information( self ):
        """
            Initialize information for host business logic.

            Receive:    None

            Returns:    None
        """

        self._information = {
            "success":          False,  # Is the setup process was successful
            "running":          False,  # Is server running
            "last_error":       ""      # Last error message
        }

        self._clients = [ ]

        self._command_pool = queue.Queue( )

        self._host_client = c_client_handle( )
        self._host_client.attach_network(   self._network )
        self._host_client.attach_files(     self._files )

    # endregion

    # region : Connection

    def setup( self, ip: str, port: int, username: str, max_clients: int ):

        # I dont use @safe_call since I need to add debug options later on

        try:

            # Just save the information
            self._information[ "ip" ]           = ip
            self._information[ "port" ]         = port
            self._information[ "username" ]     = username
            self._information[ "max_clients" ]  = max_clients


            self._host_client.attach_information( "username", username )

            # Start connection using network protocol
            self._network.start_connection( CONNECTION_TYPE_SERVER, ip, port )

            # Set success setup flag to true
            self._information[ "success" ] = True

        except Exception as e:

            # In case of some error. Handle it
            self._information[ "last_error" ]   = f"Error occurred on .setup() : {e}"
            self._information[ "success" ]      = False
            

    def start( self ) -> bool:
        """
            Start the server for host business logic.

            Receive:    None

            Returns:    bool - Is the server started successfully
        """

        if not self._information[ "success" ]:
            self._information[ "last_error" ]   = f"Cannot start the server execution if it hasn't been setup."
            return False
        
        # Update is Running flag
        self._information[ "running" ] = True

        # Call event
        self.__event_host_start( )

        # Start to listen for new connections
        self._network.look_for_connections( )

        # Start the server process
        self.__attach_processes( )

        return True


    def terminate( self ):
        """
            Terminate the host.

            Receive:    None

            Returns:    None
        """

        if not self._information[ "running" ]:
            return self._network.end_connection( )
 
        # Update is Running flag
        self._information[ "running" ] = False
        c_debug.log_information( "Set [running] flag to False" )

        # Call event
        self.__event_host_stop( )
        c_debug.log_information( "Called __event_host_stop( )" )

        # Disconnect from the database
        self._database.disconnect( )
        c_debug.log_information( "Disconnected from the database" )

        # Disconnect all the remaining clients
        for client in self._clients:
            client: c_client_handle = client

            client.disconnect( True, False )

        c_debug.log_information( "Disconnected every client" )

        self._clients.clear( )
        c_debug.log_information( "Cleared client list" )

        # Close the network connection
        self._network.end_connection( )
        c_debug.log_information( "Closed network connection" )


    def generate_code( self ) -> str:
        """
            Generate a code for the client to connect to the server.

            Receive:    None

            Returns:    str - Generated code
        """

        local_ip, local_port = self._network.get_address( )

        result = f"{local_ip}:{local_port}"
        return base64.b64encode( result.encode( ) ).decode( )
    
    # endregion

    # region : Processes

    def __attach_processes( self ):
        """
            Attach processes for the host business logic.

            Receive:    None

            Returns:    None
        """

        # Start the process for handling connections
        self._information[ "connection_thread" ] = self.__process_handle_connections( )

        # Start the process for handling commands
        self._information[ "command_thread" ] = self.__process_handle_commands( )


    @standalone_execute
    def __process_handle_connections( self ):
        """
            Process for handling connections.

            Receive:    None
            
            Returns:    None
        """

        while self._information[ "running" ]:

            while len( self._clients ) >= self._information[ "max_clients" ]:
                time.sleep( SLEEP_ON_IDLE )

            # Get the new client
            client_socket, client_addr = self._network.accept_connection( TIMEOUT_CONNECTION )

            # If there is no client, continue
            if client_socket is None or client_addr is None:
                continue

            self.__event_client_connected( client_socket, client_addr )


    @standalone_execute
    def __process_handle_commands( self ):
        """
            Process for handling commands.

            Receive:    None

            Returns:    None
        """

        while self._information[ "running" ] or not self._command_pool.empty( ):

            if not self._command_pool.empty( ):

                # Get the command from the pool
                command: c_command = self._command_pool.get( block=False )

                # If there is no command, continue
                if command is None:
                    continue

                self.__handle_command( command )

            else:
                
                # If our command queue is empty, just sleep for 0.1 seconds.
                # Otherwise this thread will run million times per second.
                time.sleep( TIMEOUT_COMMAND )

    # endregion

    # region : Commands

    @safe_call( c_debug.log_error )
    def __handle_command( self, command: c_command ):
        """
            Handle command request.

            Receive :
            - command - Command object from client

            Returns :   None
        """

        base_command_callbacks = {
            FILES_COMMAND_PREPARE_UPDATE:   self.__command_execute_prepare_update,
            FILES_COMMAND_DISCARD_UPDATE:   self.__command_execute_discard_update,
            FILES_COMMAND_UPDATE_LINE:      self.__command_execute_commit_update,
            FILES_COMMAND_DELETE_LINE:      self.__command_execute_commit_delete,
            FILES_COMMAND_APPLY_UPDATE:     self.__command_execute_accept_offset,
            FILES_COMMAND_UPDATE_FILE_NAME: self.__command_execute_change_file_name
        }

        base_command_callbacks[ command.command( ) ]( command.client( ), command.arguments( ) )

        # Clear the memory from useless command that we processed already
        del command

    @safe_call( c_debug.log_error )
    def __command_execute_prepare_update( self, client: c_client_handle, arguments: list ):
        """
            Command for prepare line update.

            Receive :
            - client    - Client handle that requested
            - arguments - Arguments from the command

            Returns :   None
        """

        file_name:      str = arguments[ 0 ]
        line_number:    int = arguments[ 1 ]

        file: c_virtual_file = client.files( ).search_file( file_name )

        is_locked:  bool    = file.is_line_locked( line_number )
        response:   str     = is_locked and "1" or "0"

        if not is_locked:
            client.selected_line( line_number )
            file.lock_line( line_number )

            client_username: str = client( "username" ) or "Failed"

            self.__broadcast_for_shareable_clients( file, client, self.__broadcast_lock_line, line_number, client_username )

            self.__event_line_lock( file.name( ), line_number, client_username )

        message: str = self._files.format_message( FILES_COMMAND_PREPARE_RESPONSE, [ file.name( ), str( line_number ), response ] )
        client.send_quick_message( message )


    def __command_execute_discard_update( self, client: c_client_handle, arguments: list ):
        """
            Command for discard line update.

            Receive :
            - client    - Client handle that requested
            - arguments - Arguments from the command

            Returns :   None
        """

        file_name:      str = arguments[ 0 ]
        line_number:    int = arguments[ 1 ]

        file: c_virtual_file = client.files( ).search_file( file_name )

        file.unlock_line( line_number )
        client.selected_line( 0 )

        self.__broadcast_for_shareable_clients( file, client, self.__broadcast_unlock_line, line_number )

        self.__event_line_unlock( file.name( ), line_number )

    
    def __command_execute_commit_update( self, client: c_client_handle, arguments: list ):
        """
            Command for commit line update.

            Receive :
            - client    - Client handle that requested
            - arguments - Arguments from the command

            Returns :   None
        """

        file_name:      str     = arguments[ 0 ]
        line_number:    int     = arguments[ 1 ]
        new_lines:      list    = arguments[ 2 ]

        file: c_virtual_file = client.files( ).search_file( file_name )

        file.unlock_line( line_number )
        client.selected_line( 0 )

        file.change_line( line_number, new_lines, { "user": client( "username" ) } )

        self.__broadcast_for_shareable_clients( file, client, self.__broadcast_update_line, line_number, new_lines )

        if not client == self._host_client:
            self.__correct_host_offset( file, line_number, len( new_lines ) )
            self.__event_line_update( file.name( ), line_number, new_lines )
    

    def __command_execute_commit_delete( self, client: c_client_handle, arguments: list ):
        """
            Command for commit line delete.

            Receive :
            - client    - Client handle that requested
            - arguments - Arguments from the command

            Returns :   None
        """

        file_name:      str     = arguments[ 0 ]
        line_number:    int     = arguments[ 1 ]

        file: c_virtual_file = client.files( ).search_file( file_name )

        file.unlock_line( line_number )
        client.selected_line( 0 )

        file.remove_line( line_number, { "user": client( "username" ) } )

        self.__broadcast_for_shareable_clients( file, client, self.__broadcast_delete_line, line_number )

        if not client == self._host_client:
            self.__correct_host_offset( file, line_number, 0 )
            self.__event_line_delete( file.name( ), line_number )


    def __command_execute_accept_offset( self, client: c_client_handle, arguments: list ):
        """
            Command for accept offset change.

            Receive :
            - client    - Client handle that requested
            - arguments - Arguments from the command

            Returns :   None
        """

        update_type: int = arguments[ 0 ]
        if update_type == FILE_UPDATE_CONTENT:

            # I know it technically cause bottleneck issue, but this is the system.
            # Simple and kinda quick... ( or at least should be )

            # This has to be ordered since the line change can be delayed

            # For example
            # Change [2]
            # OTHER...
            # Change [1]
            # - HEAD OF THE QUEUE

            # CHANGE 1 has been committed and the client accepted it, but 
            # there is still Change [2]
            # in the queue waiting. Without this, it will mess everything up.

            offset: int = arguments[ 1 ]
            return client.remove_offset( offset )
        
        if update_type == FILE_UPDATE_NAME:
            
            old_index: str = arguments[ 1 ]
            new_index: str = arguments[ 2 ]

            return client.files( ).update_name( old_index, new_index )
        
    
    def __command_execute_change_file_name( self, client: c_client_handle, arguments: list ):
        
        old_index:          str = arguments[ 0 ]
        new_index:          str = arguments[ 1 ]
        new_default_level:  int = arguments[ 2 ]

        file: c_virtual_file = self._files.update_name( old_index, new_index )
        file.access_level( new_default_level )

        self.__broadcast_for_shareable_clients( None, client, self.__broadcast_change_file_name, old_index, new_index )

    
    # endregion

    # region : Broadcasting

    def __broadcast_for_shareable_clients( self, file: c_virtual_file, exception: c_client_handle, broadcast_function: any, *args ):
        """
            Execute broadcase function for each client that shares the same file.

            Receive :
            - file                  - Specific shared file
            - exception             - Avoid broadcasting to him
            - broadcase_function    - Function to execute for each client

            Returns :   None
        """

        for client in self._clients:
            client: c_client_handle = client

            if ( file is not None and client.selected_file( ) == file.name( ) ) or file is None:
                
                if exception is None or client != exception:
                    broadcast_function( client, file, *args )


    def __broadcast_lock_line( self, client: c_client_handle, file: c_virtual_file, line: int, username: str ):
        """
            Notify the client that a specific line is locked.

            Receive :
            - client    - Client to notify
            - file      - File that is shared
            - line      - Locked line

            Returns :   None
        """

        # TODO ! Add check if the client can edit

        message = self._files.format_message( FILES_COMMAND_PREPARE_UPDATE, [ file.name( ), str( line ), username ] )
        client.send_quick_message( message )
    

    def __broadcast_unlock_line( self, client: c_client_handle, file: c_virtual_file, line: int ):
        """
            Notify the client that a specific line is unlocked.

            Receive :
            - client    - Client to notify
            - file      - File that is shared
            - line      - Locked line

            Returns :   None
        """

        # TODO ! Add check if the client can edit

        message = self._files.format_message( FILES_COMMAND_DISCARD_UPDATE, [ file.name( ), str( line ) ] )
        client.send_quick_message( message )
    

    def __broadcast_update_line( self, client: c_client_handle, file: c_virtual_file, line: int, new_lines: list ):
        """
            Notify the client that a specific line is updated.

            Receive :
            - client    - Client to notify
            - file      - File that is shared
            - line      - Locked line
            - new_lines - New lines

            Returns :   None
        """

        client_line: int = client.selected_line( )
        count_new_lines = len( new_lines ) - 1

        if client_line > 0 and client_line > line:

            if file.is_line_locked( client_line ):
                file.unlock_line( client_line )
                file.lock_line( client_line + count_new_lines )

            client.add_offset( count_new_lines )
            client.selected_line( client_line + count_new_lines )

        message = self._files.format_message( FILES_COMMAND_UPDATE_LINE, [ file.name( ), str( line ), str( count_new_lines + 1 ) ] )
        client.send_quick_message( message )

        for new_line in new_lines:
            new_line: str = new_line

            if new_line == "":
                new_line = "\n"

            client.send_quick_bytes( base64.b64encode( new_line.encode( ) ) )


    def __broadcast_delete_line( self, client: c_client_handle, file: c_virtual_file, line: int ):
        """
            Notify the client that a specific line is deleted.

            Receive :
            - client    - Client to notify
            - file      - File that is shared
            - line      - Locked line

            Returns :   None
        """

        client_line: int = client.selected_line( )

        if client_line > 0 and client_line > line:

            if file.is_line_locked( client_line ):
                file.unlock_line( client_line )
                file.lock_line( client_line - 1 )

            client.add_offset( -1 )
            client.selected_line( client_line - 1 )

        message = self._files.format_message( FILES_COMMAND_DELETE_LINE, [ file.name( ), str( line ) ] )
        client.send_quick_message( message )


    def __broadcast_change_file_name( self, client: c_client_handle, file: c_virtual_file, old_index: str, new_index: str ):

        client_files: c_files_manager_protocol = client.files( )
        file = client_files.search_file( old_index )

        if not file:
            return

        if file.access_level( ) == FILE_ACCESS_LEVEL_HIDDEN:
            return client.files( ).update_name( old_index, new_index )
        
        message = self._files.format_message( FILES_COMMAND_UPDATE_FILE_NAME, [ old_index, new_index ] )
        client.send_quick_message( message )

    # endregion

    # region : Files

    def initialize_base_values( self, path: str, default_access: int, scan_types: int, should_scan_virtual: bool ):
        """
            Create and setup the project files path.

            Receive :
            - path - Path string for files

            Returns :   None
        """

        self._information[ "original_path" ]        = path
        self._information[ "default_access" ]       = default_access
        self._information[ "scan_types" ]           = scan_types
        self._information[ "should_scan_virtual" ]  = should_scan_virtual

        self.__setup_path( )

    
    def connect_to_database( self, password: str ) -> bool:

        # Load path or create database
        self._database.load_path( self._information[ "normal_path" ] )

        # Try to connect to database based on username and password
        result: bool = self._database.connect( self._information[ "username" ], password )
        if not result:
            self._information[ "last_error" ] = f"Failed to connect to database. { self._database.last_error( ) }"
            return False
        
        return True

    
    def complete_setup_files( self ):

        self.__setup_files( )

        self.__event_files_refresh( )


    def create_empty_file( self, path: str, name: str, access_level: int = FILE_ACCESS_LEVEL_HIDDEN ):

        # Need to parse the data.
        # We assume that this file is places in the .original_path\\DEFAULT_FOLDER

        # TODO ! Maybe create the file on the default path ?

        normalized_path = os.sep.join( [ path, name ] )
        normalized_name = normalized_path.replace( self._information[ "normal_path" ] + os.sep, "" )
        
        file: c_virtual_file = self._files.search_file( normalized_name )
        if file:
            return
        
        file = self._files.create_new_file( normalized_name, access_level )
        r = file.create( self._information[ "normal_path" ], f"File created by { self._information[ 'username' ] }" )

        if r is not None:
            c_debug.log_error( r )

        # Now we need to setup the files for connected clients
        if len( self._clients ) == 0:
            return

        for client in self._clients:
            client: c_client_handle = client

            client_files: c_files_manager_protocol = client.files( )
            
            for file_index in self._files.get_files( ):
                v_file: c_virtual_file = self._files.search_file( file_index )

                if v_file and not client_files.search_file( file_index ):
                    client_files.copy( v_file )

                    client.change_access_level( v_file.name( ), v_file.access_level( ) )


    def __setup_path( self ):
        """
            Setup Folder for files.

            Receive :   None

            Returns :   None
        """

        original_path   = self._information[ "original_path" ]
        normal_path     = f"{ original_path }\\{ DEFAULT_FOLDER_NAME }"

        self._information[ "normal_path" ] = normal_path
        
        if not os.path.exists( normal_path ):
            os.mkdir( normal_path )


    def __setup_files( self ):
        """
            Setup files of the project.

            Receive :   None

            Returns :   None
        """

        # Here need to make a copy of each file to the new path.
        # Besides, create for each file another file that stores all the changes
        original_path:  str = self._information[ "original_path" ]
        normal_path:    str = self._information[ "normal_path" ]

        scan_types:             int    = self._information[ "scan_types" ]
        should_scan_virtual:    bool   = self._information[ "should_scan_virtual" ]

        if should_scan_virtual:
            self.__dump_previous_path( normal_path )
    
        if not scan_types == ENUM_SCAN_DISABLE:
            self.__dump_path( original_path )
            

    def __dump_path( self, path: str ):
        """
            Dump specific path.

            Receive : 
            - path - Full path to a folder to dump

            Returns :   None
        """
        
        original_path           = self._information[ "original_path" ]
        normal_path             = self._information[ "normal_path" ]
        access_level            = self._information[ "default_access" ]
        should_avoid_rescanning = self._information[ "scan_types" ] == ENUM_SCAN_CREATE_NEW

        allowed_file_types = ( ".py", ".cpp", ".hpp", ".c", ".h", ".cs", ".txt" )

        with os.scandir( path ) as entries:
            
            for entry in entries:
                
                if entry.is_file( ):
                    # Is File

                    fixed_name = f"{ path.replace( original_path, '' ) }\\{ entry.name }"
                    fixed_name = fixed_name.lstrip( "\\" )

                    if not fixed_name.endswith( allowed_file_types ):
                        continue

                    # Avoid recreating the same file.
                    if should_avoid_rescanning and self._files.search_file( fixed_name ) is not None:
                        continue
                    
                    file = self._files.create_new_file( fixed_name, access_level, True )
                    r = file.copy( original_path, normal_path )

                    if r is not None:
                        c_debug.log_error( r )

                if entry.is_dir( ) and entry.name != DEFAULT_FOLDER_NAME and not entry.name.startswith( "." ):
                    # Is Folder
                    
                    self.__dump_path( f"{ path }\\{ entry.name }" )
    

    def __dump_previous_path( self, path: str ):

        normal_path     = self._information[ "normal_path" ]
        access_level    = self._information[ "default_access" ]

        allowed_file_types = ( ".py", ".cpp", ".hpp", ".c", ".h", ".cs", ".txt" )

        with os.scandir( path ) as entries:
            
            for entry in entries:
                
                if entry.is_file( ):
                    # Is File
                    
                    fixed_name = f"{ path.replace( normal_path, '' ) }\\{ entry.name }"
                    fixed_name = fixed_name.lstrip( "\\" )

                    # Make sure there is no junk added by mistake or not.
                    if not fixed_name.endswith( allowed_file_types ):
                        continue

                    # Dont create virtual file for changes file
                    if fixed_name.endswith("_changes.txt"):
                        continue
                    
                    # Create instance of virtual file
                    file = self._files.create_new_file( fixed_name, access_level, True )
                    file.attach( normal_path )

                if entry.is_dir( ) and entry.name != DEFAULT_FOLDER_NAME and not entry.name.startswith( "." ):
                    # Is Folder
                    
                    self.__dump_previous_path( f"{ path }\\{ entry.name }" )
    
    # endregion

    # region : Host actions

    @static_arguments
    def request_file( self, file_name: str ):
        """
            Trigger the set file event to receive a file's content.

            Receive :
            - file_name - File's name

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        self._host_client.selected_file( file )
        
        self.__event_file_set( file )
        self.__event_file_update( file )

        for line in file.locked_lines( ):
            self.__event_line_lock( file.name( ), line )
    

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
        
        # First check if line is locked
        is_locked: bool = file.is_line_locked( line )
        if is_locked:
            return
        
        file.lock_line( line )
        self._host_client.selected_line( line )

        self.__broadcast_for_shareable_clients( file, None, self.__broadcast_lock_line, line, self._information[ "username" ] )

        self.__event_accept_line( file.name( ), line )

    
    @standalone_execute
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
        
        is_locked: bool = file.is_line_locked( line )
        if not is_locked:
            return
        
        file.unlock_line( line )
        self._host_client.selected_line( 0 )

        self.__broadcast_for_shareable_clients( file, None, self.__broadcast_unlock_line, line )


    def update_line( self, file_name: str, line: int, lines: list ):
        """
            Update lines for all clients.

            Receive :
            - file_name - File name
            - line      - Line number
            - lines     - List of changed lines

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        new_command: c_command = c_command( self._host_client, ENUM_PROTOCOL_FILES, FILES_COMMAND_UPDATE_LINE, [ ] )

        new_command.add_arguments( file.name( ) )
        new_command.add_arguments( line )
        new_command.add_arguments( lines )

        self._command_pool.put( new_command )

    
    def delete_line( self, file_name: str, line: int ):
        """
            Delete the line for all clients.

            Receive :
            - file_name - File name
            - line      - Line number

            Returns :   None
        """

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return
        
        new_command: c_command = c_command( self._host_client, ENUM_PROTOCOL_FILES, FILES_COMMAND_DELETE_LINE, [ ] )

        new_command.add_arguments( file.name( ) )
        new_command.add_arguments( line )

        self._command_pool.put( new_command )

    
    def find_file_information( self, file_name: str ) -> tuple:
        
        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            return False, ( "Failed to find file" )
        
        file_name, file_type        = file.name( True )
        normalized_file_name:   str = file_name.split( os.sep )[ -1 ]
        file_size:              str = str( file.size( ) )

        return True, ( normalized_file_name, file_type, file_size, file.access_level( ) )
    

    def update_file_details( self, old_index: str, new_index: str, new_default_level: int ):
        
        file: c_virtual_file = self._files.search_file( old_index )
        if not file:
            return

        new_command: c_command = c_command( self._host_client, ENUM_PROTOCOL_FILES, FILES_COMMAND_UPDATE_FILE_NAME, [ ] )

        new_command.add_arguments( old_index )
        new_command.add_arguments( new_index ) 
        new_command.add_arguments( new_default_level ) 
        
        self._command_pool.put( new_command )

    # endregion

    # region : Events

    def __event_host_start( self ):
        """
            Event when the host server started.

            Receive:    None

            Returns:    None
        """

        event: c_event = self._events[ "on_server_start" ]
        event.invoke( )

    
    def __event_host_stop( self ):
        """
            Event when the host server stopped.

            Receive:    None

            Returns:    None
        """

        event: c_event = self._events[ "on_server_stop" ]
        event.invoke( )

    
    def __event_client_connected( self, client_socket: socket, client_address: tuple ):
        """
            Event when a client connected to the server.

            Receive:    
            - client_socket     - Client socket
            - client_address    - Client address

            Returns:    None
        """

        # Create a new client handle
        new_client = c_client_handle( )

        # Save the client object
        self._clients.append( new_client )

        # Set the client events
        host_log_fn = lambda event: self.log_information( event( "message" ), event( "save_in_app" ), event( "log_type" ), event( "user" ) )

        new_client.set_event( "on_client_disconnected", self.__event_client_disconnected,   "Host Client Disconnect" )
        new_client.set_event( "on_client_command",      self.__event_client_command,        "Host Client Command" )
        new_client.set_event( "on_client_log",          host_log_fn,                        "Host Logging" )

        # Load path for database.
        new_client.load_database( self._database )

        # Attach files for client
        new_client.load_files( self._files )

        # Connect the client
        new_client.connect( client_socket, client_address )

        # Call the event
        event: c_event = self._events[ "on_client_connected" ]
        event.invoke( )

    
    def __event_client_disconnected( self, event ):
        """
            Event when a client disconnected from the server.

            Receive:    
            - event - Event information

            Returns:    None
        """

        if event( "remove" ) == 1:
            client: c_client_handle = event( "client" )

            # Remove the client from the list
            self._clients.remove( client )

        # Call the event
        event: c_event = self._events[ "on_client_disconnected" ]
        event.invoke( )

    
    def __event_client_command( self, event ):
        """
            Event when a client sent a command.

            Receive:    
            - event - Event information

            Returns:    None
        """

        command: c_command = event( "command" )
        if command is None:
            return

        # Add the command to the pool
        self._command_pool.put( command )

        # Call the event
        event: c_event = self._events[ "on_client_command" ]
        event.invoke( )

    
    def __event_files_refresh( self ):
        """
            Event when the host files are refreshed.

            Receive :   None

            Returns :   None
        """

        files = self._files.get_files( )

        result = [ ]
        for index in files:
            file: c_virtual_file = files[ index ]

            result.append( file.name( ) )

        event: c_event = self._events[ "on_files_refresh" ]
        event.attach( "files", result )

        event.invoke( )


    def __event_file_set( self, file: c_virtual_file ):
        """
            Event when the the host user request file.

            Receive :
            - file - File's reference

            Returns :   None
        """

        event: c_event = self._events[ "on_file_set" ]
        event.attach( "file", file.name( ) )

        event.invoke( )

    
    def __event_file_update( self, file: c_virtual_file ):
        """
            Event callback for updating a file

            Receive :
            - file - File's reference

            Returns :   None
        """

        event: c_event = self._events[ "on_file_update" ]
        
        for line in file.read_lines( ):
            event.attach( "line_text", line )
            event.invoke( )

    
    def __event_accept_line( self, file: str, line: int ):
        """
            Event callback for accepting the line

            Receive :
            - file      - File's name
            - line      - Line number

            Returns :   None
        """

        event: c_event = self._events[ "on_accept_line" ]

        event.attach( "file",   file )
        event.attach( "line",   line )

        event.invoke( )

    
    def __event_line_lock( self, file: str, line: int, locked_by: str = "?" ):
        """
            Event callback for locking a line.

            Receive :
            - file      - File's name
            - line      - Line number

            Returns :   None
        """

        if file != self._host_client.selected_file( ):
            return

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

        if file != self._host_client.selected_file( ):
            return

        event: c_event = self._events[ "on_line_unlock" ]

        event.attach( "file", file )
        event.attach( "line", line )

        event.invoke( )


    def __event_line_update( self, file: str, line: int, lines: list ):
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
        event.attach( "new_lines",  lines )

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


    def __event_added_log( self, message: str, log_type: int = ENUM_LOG_INFO, user: str = "system", time: str = "unk_time" ):

        event: c_event = self._events[ "on_added_log" ]

        event.attach( "message",    message )
        event.attach( "user",       user )
        event.attach( "time",       time )
        event.attach( "type",       log_type )

        event.invoke( )


    def set_event( self, event_type: str, callback: any, index: str, allow_arguments: bool = True ):
        """
            Add function to be called on specific event.

            Receive :
            - event_type                    - Event name
            - callback                      - Function to execute
            - index                         - Function index
            - allow_arguments [optional]    - Allow function to get arguments

            Returns :   None
        """

        if not event_type in self._events:
            raise Exception( "Invalid event type to attach" )
        
        event: c_event = self._events[ event_type ]
        event.set( callback, index, allow_arguments )

    # endregion

    # Utilities

    def __correct_host_offset( self, file: c_virtual_file, line: int, new_lines: int ):
        """
            Correct the host file locked line on change.

            Receive :
            - file      - File's reference
            - line      - Changed line number
            - new_lines - New lines that changed

            Returns :   None
        """

        client_line: int = self._host_client.selected_line( )
        count_new_lines = new_lines - 1

        if client_line > 0 and client_line > line:

            if file.is_line_locked( client_line ):
                file.unlock_line( client_line )
                file.lock_line( client_line + count_new_lines )

            self._host_client.selected_line( client_line + count_new_lines )


    def find_client( self, username: str ) -> c_client_handle:
        """
            Search client by username.

            Receive :
            - username - Client's username

            Returns :   Client object on find or None on fail
        """

        for client in self._clients:
            client: c_client_handle = client

            if client( "username" ) == username:
                return client
            
        return None
    

    def get_host_client( self ) -> c_client_handle:

        return self._host_client
    

    def log_information( self, message: str, save_in_app: bool = True, log_type: int = ENUM_LOG_INFO, user: str = "system" ):
        
        if save_in_app:
            self.__event_added_log( message, log_type, user, time.strftime( "%y-%m-%d %H:%M:%S", time.localtime( ) ) )

        if log_type == ENUM_LOG_INFO:
            return c_debug.log_information( f"{ user } - { message }" )
        
        if log_type == ENUM_LOG_ERROR:
            c_debug.log_error( f"{ user } - { message }" )


    def __call__( self, index: str ):
        
        if index in self._information:
            return self._information[ index ]
        
        return None
    
    # endregion

    def clients( self ) -> list:

        return self._clients