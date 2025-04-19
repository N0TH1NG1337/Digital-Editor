"""
    project     : Digital Editor

    type:       : Protocol
    file        : Security

    description : Security Protocol class
"""

# This protocol will contain security measures use to secure data.
# The encryption in this protocol will be hybrid encryption.

# On the start the encryption will be asymmetric to exchange and establish secure connection
# On the process, the connection will be secured by symmetric encryption to be faster, since
# we are going to transfer large amount of data

import os
import random

from cryptography.hazmat.primitives.asymmetric  import rsa
from cryptography.hazmat.primitives.asymmetric  import padding

from cryptography.hazmat.primitives             import hashes, serialization
from cryptography.hazmat.primitives.ciphers     import Cipher, algorithms, modes

from cryptography.hazmat.backends               import default_backend

from cryptography.hazmat.primitives.kdf.scrypt  import Scrypt

from argon2                                     import PasswordHasher   as argon2_password_hasher
from argon2                                     import Type             as argon2_type
from argon2                                     import low_level        as argon2_low_level

from utilities.wrappers                         import safe_call
from utilities.debug                            import *

QUICK_KEY_SIZE      = 32
SHUFFLE_KEY_SIZE    = 16
SALT_SIZE           = 16

SHARE_TYPE_LONG_PART    = 1
SHARE_TYPE_QUICK_PART   = 2


