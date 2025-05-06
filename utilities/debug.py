"""
    project     : Digital Editor

    type        : Utility
    file        : Debug

    description : Provides static methods for enabling, disabling, and writing
                  log messages (errors and general information) to a specified
                  log file.
"""

import logging as log_lib

ENABLE_DEBUG_LOGGING: bool = False


class c_debug:

    @staticmethod
    def load_basic_debugging( file_name: str ):
        """
        Enables basic logging to a specified file.

        Receive :
        - file_name (str): The path to the file where log messages will be written.

        Returns : None
        """

        global ENABLE_DEBUG_LOGGING
        ENABLE_DEBUG_LOGGING = True

        log_lib.basicConfig( filename = file_name, format = "%(asctime)s - %(message)s", level = log_lib.INFO )


    @staticmethod    
    def disable_basic_debugging( ):
        """
        Disables basic logging.

        Receive : None

        Returns : None
        """

        global ENABLE_DEBUG_LOGGING
        ENABLE_DEBUG_LOGGING = False


    @staticmethod
    def log_error( error_msg: any ):
        """
        Logs a specific error message to the debugging log file.

        Receive :
        - error_msg (any): The error message to be logged.

        Returns : None
        """

        global ENABLE_DEBUG_LOGGING
        if not ENABLE_DEBUG_LOGGING:
            return

        log_lib.info( f"error - { error_msg }" )

    
    @staticmethod
    def log_information( info: any ):
        """
        Logs a specific informational message to the debugging log file.

        Receive :
        - info (any): The informational message to be logged.

        Returns : None
        """

        global ENABLE_DEBUG_LOGGING
        if not ENABLE_DEBUG_LOGGING:
            return

        log_lib.info( f"info - { info }\n" )

    