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


class active_window:
    def get(self):
        pass

    def set(self):
        pass

    def close(self):
        pass

    def minimize(self):
        pass


class gnome:
    name='gnome'

    def raise_or_run(self, command):
        pass

    def process_command(self, command):
        pass

