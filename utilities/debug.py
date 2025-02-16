"""
    project     : Digital Editor

    type:       : Utility
    file        : Debug

    description : Debug handler
"""

import logging as log_lib

ENABLE_DEBUG_LOGGING: bool = False


class c_debug:

    @staticmethod
    def load_basic_debugging( file_name: str ):
        """
            Enable basic logging.

            Receive :
            - file_name - Output log file path.

            Returns :   None
        """
        global ENABLE_DEBUG_LOGGING
        ENABLE_DEBUG_LOGGING = True

        log_lib.basicConfig( filename = file_name, format = "%(asctime)s - %(message)s", level = log_lib.INFO )


    @staticmethod    
    def disable_basic_debugging( ):
        """
            Disable basic logging.

            Receive :   None

            Returns :   None
        """
        global ENABLE_DEBUG_LOGGING
        ENABLE_DEBUG_LOGGING = False


    @staticmethod
    def log_error( error_msg: any ):
        """
            Log into file specific error messsage.

            Receive :
            - error_msg - Error message to log

            Returns :   None
        """
        global ENABLE_DEBUG_LOGGING
        if not ENABLE_DEBUG_LOGGING:
            return

        log_lib.info( f"error - { error_msg }" )

    
    @staticmethod
    def log_information( info: any ):
        """
            Log into file specific information messsage.

            Receive :
            - info - information message to log

            Returns :   None
        """
        global ENABLE_DEBUG_LOGGING
        if not ENABLE_DEBUG_LOGGING:
            return

        log_lib.info( f"info - { info }\n" )

    