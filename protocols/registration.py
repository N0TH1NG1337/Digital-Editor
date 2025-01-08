"""
    project     : Digital Editor

    type:       : Protocol
    file        : Registration

    description : Registration Protocol class
"""

REGISTRATION_HEADER         = "RP_UNK"

REGISTRATION_COMMAND_REG    = "RegCMDUser"
REGISTRATION_COMMAND_LOG    = "LogCMDUser"

class c_registration_protocol:
    
    def __init__( self ):
        """ 
            Initialize registration protocol.

            Receive :   None

            Returns :   None
        """

        pass


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
    

    def get_header( self ) -> str:
        return REGISTRATION_HEADER