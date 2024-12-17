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
            Send string value.

            Receive : 
            - value - Text willing to send

            Returns :   None
        """

        if self._connection( ) is INVALID:
            raise Exception( "Invalid connection. make sure you have established connection" )

        encoded_value = value.encode( )
        del value   # Delete useless copy of string

        details: list = self.get_raw_details( len( encoded_value ) )
        
        for chunk in details:
            start       = chunk[ 0 ]
            end         = chunk[ 1 ]
            has_next    = chunk[ 2 ]

            self.send_raw( encoded_value[ start:end ], has_next )

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
    
    def send_raw( self, raw_chunk: bytes, has_next: bool ):
        """
            Send raw bytes chunk.

            Receive :
            - raw_chunk - Just chunk of bytes selected after .get_raw_details( ) was called.
            - has_next  - Has more chunks go send after this one.

            Returns :   None
        """

        correct_value = self.value_format( raw_chunk, has_next )

        for i in correct_value:
            self._connection( ).send( i )


    @safe_call( None )
    def receive( self, timeout: int = -1 ) -> bytes:
        """
            Pop bytes from buffer. 

            Receive : 
            - timeout [optional] - Timeout for receiving something.

            Returns :   Bytes
        """

        # TODO ! Although this works, for large amount of bytes files it can be a problem.
        # Bytes are premetive type and therefore they are copying and not just passing as refrence.

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

    def value_format( self, value: any, has_next: bool = False ) -> list:
        """
            Format the value for a config to send.

            Reecive : 
            - value                 - Value willing to send [ str | bytes ]
            - has_next [optional]   - If there is something else afterwards to receive

            Returns :   List 
        """

        length = str( len( value ) ).zfill( HEADER_SIZE )
        
        result = [ ]

        result.append( ( has_next and "1" or "0" ).encode( ) )
        result.append( length.encode( ) )

        if type( value ) == bytes:
            result.append( value )

        else:
            result.append( value.encode( ) ) 
           
        return result
    
    def is_valid( self ) -> bool:
        """
            Is connection still valid.

            Receive :   None

            Returns :   Result
        """

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