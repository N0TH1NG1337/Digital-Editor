"""
    project     : Digital Editor

    type        : Protocol
    file        : Security

    description : Security Protocol class for the Digital Editor
"""

import os

from cryptography.hazmat.primitives.asymmetric      import ec
from cryptography.hazmat.primitives.asymmetric      import padding

from cryptography.hazmat.primitives                 import hashes, serialization, hmac
from cryptography.hazmat.primitives.ciphers         import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead    import ChaCha20Poly1305 as chacha20_poly1305

from cryptography.hazmat.backends                   import default_backend

from cryptography.hazmat.primitives.kdf.hkdf        import HKDF

from argon2                                         import PasswordHasher   as argon2_password_hasher
from argon2                                         import Type             as argon2_type
from argon2                                         import low_level        as argon2_low_level

from utilities.wrappers                             import safe_call
from utilities.debug                                import *

SIZE_INNER_LAYER_KEY:   int = 32
SIZE_OUTER_LAYER_KEY:   int = 32

SIZE_SALT:              int = 16
SIZE_IV:                int = 16

SIZE_NONCE:             int = 12
SIZE_AES_KEY:           int = 32

ENUM_COMPLEX_KEY:       int = 1
ENUM_INNER_LAYER_KEY:   int = 2
ENUM_OUTER_LAYER_KEY:   int = 3

COMMAND_ROTATE_KEY:     str = "RotateKey"
COMMAND_OUTOF_SYNC:     str = "OutOfSync"

ROTATION_MAX:           int = 100


