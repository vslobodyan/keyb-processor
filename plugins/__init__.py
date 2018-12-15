
class Plugins:
    available = {}

    def add(self, name, description, _class):
        """Добавление класса плагина в список доступных для пользователя."""
        self.available['name'] = [description, _class]

    def find(self):
        pass

    def print(self):
        print('Plugins:')
        for key in self.available:
            print('key: %s, value: %s' % (key, self.available[key]))

    def __init__(self):
        # Импортируем все модули в каталоге

        self.print()
