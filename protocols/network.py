# Protocols. Network .py

from utilities.safe import safe_call
import socket
import select

INVALID             = None

HEADER_SIZE         = 4
CHUNK_SIZE          = 1024
SEPERATE_RAW        = "<<"
DISCONNECT_MSG      = "_DISCONNECT_"

CONNECTION_TYPE_CLIENT  = 1
CONNECTION_TYPE_SERVER  = 2

class c_connection:

    _ip:    str
    _port:  int

    _socket: socket

    def __init__( self ):
        self._ip        = INVALID
        self._port      = INVALID

        self._socket    = INVALID

    def start( self, type_socket: int, ip: str, port: int ) -> bool:
        self._ip    = ip
        self._port  = port

        self._socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )

        if type_socket == CONNECTION_TYPE_CLIENT:
            self._socket.connect( ( self._ip, self._port ) )

            return True
        
        if type_socket == CONNECTION_TYPE_SERVER:
            self._socket.bind( ( self._ip, self._port ) )

            return True
        
        raise Exception( "Invalid socket type entered" )
    
    def attach( self, ip: str, port: int, socket_obj: socket ):

        self._ip = ip
        self._port = port

        self._socket = socket_obj

        return self
    
    def end( self ):

        if self._socket is INVALID:
            raise Exception( "Cannot end connection if not started" )
        
        self._socket.close( )
        
        # Release the object. in any way, we can create a new one
        self._socket = INVALID
    
    def address( self ) -> tuple:
        
        return self._ip, self._port

    def __call__( self ) -> socket:
        return self._socket


class c_network_protocol:

    _connection:        c_connection

    def __init__( self, connection: c_connection = None ):
        
        self._connection = connection is None and c_connection( ) or connection

    def start_connection( self, type_connection: int, ip: str, port: int ):

        self._connection.start( type_connection, ip, port )

    def end_connection( self ):

        self._connection.end( )

    def look_for_connections( self ):

        self._connection( ).listen( )

    def accept_connection( self, timeout: float = -1 ) -> tuple:
        
        if timeout == -1:
            # Right away accept
            return self._connection( ).accept( )
        
        try:
                 
            self._connection( ).settimeout( timeout )

            return self._connection( ).accept( )
        
        except Exception as e:

            # If timed out
            return None, None
        

    def send( self, value: str ):
        
        if self._connection( ) is INVALID:
            raise Exception( "Invalid connection. make sure you have established connection" )
        
        result: str     = self.value_format( value, False )
        result: bytes   = result.encode( )

        self._connection( ).send( result )

    def send_raw( self, raw: bytes ):

        if self._connection( ) is INVALID:
            raise Exception( "Invalid connection. make sure you have established connection" )
        
        raw_size: int = len( raw )

        result: str     = self.value_format( raw_size, True )
        result: bytes   = result.encode( )

        self._connection( ).send( result )

        total_sent = 0

        while total_sent < raw_size:
            remaining = raw[ total_sent: ]
            size = min( CHUNK_SIZE, len( remaining ) )
            chunk = remaining[ :size ]

            self._connection( ).send( chunk )
            total_sent = total_sent + size

    @safe_call( None )
    def receive( self, timeout: int = -1 ):

        if self._connection( ) is INVALID:
            raise Exception( "Invalid connection. make sure you have established connection" )

        if timeout != -1:
            self._connection( ).settimeout( timeout )

        length:     int     = int( self._connection( ).recv( HEADER_SIZE ).decode( ) )
        is_raw:     bool    = self._connection( ).recv( 1 ).decode( ) == "1"

        data = self.__receive_fixed( length ).decode( )

        if not is_raw:
            return data
            
        # If Raw
        # Since this is protected call, if we somehow messed this up, will receive None
        return self.__receive_fixed( int( data ) )
        
    def __receive_fixed( self, length: int ) -> bytes:

        received_raw_data = b''

        while len(received_raw_data) < length:
            this_size = min( length - len( received_raw_data ), CHUNK_SIZE )

            chunk_data = self._connection( ).recv( this_size )
            received_raw_data += chunk_data

        return received_raw_data

    def value_format( self, value: str | bytes, is_raw: bool ):

        length = str( len( str( value ) ) ).zfill( HEADER_SIZE )
        return f"{ length }{ is_raw and 1 or 0 }{ value }"
    
    def is_valid( self ) -> bool:

        return self._connection( ) is not INVALID

    def get_address( self ) -> tuple:

        host_name = socket.gethostname( )
        ip_addr = socket.gethostbyname( host_name )

        return ip_addr, self._connection.address( )[1]