class c_digital_key:

    # This is the assymetric keys
    private_key:            ec.EllipticCurvePrivateKey
    public_key:             ec.EllipticCurvePublicKey
    shared_public_key:      ec.EllipticCurvePublicKey

    # This is for the dual layers
    inner_layer_key:        bytes   # First layer

    outer_layer_input_key:  bytes
    outer_layer_output_key: bytes

    input_sequence_number:  int
    output_sequence_number: int
    
    def __init__( self ):
        """
        Default constructor for Digital Key object.

        Receive: None

        Returns:
        - c_digital_key: Handle for keys
        """

        # Create the ECC pair keys
        self.private_key:   ec.EllipticCurvePrivateKey  = ec.generate_private_key( curve=ec.SECP256R1( ), backend=default_backend( ) )
        self.public_key:    ec.EllipticCurvePublicKey   = self.private_key.public_key( ) 

        # Prepare to save the inner and outer layer key
        self.inner_layer_key:           bytes   = b''
        self.outer_layer_input_key:     bytes   = b''
        self.outer_layer_output_key:    bytes   = b''

        # Nolify the shared public key value at start
        self.shared_public_key = None

        self.input_sequence_number  = 0
        self.output_sequence_number = 0

    
    def share_public_key( self ) -> tuple:
        """
        Share the current public key using x9.62 and compressed point.

        Receive: None

        Returns:
        - tuple: Containing the public key and its signatured value
        """

        public_key: bytes = self.public_key.public_bytes( 
            serialization.Encoding.X962, 
            format=serialization.PublicFormat.CompressedPoint
        )

        signature: bytes = self.private_key.sign( 
            public_key,
            ec.ECDSA( hashes.SHA256( ) )
        )

        return public_key, signature
    

    @safe_call( c_debug.log_error )
    def load_public_key( self, public_key: bytes, signature: bytes ) -> bool:
        """
        Load the public key and save it.

        Receive: 
        - public_key (bytes): Public key value
        - signature: (bytes): Signed public key value

        Returns: 
        - bool: If the loading operation was successfully done
        """

        #shared_public_key = serialization.load_pem_public_key( public_key, default_backend( ) )
        shared_public_key = ec.EllipticCurvePublicKey.from_encoded_point( ec.SECP256R1( ), public_key )

        shared_public_key.verify(
            signature, public_key,
            ec.ECDSA( hashes.SHA256( ) )
        )

        self.shared_public_key = shared_public_key

        return True
    

    def generate_nonce_challenge( self ) -> tuple:
        """
        Start a nonce challenge.

        Receive: None

        Returns: 
        - tuple: The challenge information like encrypted nonce, emph key and more
        """

        if not self.shared_public_key:
            return None
        
        ephemeral_private_key = ec.generate_private_key( curve=ec.SECP256R1( ), backend=default_backend( ) )
        ephemeral_public_key = ephemeral_private_key.public_key( )

        shared_secret = ephemeral_private_key.exchange( ec.ECDH( ), self.shared_public_key )

        aes_key = HKDF(
            algorithm   = hashes.SHA256( ),
            length      = SIZE_AES_KEY,
            salt        = None,
            info        = b'nonce_challenge',
            backend     = default_backend( )
        ).derive( shared_secret )

        nonce:  bytes   = os.urandom( SIZE_NONCE * 3 )
        iv:     bytes   = os.urandom( SIZE_IV )

        encrpytor = Cipher( algorithms.AES( aes_key ), modes.GCM( iv ), backend=default_backend( ) ).encryptor( )

        encrypted_nonce: bytes = iv + ( encrpytor.update( nonce ) + encrpytor.finalize( ) ) + encrpytor.tag

        ephemeral_public_key_bytes = ephemeral_public_key.public_bytes( 
            serialization.Encoding.X962, 
            format=serialization.PublicFormat.CompressedPoint
        )

        return encrypted_nonce, nonce, ephemeral_public_key_bytes


    @safe_call( c_debug.log_error )
    def respond_to_nonce_challenge( self, encrypted_nonce: bytes, ephemeral_public_key_bytes: bytes ) -> bytes:
        """
        Peform the nonce challenge.
        
        Receive:
        - encrypted_nonce (bytes): The encrypted nonce that needs to be decrypted
        - ephemeral_public_key_bytes (bytes): eph public key that used in this challenge

        Returns:
        - bytes: Signed nonce value
        """

        #ephemeral_public_key = serialization.load_der_public_key( ephemeral_public_key_bytes, default_backend( ) )
        ephemeral_public_key = ec.EllipticCurvePublicKey.from_encoded_point( ec.SECP256R1( ), ephemeral_public_key_bytes )

        shared_secret = self.private_key.exchange( ec.ECDH( ), ephemeral_public_key )

        aes_key = HKDF(
            algorithm=hashes.SHA256( ),
            length=SIZE_AES_KEY,
            salt=None,
            info=b'nonce_challenge',
            backend=default_backend( )
        ).derive( shared_secret )

        iv:     bytes   = encrypted_nonce[ :16 ]
        tag:    bytes   = encrypted_nonce[ -16: ]
        encrypted_nonce = encrypted_nonce[ 16:-16 ]

        decryptor = Cipher( algorithms.AES( aes_key ), modes.GCM( iv, tag ), backend=default_backend( ) ).decryptor( )
        nonce = decryptor.update( encrypted_nonce ) + decryptor.finalize( )

        signature = self.private_key.sign( nonce, ec.ECDSA( hashes.SHA256( ) ) )

        return signature
    

    @safe_call( c_debug.log_error )
    def verify_nonce_response( self, nonce: bytes, signature: bytes ) -> bool:
        """
        Verify the challenge response.

        Receive:
        - nonce (bytes): Original nonce value
        - signature (bytes): Signed nonces value

        Returns:
        - bool: Result if success or fail
        """

        if not self.shared_public_key:
            return False
        
        self.shared_public_key.verify( signature, nonce, ec.ECDSA( hashes.SHA256( ) ) )

        return True

    
    def share_inner_layer_key( self ) -> bytes:
        """
        Share the inner layer encryption key.

        Receive: None

        Returns:
        - bytes: Protected inner layer key
        """
        
        return self.encrypt_using_derived_key( self.inner_layer_key, b'inner_layer_key' )
    

    def share_outer_layer_key( self ) -> bytes:
        """
        Share the outer layer encryption key.

        Receive: None

        Returns:
        - bytes: Protected outer layer key
        """

        return self.encrypt_using_derived_key( self.outer_layer_output_key, b'outer_layer_key' )
    

    @safe_call( c_debug.log_error )
    def load_inner_layer_key( self, encrypted_value: bytes ) -> bool:
        """
        Load inner layer key.

        Receive:
        - encrypted_value (bytes): Encrypted inner layer key

        Returns:
        - bool: Result if key loaded
        """

        self.inner_layer_key = self.decrypt_using_derived_key( encrypted_value, b'inner_layer_key' )
        return self.inner_layer_key != None
    

    @safe_call( c_debug.log_error )
    def load_outer_layer_key( self, encrypted_value: bytes ) -> bool:
        """
        Load outer layer key.

        Receive:
        - encrypted_value (bytes): Encrypted outer layer key

        Returns:
        - bool: Result if key loaded
        """

        self.outer_layer_output_key = self.decrypt_using_derived_key( encrypted_value, b'outer_layer_key' )
        return self.outer_layer_output_key != None


    def encrypt_using_derived_key( self, data: bytes, info: bytes ) -> bytes:
        """
        Encrypt a specific bytes using eph key to avoid using too much the regular asy key.

        Receive:
        - data (bytes): Information to protect
        - info (bytes): Additional value for the key derive

        Returns:
        - bytes: Protected value
        """

        ephemeral_private_key = ec.generate_private_key( curve=ec.SECP256R1( ), backend=default_backend( ) )
        ephemeral_public_key = ephemeral_private_key.public_key( )

        shared_secret = ephemeral_private_key.exchange( ec.ECDH( ), self.shared_public_key )

        aes_key = HKDF(
            algorithm=hashes.SHA256( ),
            length=SIZE_AES_KEY,
            salt=None,
            info=info,
            backend=default_backend( )
        ).derive( shared_secret )

        iv:     bytes   = os.urandom( SIZE_IV )

        encrpytor               = Cipher( algorithms.AES( aes_key ), modes.GCM( iv ), backend=default_backend( ) ).encryptor( )
        encrypted_key: bytes    = iv + ( encrpytor.update( data ) + encrpytor.finalize( ) ) + encrpytor.tag

        ephemeral_public_key_bytes = ephemeral_public_key.public_bytes( 
            serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )

        return ephemeral_public_key_bytes + encrypted_key
    

    @safe_call( c_debug.log_error )
    def decrypt_using_derived_key( self, encrypted_value: bytes, info: bytes ) -> bytes:
        """
        Decrypt a specific bytes using eph key to avoid using too much the regular asy key.

        Receive:
        - encrypted_value (bytes): Protected information
        - info (bytes): Additional value for the key derive

        Returns:
        - bytes: Unprotected value
        """

        ephemeral_public_key_bytes = encrypted_value[ :33 ]  # compressed point
        encrypted_value = encrypted_value[ 33: ]

        #ephemeral_public_key = serialization.load_der_public_key( ephemeral_public_key_bytes, default_backend( ) )
        ephemeral_public_key = ec.EllipticCurvePublicKey.from_encoded_point( ec.SECP256R1( ), ephemeral_public_key_bytes )

        shared_secret = self.private_key.exchange( ec.ECDH( ), ephemeral_public_key )

        aes_key = HKDF(
            algorithm=hashes.SHA256( ),
            length=SIZE_AES_KEY,
            salt=None,
            info=info,
            backend=default_backend( )
        ).derive( shared_secret )

        iv:     bytes   = encrypted_value[ :16 ]
        tag:    bytes   = encrypted_value[ -16: ]
        encrypted_value   = encrypted_value[ 16:-16 ]

        decryptor = Cipher( algorithms.AES( aes_key ), modes.GCM( iv, tag ), backend=default_backend( ) ).decryptor( )

        return decryptor.update( encrypted_value ) + decryptor.finalize( )


    def derive_key_from_sequence( self, output_number: bool = False, offset: int = 0 ):
        """
        Create a key for outer layer protection from a seq number.

        Receive:
        - output_number (bool, optional): Should use output seq number and not input number
        - offset (int, optional): Offset for the seq number

        Returns:
        - bytes: Drived ready to use 32 bytes key
        """

        if output_number:
            return HKDF(
                algorithm   = hashes.SHA256( ),
                length      = SIZE_OUTER_LAYER_KEY,
                salt        = None,
                info        = str( self.output_sequence_number + offset ).encode( ),
                backend     = default_backend( )
            ).derive( self.outer_layer_output_key )
    
        return HKDF(
            algorithm   = hashes.SHA256( ),
            length      = SIZE_OUTER_LAYER_KEY,
            salt        = None,
            info        = str( self.input_sequence_number + offset ).encode( ),
            backend     = default_backend( )
        ).derive( self.outer_layer_input_key )
    

    def sync_outer_level_keys( self ):
        """
        Set the output layer keys to be the same.
        This used to define a complete key rotation process.

        Receive: None

        Returns: None
        """

        self.outer_layer_input_key = self.outer_layer_output_key

    
    def sign_data( self, data: bytes ) -> bytes:
        """
        Sign a specific information using EC curve.

        Receive:
        - data (bytes): Information to sign

        Returns:
        - bytes: Signed data
        """

        return self.private_key.sign( data, ec.ECDSA( hashes.SHA256( ) ) )
    

    def verify_data( self, data: bytes, signature: bytes ) -> bool:
        """
        Verify a specific signatured value.

        Receive:
        - data (bytes): Original data
        - signature (bytes): Signed data

        Returns: 
        - bool: Is the signature correct
        """

        try:
            self.shared_public_key.verify( signature, data, ec.ECDSA( hashes.SHA256( ) ) )
            return True
        except:
            return False


