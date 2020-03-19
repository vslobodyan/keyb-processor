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

    def get_id_of_windows(self, window_name, window_title=None, get_all=False):
        # Получаем список всех открытых окон
        c = "wmctrl -lx"
        stdoutdata = subprocess.check_output(c.split())
        str_outdata = stdoutdata.decode()
        print('str_outdata: %s' % str_outdata)
        ids = []

        if window_name in str_outdata:
            # Окно (возможно) уже запущено. Ищем совпадение по вхождению указанного класса и заголовка
            print('In wmctrl window list output we have something like "%s"' % window_name)
            for line in str_outdata.splitlines():
                line_columns = line.split()
                # print('line_columns=%s' % line_columns)
                line_wmclass = line_columns[2]
                line_wmtitle = " ".join(line_columns[4:])
                # print('line_wmclass="%s", line_wmtitle="%s"' % (line_wmclass,line_wmtitle))
                if window_name.lower() in line_wmclass.lower():
                    print('window_name found in line "%s"' % line)
                    if window_title:
                        print('Searching window title "%s" in "%s"' % (window_title, line_wmtitle))
                        if window_title.lower() in line_wmtitle.lower():
                            print(' Title was found. We found exact window.')
                        else:
                            print(' Win title not matching. Continue searching..')
                            continue
                    win_id = line.split()[0]
                    print('win_id: %s' % win_id)
                    ids.append(win_id)
                    if not get_all:
                        break
        return ids

    def raise_or_run(self, *args, raise_all=False):
        print('Raise or run: %s (all=%s)' % (args, raise_all))
        # Разбираем аргументы
        # print('len(locals()=%s' % len(locals()))
        if len(locals())<2:
            print('Not enough arguments for run or raise! (must be 2, get %s)' % len(locals()))
        else:
            prog_exec = args[0][0]
            print('prog_exec=%s' % prog_exec)
            window_name = args[0][1]
            window_title = " ".join(args[0][2:])
            print('window_name=%s, window_title=%s' % (window_name, window_title))
            # Получаем id нужных окон
            win_ids = self.get_id_of_windows(window_name, window_title, raise_all)
            if win_ids:
                print('Окна найдены. Поднимаем их.')
                for win_id in win_ids:
                    print('win_id: %s' % win_id)
                    c = "wmctrl -ia %s" % win_id
                    print('wmctrl command: %s' % c)
                    subprocess.run(c.split())
            else:
                print('Окна не найдены. Запускаем указанную команду.')
                self.exec_detached(prog_exec)

            # # Проверяем, есть-ли уже такое окно
            # # Получаем список всех открытых окон
            # c = "wmctrl -lx"
            # stdoutdata = subprocess.check_output(c.split())
            # str_outdata = stdoutdata.decode()
            # # Если есть - активируем его
            # print('str_outdata: %s' % str_outdata)
            #
            # window_was_found = False
            #
            # if window_name in str_outdata:
            #     # Окно (возможно) уже запущено. Надо на него переключиться
            #     if raise_all:
            #         print('We found win(s) "%s" and we raise all windows with same name now.' % window_name)
            #         # print('We have LG output on search "%s" window: %s' % (window_name,stdoutdata))
            #         for line in str_outdata.splitlines():
            #             line_columns = line.split()
            #             # print('line_columns=%s' % line_columns)
            #             line_wmclass = line_columns[2]
            #             line_wmtitle = " ".join(line_columns[4:])
            #             # print('line_wmclass="%s", line_wmtitle="%s"' % (line_wmclass,line_wmtitle))
            #             if window_name in line_wmclass:
            #                 print('Line found: %s' % line)
            #                 if window_title:
            #                     print('Searching title "%s" in "%s"' % (window_title, line_wmtitle))
            #                     if window_title in line_wmtitle:
            #                         print(' Title was found. Raise this window.')
            #                     else:
            #                         print(' Win title not matching. Continue searching..')
            #                         continue
            #                 win_id = line.split()[0]
            #                 print('win_id: %s' % win_id)
            #                 c="wmctrl -ia %s" % win_id
            #                 print('wmctrl command: %s' % c)
            #                 window_was_found = True
            #                 subprocess.run(c.split())
            #     else:
            #         if window_title:
            #             print('We found win "%s" and we raise first window with that class and title contains "%s" now.' % (window_name,window_title))
            #             # c = "wmctrl -x -a " + window_name
            #             c = 'wmctrl -a %s -r %s' % (window_name, window_title)
            #         else:
            #             print('We found win "%s" and we raise first window with same name now.' % window_name)
            #             c = "wmctrl -x -a "+window_name
            #         print('wmctrl command: %s' % c)
            #         subprocess.run(c.split())
            #
            #         window_was_found = True
            # #else:
            # if not window_was_found:
            #     # Если нет - запускаем программу заново
            #     print('Window not found. We will run program "%s" again.' % prog_exec)
            #     # subprocess.run(prog_exec)
            #     # Запускаем как отдельный независимый процесс, и не ждем завершения выполнения.
            #     self.exec_detached(prog_exec)


    def raise_all_or_run(self, *args):
        self.raise_or_run(*args, raise_all=True)

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

        self.functions.add('raise',
                           'Raise first window with defined name or run app. Parameters: COMMAND WINDOW_NAME',
                           self.raise_or_run)
        self.functions.add('raise_all',
                           'Raise all windows with defined name or run app. Parameters: COMMAND WINDOW_NAME',
                           self.raise_all_or_run)
        self.functions.add('close', 'Close active window', self.close)
        # self.functions.add('minimize', 'Minimize active window', self.minimize)
        # self.functions.print()

# Начальная инициализация класса, чтобы сработало при импорте
# gnome = Gnome()
# plugin = Plugin()
