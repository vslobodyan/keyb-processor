"""
Базовый класс плагина.
Скелет для навешивания остальных функций.
"""

class Functions:
    available = {}

    def add(self, name, description, func):
        """Добавление функции в список доступных для пользователя."""
        self.available['name']=[description, func]

    def find(self):
        pass

    def print(self):
        print('Functions:')
        for key in self.available:
            print('key: %s, value: %s' % (key, self.available[key]))


class plugin:
    functions = None
    name = ""
    description = ""

    def __init__(self, name="", description="", plugins=None):
        self.name = name
        self.description = description
        self.functions = Functions()
        plugins.add(name, description, self)
