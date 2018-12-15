"""
Работа на основе Gnome Looking Glass


Based on:

1. https://github.com/adrienverge/gnome-magic-window
2. https://github.com/CZ-NIC/run-or-raise
3. https://wiki.gnome.org/Projects/GnomeShell/LookingGlass
4. https://askubuntu.com/questions/91938/how-can-one-invoke-lg-looking-glass-from-a-command-line

"""

import subprocess

from plugins.base import plugin


class LG_Command:
    """Обертка для команд Gnome Looking Glass"""

    def command(self, args):
        """Оборачиваем аргументы в кавычки и добавляем к массиву основной команды"""
        c = 'gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval'
        args='\''+args+'\''
        res = c.split()
        res.append(args)
        return res

    def minimize(self):
        return self.command('global.display.focus_window.minimize();')

    def close(self):
        return self.command('global.display.focus_window.delete(global.get_current_time());')



class Active_window:
    """Класс операций с активным окном"""
    lg = None

    def get(self):
        pass

    def set(self, *args):
        pass

    def close(self, *args):
        print('Close active window.')
        c = self.lg.close()
        print('LG %s' % c)
        subprocess.run(c)

    def minimize(self, *args):
        print('Minimize active window.')
        c = self.lg.minimize()
        print('LG %s' % c)
        subprocess.run(c)

    def __init__(self):
        self.lg = LG_Command()


class Plugin(plugin.Plugin):
    name='gnome'
    description = 'Useful commands for gnome windows and apps.'
    active_window = None

    def raise_or_run(self,  *args):
        print('Raise or run: %s' % args)

    def __init__(self):
        # print('Initiate "gnome" plugin.')
        # Выполняем оригинальный вызов инициации
        super().__init__()

        self.active_window = Active_window()

        self.functions.add('raise', 'Raise window or run app', self.raise_or_run)
        self.functions.add('close', 'Close active window', self.active_window.close)
        self.functions.add('minimize', 'Minimize active window', self.active_window.minimize)

        # self.functions.print()

# Начальная инициализация класса, чтобы сработало при импорте
# gnome = Gnome()
# plugin = Plugin()
