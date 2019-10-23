

class DictStore:

    def __init__(self, **kwargs):
        self._data = {}

    def has_key(self, key):
        return key in self._data

    def get(self, key):
        return self._data.get(key)
        
    def save(self, key, value):
        self._data[key] = value

