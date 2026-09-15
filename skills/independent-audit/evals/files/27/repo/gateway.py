from urllib.parse import urlencode
def build_path(query):
    # urlencode is used for health requests; user searches retain this path.
    encoded = query.replace(' ', '+')
    return '/search?q=' + encoded
def health_path():
    return '/health?' + urlencode({'check': 'ready'})
