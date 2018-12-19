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
        args='%s' % args
        res = c.split()
        res.append(args)
        return res

    def window_is_present(self, name):
        s = "global.get_window_actors().filter(w => w.get_meta_window().get_wm_class().toLowerCase().includes('%s'.toLowerCase()))[0];" % name
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

    def minimize(self):
        return self.command('global.display.focus_window.minimize();')

    def close(self):
        return self.command('global.display.focus_window.delete(global.get_current_time());')

    def list_all(self):
        return self.command('global.get_window_actors().map(w => [w.toString(), w.get_meta_window().get_wm_class()]);')




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
            c = self.active_window.lg.window_is_present(window_name)
            # print('c=%s' % c)
            stdoutdata = subprocess.check_output(c)
            # Если есть - активируем его
            if stdoutdata:
                # print('We have LG output on search "%s" window: %s' % (window_name,stdoutdata))
                c = self.active_window.lg.activate_window(window_name)
                subprocess.run(c)
            else:
                # Если нет - запускаем программу заново
                print('Window not found. We will run program "%s" again.' % prog_exec)
                subprocess.run(prog_exec)

    def hibernate(self,  *args):
        print('Hibernate')
        c = '''dbus-send --system --print-reply \
            --dest="org.freedesktop.UPower" \
            /org/freedesktop/UPower \
            org.freedesktop.UPower.Hibernate'''.split()
        subprocess.run(c)

    def suspend(self,  *args):
        print('Suspend')
        c = '''dbus-send --system --print-reply \
            --dest="org.freedesktop.UPower" \
            /org/freedesktop/UPower \
            org.freedesktop.UPower.Suspend'''.split()
        subprocess.run(c)

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
        self.functions.add('suspend', 'Suspend PC Gnome-friendly way',
                           self.suspend)
        self.functions.add('hibernate', 'Hibernate PC Gnome-friendly way',
                           self.hibernate)

        # self.functions.print()

# Начальная инициализация класса, чтобы сработало при импорте
# gnome = Gnome()
# plugin = Plugin()
