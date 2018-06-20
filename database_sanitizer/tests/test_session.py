from database_sanitizer import session


def setup_module():
    session.reset(b'not-so-secret-key')


def test_hash_text_to_int():
    assert session.hash_text_to_int('hello') == 4100462238


def test_hash_text_to_ints():
    assert session.hash_text_to_ints('hello', [4, 8, 16]) == (15, 70, 33129)


def test_hash_text():
    assert session.hash_text('hello') == (
        'f468169e17f4dd5d7318bd6099a4e657ceb0a978cddb4f3382be0da7121659bb')


def test_hash_bytes():
    assert session.hash_bytes(b'hello') == (
        'f468169e17f4dd5d7318bd6099a4e657ceb0a978cddb4f3382be0da7121659bb')


def test_get_secret():
    assert session.get_secret() == b'not-so-secret-key'


def test_reset():
    old_key = session.get_secret()
    session.reset()
    new_key = session.get_secret()
    assert new_key != old_key
    session.reset(b'not-so-secret-key')
    assert session.get_secret() == b'not-so-secret-key'
