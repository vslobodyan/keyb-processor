"""
Работа на основе Gnome Looking Glass


Based on:

1. https://github.com/adrienverge/gnome-magic-window
2. https://github.com/CZ-NIC/run-or-raise
3. https://wiki.gnome.org/Projects/GnomeShell/LookingGlass
4. https://askubuntu.com/questions/91938/how-can-one-invoke-lg-looking-glass-from-a-command-line


The Activites Overview can be activated by:
dbus-send --session --type=method_call --dest=org.gnome.Shell /org/gnome/Shell org.gnome.Shell.Eval string:'Main.overview.toggle();'

Activate the app drawer:
gdbus call -e -d org.gnome.Shell -o /org/gnome/Shell -m org.gnome.Shell.ShowApplications

Надо переписать функции работы с GLG на вот эти:
https://github.com/adrienverge/gnome-magic-window/blob/master/gnome-magic-window
Может быть, они не падают при фильтрации окон.

сделать проверки (и is_window_backed() в том числе) как в этой функции
https://gitlab.gnome.org/GNOME/gnome-shell/blob/master/js/ui/lookingGlass.js#L308


"""

import subprocess

from plugins.base import plugin


class LG_Command:
    """Обертка для команд Gnome Looking Glass"""

    def command(self, args):
        """Оборачиваем аргументы в кавычки и добавляем к массиву основной команды"""
        c = 'gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval'
        args='%s' % args
        res = c.split()
        res.append(args)
        return res

    def window_is_present(self, name):
        s = '"global.get_window_actors().filter(w => w.get_meta_window().get_wm_class().toLowerCase().includes(\'%s\'.toLowerCase()))[0];"' % name
        return self.command(s)

    def activate_window(self, name):
        s = """const Main = imports.ui.main;
                const window = global.get_window_actors()
                   .filter(w => w.get_meta_window()
                   .get_wm_class().toLowerCase()
                   .includes('%s'.toLowerCase()))[0];
                if (window) {
                    Main.activateWindow(window.get_meta_window());
                }""" % name
        return self.command(s)


    def set_active_window(self, id):
        s = """
            const Main = imports.ui.main;
            const window = global.get_window_actors()
                   .filter(w => w.toString() === "%s")[0];
            if (window) {
                Main.activateWindow(window.get_meta_window());
            }
            """ % id
        return self.command(s)


    def minimize(self):
        return self.command('global.display.focus_window.minimize();')

    def close(self):
        return self.command('global.display.focus_window.delete(global.get_current_time());')

    def list_all(self):
        return self.command('"global.get_window_actors().map(w => [w.toString(), w.get_meta_window().get_wm_class()]);"')



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
        # print('LG %s' % c)
        subprocess.run(c)

    def minimize(self, *args):
        print('Minimize active window.')
        c = self.lg.minimize()
        # print('LG %s' % c)
        subprocess.run(c)

    def __init__(self):
        self.lg = LG_Command()


class Plugin(plugin.Plugin):
    name='gnome'
    description = 'Useful commands for gnome windows and apps.'
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
            # c = self.active_window.lg.window_is_present(window_name)

            c = self.active_window.lg.list_all()
            string_command = ' '.join(c)
            print('Получаем все открытые окна, c=%s' % string_command)
            # print('Проверяем, есть-ли уже такое окно, c=%s' % string_command)
            # print('Пробуем сразу активировать данное окно, c=%s' % string_command)
            # stdoutdata = subprocess.check_output(c)
            stdoutdata = subprocess.getoutput(string_command)
            print('stdoutdata = %s' % stdoutdata)

            output = stdoutdata
            output_r = output.rfind("'")
            output_l = output.find("'")+1
            print('output_r:', output_r)
            print('output_l:', output_l)

            # output = output[output_l,output_r]
            # print('output[output_l,output_r]: ', output[output_l:output_r])

            windows_output = output[output_l:output_r].lstrip('[[').rstrip(']]')
            print('windows_output=%s' % windows_output)


            window_id = None

            # import ast
            # testarray = ast.literal_eval(windows_output)
            windows_array = windows_output.split('],[')
            for win in windows_array:
                print('win: %s' % win)
                win_id,win_class = win.split(',')
                win_id = win_id.lstrip('"').rstrip('"')
                win_class = win_class.lstrip('"').rstrip('"')
                print('win_id:%s,win_class:%s.' % (win_id,win_class))
                if window_name.lower() in win_class.lower():
                    print('Окно найдено. ID: %s' % win_id)
                    window_id = win_id
                    break

            # print('windows_array: %s' % windows_array)

            # second_value = output[1].rstrip(')').lstrip(' ')
            # print('second_value=%s' % second_value)

            # window_name

            # Если есть - активируем его
            # if second_value == "''":
            if window_id:
                # print('We have LG output on search "%s" window: %s' % (window_name,stdoutdata))
                # c = self.active_window.lg.activate_window(window_name)
                c = self.active_window.lg.set_active_window(window_id)
                print('c: %s' % c)
                subprocess.run(c)
            else:
                # Если нет - запускаем программу заново
                print('Window not found. We will run program "%s" again.' % prog_exec)
                # subprocess.run(prog_exec)
                # Запускаем как отдельный независимый процесс, и не ждем завершения выполнения.
                self.exec_detached(prog_exec)

    # def hibernate(self,  *args):
    #     print('Hibernate')
    #     c = '''dbus-send --system --print-reply \
    #         --dest="org.freedesktop.UPower" \
    #         /org/freedesktop/UPower \
    #         org.freedesktop.UPower.Hibernate'''.split()
    #     subprocess.run(c)
    #
    # def suspend(self,  *args):
    #     print('Suspend')
    #     c = '''dbus-send --system --print-reply \
    #         --dest="org.freedesktop.UPower" \
    #         /org/freedesktop/UPower \
    #         org.freedesktop.UPower.Suspend'''.split()
    #     subprocess.run(c)

    def lock(self,  *args):
        print('Lock')
        c = '''dbus-send --type=method_call --dest=org.gnome.ScreenSaver \
                /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock'''.split()
        subprocess.run(c)


    def __init__(self):
        # print('Initiate "gnome" plugin.')
        # Выполняем оригинальный вызов инициации
        super().__init__()

        self.active_window = Active_window()

        self.functions.add('raise', 'Raise window or run app. Parameters: COMMAND WINDOW_NAME (check name in "lg")', self.raise_or_run)
        self.functions.add('close', 'Close active window', self.active_window.close)
        self.functions.add('minimize', 'Minimize active window', self.active_window.minimize)

        self.functions.add('lock', 'Lock screen', self.lock)

        # self.functions.add('suspend', 'Suspend PC Gnome-friendly way',
        #                    self.suspend)
        # self.functions.add('hibernate', 'Hibernate PC Gnome-friendly way',
        #                    self.hibernate)

        # self.functions.print()

# Начальная инициализация класса, чтобы сработало при импорте
# gnome = Gnome()
# plugin = Plugin()
