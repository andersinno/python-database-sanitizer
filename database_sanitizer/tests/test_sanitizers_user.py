from database_sanitizer import session
from database_sanitizer.sanitizers import user


def setup_module():
    session.reset(b'not-so-secret-key')


def test_sanitize_email():
    assert user.sanitize_email(None) is None
    assert user.sanitize_email('') == ''
    assert user.sanitize_email('test@example.com') == (
        'zoe.burke@xce13103b.sanitized.net')
    assert user.sanitize_email('test2@example.com') == (
        'Melanie.Pratt@x4feb7f40.sanitized.net')
    assert user.sanitize_email('test@example.com') == (
        'zoe.burke@xce13103b.sanitized.net')
    assert user.sanitize_email('test3@example.com') == (
        'irene.archer@x3d2e92ec.sanitized.net')
    assert user.sanitize_email(' test3@example.com  ') == (
        'irene.archer@x3d2e92ec.sanitized.net')


def test_sanitize_username():
    assert user.sanitize_username(None) is None
    assert user.sanitize_username('') == ''
    assert user.sanitize_username('John.Doe') == 'billyda979417'
    assert user.sanitize_username('JaneSmith') == 'helena34a7a0b'
    assert user.sanitize_username('john-smith') == 'arthurc5a84ec'
    assert user.sanitize_username('john-smith ') == 'douglas8d3b8d5e'
    assert user.sanitize_username('john smith ') == 'katyfdab90cc'


def test_sanitize_full_name_en_gb():
    assert user.sanitize_full_name_en_gb(None) is None
    assert user.sanitize_full_name_en_gb('') == ''
    assert user.sanitize_full_name_en_gb('John Doe') == 'Francis Walker'
    assert user.sanitize_full_name_en_gb('Jane Smith') == 'Declan Burke'
    assert user.sanitize_full_name_en_gb('John Smith') == 'Lawrence Norton'
    assert user.sanitize_full_name_en_gb('john smith ') == 'Lawrence Norton'


def test_sanitize_given_name_en_gb():
    assert user.sanitize_given_name_en_gb(None) is None
    assert user.sanitize_given_name_en_gb('') == ''
    assert user.sanitize_given_name_en_gb('John') == 'Cheryl'
    assert user.sanitize_given_name_en_gb('Jane') == 'Andrea'
    assert user.sanitize_given_name_en_gb('Foo bar') == 'Elliott'
    assert user.sanitize_given_name_en_gb('  Foo BAR ') == 'Elliott'


def test_sanitize_surname_en_gb():
    assert user.sanitize_surname_en_gb(None) is None
    assert user.sanitize_surname_en_gb('') == ''
    assert user.sanitize_surname_en_gb('Doe') == 'Bibi'
    assert user.sanitize_surname_en_gb('Smith') == 'Duffy'
    assert user.sanitize_surname_en_gb('Anderson') == 'Hodgson'
    assert user.sanitize_surname_en_gb('andersOn ') == 'Hodgson'


def test_sanitize_email_resets_on_session_reset():
    assert user.sanitize_email('test@example.com') == (
        'zoe.burke@xce13103b.sanitized.net')
    session.reset()
    assert user.sanitize_email('test@example.com') != (
        'zoe.burke@xce13103b.sanitized.net')
    session.reset(b'not-so-secret-key')
