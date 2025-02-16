"""
    project     : Digital Editor

    type:       : Utility
    file        : Wrappers

    description : Wrappers for functions
"""

from functools import   wraps
import                  threading

def safe_call( call_on_fail: any = None, ignore_errors: list = [ ] ):
    """
        Protected call wrap function

        Receive :   
        - call_on_fail [optional]   - execute function on fail
        - ignore_errors [optional]  - ignore specific errors
        - function                  - function to protect

        Returns :   Wrap function
    """

    def decorator( function ):

        @wraps( function )
        def safe_fn( *args, **kwargs ):

            try:
                return function( *args, **kwargs )

            except Exception as e:
                
                e_str: str = str( e )

                for error in ignore_errors:
                    error: str = error

                    if error == e_str or e_str.startswith( error ):
                        return

                if hasattr( function, "__qualname__" ):
                    class_name = function.__qualname__.split( '.' )[ 0 ]
                    error_msg = f"Found error in function { function.__name__ }(...) from class { class_name }:\n{ e }\n"

                else:
                    error_msg = f"Found error in function { function.__name__ }:\n{ e }\n"

                if call_on_fail is not None:
                    call_on_fail( error_msg )

                return None

        return safe_fn

    return decorator


def standalone_execute( function ):
    """
        Standalone call wrap function.
        Can execute functions without messing up the program flow.

        Receive :   
        - function - function to protect

        Returns :   Wrap function
    """

    @wraps( function )
    def execute( *args ):

        thread = threading.Thread( target=function, args=args )
        thread.start( )

        return thread

    return execute


def static_arguments( function ):
    """
        A function wrapper that receives static arguments.
        This allows to set once the arguments, and call the function with same
        arguments.

        Receive :
        - function - Function to wrap

        Returns :   Wrap function
    """

    @wraps( function )
    def execute( *args ):

        def static( ):
            return function( *args )
        
        return static

    return execute