def sanitize_null(value):
    return None


def sanitize_empty_json_dict(value):
    return '{}'


def sanitize_empty_json_list(value):
    return '[]'


def sanitize_invalid_django_password(value):
    return '!'
