"""
    project     : Digital Editor

    type:       : Protocol
    file        : Registration

    description : Registration Protocol class
"""

REGISTRATION_HEADER         = "RP_UNK"

REGISTRATION_COMMAND_REG    = "RegCMDUser"
REGISTRATION_COMMAND_LOG    = "LogCMDUser"
REGISTRATION_RESPONSE       = "RegRes"

# The registration protocol will be used to register and login users.
# However, it will be created for each user seperatly on the host side.

# In order to make sure everything works together, the host must provide fixed and static path for database
# Which will be create if not exists.

# Otherwise, the protocol will load and connect to that database.
# Now lets change a little bit the protocol.

# First, instead of a single file, there will be a folder as database.
# The folder will contain a file that called .index
# This file will be a json file that will have a specification, for each user its id.
# The id will be the user file name that will be encrypted with AES and host connected username ?

from protocols.security import c_security
from utilities.wrappers import safe_call
from utilities.debug    import *

import datetime
import base64
import json
import os
import re
import uuid

DATABASE_NAME = ".database"

class c_database:
    # Class for database operations
    
    _last_error:        str
    _database_path:     str

    _host_index:        str
    _host_password:     str

    _ids:               dict

    # region : Initialization

    def __init__( self ):
        """
            Initialize database.

            Receive :   None
            
            Returns :   None
        """

        self._last_error    = ""
        self._database_path = None


    def load_path( self, path: str ):
        """
            Load path for database.

            Receive :
            - path      - Path to database

            Returns :   None
        """

        self._database_path = path
        self.__init_database( )


    def connect( self, username: str, password: str ):
        """
            Connect to database.

            Receive :
            - username  - Username of creator
            - password  - Password of creator

            Returns :   None
        """

        self._host_index    = username
        self._host_password = password

        # Now we need to check if the host exists in the index file.
        index_path: str = os.path.join( self._database_path, DATABASE_NAME, "index.unk" )

        if not os.path.exists( index_path ):
            self._last_error = "Failed to connect to database. reason : Unknown."
            return False
        
        with open( index_path, "r" ) as file:
            index_data: dict = json.loads( file.read( ) )

        if self._host_index not in index_data:
            # Create a new host id in the index file

            self._ids = { }

            index_data[ self._host_index ] = { }
            # Each field in this will be a username of a client that registered to this host.
            # And the value will be the unique id of the client for user file indexing.

            with open( index_path, "w" ) as file:
                file.write( json.dumps( index_data ) )

        else:
            self._ids = index_data[ self._host_index ]
        
        return True


    def disconnect( self ):
        """
            Disconnect from database.

            Receive :   None
            
            Returns :   None
        """

        # Open the index file and save the ids to the host index
        index_path: str = os.path.join( self._database_path, DATABASE_NAME, "index.unk" )

        with open( index_path, "r" ) as file:
            index_data: dict = json.loads( file.read( ) )

        index_data[ self._host_index ] = self._ids

        with open( index_path, "w" ) as file:
            file.write( json.dumps( index_data ) )

    # endregion

    # region : Utilities

    def __init_database( self ):
        """
            Initialize database.

            Receive :   None
            
            Returns :   None
        """

        database_dir: str = os.path.join( self._database_path, DATABASE_NAME )

        if os.path.exists( database_dir ):
            return

        # Create the database directory
        os.makedirs( database_dir, exist_ok=True )

        # Create the index file inside the database directory
        index_path = os.path.join( database_dir, "index.unk" )
        
        with open( index_path, "w" ) as file:
            first_data = {
                "__Creation_Date": datetime.date.today( ).strftime( "%d/%m/%Y" ),
                "__Creator": "system"
            }
            file.write( json.dumps( first_data ) )


    def __create_user_file( self, username: str ):
        """
            Create a user file.

            Receive :
            - username  - Username of the user

            Returns :   None
        """

        user_id: str = f"{ self._ids[ username ] }.unk"

        user_path: str = os.path.join( self._database_path, DATABASE_NAME, user_id )

        if os.path.isfile( user_path ):
            return

        with open( user_path, "wb" ) as file:

            information: dict = {
                "__Creation_Date": datetime.date.today( ).strftime( "%d/%m/%Y" ),
                "__Creator": self._host_index
            }

            string_data: str = json.dumps( information )
            encrypted_data: bytes = c_security( ).fast_encrypt( string_data.encode( ), self._host_password.encode( ) )

            file.write( encrypted_data )


    def __get_user_index( self, username: str ) -> str:
        """
            Get the user index.

            Receive :
            - username  - Username of the user

            Returns :   String id
        """

        # Now lets check if there is any user in the host index
        if username in self._ids:
            return self._ids[ username ]

        # If not, we need to create a new user index
        self._ids[ username ] = str( uuid.uuid4( ) )

        self.__create_user_file( username )

        return self._ids[ username ]
    

    def get_id( self, username: str ) -> str:
        """
            Get the id of the user.

            Receive :
            - username  - Username of the user

            Returns :   String id
        """

        return self.__get_user_index( username )
    

    def check_id( self, username: str ) -> bool:
        """
            Check if the user id exists.

            Receive :
            - username  - Username of the user

            Returns :   Result if success
        """

        return username in self._ids
    

    def get_password( self ) -> str:
        """
            Get the password of the host.

            Receive :   None
            
            Returns :   Password of the host
        """

        return self._host_password

    
    def get_database_path( self ) -> str:
        """
            Get the database path.

            Receive :   None
            
            Returns :   Database path
        """

        return self._database_path
    

    def last_error( self ) -> str:
        """
            Get the last error that occured in this protocol.

            Receive :   None
            
            Returns :   String error
        """

        return self._last_error
    
    # endregion



