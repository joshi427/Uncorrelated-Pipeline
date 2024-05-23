

class Company:
    def __init__(self, name, url=''):
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not isinstance(url, str):
            raise TypeError("url must be a string")

        self.name = name
        self.url = url
