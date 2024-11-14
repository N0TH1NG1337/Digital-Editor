# Utils. Safe .py

# Changes : 
# - file init

from functools import   wraps
import                  threading

def safe_call( call_on_fail: any = None ):
    """
        Safe call wrapper for functions
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

    @wraps( function )
    def execute( *args ):

        thread = threading.Thread( target=function, args=args )
        thread.start( )

    return execute