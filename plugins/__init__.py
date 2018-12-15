
from os.path import dirname, basename, isfile
import glob
import sys
import inspect

class Plugins:
    available = {}

    def add(self, name, _class):
        """Добавление класса плагина в список доступных для пользователя."""
        self.available[name] = _class

    def find(self):
        pass

    def print(self):
        print('Loaded plugins:')
        for key in self.available:
            obj = self.available[key]
            # print(' name: %s, desc: %s' % (key, obj.description))
            print(' %s - %s' % (key, obj.description))
            obj.functions.print()
        # print()

    def __init__(self):
        # print('Initiate plugins.')
        # Импортируем все модули в каталоге
        plugins_path = dirname(__file__) + "/*.py"
        print('Path for plugins: %s' % plugins_path)
        modules = glob.glob(plugins_path)
        founded_plugins = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
        print('Founded plugins: %s' % founded_plugins)
        # Импортируем найденные модули
        for one_plugin in founded_plugins:
            plugin_name = __name__+'.'+one_plugin
            print('Import %s module' % plugin_name)
            __import__(plugin_name, locals(), globals())
            # print('Found classes:')
            for name, obj in inspect.getmembers(sys.modules[plugin_name]):
                if inspect.isclass(obj):
                    # print(' ', obj, obj.__name__)
                    if obj.__name__ == 'Plugin':
                        print('Initiate "%s" plugin.' % obj.name)
                        # print('Найден новый класс плагина')
                        self.add(obj.name, obj())

        # self.print()
