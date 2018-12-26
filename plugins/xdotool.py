"""

Based on:

1. https://askubuntu.com/questions/4876/can-i-minimize-a-window-from-the-command-line
2. https://unix.stackexchange.com/questions/254820/xdotool-how-to-search-for-window-by-title-and-class-with-different-patterns-si
3. https://ubuntuincident.wordpress.com/2013/01/10/find-window-by-its-name-and-activate-it-bring-to-foreground/

"""

import subprocess

from plugins.base import plugin


class Plugin(plugin.Plugin):
    name='xdotool'
    description = 'Useful window management commands on Xorg using the xdotool.'

    # def raise_or_run(self,  *args):


    # xdotool search --onlyvisible --class 'opera'
    # xdotool windowactivate 37748739

    #     print('Raise or run: %s' % args)
    #     # Разбираем аргументы
    #     # print('len(locals()=%s' % len(locals()))
    #     if len(locals())<2:
    #         print('Not enough arguments for run or raise! (must be 2, get %s)' % len(locals()))
    #     else:
    #         prog_exec = args[0][0]
    #         print('prog_exec=%s' % prog_exec)
    #         window_name = args[0][1]
    #         print('window_name=%s' % window_name)
    #         # Проверяем, есть-ли уже такое окно
    #         c = self.active_window.lg.window_is_present(window_name)
    #         # print('c=%s' % c)
    #         stdoutdata = subprocess.check_output(c)
    #         # Если есть - активируем его
    #         if stdoutdata:
    #             # print('We have LG output on search "%s" window: %s' % (window_name,stdoutdata))
    #             c = self.active_window.lg.activate_window(window_name)
    #             subprocess.run(c)
    #         else:
    #             # Если нет - запускаем программу заново
    #             print('Window not found. We will run program "%s" again.' % prog_exec)
    #             subprocess.run(prog_exec)

    def close(self,  *args):
    # Убивает весь процесс напрочь. Не надо использовать.
        print('Close active window')
        c = '''xdotool getactivewindow windowclose'''.split()
        subprocess.run(c)

    def minimize(self,  *args):
        print('Minimize active window')
        c = '''xdotool getactivewindow windowminimize'''.split()
        subprocess.run(c)

    def __init__(self):
        # Выполняем оригинальный вызов инициации
        super().__init__()

        # self.functions.add('raise', 'Raise window or run app. Parameters: COMMAND WINDOW_NAME', self.raise_or_run)
        # self.functions.add('close', 'Close active window', self.close)
        self.functions.add('minimize', 'Minimize active window', self.minimize)
        # self.functions.print()

# Начальная инициализация класса, чтобы сработало при импорте
# gnome = Gnome()
# plugin = Plugin()
