"""
Работа на основе Gnome Looking Glass


Based on:

1. https://github.com/adrienverge/gnome-magic-window
2. https://github.com/CZ-NIC/run-or-raise
3. https://wiki.gnome.org/Projects/GnomeShell/LookingGlass
4. https://askubuntu.com/questions/91938/how-can-one-invoke-lg-looking-glass-from-a-command-line

"""
# Gnome Looking Glass
# gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval 'ARGS'

# Minimize active window
# ARGS = global.display.focus_window.minimize();

# Close active window
# ARGS = global.display.focus_window.delete(global.get_current_time());

from plugins.base import plugin

import plugins

class Active_window:
    def get(self):
        pass

    def set(self, *args):
        pass

    def close(self, *args):
        print('Close active window.')

    def minimize(self, *args):
        print('Minimize active window.')


class Plugin(plugin.Plugin):
    name='gnome'
    description = 'Useful commands for gnome windows and apps.'
    active_window = None

    def raise_or_run(self,  *args):
        print('Raise or run: %s' % args)

    def process_command(self, command):
        pass

    def __init__(self):
        # print('Initiate "gnome" plugin.')
        # Выполняем оригинальный вызов инициации
        super().__init__()

        self.active_window = Active_window()

        self.functions.add('raise', 'Raise window or run app', self.raise_or_run)
        self.functions.add('close', 'Close active window', self.active_window.close)
        self.functions.add('minimize', 'Mnimize active window', self.active_window.minimize)

        # self.functions.print()

# Начальная инициализация класса, чтобы сработало при импорте
# gnome = Gnome()
# plugin = Plugin()