class c_security:
    
    # region : Private attributes

    _key:               c_digital_key
    _password_hasher:   argon2_password_hasher

    _last_error:    str

    # endregion

    # region : Initialize

    def __init__( self ):
        """
        Default constructor for security protocol.

        Receive: None

        Returns:
        - c_security: Protocol instance
        """

        self._last_error = ""
        self._password_hasher = argon2_password_hasher( time_cost=3, memory_cost=65536, parallelism=4 )

        self._key = c_digital_key( )

    
    def share( self, sharing_type: int, new_value: any = None ) -> any:
        """
        Share or Load information.

        Receive:
        - sharing_type (int): Type of value that is being shared
        - new_value (any, optional): Value to load

        Returns:
        - any: If new_value is None, the method will return a value based on share type
        """

        if sharing_type == ENUM_COMPLEX_KEY:
            # Share public key

            if new_value is None:
                return self._key.share_public_key( )
            
            if type( new_value ) == tuple and len( new_value ) == 2:
                return self._key.load_public_key( new_value[ 0 ], new_value[ 1 ] )
            
            return False
        
        if sharing_type == ENUM_INNER_LAYER_KEY:
            # Share first layer key

            if new_value is None:
                return self._key.share_inner_layer_key( )
            
            return self._key.load_inner_layer_key( new_value )
        
        if sharing_type == ENUM_OUTER_LAYER_KEY:
            # Share second layer key

            if new_value is None:
                return self._key.share_outer_layer_key( )
            
            return self._key.load_outer_layer_key( new_value )
        
        raise Exception( "Invalid share type" )


    def generate_key( self, type: int ):
        """
        Generate key based on layer type and loads it.

        Receive:
        - type (int): Layer index

        Returns: None
        """

        if type == ENUM_INNER_LAYER_KEY:
            self._key.inner_layer_key = os.urandom( SIZE_INNER_LAYER_KEY )
            
        elif type == ENUM_OUTER_LAYER_KEY:
            self._key.outer_layer_output_key = os.urandom( SIZE_OUTER_LAYER_KEY )
            
    # endregion

    # region : Challenge

    def initiate_challenge( self ) -> tuple:
        """
        Start a nonce challenge.

        Receive: None

        Returns: 
        - tuple: The challenge information like encrypted nonce, emph key and more
        """

        return self._key.generate_nonce_challenge( )
    

    def respond_to_challenge( self, encrypted_nonce: bytes, ephemeral_public_key_bytes: bytes ) -> bytes:
        """
        Peform the nonce challenge.
        
        Receive:
        - encrypted_nonce (bytes): The encrypted nonce that needs to be decrypted
        - ephemeral_public_key_bytes (bytes): eph public key that used in this challenge

        Returns:
        - bytes: Signed nonce value
        """

        return self._key.respond_to_nonce_challenge( encrypted_nonce, ephemeral_public_key_bytes )
    
    
    def verify_challenge( self, nonce: bytes, signature: bytes ) -> bool:
        """
        Verify the challenge response.

        Receive:
        - nonce (bytes): Original nonce value
        - signature (bytes): Signed nonces value

        Returns:
        - bool: Result if success or fail
        """

        return self._key.verify_nonce_response( nonce, signature )

    # endregion

    # region : Complex operations

    @safe_call( c_debug.log_error )
    def complex_protection( self, data: any, info: bytes = b'' ) -> bytes:
        """
        Encrypt information using heavy method.

        Receive:
        - data (any): Information to protect
        - info (bytes, optional): Additional key information

        Returns:
        - bytes: Protected value
        """

        if type( data ) == str:
            data: bytes = data.encode( )

        return self._key.encrypt_using_derived_key( data, info )
    

    @safe_call( c_debug.log_error )
    def complex_remove_protection( self, data: bytes, info: bytes = b'' ) -> bytes:
        """
        Decrypt information using heavy method.

        Receive:
        - data (bytes): Encrypted information
        - info (bytes, optional): Additional key information

        Returns:
        - bytes: Unprotected value
        """

        return self._key.decrypt_using_derived_key( data, info )
    
    # endregion

    # region : Inner Layer operations

    @safe_call( c_debug.log_error )
    def inner_protect( self, data: any ) -> bytes:
        """
        Inner layer protection methos.

        Receive:
        - data (any): Information to encrypt

        Returns:
        - bytes: Encrypted value using first layer
        """

        if type( data ) == str:
            data: bytes = data.encode( )

        iv = os.urandom( SIZE_IV )

        cipher      = Cipher( algorithms.AES( self._key.inner_layer_key ), modes.GCM( iv ), backend=default_backend( ) )
        encryptor   = cipher.encryptor( )

        return iv + ( encryptor.update( data ) + encryptor.finalize( ) ) + encryptor.tag
    

    @safe_call( c_debug.log_error )
    def inner_unprotect( self, data: bytes ) -> bytes:
        """
        Remove first layer protection.

        Receive:
        - data (bytes): Encrypted value

        Returns:
        - bytes: Original value
        """

        if data is None:
            return None

        iv      = data[ :16 ]
        tag     = data[ -16: ]
        data    = data[ 16:-16 ]

        cipher      = Cipher( algorithms.AES( self._key.inner_layer_key ), modes.GCM( iv, tag ), backend=default_backend( ) )
        decryptor   = cipher.decryptor( )

        return decryptor.update( data ) + decryptor.finalize( )

    # endregion

    # region : Outer Layer operations

    @safe_call( c_debug.log_error )
    def outer_protect( self, data: bytes ) -> bytes:
        """
        Outer layer protection methos.

        Receive:
        - data (bytes): First layer result to encrypt

        Returns:
        - bytes: Encrypted value using second layer
        """

        key:    bytes = self._key.derive_key_from_sequence( output_number=True )
        nonce:  bytes = os.urandom( SIZE_NONCE )

        cipher = chacha20_poly1305( key )
        cipher_text = cipher.encrypt( nonce, data, associated_data=None )

        return nonce + cipher_text
    

    @safe_call( c_debug.log_error )
    def outer_unprotect( self, data: bytes ) -> bytes:
        """
        Remove second layer protection.

        Receive:
        - data (bytes): Encrypted value

        Returns:
        - bytes: First layer encrypted value
        """

        nonce:  bytes = data[ :SIZE_NONCE ]
        data:   bytes = data[ SIZE_NONCE: ]

        key:    bytes = self._key.derive_key_from_sequence( output_number=False )

        cipher = chacha20_poly1305( key )

        return cipher.decrypt( nonce, data, associated_data=None )

    # endregion

    # region : Dual Layers operations

    @safe_call( c_debug.log_error )
    def dual_protect( self, data: any ) -> bytes:
        """
        Protect value using dual layer encryption.

        Receive:
        - data (any): Information to protect

        Returns:
        - bytes: Result of the protection
        """

        if type( data ) == str:
            data: bytes = data.encode( )

        return self.outer_protect( self.inner_protect( data ) )
    

    @safe_call( c_debug.log_error )
    def dual_unprotect( self, data: bytes ) -> bytes:
        """
        Remove dual layer protection.

        Receive:
        - data (bytes): Protected value

        Returns:
        - bytes: Original information
        """

        return self.inner_unprotect( self.outer_unprotect( data ) )

    # endregion

    # region : Fast operations

    def fast_encrypt( self, data: bytes, key: bytes, salt: bytes ) -> bytes:
        """
        Standalone encryption method.

        Receive:
        - data (bytes): Information to encrypt
        - key (bytes): Base to to derive from an ChaCha20 key
        - salt (bytes): Salt value for derive process

        Returns:
        - bytes: Encrypted value
        """

        derived_key:    bytes = self.__convert_to_chacha_key( key, salt )
        nonce:          bytes  = os.urandom( SIZE_NONCE )
        
        cipher = chacha20_poly1305( derived_key )

        return nonce + cipher.encrypt( nonce, data, associated_data=None )


    def fast_decrypt(self, data: bytes, key: bytes, salt: bytes) -> bytes:
        """
        Standalone descrpytion method.

        Receive:
        - data (bytes): Encrypted value
        - key (bytes): Base to to derive from an ChaCha20 key
        - salt (bytes): Salt value for derive process

        Returns:
        - bytes: Original information
        """

        derived_key:    bytes = self.__convert_to_chacha_key( key, salt )
        nonce:          bytes = data[ :SIZE_NONCE ]
        data:           bytes = data[ SIZE_NONCE: ]

        cipher = chacha20_poly1305( derived_key )

        return cipher.decrypt( nonce, data, associated_data=None )
    
    # endregion

    # region : Hashing

    def preform_hashing( self, value: any ) -> tuple:
        """
        Hash value using Argon2id.

        Receive:
        - value (any): Any value to hash

        Returns:
        - bytes: Hash result
        """

        if type( value ) == str:
            value: bytes = value.encode( )

        salt: bytes = os.urandom( SIZE_SALT )
        hash: str = self._password_hasher.hash( value, salt=salt )

        return hash, salt.hex( )


    def verify( self, value: any, hashed_value: str ) -> bool:
        """
        Verify hash value and the original.

        Receive:
        - value (any): Original value
        - hashed_value (bytes): Hashed value

        Returns:
        - bool: Success if the hashed value matches the original one
        """

        if type( value ) == str:
            value: bytes = value.encode( )

        try:
            return self._password_hasher.verify( hashed_value, value )
        
        except Exception as e:
            return False

    # endregion

    # region : Utilities

    def increase_input_sequence_number( self ):
        """
        Increase input seq number.

        Receive: None

        Returns: None
        """

        self._key.input_sequence_number += 1

    
    def reset_input_sequence_number( self ):
        """
        Reset input seq number

        Receive: None

        Returns: None
        """
        
        self._key.input_sequence_number = 0


    def increase_output_sequence_number( self ):
        """
        Increase output seq number.

        Receive: None

        Returns: None
        """

        self._key.output_sequence_number += 1

    
    def reset_output_sequence_number( self ):
        """
        Reset output seq number

        Receive: None

        Returns: None
        """

        self._key.output_sequence_number = 0


    def sync_outer_level_keys( self ):
        """
        Set the output layer keys to be the same.
        This used to define a complete key rotation process.

        Receive: None

        Returns: None
        """

        self._key.sync_outer_level_keys( )

    
    def should_rotate( self ) -> bool:
        """
        Checks if the server should start the key rotation process.

        Receive: None

        Returns:
        - bool: True if the key rotation should be performed
        """

        return self._key.output_sequence_number > ROTATION_MAX or self._key.input_sequence_number > ROTATION_MAX


    def sign_data( self, data: bytes ) -> bytes:
        """
        Sign a specific information using EC curve.

        Receive:
        - data (bytes): Information to sign

        Returns:
        - bytes: Signed data
        """

        return self._key.sign_data( data )
    

    def verify_data( self, data: bytes, signature: bytes ) -> bool:
        """
        Verify a specific signatured value.

        Receive:
        - data (bytes): Original data
        - signature (bytes): Signed data

        Returns: 
        - bool: Is the signature correct
        """

        return self._key.verify_data( data, signature )


    def __convert_to_chacha_key( self, password: bytes, salt: bytes ) -> bytes:
        """
        Convert a plain text password value into encryption key.

        Receive:
        - password (bytes): Raw password value 
        - salt (bytes): Salt value for key creation

        Returns:
        - bytes: 32-bytes key
        """
        
        return argon2_low_level.hash_secret_raw(
            secret      = password,
            salt        = salt,
            time_cost   = 3,
            memory_cost = 65536,
            parallelism = 4,
            hash_len    = 32,
            type        = argon2_type.ID
        )
    
    # endregion
    