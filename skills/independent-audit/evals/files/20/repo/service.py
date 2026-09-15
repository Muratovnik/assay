import json
def decode(text):
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('Object required')
    return value
