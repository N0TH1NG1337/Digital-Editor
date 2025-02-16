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
# Moreover, the database used for this will be simple json file with base64 encoding.

# Note ! Data fields that are with prefix __name are protected, you should not edit them at any cost.

from protocols.security import c_security
from utilities.wrappers import safe_call
from utilities.debug    import *

import datetime
import base64
import json
import os
import re

DATABASE_NAME = "users.unk"


class c_registration_protocol:

    _last_error:    str
    _project_path:  str
    
    # region : Initialization

    def __init__( self ):
        """ 
            Initialize registration protocol.

            Receive :   None

            Returns :   None
        """

        self._last_error    = ""
        self._project_path  = None

    
    def load_path_for_database( self, path: str, username: str = None ):
        """
            Load path for database.

            Receive :
            - path      - Path to database
            - username  - Username of creator

            Returns : None
        """

        self._project_path = path
        self.__create_database( username )

    # endregion

    # region : Formatting and Parsing

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
    
    # endregion

    # region : Registration

    @safe_call( c_debug.log_error )
    def register_user( self, username: str, password: str ) -> bool:
        """
            Try to register a new user.

            Receive :
            - username  - The user's nickname
            - password  - Password of the user

            Returns :   Result if success
        """

        result, error_str = self.validate_username( username )
        if not result:
            self._last_error = f"Failed to register user. reason : { error_str }"

        full_path: str = os.path.join( self._project_path, DATABASE_NAME )

        if not os.path.exists( full_path ):
            self._last_error = "Failed to register user. reason : Unknown."
            return False
        
        #with open( full_path, 'rb' ) as file:
        #    users: dict = json.loads( base64.b64decode( file.read( ) ).decode( ) )
        with open( full_path, 'r' ) as file:
            users: dict = json.loads( file.read( ) )

        if username in users:
            self._last_error = "Failed to register user. Username is in use."
            return False
        
        security: c_security    = c_security( )
        salt, hashed_password   = security.preform_hashing( password )
        
        users[ username ] = {
            "p1": salt,
            "p2": hashed_password,
            "p3": base64.b64encode( datetime.date.today( ).strftime( "%M:%H->%d/%m/%Y" ).encode( ) ).hex( ) 
        }

        #with open( full_path, 'wb' ) as file:
        #    file.write( base64.b64encode( json.dumps( users ).encode( ) ) )
        with open( full_path, 'w' ) as file:
            file.write( json.dumps( users ) )

        return True

    # endregion

    # region : Login

    @safe_call( c_debug.log_error )
    def login_user( self, username: str, password: str ) -> bool:
        """
            Try to login an user.

            Receive :
            - username  - The user nickname
            - password  - Password of the user

            Returns :   Result if success
        """

        result, error_str = self.validate_username( username )
        if not result:
            self._last_error = f"Failed to login user. Invalid username, reason : { error_str }"

        full_path: str = os.path.join( self._project_path, DATABASE_NAME )

        if not os.path.exists( full_path ):
            self._last_error = "Failed to login user. reason : Unknown."
            return False
        
        #with open( full_path, 'rb' ) as file:
        #    users: dict = json.loads( base64.b64decode( file.read( ) ).decode( ) )
        with open( full_path, "r" ) as file:
            users: dict = json.loads( file.read( ) )

        if not username in users:
            self._last_error = "Failed to login user. Username not found."
            return False
        
        current_user_data: dict = users[ username ].copy( )
        del users

        security:   c_security  = c_security( )
        result:     bool        = security.verify( password, current_user_data[ "p1" ], current_user_data[ "p2" ] )

        if not result:
            self._last_error = "Failed to login user. Invalid password."
            return False
        
        return True

    # endregion

    # region : Utilities

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


    def __create_database( self, username: str = None ):
        """
            Create database for users.

            Receive :   None

            Returns :   None
        """

        full_path: str = os.path.join( self._project_path, DATABASE_NAME )

        if os.path.exists( full_path ):
            return

        #with open( full_path, "wb" ) as file:
        with open( full_path, "w" ) as file:

            first_data = {

                "__Creation_Date": datetime.date.today( ).strftime( "%d/%m/%Y" ),
                "__Creator": username
            }

            #file.write( base64.b64encode( json.dumps( first_data ).encode( ) ) )
            file.write( json.dumps( first_data ) )


    def last_error( self ) -> str:
        """
            Get the last error that occured in this protocol.

            Receive :   None

            Returns :   String error
        """

        return self._last_error


    def header( self ) -> str:
        """
            Get the protocol header.

            Receive :   None

            Returns :   String
        """

        return REGISTRATION_HEADER