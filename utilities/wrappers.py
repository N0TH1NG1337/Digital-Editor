"""
    project     : Digital Editor

    type:       : Utility
    file        : Wrappers

    description : Wrappers for functions
"""

from functools import   wraps
import                  threading

def safe_call( call_on_fail: any = None ):
    """
        Protected call wrap function

        Receives:   

        - call_on_fail [optional]   - execute function on fail
        - function                  - function to protect

        Returns:    Wrap function
    """

    def decorator( function ):

        @wraps( function )
        def safe_fn( *args, **kwargs ):

            try:
                return function( *args, **kwargs )

            except Exception as e:

                error_msg = f"Found error in function { function.__name__ }:\n{ e }"

                if call_on_fail is not None:
                    call_on_fail( error_msg )

                return None

        return safe_fn

    return decorator


def standalone_execute( function ):
    """
        Standalone call wrap function.
        Can execute functions without messing up the program flow.

        Receives:   

        - function                  - function to protect

        Returns:    Wrap function
    """

    @wraps( function )
    def execute( *args ):

        thread = threading.Thread( target=function, args=args )
        thread.start( )

        return thread

    return execute