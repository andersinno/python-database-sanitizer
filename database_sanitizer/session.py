"""
API to sanitation session.

Sanitation session allows having a state within a single sanitation
process.

One important thing stored to the session is a secret key which is
generated to a new random value for each sanitation session, but it
stays constant during the whole sanitation process. Its value is never
revealed, so that it is possible to generate such one way hashes with
it, that should not be redoable afterwards. I.e. during the sanitation
session it's possible to do ``hash(C) -> H`` for any clear text C, but
it is not possible to check if H is the hashed value of C after the
sanitation session has ended.
"""

import hashlib
import hmac
import random
import sys
import threading

from six import int2byte

if sys.version_info >= (3, 6):
    from typing import Callable, Optional, Sequence  # noqa


SECRET_KEY_BITS = 128


_thread_local_storage = threading.local()


def hash_text_to_int(value, bit_length=32):
    # type: (str, int) -> int
    hash_value = hash_text(value)
    return int(hash_value[0:(bit_length // 4)], 16)


def hash_text_to_ints(value, bit_lengths=(16, 16, 16, 16)):
    # type: (str, Sequence[int]) -> Sequence[int]
    hash_value = hash_text(value)
    hex_lengths = [x // 4 for x in bit_lengths]
    hex_ranges = (
        (sum(hex_lengths[0:i]), sum(hex_lengths[0:(i + 1)]))
        for i in range(len(hex_lengths)))
    return tuple(int(hash_value[a:b], 16) for (a, b) in hex_ranges)


def hash_text(value, hasher=hashlib.sha256, encoding='utf-8'):
    # type: (str, Callable, str) -> str
    return hash_bytes(value.encode(encoding), hasher)


def hash_bytes(value, hasher=hashlib.sha256):
    # type: (bytes, Callable) -> str
    return hmac.new(get_secret(), value, hasher).hexdigest()


def get_secret():
    # type: () -> bytes
    """
    Get session specific secret key.
    """
    if not getattr(_thread_local_storage, 'secret_key', None):
        _initialize_session()
    return _thread_local_storage.secret_key  # type: ignore


def reset(secret_key=None):
    # type: (Optional[bytes]) -> None
    """
    Reset the session.

    By default, this resets the value of the secret to None so that, if
    there was an earlier sanitation process ran on the same thread, then
    a next call that needs the secret key of the session will generate a
    new value for it.

    This may also be used to set a predifend value for the secret key.
    """
    _thread_local_storage.secret_key = secret_key


def _initialize_session():
    # type: () -> None
    sys_random = random.SystemRandom()
    _thread_local_storage.secret_key = b''.join(
        int2byte(sys_random.randint(0, 255))
        for _ in range(SECRET_KEY_BITS // 8))
