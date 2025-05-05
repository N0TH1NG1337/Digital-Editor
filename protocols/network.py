"""
    project     : Digital Editor

    type:       : Protocol
    file        : Network

    description : Network Protocol class
"""


from protocols.security import *
from utilities.wrappers import safe_call
from utilities.debug    import *
import socket
import base64

INVALID                 = None

HEADER_SIZE             = 4
CHUNK_SIZE              = 1024
DISCONNECT_MSG          = "_DISCONNECT_"
PING_MSG                = "PING"

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


    @safe_call( None )
    def start( self, type_socket: int, ip: str, port: int, timeout: int = -1 ) -> bool:
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

        if timeout > -1:
            self._socket.settimeout( timeout )

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
            return
        
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

        self._connection    = connection is None and c_connection( ) or connection


    def start_connection( self, type_connection: int, ip: str, port: int, timeout: int = -1 ) -> bool:
        """
            Start connection based on type, ip and port.

            Receive :
            - type_connection   - Connection type
            - ip                - Ip to search / attach
            - port              - Port for connection 

            Returns :   None
        """

        return self._connection.start( type_connection, ip, port, timeout )


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

    def get_raw_details( self, length: int ) -> list:
        """
            Convert raw bytes length into config for sending it by chunks.

            Receive :
            - length - Raw bytes amount

            Returns :   List
        """

        result = [ ]

        total = 0

        while total < length:
            start = total
            
            remain = length - total
            size = min( CHUNK_SIZE, remain )

            end = total + size

            current_chunk = [ start, end, total + size < length ]
            result.append( current_chunk )

            total = total + size

        return result

    @safe_call( c_debug.log_error )
    def send_bytes( self, raw_bytes: bytes ) -> bool:
        """
            Send full raw bytes.

            Receive :
            - raw_bytes - Full length bytes to send

            Returns :   None
        """

        connection_object = self._connection( )
        if not connection_object:
            return False
        
        length: int = len( raw_bytes )
        
        if length > 9999:
            return False
        
        connection_object.send( self.get_message_header( length ) )
        connection_object.send( raw_bytes )

        return True

    @safe_call( None ) 
    def receive_chunk( self, timeout: int = -1 ) -> bytes:

        if self._connection( ) is INVALID:
            return None
        
        if timeout != -1:
            self._connection( ).settimeout( timeout )
            
        length: int = int( self._connection( ).recv( HEADER_SIZE ).decode( ) )

        return self.__receive_fixed( length )


    def __receive_fixed( self, length: int ) -> bytes:
        """
            Utility to pop from buffer fixed length of data.

            Receive : 
            - length - Length of the bytes seq

            Returns :   Bytes
        """

        received_raw_data = b''     

        while len(received_raw_data) < length:
            this_size = min( length - len( received_raw_data ), CHUNK_SIZE )

            chunk_data = self._connection( ).recv( this_size )
            received_raw_data += chunk_data

        return received_raw_data
    

    def get_message_header( self, length: int ) -> bytes:

        return str( length ).zfill( HEADER_SIZE ).encode( )
    
    
    def is_valid( self, try_ping: bool = False ) -> bool:
        """
            Is connection still valid.

            Receive :   None

            Returns :   Result
        """

        if try_ping:
            try:
                self.send_bytes( PING_MSG.encode( ) )

                return True
            except Exception:
                return False

        return self._connection( ) is not INVALID
    

    def get_address( self, raw_ip: bool = False ) -> tuple:
        """
            Get address of current connection.

            Receive :   
            - raw_ip [optional] - Raw registered IP

            Returns :   Tuple ( ip, port )
        """

        # Use this method to get ip since for server we specify 0.0.0.0
        host_name = socket.gethostname( )
        ip_addr = socket.gethostbyname( host_name )
        
        if raw_ip:
            ip_addr = self._connection.address( )[ 0 ]

        return ip_addr, self._connection.address( )[ 1 ]
    