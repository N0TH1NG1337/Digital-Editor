"""
    project     : Digital Editor

    type:       : Protocol
    file        : Network

    description : Network Protocol class
"""


from utilities.wrappers import safe_call
import socket

INVALID                 = None

HEADER_SIZE             = 4
CHUNK_SIZE              = 1024
SEPERATE_RAW            = "<<"
DISCONNECT_MSG          = "_DISCONNECT_"

CONNECTION_TYPE_CLIENT  = 1
CONNECTION_TYPE_SERVER  = 2


class c_connection:

    _ip:    str
    _port:  int

    _socket: socket

    def __init__( self ):
        """
            Default constructor for connection object.

            Receive :   None

            Returns :   Connection object
        """

        self._ip        = INVALID
        self._port      = INVALID

        self._socket    = INVALID


    def start( self, type_socket: int, ip: str, port: int ) -> bool:
        """
            Start connection based on type, ip and port.

            Receive :
            - type_socket   - Connection type
            - ip            - Ip to search / attach
            - port          - Port for connection 

            Returns :   Result of connection
        """

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
        """
            Attach connection details for current object.

            Receive :
            - ip            - Ip value of details
            - port          - Port value of details
            - socket_obj    - Socket object of the connection

            Returns :   Connection object with details
        """

        self._ip = ip
        self._port = port

        self._socket = socket_obj

        return self


    def end( self ):
        """
            End connection.

            Receive :   None

            Returns :   None
        """

        if self._socket is INVALID:
            raise Exception( "Cannot end connection if not started" )
        
        self._socket.close( )
        
        # Release the object. in any way, we can create a new one
        self._socket = INVALID


    def address( self ) -> tuple:
        """
            Get address of this connection.

            Receive :   None

            Returns :   Address tuple (ip: str, port: int)
        """

        return self._ip, self._port


    def __call__( self ) -> socket:
        """
            Receive Socket object of the connection. 

            Receive :   None

            Returns :   Socket object
        """

        return self._socket


class c_network_protocol:

    _connection:        c_connection

    def __init__( self, connection: c_connection = None ):
        """
            Default constructor for Network Protocol.

            Receive : 
            - connection [optional] - Ready connection object.

            Returns : Network Protocol object
        """

        self._connection = connection is None and c_connection( ) or connection


    def start_connection( self, type_connection: int, ip: str, port: int ):
        """
            Start connection based on type, ip and port.

            Receive :
            - type_connection   - Connection type
            - ip                - Ip to search / attach
            - port              - Port for connection 

            Returns :   None
        """

        self._connection.start( type_connection, ip, port )

    def end_connection( self ):
        """
            End connection.

            Receive :   None

            Returns :   None
        """

        self._connection.end( )

    def look_for_connections( self ):
        """
            Look / Listen for connections.

            Receive :   None

            Returns :   None
        """

        self._connection( ).listen( )

    def accept_connection( self, timeout: float = -1 ) -> tuple:
        """
            Accept connection from client.

            Receive : 
            - timeout [optional] - Timeout waiting for new client

            Returns :   Client details (socket, (ip, port) )
        """
        
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
        """

        """

        if self._connection( ) is INVALID:
            raise Exception( "Invalid connection. make sure you have established connection" )
        
        result: str     = self.value_format( value, False )
        result: bytes   = result.encode( )

        self._connection( ).send( result )

    def send_raw( self, raw: bytes ):

        if self._connection( ) is INVALID:
            raise Exception( "Invalid connection. make sure you have established connection" )
        
        raw_size: int = len( raw )

        total_sent = 0

        while total_sent < raw_size:
            remaining = raw[ total_sent: ]
            size = min( CHUNK_SIZE, len( remaining ) )
            chunk = remaining[ :size ]

            format_value = self.value_format( chunk, total_sent + size < raw_size )

            self._connection( ).send( format_value.encode( ) )
            total_sent = total_sent + size

    @safe_call( None )
    def receive( self, timeout: int = -1 ) -> bytes:

        if self._connection( ) is INVALID:
            raise Exception( "Invalid connection. make sure you have established connection" )

        if timeout != -1:
            self._connection( ).settimeout( timeout )

        data = b''
        has_next: bool = True

        while has_next:
            has_next:   bool    = self._connection( ).recv( 1 ).decode( ) == "1"
            length:     int     = int( self._connection( ).recv( HEADER_SIZE ).decode( ) )

            data += self.__receive_fixed( length )

        return data
        
    def __receive_fixed( self, length: int ) -> bytes:

        received_raw_data = b''

        while len(received_raw_data) < length:
            this_size = min( length - len( received_raw_data ), CHUNK_SIZE )

            chunk_data = self._connection( ).recv( this_size )
            received_raw_data += chunk_data

        return received_raw_data

    def value_format( self, value: str | bytes, has_next: bool = False ):

        length = str( len( value ) ).zfill( HEADER_SIZE )

        return f"{ has_next and 1 or 0 }{ length }{ value }"
    
    def is_valid( self ) -> bool:

        return self._connection( ) is not INVALID

    def get_address( self ) -> tuple:

        host_name = socket.gethostname( )
        ip_addr = socket.gethostbyname( host_name )

        return ip_addr, self._connection.address( )[1]