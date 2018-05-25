import uuid

from database_sanitizer.session import hash_text

NIL_UUID = '00000000-0000-0000-0000-000000000000'
NIL_UUID_WITHOUT_DASHES = NIL_UUID.replace('-', '')


def sanitize_uuid4(value):
    if not value:
        return value
    if value.replace('-', '') == NIL_UUID_WITHOUT_DASHES:
        return NIL_UUID
    return str(uuid.UUID(hash_text(value)[:32], version=4))
