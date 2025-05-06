"""
    project     : Digital Editor

    type        : Utility
    file        : Wrappers

    description : Provides decorator functions to modify or enhance the behavior
                  of other functions, such as adding error handling, background
                  execution, or static arguments.
"""

from functools import   wraps
import                  threading

def safe_call( call_on_fail: any = None, ignore_errors: list = [ ] ):
    """
    A decorator for wrapping function calls in a try-except block for safety.

    This decorator allows you to execute a specified function and gracefully
    handle any exceptions that might occur during its execution. You can
    optionally provide a function to be called when an error occurs and a list
    of specific error messages to ignore.

    Receive:
    - call_on_fail (any, optional): A callable (function or method) to be
                                     executed if an exception occurs within the
                                     decorated function. (no function called on failure).
    - ignore_errors (list, optional): A list of strings. If the string
                                       representation of an exception contains
                                       any of these strings, the exception will
                                       be silently ignored. Defaults to
                                       an empty list (no errors ignored).

    Returns:
    - Wrap function: A decorator that can be applied to other functions.
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

                    try:
                        if e_str.index( error ):
                            return
                    except:
                        pass

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
    A decorator to execute a function in a separate thread.

    This decorator allows you to run a given function in a background thread,
    preventing it from blocking the main program flow. Any exceptions raised
    within the threaded function will not directly interrupt the main program.

    Receive:
    - function (callable): The function to be executed in a separate thread.

    Returns:
    - Wrap function: A decorator that, when applied to a function, will cause
                     invocations of that function to run in a new thread. The
                     decorator returns the Thread object created.
    """

    @wraps( function )
    def execute( *args ):

        thread = threading.Thread( target=function, args=args )
        thread.start( )

        return thread

    return execute


def static_arguments( function ):
    """
    A decorator that allows a function to be called repeatedly with the same initial arguments.

    This decorator captures the arguments provided during the first call and
    returns a new function that, when called subsequently,
    will execute the original function using these captured arguments. This is
    useful for creating callable objects with pre-set parameters.

    Receive:
    - function (callable): The function to be wrapped.

    Returns:
    - Wrap function: A decorator that, when applied to a function, returns a
                     new function that always calls the original
                     function with the arguments provided during the initial
                     call to the decorated function.
    """

    @wraps( function )
    def execute( *args ):

        def static( ):
            return function( *args )
        
        return static

    return execute