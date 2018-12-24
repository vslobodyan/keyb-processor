"""

Based on:

1. https://askubuntu.com/questions/4876/can-i-minimize-a-window-from-the-command-line
2. https://ubuntuforums.org/showthread.php?t=2390045
3. https://stackoverflow.com/questions/606191/convert-bytes-to-a-string
"""

import subprocess

from plugins.base import plugin


class Plugin(plugin.Plugin):
    name='wmctrl'
    description = 'Useful window management commands on Xorg using the wmctrl. Use "wmctrl -lx" to look names.'
    active_window = None

    def raise_or_run(self,  *args):
        print('Raise or run: %s' % args)
        # Разбираем аргументы
        # print('len(locals()=%s' % len(locals()))
        if len(locals())<2:
            print('Not enough arguments for run or raise! (must be 2, get %s)' % len(locals()))
        else:
            prog_exec = args[0][0]
            print('prog_exec=%s' % prog_exec)
            window_name = args[0][1]
            print('window_name=%s' % window_name)
            # Проверяем, есть-ли уже такое окно

            # Получаем список всех открытых окон
            c = "wmctrl -lx"
            stdoutdata = subprocess.check_output(c.split())
            str_outdata = stdoutdata.decode()
            # Если есть - активируем его
            print('str_outdata: %s' % str_outdata)

            if window_name in str_outdata:
                # Окно уже запущено. Надо на него переключиться
                print('We found win "%s"' % window_name)
                # print('We have LG output on search "%s" window: %s' % (window_name,stdoutdata))
                c = "wmctrl -x -a "+window_name
                subprocess.run(c.split())
            else:
                # Если нет - запускаем программу заново
                print('Window not found. We will run program "%s" again.' % prog_exec)
                subprocess.run(prog_exec)

    def close(self,  *args):
        print('Close active window')
        c = '''wmctrl -c :ACTIVE:'''.split()
        subprocess.run(c)

    # def minimize(self,  *args):
    #     print('Minimize active window')
    #     c = '''wmctrl -c :ACTIVE:'''.split()
    #     subprocess.run(c)

    def __init__(self):
        # Выполняем оригинальный вызов инициации
        super().__init__()

        self.functions.add('raise', 'Raise window or run app. Parameters: COMMAND WINDOW_NAME', self.raise_or_run)
        self.functions.add('close', 'Close active window', self.close)
        # self.functions.add('minimize', 'Minimize active window', self.minimize)
        # self.functions.print()

# Начальная инициализация класса, чтобы сработало при импорте
# gnome = Gnome()
# plugin = Plugin()
