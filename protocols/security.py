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
    def load_public_key( self, public_key: bytes, signature ) -> bool:

        #shared_public_key = serialization.load_pem_public_key( public_key, default_backend( ) )
        shared_public_key = ec.EllipticCurvePublicKey.from_encoded_point( ec.SECP256R1( ), public_key )

        shared_public_key.verify(
            signature, public_key,
            ec.ECDSA( hashes.SHA256( ) )
        )

        self.shared_public_key = shared_public_key

        return True
    

    def generate_nonce_challenge( self ) -> tuple:

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

        if not self.shared_public_key:
            return False
        
        self.shared_public_key.verify( signature, nonce, ec.ECDSA( hashes.SHA256( ) ) )

        return True

    
    def share_inner_layer_key( self ) -> bytes:

        return self.encrypt_using_derived_key( self.inner_layer_key, b'inner_layer_key' )
    

    def share_outer_layer_key( self ) -> bytes:

        return self.encrypt_using_derived_key( self.outer_layer_output_key, b'outer_layer_key' )
    

    @safe_call( c_debug.log_error )
    def load_inner_layer_key( self, encrypted_value: bytes ) -> bool:

        self.inner_layer_key = self.decrypt_using_derived_key( encrypted_value, b'inner_layer_key' )
        return self.inner_layer_key != None
    

    @safe_call( c_debug.log_error )
    def load_outer_layer_key( self, encrypted_value: bytes ) -> bool:

        self.outer_layer_output_key = self.decrypt_using_derived_key( encrypted_value, b'outer_layer_key' )
        return self.outer_layer_output_key != None


    def encrypt_using_derived_key( self, data: bytes, info: bytes ) -> bytes:

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

        ephemeral_public_key_bytes = encrypted_value[ :33 ]  # P-256 compressed point
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
        self.outer_layer_input_key = self.outer_layer_output_key

    
    def sign_data( self, data: bytes ) -> bytes:
        return self.private_key.sign( data, ec.ECDSA( hashes.SHA256( ) ) )
    
    def verify_data( self, data: bytes, signature: bytes ) -> bool:
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
            Default constructor for security protocol
        """

        self._last_error = ""
        self._password_hasher = argon2_password_hasher( time_cost=3, memory_cost=65536, parallelism=4 )

        self._key = c_digital_key( )

    
    def share( self, sharing_type: int, new_value: any = None ) -> any:

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

        if type == ENUM_INNER_LAYER_KEY:
            self._key.inner_layer_key = os.urandom( SIZE_INNER_LAYER_KEY )
            
        elif type == ENUM_OUTER_LAYER_KEY:
            self._key.outer_layer_output_key = os.urandom( SIZE_OUTER_LAYER_KEY )
            

    # endregion

    # region : Challenge

    def initiate_challenge( self ) -> tuple:

        return self._key.generate_nonce_challenge( )
    

    def respond_to_challenge( self, encrypted_nonce: bytes, ephemeral_public_key_bytes: bytes ) -> bytes:

        return self._key.respond_to_nonce_challenge( encrypted_nonce, ephemeral_public_key_bytes )
    
    
    def verify_challenge( self, nonce: bytes, signature: bytes ) -> bool:

        return self._key.verify_nonce_response( nonce, signature )

    # endregion

    # region : Complex operations

    @safe_call( c_debug.log_error )
    def complex_protection( self, data: any, info: bytes = b'' ) -> bytes:

        if type( data ) == str:
            data: bytes = data.encode( )

        return self._key.encrypt_using_derived_key( data, info )
    

    @safe_call( c_debug.log_error )
    def complex_remove_protection( self, data: bytes, info: bytes = b'' ) -> bytes:

        return self._key.decrypt_using_derived_key( data, info )
    
    # endregion

    # region : Inner Layer operations

    @safe_call( c_debug.log_error )
    def inner_protect( self, data: any ) -> bytes:

        if type( data ) == str:
            data: bytes = data.encode( )

        iv = os.urandom( SIZE_IV )

        cipher      = Cipher( algorithms.AES( self._key.inner_layer_key ), modes.GCM( iv ), backend=default_backend( ) )
        encryptor   = cipher.encryptor( )

        return iv + ( encryptor.update( data ) + encryptor.finalize( ) ) + encryptor.tag
    

    @safe_call( c_debug.log_error )
    def inner_unprotect( self, data: bytes ) -> bytes:

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
        
        key:    bytes = self._key.derive_key_from_sequence( output_number=True )
        nonce:  bytes = os.urandom( SIZE_NONCE )

        cipher = chacha20_poly1305( key )
        cipher_text = cipher.encrypt( nonce, data, associated_data=None )

        return nonce + cipher_text
    

    @safe_call( c_debug.log_error )
    def outer_unprotect( self, data: bytes ) -> bytes:

        nonce:  bytes = data[ :SIZE_NONCE ]
        data:   bytes = data[ SIZE_NONCE: ]

        key:    bytes = self._key.derive_key_from_sequence( output_number=False )

        cipher = chacha20_poly1305( key )

        return cipher.decrypt( nonce, data, associated_data=None )

    # endregion

    # region : Dual Layers operations

    @safe_call( c_debug.log_error )
    def dual_protect( self, data: any ) -> bytes:

        if type( data ) == str:
            data: bytes = data.encode( )

        return self.outer_protect( self.inner_protect( data ) )
    

    @safe_call( c_debug.log_error )
    def dual_unprotect( self, data: bytes ) -> bytes:

        return self.inner_unprotect( self.outer_unprotect( data ) )

    # endregion

    # region : Fast operations

    def fast_encrypt( self, data: bytes, key: bytes, salt: bytes ) -> bytes:

        derived_key:    bytes = self.__convert_to_chacha_key( key, salt )
        nonce:          bytes  = os.urandom( SIZE_NONCE )
        
        cipher = chacha20_poly1305( derived_key )

        return nonce + cipher.encrypt( nonce, data, associated_data=None )


    def fast_decrypt(self, data: bytes, key: bytes, salt: bytes) -> bytes:

        derived_key:    bytes = self.__convert_to_chacha_key( key, salt )
        nonce:          bytes = data[ :SIZE_NONCE ]
        data:           bytes = data[ SIZE_NONCE: ]

        cipher = chacha20_poly1305( derived_key )

        return cipher.decrypt( nonce, data, associated_data=None )
    
    # endregion

    # region : Hashing

    def preform_hashing( self, value: any ) -> tuple:

        if type( value ) == str:
            value: bytes = value.encode( )

        salt: bytes = os.urandom( SIZE_SALT )
        hash: str = self._password_hasher.hash( value, salt=salt )

        return hash, salt.hex( )


    def verify( self, value: any, hashed_value: str ) -> bool:

        if type( value ) == str:
            value: bytes = value.encode( )

        try:
            return self._password_hasher.verify( hashed_value, value )
        
        except Exception as e:
            return False

    # endregion

    # region : Utilities

    def increase_input_sequence_number( self, offset: int = 1 ):
        
        self._key.input_sequence_number += 1

    
    def reset_input_sequence_number( self ):

        self._key.input_sequence_number = 0


    def increase_output_sequence_number( self, offset: int = 1 ):
        
        self._key.output_sequence_number += offset

    
    def reset_output_sequence_number( self ):

        self._key.output_sequence_number = 0


    def sync_outer_level_keys( self ):

        self._key.sync_outer_level_keys( )

    
    def should_rotate( self ) -> bool:

        return self._key.output_sequence_number > ROTATION_MAX or self._key.input_sequence_number > ROTATION_MAX


    def sign_data( self, data: bytes ) -> bytes:
        return self._key.sign_data( data )
    
    def verify_data( self, data: bytes, signature: bytes ) -> bool:
        return self._key.verify_data( data, signature )

    def __convert_to_chacha_key( self, password: bytes, salt: bytes ) -> bytes:
        
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
    