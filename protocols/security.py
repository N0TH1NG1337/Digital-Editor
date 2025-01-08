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
# we are going to tranfer large amount of data

from cryptography.hazmat.primitives.asymmetric  import rsa
from cryptography.hazmat.primitives.asymmetric  import padding
from cryptography.hazmat.primitives             import hashes


class c_security:
    
    # region : Private attributes

    _slow_key:      rsa.RSAPrivateKey
    _fast_key:      any

    _last_error:    str

    # endregion

    # region : Initialize

    def __init__( self ):
        """
            Default constructor for security protocol
        """

        self._last_error = ""

    # endregion

    