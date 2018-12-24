"""
Базовый класс плагина.
Скелет для навешивания остальных функций.
"""

class Function:
    name = ''
    description = ''
    func = None

    def __init__(self, name='', description='', func=None):
        self.name = name
        self.description = description
        self.func = func


class Functions:
    available = {} # {Function_Name: function,}

    def add(self, name, description, func):
        """Добавление функции в список доступных для пользователя."""
        func = Function(name, description, func)
        self.available[name]=func

    def find(self):
        pass

    def print(self):
        print('\tFunctions:')
        for key in self.available:
            # print('name: %s, desc: %s, func: %s' % (key, self.available[key].description, self.available[key].func))
            # print(' name: %s, desc: %s' % (key, self.available[key].description))
            print('\t%s - %s' % (key, self.available[key].description))

        # print()
    def __init__(self):
        self.available = {}


class Plugin:
    name = ""
    description = ""
    functions = None

    def __init__(self):
        self.functions = Functions()
        # plugins.add(name, description, self)
