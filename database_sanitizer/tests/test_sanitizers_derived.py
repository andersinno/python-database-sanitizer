from database_sanitizer import session
from database_sanitizer.sanitizers import derived


def setup_module():
    session.reset(b'not-so-secret-key')


def test_sanitize_uuid4():
    assert derived.sanitize_uuid4(None) is None
    assert derived.sanitize_uuid4('') == ''
    assert derived.sanitize_uuid4('0') == (
        'e3a5862f-cffb-4d89-ab3e-5563b27e287a')
    assert derived.sanitize_uuid4('00000000000000000000000000000000') == (
        '00000000-0000-0000-0000-000000000000')
    assert derived.sanitize_uuid4('00000000-0000-0000-0000-000000000000') == (
        '00000000-0000-0000-0000-000000000000')
    assert derived.sanitize_uuid4('e3a5862f-cffb-4d89-ab3e-5563b27e287a') == (
        '88b0225e-6090-459a-999d-9b3a3ab28c53')
