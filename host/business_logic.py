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

import threading
import base64
import queue
import time
import os

DEFAULT_FOLDER_NAME:    str     = "Digital Files"

TIMEOUT_CONNECTION:     float   = 0.5
TIMEOUT_MSG:            float   = 0.5
TIMEOUT_COMMAND:        float   = 0.1

ENUM_PROTOCOL_FILES:    int     = 1
ENUM_PROTOCOL_NETWORK:  int     = 2
ENUM_PROTOCOL_UNK:      int     = 0


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
    _registration:      c_registration_protocol     # Clients register process
    _security:          c_security                  # Clients security protocol

    _information:       dict                        # Clients information
    _events:            dict                        # Each client events

    _selected_file:     c_virtual_file              # Selected file
    _selected_line:     int                         # Selected line

    _offsets:           list                        # Offsets for missed lines
    # We dont want modded client to spoof index change response.
    # As a result each change will be added to a list, and in general used as sum( ) for offset
    # And checks if one offset is responded, just remove from the list.

    _trust_factor:      int                         # Trust factor for the client
    _is_modded:         bool                        # Is the client modded
    _issues:            list                        # Issues that the client created that lowered the trust factor
    # This part will be used to keep track of the issues that the client created.
    # If the client created an issue, the trust factor will be lowered.
    # If the client didn't create any issue in a while, the trust factor will be increased.
    # The trust factor will be between 100 - 0. If the trust factor is 0, the client will be disconnected.

    _files_commands:    dict

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
            "on_client_connected":      c_event(),
            "on_client_disconnected":   c_event(),
            "on_client_command":        c_event()
        }

    
    def __initialize_information( self ):
        """
            Initialize information for client handle.

            Receive:    None

            Returns:    None
        """

        self._network       = None
        self._files         = c_files_manager_protocol( )
        self._registration  = c_registration_protocol( )
        self._security      = c_security( )

        self._information = {
            "last_error":   "",
            "username":     "unknown"
        }

        self._selected_file     = None
        self._selected_line     = 0
        self._trust_factor      = 50
        self._offsets           = [ ]

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

        c_debug.log_information( f"New connection. Ip - { address[ 0 ] } : Port - { address[ 1 ] }" )

        # Attach connection
        self.__attach_connection( socket_object, address )

        # Protect connection
        if not self.__secure_connection( ):
            return self.disconnect( False )

        # Register the connection
        if not self.__register_connection( ):
            return self.disconnect( False )

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

        # Receive Client's public key
        self._security.share( SHARE_TYPE_LONG_PART, self._network.receive( ) )

        # Share host's client handle public key
        self._network.send_bytes( self._security.share( SHARE_TYPE_LONG_PART ) )

        # Generate quick key
        self._security.generate_quick_key( )

        # Share the quick key with the client
        self._network.send_bytes( self._security.share( SHARE_TYPE_QUICK_PART ) )

        return True
    

    def __register_connection( self ) -> bool:
        """
            Register the connection to the server.

            Receive:    None

            Returns:    Result
        """

        # Here will be the registration process

        raw_msg: str = self._security.remove_strong_protection( self._network.receive( ) ).decode( )
        
        if not raw_msg.startswith( self._registration.header( ) ):
            self._information[ "last_error" ] = "Cannot receive normalized registration information about client"
            return self.disconnect( False )

        command, arguments = self._registration.parse_message( raw_msg )
        if not command or not arguments:
            self._information[ "last_error" ] = "Failed to parse message"
            return 
        
        success = False

        # username: str = arguments[ 0 ]
        # password: str = arguments[ 1 ]

        if command == REGISTRATION_COMMAND_REG:
            # Register
            
            success:    bool        = self._registration.register_user( arguments[ 0 ], arguments[ 1 ] )
        
        elif command == REGISTRATION_COMMAND_LOG:
            # Logic
            
            success:    bool        = self._registration.login_user( arguments[ 0 ], arguments[ 1 ] )


        response:   str         = self._registration.format_message( 
            REGISTRATION_RESPONSE, 
            [ 
                success and "1" or "0", 
                self._registration.last_error( ) 
            ] 
        )

        self.send_quick_message( response )
        
        if success:
            
            c_debug.log_information( f"Client with username ( { arguments[ 0 ] } ) completed registration" )

            self._information[ "username" ] = arguments[ 0 ]
            return True

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


    def disconnect( self, notify_the_client: bool = True ):
        """
            Disconnect the client from the server.

            Receive:    
            - notify_the_client  - Notify the client about the disconnection

            Returns:    None
        """

        # Potentially notify the client
        if notify_the_client:
            self.send_quick_message( DISCONNECT_MSG )

        # End the connection
        self._network.end_connection( )

        # Call the event
        self.__event_client_disconnected( notify_the_client )

        c_debug.log_information( f"Client ( { self( 'username' ) } ) - disconnected" )

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

            #if not self.check_trust_factor( ):
            #    return self.disconnect( False )
            
            message: bytes = self.__receive( )

            if not message:
                continue
            
            # Decode the message
            message: str = message.decode( )
        
            self.__handle_message( message )


    def __receive( self ) -> bytes:
        """
            Wrap the receive and the security part.

            Receive :   None

            Returns :   Received Bytes
        """

        # Receive the key and remove the protection
        key: bytes = self._security.remove_strong_protection( self._network.receive( TIMEOUT_MSG ) )
        if not key:
            return None
                
        # Receive the message
        message: bytes = self._network.receive( TIMEOUT_MSG )

        # If there is no message, continue
        if message is None:
            return None

        # Remove shuffle and protection
        return self._security.remove_quick_protection( self._security.unshuffle( key, message ) )


    def __handle_message( self, message: str ):
        """
            Handle message from client.

            Receive :
            - message - Client's message

            Returns :   None
        """

        # Manual checks
        if message == DISCONNECT_MSG:
            return self.disconnect( False )

        if message == PING_MSG:
            return c_debug.log_information( f"Client ( { self( 'username' ) } ) - pinged" )

        # Try to parse the message and create new command object
        new_command = self.__parse_message( message )

        # Remove the message string it self
        del message

        if not self.__verify( new_command ):
            del new_command
            return

        # Check if the client handle can handle the command by it self
        # Note ! In some cases, there will be callback for a command, but later it will pass
        # the command object to the command pool, to order the command result.
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


    def __verify( self, command: c_command ) -> bool:
        """
            Verify if the command is valid.

            Receive :
            - command - Command object

            Returns :   Result 
        """

        protocol = command.protocol( )

        if protocol == ENUM_PROTOCOL_UNK:
            self.lower_trust_factor( 10, "Invalid command" )
            return False

        if protocol == ENUM_PROTOCOL_FILES:
            return command.command( ) in self._files_commands

        return True


    def send_quick_message( self, message: str ):
        """
            Send a quick message to the host.

            Receive :
            - message - Message to send

            Returns :   None
        """

        key: bytes = self._security.generate_shaffled_key( )
        
        self._network.send_bytes( self._security.strong_protect( key ) )
        self._network.send_bytes( self._security.shuffle( key, self._security.quick_protect( message.encode( ) ) ) )
    

    def send_quick_bytes( self, data: bytes ):
        """
            Send a quick bytes to the client.

            Receive :
            - message - Message to send

            Returns :   None
        """

        key: bytes = self._security.generate_shaffled_key( )
        
        self._network.send_bytes( self._security.strong_protect( key ) )
        self._network.send_bytes( self._security.shuffle( key, self._security.quick_protect( data ) ) )

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


    def __event_client_disconnected( self, notify_the_client: bool ):
        """
            Event when the client disconnected from the server.

            Receive:    
            - notify_the_client  - Notify the client about the disconnection

            Returns:    None
        """

        event: c_event = self._events[ "on_client_disconnected" ]
        event.attach( "client", self )
        event.attach( "notify", notify_the_client and "1" or "0" )

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

    
    def load_database( self, path: str, username: str ):
        """
            Load path for database of registration protocol.

            This must be called before .connect( )

            Receive :
            - path      - Path to database
            - username  - Username of creator

            Returns :   None
        """

        self._registration.load_path_for_database( path, username )


    def __share_files( self, command: c_command ):
        """
            Share with client the allowed files.

            Receive :   
            - command - Original command

            Returns :   None
        """

        c_debug.log_information( f"Client ( { self( 'username' ) } ) - requested files" )

        files_list: str = self._files.share_files( )
        self.send_quick_message( files_list )

    
    def __get_file( self, command: c_command ):
        """
            Share the file with the client.

            Receive :   
            - command - Original command

            Returns :   None
        """

        file_name: str = command.arguments( )[ 0 ]

        file: c_virtual_file = self._files.search_file( file_name )
        if file is None:
            return 
        
        if file.access_level( ) == FILE_ACCESS_LEVEL_HIDDEN:
            return
        
        c_debug.log_information( f"Client ( { self( 'username' ) } ) - requested file { file.name( ) }" )

        self._selected_file = file

        file_size:  int     = file.size()
        config:     list    = self._network.get_raw_details( file_size )

        self.send_quick_message( self._files.format_message( FILES_COMMAND_SET_FILE, [ file.name( ), str( file_size ) ] ) )

        key: bytes = self._security.generate_shaffled_key( )
        self._network.send_bytes( self._security.strong_protect( key ) )

        for chunk_info in config:
            start       = chunk_info[ 0 ]
            end         = chunk_info[ 1 ]
            has_next    = chunk_info[ 2 ]

            file_chunk = file.read( start, end )
            self._network.send_raw( self._security.shuffle( key, self._security.quick_protect( file_chunk ) ), has_next )

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

        if line_number is None:
            # TODO ! Check maybe ?
            return

        if self._selected_line != 0:
            # TODO ! Lower the trust factor
            # Moreover ...
            return

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            # TODO ! Lower the trust factor
            return
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            # TODO ! Lower the trust factor
            return
        
        # In general the locked lines should show up for the client
        # and it doesnt need to request it if locked
        if file.is_line_locked( line_number ):
            # This can happen only in 1 cases.
            # 1. The client didnt have time to register line lock
            # 2. The client is modded

            # To be sure, will add more checks later
            self._is_modded = True  

        c_debug.log_information( f"Client ( { self( 'username' ) } ) - requested line { line_number } in file { file.name( ) }" )

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

        if line_number is None:
            # TODO ! Check maybe ?
            return

        if self._selected_line == 0:
            # TODO ! Lower the trust factor
            # Moreover ...
            return

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            # TODO ! Lower the trust factor
            return
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            # TODO ! Lower the trust factor
            return

        # Fix the client offset...P
        line_number += self.get_offset( )

        if line_number != self.selected_line( ):
            # TODO ! Lower the trust factor
            return

        # This check will pass anyway if [ line_number == self.selected_line( ) ]
        # is_locked: bool = file.is_line_locked( line_number )
        # if not is_locked:
        #     # TODO ! Lower the trust factor
        #     return

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

        if line_number is None or lines_number is None:
            # TODO ! Check maybe ?
            return

        if self._selected_line == 0:
            # TODO ! Lower the trust factor
            # Moreover ...
            return

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            # TODO ! Lower the trust factor
            return
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            # TODO ! Lower the trust factor
            return
        
        # Fix the client offset...
        line_number += self.get_offset( )

        if line_number != self.selected_line( ):
            # TODO ! Lower the trust factor
            return

        new_lines: list = [ ]
        for index in range( lines_number ):
            new_line: bytes = self.__receive( )

            if not new_line:
                raise Exception( f"Failed to get line on index { index + 1 }" )
            
            new_line: str = base64.b64decode( new_line ).decode( )
            if new_line == "\n":
                new_line = ""
            
            new_lines.append( new_line )

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

        if line_number is None:
            # TODO ! Check maybe ?
            return

        if self._selected_line == 0:
            # TODO ! Lower the trust factor
            # Moreover ...
            return

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            # TODO ! Lower the trust factor
            return
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            # TODO ! Lower the trust factor
            return
        
        # Fix the client offset...
        line_number += self.get_offset( )

        if line_number != self.selected_line( ):
            # TODO ! Lower the trust factor
            return
        
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

        # Here we just preform all the checks...
        arguments:      list    = command.arguments( )

        # Convert the arguments into real values
        file_name:      str     = arguments[ 0 ]
        offset_number:  int     = math.cast_to_number( arguments[ 1 ] )

        if offset_number is None:
            # TODO ! Check maybe ?
            return

        file: c_virtual_file = self._files.search_file( file_name )
        if not file:
            # TODO ! Lower the trust factor
            return
        
        access_level: int = file.access_level( )
        if access_level != FILE_ACCESS_LEVEL_EDIT:
            # TODO ! Lower the trust factor
            return
        
        if not self.is_offset( offset_number ):
            # TODO ! Lower the trust factor
            return
        
        command.clear_arguments( )
        command.add_arguments( offset_number )

        # In the end process the command in commands pool
        self.__event_client_command( command )
    

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
        
        #file.change_access_level( new_level )
        c_debug.log_information( f"Client ( { self( 'username' ) } ) - changed access level of file { file_name } to { new_level }" )

        file.access_level( new_level )

        # Prepare messafe for client
        message: str = self._files.format_message( FILES_COMMAND_CHANGE_LEVEL, [ file.name( ), str( new_level ) ] )
        self.send_quick_message( message )
        
    
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

    
    def check_trust_factor( self ) -> bool:
        """
            Check if the current client trust factor is valid.

            Receive :   None

            Returns :   Result if valid
        """
        
        return self._trust_factor > 0
    

    def get_trust_factor( self ) -> int:
        """
            Get client's trust factor value.

            Receive :   None

            Returns :   Number value
        """

        return self._trust_factor

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

    _network:       c_network_protocol
    _files:         c_files_manager_protocol

    _information:   dict
    _events:        dict
    
    _command_pool:  queue.Queue

    _clients:       list

    _host_client:   c_client_handle     # For the host user should be also client that contains the information about file and line...
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

        self._network = c_network_protocol()
        self._files   = c_files_manager_protocol()

    
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
            "on_line_delete":           c_event( )
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

    def setup( self, ip: str, port: int, username: str ):
        """
            Setup the server for host business logic.

            Receive:    
            - ip    - IP address      
            - port  - Port number

            Returns:    None
        """

        # I dont use @safe_call since I need to add debug options later on

        try:

            # Just save the information
            self._information[ "ip" ]       = ip
            self._information[ "port" ]     = port
            self._information[ "username" ] = username

            self._host_client.attach_information( "username", username )

            # Start connection using network protocol
            self._network.start_connection( CONNECTION_TYPE_SERVER, ip, port )

            # Set success setup flag to true
            self._information[ "success" ] = True

        except Exception as e:

            # In case of some error. Handle it
            self._information[ "last_error" ]   = f"Error occured on .setup() : {e}"
            self._information[ "success" ]      = False
            

    def start( self ) -> bool:
        """
            Start the server for host business logic.

            Receive:    None

            Returns:    bool - Is the server started successfully
        """

        if not self._information[ "success" ]:
            self._information[ "last_error" ]   = f"Cannot start the server execution if it hasn't been setupped."
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
            return

        # Update is Running flag
        self._information[ "running" ] = False

        # Call event
        self.__event_host_stop( )

        # Disconnect all the remaining clients
        for client in self._clients:
            client: c_client_handle = client

            client.disconnect( True )

        self._clients.clear( )

        # Close the network connection
        self._network.end_connection( )


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

        while self._information[ "running" ]:

            if not self._command_pool.empty( ):

                # Get the command from the pool
                command: c_command = self._command_pool.get( block=False )

                # If there is no command, continue
                if command is None:
                    continue

                self.__handle_command( command )

            else:
                
                # If our command queue is empty, just sleep for 0.1 seconds.
                # Othersize this thread will run million times per second.
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
            FILES_COMMAND_APPLY_UPDATE:     self.__command_execute_accept_offset
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

            self.__broadcast_for_shareable_clients( file, client, self.__broadcast_lock_line, line_number )

            self.__event_line_lock( file.name( ), line_number )

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

        # I know it technically cause bottleneck issue, but this is the system.
        # Simple and kinda quick... ( or at least should be )

        # This has to be ordered since the line change can be delayed

        # For example
        # Change [2]
        # OTHER...
        # Change [1]
        # - HEAD OF THE QUEUE

        # CHANGE 1 has been commited and the client accepted it, but 
        # there is still Change [2]
        # in the queue waiting. Without this, it will mess everything up.

        offset: int = arguments[ 0 ]
        client.remove_offset( offset )
        
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

            if client.selected_file( ) == file.name( ):
                
                if exception is None or client != exception:
                    broadcast_function( client, file, *args )


    def __broadcast_lock_line( self, client: c_client_handle, file: c_virtual_file, line: int ):
        """
            Notify the client that a specific line is locked.

            Receive :
            - client    - Client to notify
            - file      - File that is shared
            - line      - Locked line

            Returns :   None
        """

        # TODO ! Add check if the client can edit

        message = self._files.format_message( FILES_COMMAND_PREPARE_UPDATE, [ file.name( ), str( line ) ] )
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

    # endregion

    # region : Files

    def initialize_path( self, path: str, default_access_level: str ):
        """
            Create and setup the project files path.

            Receive :
            - path - Path string for files

            Returns :   None
        """

        self._information[ "original_path" ] = path
        self._information[ "default_access" ] = default_access_level

        self.__setup_default_access_level( )

        self.__setup_path( )

        self.__setup_files( )

        self.__event_files_refresh( )


    def __setup_default_access_level( self ):
        """
            Setup default access level for new users.

            Receive :   None

            Returns :   None
        """

        level: str = self._information[ "default_access" ]

        del self._information[ "default_access" ]

        level_number = {
            "Hidden":   FILE_ACCESS_LEVEL_HIDDEN,
            "Edit":     FILE_ACCESS_LEVEL_EDIT,
            "Limit":    FILE_ACCESS_LEVEL_LIMIT
        }

        if level not in level_number:
            raise Exception( "Invalid access level type" )
        
        self._information[ "default_access" ] = level_number[ level ]


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
        original_path   = self._information[ "original_path" ]

        self.__dump_path( original_path )


    def __dump_path( self, path: str ):
        """
            Dump specific path.

            Receive : 
            - path - Full path to a folder to dump

            Returns :   None
        """
        
        original_path   = self._information[ "original_path" ]
        normal_path     = self._information[ "normal_path" ]
        access_level    = self._information[ "default_access" ]

        with os.scandir( path ) as entries:
            
            for entry in entries:
                
                if entry.is_file( ):
                    # Is File

                    # TODO ! Check if the file already copied

                    fixed_name = f"{ path.replace( original_path, '' ) }\\{ entry.name }"
                    fixed_name = fixed_name.lstrip( "\\" )
                    
                    file = self._files.create_new_file( fixed_name, access_level, True )
                    r = file.copy( original_path, normal_path )

                    if r is not None:
                        c_debug.log_error( r )

                if entry.is_dir( ) and entry.name != DEFAULT_FOLDER_NAME and not entry.name.startswith( "." ):
                    # Is Folder
                    
                    self.__dump_path( f"{ path }\\{ entry.name }" )
            
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

        self.__broadcast_for_shareable_clients( file, None, self.__broadcast_lock_line, line )

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
        new_client.set_event( "on_client_disconnected", self.__event_client_disconnected,   "Host Client Disconnect" )
        new_client.set_event( "on_client_command",      self.__event_client_command,        "Host Client Command" )

        # Load path for database.
        new_client.load_database( self._information[ "normal_path" ], self._information[ "username" ] )

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

        if event( "notify" ) == "0":
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
        self._command_pool.put( event( "command" ) )

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

    
    def __event_line_lock( self, file: str, line: int ):
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
    
    # endregion

    def clients( self ) -> list:
        return self._clients