class c_digital_key:

    private_key:        rsa.RSAPrivateKey
    public_key:         rsa.RSAPublicKey
    shared_public_key:  rsa.RSAPublicKey

    quick_key:          bytes
    
    def __init__( self ):
        """
            Initialize digital key for safety protocol.

            Receive :
            - generate_quick_key [optional] - If quick key should be generated or setted.

            Returns :   Digital Key object
        """  

        self.private_key = rsa.generate_private_key( public_exponent = 65537, key_size = 2048 )
        self.public_key = self.private_key.public_key( )  

        self.quick_key     = b''

        self.shared_public_key = None

    
    def share_public_key( self ) -> bytes:
        """
            Share this digital key public key.

            Receive :   None

            Returns :   Bytes of PEM format public key
        """

        return self.public_key.public_bytes( serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo )
    

    def load_public_key( self, public_pem_key: bytes ):
        """
            Initialize public key.

            Receive :
            - public_key - Public key 

            Returns :   None
        """

        self.shared_public_key = serialization.load_pem_public_key( public_pem_key )
    

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

    
    def share( self, sharing_type: int, new_value: any = None ):
        """
            Share / Update specific value based on the share type.

            Receive :
            - sharing_type          - Type of value to share.
            - new_value [optional]  - Set a new value based on share type
            
            Returns :   Any type
        """

        if sharing_type == SHARE_TYPE_LONG_PART:
            # Share public key

            if new_value is None:
                return self._key.share_public_key( )
            
            return self._key.load_public_key( new_value )
            

        if sharing_type == SHARE_TYPE_QUICK_PART:

            if new_value is None:
                return self._key.shared_public_key.encrypt(

                    # Quick key to encrypt
                    self._key.quick_key,

                    # Padding settings
                    self.__default_padding( ) 
                )
            
            # If not load it
            self._key.quick_key = self._key.private_key.decrypt(

                # Encrypted quick key
                new_value,

                # Padding settings
                self.__default_padding( )
            )

            return
        
        
        raise Exception( "Invalid share type" )
    

    def generate_quick_key( self ):
        """
            Generate quick key.

            Receive :   None

            Returns :   None
        """

        self._key.quick_key = os.urandom( QUICK_KEY_SIZE )

    
    def generate_shuffled_key( self ) -> bytes:
        """
            Generate shuffle key.

            Receive :   None

            Returns :   Bytes
        """

        key = os.urandom( SHUFFLE_KEY_SIZE )

        sha_hash = hashes.Hash( hashes.SHA256( ) )
        sha_hash.update( key )

        return sha_hash.finalize( )
    
    # endregion

    # region : Encryption

    @safe_call( c_debug.log_error )
    def strong_protect( self, data: bytes ) -> bytes:
        """
            Use strong protection to protect this data.

            Receive :
            - data - Information to protect

            Returns :   Protected bytes
        """

        return self._key.shared_public_key.encrypt( data, self.__default_padding( ) )
    

    @safe_call( c_debug.log_error )
    def quick_protect( self, data: bytes ) -> bytes:
        """
            Use quick protection to protect this data.

            Receive :
            - data - Information to protect

            Returns :   Protected bytes
        """

        iv = os.urandom( 16 )

        cipher      = Cipher( algorithms.AES( self._key.quick_key ), modes.GCM( iv ), backend=default_backend( ) )
        encryptor   = cipher.encryptor( )

        return iv + ( encryptor.update( data ) + encryptor.finalize( ) ) + encryptor.tag
    

    def fast_encrypt( self, data: bytes, key: bytes, salt: bytes ) -> bytes:
        """
            Encrypt data with key.

            Receive :
            - data - Information to encrypt
            - key  - Key to encrypt with (will be converted to valid AES key)

            Returns : Encrypted bytes (format: iv + ciphertext + tag)
        """
        # Convert the key to a valid AES key
        aes_key = self.__convert_to_aes_key( key, salt )
        
        iv = os.urandom( 16 )
        cipher = Cipher( algorithms.AES( aes_key ), modes.GCM( iv ), backend=default_backend( ) )
        encryptor = cipher.encryptor( )

        return iv + ( encryptor.update( data ) + encryptor.finalize( ) ) + encryptor.tag
    

    # endregion

    # region : Decryption
    
    @safe_call( c_debug.log_error )
    def remove_strong_protection( self, data: bytes ) -> bytes:
        """
            Remove strong protection.

            Receive :
            - data - Protected information

            Returns :   Unprotected bytes
        """

        if data is None:
            return None

        return self._key.private_key.decrypt( data, self.__default_padding( ) )
    

    @safe_call( c_debug.log_error )
    def remove_quick_protection( self, data: bytes ) -> bytes:
        """
            Remove quick protection.

            Receive : 
            - data - Protected information

            Returns :   Unprotected bytes
        """

        if data is None:
            return None

        iv      = data[ :16 ]
        tag     = data[ -16: ]
        data    = data[ 16:-16 ]

        cipher      = Cipher( algorithms.AES( self._key.quick_key ), modes.GCM( iv, tag ), backend=default_backend( ) )
        decryptor   = cipher.decryptor( )

        return decryptor.update( data ) + decryptor.finalize( )
    

    def fast_decrypt(self, data: bytes, key: bytes, salt: bytes) -> bytes:
        """
            Decrypt data with key.

            Receive :
            - data - Encrypted information
            - key  - Key to decrypt with (will be converted to valid AES key)

            Returns : Decrypted bytes
        """
        # Convert the key to a valid AES key
        aes_key = self.__convert_to_aes_key( key, salt )

        iv = data[ :16 ]
        tag = data[ -16: ]
        data = data[ 16:-16 ]

        cipher = Cipher( algorithms.AES( aes_key ), modes.GCM( iv, tag ), backend=default_backend( ) )
        decryptor = cipher.decryptor( )

        return decryptor.update( data ) + decryptor.finalize( )
    
    # endregion

    # region : Shuffle

    def shuffle( self, key: bytes, data: bytes ) -> bytes:
        """
            Shaffle information bytes.

            Receive :
            - data - Clear Information bytes

            Returns :   Shuffled information
        """
        
        shuffled_key = self.__convert_shaffle_key( key )

        return bytes( shuffled_key[ i ] for i in data )
    

    def unshuffle( self, key: bytes, data: bytes ) -> bytes:
        """
            Remove shuffle of the information

            Receive :
            - data - Shuffled information

            Returns :   Clear information
        """

        indices = list( self.__convert_shaffle_key( key ) )

        # Create a reverse mapping of indices
        reverse_indices = [ 0 ] * 256  # Assuming 256 possible byte values
        for i, index in enumerate( indices ):
            reverse_indices[ index ] = i

        # Deshuffle the data
        return bytes( reverse_indices[ i ] for i in data )

    # endregion

    # region : Hashing

    def preform_hashing( self, value: any ) -> tuple:

        if type( value ) == str:
            value: bytes = value.encode( )

        salt: bytes = os.urandom( SALT_SIZE )
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

    def __default_padding( self ) -> padding.OAEP:
        """
            Initialize a default instance of OAEP padding.

            Receive :   None

            Returns :   OAEP padding object
        """

        return padding.OAEP(
            mgf         = padding.MGF1( algorithm = hashes.SHA256( ) ),
            algorithm   = hashes.SHA256( ),
            label       = None
        )  


    def __convert_shaffle_key( self, key: bytes ):
        """
            Convert the shuffle key into correct value to shuffle and deshuffle.

            Receive :
            - key - Shuffle key seed

            Returns :   Normalized shuffle key
        """

        random.seed( key )

        # Generate a random permutation of indices
        indices = list( range( 256 ) )  # Assuming 256 possible byte values
        random.shuffle( indices )

        return bytes( indices )
    

    def __convert_to_aes_key( self, password: bytes, salt: bytes ) -> bytes:
        
        return argon2_low_level.hash_secret_raw(
            secret=password,
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=argon2_type.ID
        )
    
    # endregion
    