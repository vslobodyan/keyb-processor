
from os.path import dirname, basename, isfile
import glob


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
        print()

    def __init__(self):
        print('Initiate plugins.')
        # Импортируем все модули в каталоге
        plugins_path = dirname(__file__) + "/*.py"
        print('Path for plugins: %s' % plugins_path)
        modules = glob.glob(plugins_path)
        __all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
        print('__all__: %s' % __all__)
        self.print()