class c_registration:
    # Class for registration operations
    
    _database:      c_database
    _last_error:    str

    _username:      str
    _password:      str # This isnt the password of the user, but the password of the host
    _index:         str

    _fields:        dict

    # region : Initialization

    def __init__( self ):
        """
            Initialize registration protocol.

            Receive :   None
            
            Returns :   None
        """

        self._database = None
        self._last_error = ""
        self._fields = None

    def load_database( self, database: c_database ):
        """
            Load database.

            Receive :
            - database  - Database to load
            
            Returns :   None
        """

        self._database = database

        self._password = self._database.get_password( )

    # endregion

    # region : Registration

    def register_user( self, username: str, password: str, addition_fields: dict = { } ) -> bool:
        """
            Register a new user.

            Receive :
            - username          - Username of the user
            - password          - Password of the user
            - addition_fields   - Additional fields to add to the user

            Returns :   Result if success
        """

        if not self._database:
            self._last_error = "Failed to register user. reason : Database not loaded."
            return False
        
        self._username = username

        result, error_str = self.validate_username( username )
        if not result:
            self._last_error = f"Failed to register user. reason : { error_str }"
            return False

        if self._database.check_id( username ):
            self._last_error = "Failed to register user. reason : Username already in use."
            return False
        
        self._index    = self._database.get_id( username )

        file_index: str = f"{ self._index }.unk"
        user_path: str = os.path.join( self._database.get_database_path( ), DATABASE_NAME, file_index )

        # Open file and write the information
        user_information: dict = { }

        security: c_security = c_security( )

        with open( user_path, "rb" ) as file:
            data: bytes = security.fast_decrypt( file.read( ), self._password.encode( ) )
        
        user_information = json.loads( data.decode( ) )
        del data

        # No need to check for the host, since the host is the one that creates the user file.
        salt, hashed_password = security.preform_hashing( password )

        user_information[ "p1" ] = salt
        user_information[ "p2" ] = hashed_password
        user_information[ "p3" ] = base64.b64encode( datetime.date.today( ).strftime( "%M:%H->%d/%m/%Y" ).encode( ) ).hex( )

        for field_name, field_value in addition_fields.items( ):
            user_information[ field_name ] = field_value

        self._fields = addition_fields

        with open( user_path, "wb" ) as file:
            file.write( security.fast_encrypt( json.dumps( user_information ).encode( ), self._password.encode( ) ) )

        return True
    

    def login_user( self, username: str, password: str ) -> bool:
        """
            Login a user.

            Receive :
            - username  - Username of the user
            - password  - Password of the user
        """

        if not self._database:
            self._last_error = "Failed to login user. reason : Database not loaded."
            return False
        
        self._username = username

        result, error_str = self.validate_username( username )
        if not result:
            self._last_error = f"Failed to login user. reason : { error_str }"
            return False
        
        if not self._database.check_id( username ):
            self._last_error = "Failed to login user. reason : Username not found."
            return False
        
        self._index = self._database.get_id( username )

        file_index: str = f"{ self._index }.unk"
        user_path: str = os.path.join( self._database.get_database_path( ), DATABASE_NAME, file_index )

        security: c_security = c_security( )

        with open( user_path, "rb" ) as file:
            data: bytes = security.fast_decrypt( file.read( ), self._password.encode( ) )
            
        user_information = json.loads( data.decode( ) )
        del data

        # Check if the password is correct
        salt, hashed_password = user_information[ "p1" ], user_information[ "p2" ]

        if not security.verify( password, salt, hashed_password ):
            self._last_error = "Failed to login user. reason : Invalid password."
            return False
        
        self._fields = user_information
        del self._fields[ "__Creation_Date" ]
        del self._fields[ "__Creator" ]
        del self._fields[ "p1" ]
        del self._fields[ "p2" ]
        del self._fields[ "p3" ]

        return True

    # endregion

    # region : Files

    def update_fields( self ):
        """
            Update all the fields of the user.

            Receive :   None
            
            Returns :   None
        """

        self._index = self._database.get_id( self._username )

        file_index: str = f"{ self._index }.unk"
        user_path: str = os.path.join( self._database.get_database_path( ), DATABASE_NAME, file_index )

        security: c_security = c_security( )

        with open( user_path, "rb" ) as file:
            data: bytes = security.fast_decrypt( file.read( ), self._password.encode( ) )
            
        user_information = json.loads( data.decode( ) )
        del data

        for field_name, field_value in self._fields.items( ):
            user_information[ field_name ] = field_value

        with open( user_path, "wb" ) as file:
            file.write( security.fast_encrypt( json.dumps( user_information ).encode( ), self._password.encode( ) ) )
 
    # endregion
        
    # region : Utilities

    def get_field( self, field_name: str ) -> any:
        """
            Get a field of the user.
        """

        return self._fields[ field_name ]
    

    def set_field( self, field_name: str, field_value: any ):
        """
            Set a field of the user.
        """

        self._fields[ field_name ] = field_value
        

    def validate_username( self, username: str ) -> tuple:
        """
            Checks if the username is valid.

            Receive :
            - username - User nickname to validate

            Returns :   Tuple ( Bool, String )
        """

        if not username or username == "":
            return False, "Username cannot be empty."

        if len( username ) < 3:
            return False, "Username must be at least 3 characters long."

        if len( username ) > 20:
            return False, "Username cannot exceed 20 characters."

        if not re.match( "^[a-zA-Z0-9_]*$", username ):
            return False, "Username can only contain english letters, numbers and underscores"

        if username.startswith( "_" ) or username.startswith( "." ):
            return False, "Username cannot start with an underscore or a period."

        if username.endswith( "." ):
            return False, "Username cannot end with a period."

        return True, ""
        

    def last_error( self ) -> str:
        """
            Get the last error that occured in this protocol.

            Receive :   None

            Returns :   String error
        """

        return self._last_error

    # endregion

    # region : Messages

    def format_message( self, message: str, arguments: list ):
        """
            Format message for Registration Protocol.

            Receive :
            - message   - Command to send
            - arguments - Arguments to follow it

            Returns :   String value
        """

        return f"{ REGISTRATION_HEADER }::{ message }->{ '->'.join( arguments ) }"


    def parse_message( self, message: str ):
        """
            Parse information from Registration Protocol message.

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
    

    def header( self ) -> str:
        """
            Get the protocol header.

            Receive :   None

            Returns :   String
        """

        return REGISTRATION_HEADER
    
    # endregion



#class c_registration_protocol:
#
#    _last_error:    str
#    _project_path:  str
#
#    _username:      str
#    _password:      str
#    _ids:           dict
#    
#    # region : Initialization
#
#    def __init__( self ):
#        """ 
#            Initialize registration protocol.
#
#            Receive :   None
#
#            Returns :   None
#        """
#
#        self._last_error    = ""
#        self._project_path  = None
#
#        self._username      = None
#        self._password      = None
#        self._ids           = {}
#
#    
#    def load_path_for_database( self, path: str ):
#        """
#            Load path for database.
#
#            Receive :
#            - path      - Path to database
#
#            Returns : None
#        """
#
#        self._project_path = path
#        self.__create_database( )
#
#    
#    def connect_to_database( self, username: str, password: str ):
#        """
#            Connect to database.
#
#            Receive :
#            - username  - Username of creator
#            - password  - Password of creator
#
#            Returns :   None
#        """
#
#        self._username      = username
#        self._password      = password
#
#        # Now we need to check if the host exists in the index file.
#        index_path: str = os.path.join( self._project_path, DATABASE_NAME, "index.unk" )
#
#        if not os.path.exists( index_path ):
#            self._last_error = "Failed to connect to database. reason : Unknown."
#            return False
#        
#        with open( index_path, "r" ) as file:
#            index_data: dict = json.loads( file.read( ) )
#
#        if self._username not in index_data:
#            # Create a new host id in the index file
#
#            self._ids = { }
#
#            index_data[ self._username ] = { }
#            # Each field in this will be a username of a client that registered to this host.
#            # And the value will be the unique id of the client for user file indexing.
#
#            with open( index_path, "w" ) as file:
#                file.write( json.dumps( index_data ) )
#
#        else:
#            self._ids = index_data[ self._username ]
#        
#        return True
#
#    # endregion
#
#    # region : Formatting and Parsing
#
#    def format_message( self, message: str, arguments: list ):
#        """
#            Format message for Registration Protocol.
#
#            Receive :
#            - message   - Command to send
#            - arguments - Arguments to follow it
#
#            Returns :   String value
#        """
#
#        return f"{ REGISTRATION_HEADER }::{ message }->{ '->'.join( arguments ) }"
#
#
#    def parse_message( self, message: str ):
#        """
#            Parse information from Registration Protocol message.
#
#            Receive :
#            - message - String value to parse
#
#            Returns : Tuple ( cmd, list[arguments] )
#        """
#
#        first_parse = message.split( "::" )
#        
#        information = first_parse[ 1 ].split( "->" )
#        command     = information[ 0 ]
#
#        # Remove command from arguments
#        information.pop( 0 )
#
#        return command, information
#    
#    # endregion
#
#    # region : Registration
#
#    @safe_call( c_debug.log_error )
#    def register_user( self, username: str, password: str ) -> bool:
#        """
#            Try to register a new user.
#
#            Receive :
#            - username  - The user's nickname
#            - password  - Password of the user
#
#            Returns :   Result if success
#        """
#
#        result, error_str = self.validate_username( username )
#        if not result:
#            self._last_error = f"Failed to register user. reason : { error_str }"
#            return False
#
#        full_path: str = os.path.join( self._project_path, DATABASE_NAME )
#
#        if not os.path.exists( full_path ):
#            self._last_error = "Failed to register user. reason : Unknown."
#            return False
#        
#        #with open( full_path, 'rb' ) as file:
#        #    users: dict = json.loads( base64.b64decode( file.read( ) ).decode( ) )
#        with open( full_path, 'r' ) as file:
#            users: dict = json.loads( file.read( ) )
#
#        if username in users:
#            self._last_error = "Failed to register user. Username is in use."
#            return False
#        
#        security: c_security    = c_security( )
#        salt, hashed_password   = security.preform_hashing( password )
#        
#        users[ username ] = {
#            "p1": salt,
#            "p2": hashed_password,
#            "p3": base64.b64encode( datetime.date.today( ).strftime( "%M:%H->%d/%m/%Y" ).encode( ) ).hex( ) 
#        }
#
#        #with open( full_path, 'wb' ) as file:
#        #    file.write( base64.b64encode( json.dumps( users ).encode( ) ) )
#        with open( full_path, 'w' ) as file:
#            file.write( json.dumps( users ) )
#
#        return True
#
#    # endregion
#
#    # region : Login
#
#    @safe_call( c_debug.log_error )
#    def login_user( self, username: str, password: str ) -> bool:
#        """
#            Try to login an user.
#
#            Receive :
#            - username  - The user nickname
#            - password  - Password of the user
#
#            Returns :   Result if success
#        """
#
#        result, error_str = self.validate_username( username )
#        if not result:
#            self._last_error = f"Failed to login user. Invalid username, reason : { error_str }"
#            return False
#
#        full_path: str = os.path.join( self._project_path, DATABASE_NAME )
#
#        if not os.path.exists( full_path ):
#            self._last_error = "Failed to login user. reason : Unknown."
#            return False
#        
#        #with open( full_path, 'rb' ) as file:
#        #    users: dict = json.loads( base64.b64decode( file.read( ) ).decode( ) )
#        with open( full_path, "r" ) as file:
#            users: dict = json.loads( file.read( ) )
#
#        if not username in users:
#            self._last_error = "Failed to login user. Username not found."
#            return False
#        
#        current_user_data: dict = users[ username ].copy( )
#        del users
#
#        security:   c_security  = c_security( )
#        result:     bool        = security.verify( password, current_user_data[ "p1" ], current_user_data[ "p2" ] )
#
#        if not result:
#            self._last_error = "Failed to login user. Invalid password."
#            return False
#        
#        return True
#
#    # endregion
#
#    # region : Utilities
#
#    def validate_username( self, username: str ) -> tuple:
#        """
#            Checks if the username is valid.
#
#            Receive :
#            - username - User nickname to validate
#
#            Returns :   Tuple ( Bool, String )
#        """
#
#        if not username or username == "":
#            return False, "Username cannot be empty."
#
#        if len( username ) < 3:
#            return False, "Username must be at least 3 characters long."
#
#        if len( username ) > 20:
#            return False, "Username cannot exceed 20 characters."
#
#        if not re.match( "^[a-zA-Z0-9_]*$", username ):
#            return False, "Username can only contain english letters, numbers and underscores"
#
#        if username.startswith( "_" ) or username.startswith( "." ):
#            return False, "Username cannot start with an underscore or a period."
#
#        if username.endswith( "." ):
#            return False, "Username cannot end with a period."
#
#        return True, ""
#
#
#    def __create_database( self ):
#        """
#            Create database directory and index file for users.
#
#            Receive :   None
#
#            Returns :   None
#        """
#
#        database_dir: str = os.path.join( self._project_path, DATABASE_NAME )
#
#        if os.path.exists( database_dir ):
#            return
#
#        # Create the database directory
#        os.makedirs( database_dir, exist_ok=True )
#
#        # Create the index file inside the database directory
#        index_path = os.path.join( database_dir, "index.unk" )
#        
#        with open( index_path, "w" ) as file:
#            first_data = {
#                "__Creation_Date": datetime.date.today( ).strftime( "%d/%m/%Y" ),
#                "__Creator": "system"
#            }
#            file.write( json.dumps( first_data ) )
#
#
#    def last_error( self ) -> str:
#        """
#            Get the last error that occured in this protocol.
#
#            Receive :   None
#
#            Returns :   String error
#        """
#
#        return self._last_error
#
#
#    def header( self ) -> str:
#        """
#            Get the protocol header.
#
#            Receive :   None
#
#            Returns :   String
#        """
#
#        return REGISTRATION_HEADER