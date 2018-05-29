from database_sanitizer.sanitizers import constant


def test_sanitize_null():
    assert constant.sanitize_null(None) is None
    assert constant.sanitize_null('') is None
    assert constant.sanitize_null('whatever') is None
    assert constant.sanitize_null('test') is None


def test_sanitize_invalid_django_password():
    assert constant.sanitize_invalid_django_password(None) == '!'
    assert constant.sanitize_invalid_django_password('') == '!'
    assert constant.sanitize_invalid_django_password('whatever') == '!'
    assert constant.sanitize_invalid_django_password('test') == '!'


def test_sanitize_empty_json_dict():
    assert constant.sanitize_empty_json_dict(None) == '{}'
    assert constant.sanitize_empty_json_dict('') == '{}'
    assert constant.sanitize_empty_json_dict('whatever') == '{}'
    assert constant.sanitize_empty_json_dict('test') == '{}'


def test_sanitize_empty_json_list():
    assert constant.sanitize_empty_json_list(None) == '[]'
    assert constant.sanitize_empty_json_list('') == '[]'
    assert constant.sanitize_empty_json_list('whatever') == '[]'
    assert constant.sanitize_empty_json_list('test') == '[]'
