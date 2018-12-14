
'''
For correct work need modules:
1. python-evdev
2. python-yaml
'''

import evdev
from evdev import InputDevice, categorize, ecodes, UInput
import yaml
import argparse

'''Based on:
 1. https://python-evdev.readthedocs.io/en/latest/tutorial.html
 2. https://stackoverflow.com/questions/19732978/how-can-i-get-a-string-from-hid-device-in-python-with-evdev
 3. https://martin-thoma.com/configuration-files-in-python/
 4. https://stackoverflow.com/questions/22368458/how-to-make-argparse-print-usage-when-no-option-is-given-to-the-code/22368785
'''

keyboards = []


class process:
    'Обвязка функций, выполняемых при обработке событий'

    def retranslate(self, ui, event_type, event_scancode, event_keystate):
    # If we decide to inject keyboard event:
        ui.write(event_type, event_scancode, event_keystate)
        ui.syn()

    def keyb_event_inject(keyb_inputs, ui):
        print('We will inject keyb codes now: %s' % keyb_inputs)
        # Press
        for one_key_code in keyb_inputs:
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            key = evdev.ecodes.ecodes[one_key_code]
            ui.write(evdev.ecodes.EV_KEY, key, 1)
        ui.syn()
        # Release
        for one_key_code in keyb_inputs:
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            key = evdev.ecodes.ecodes[one_key_code]
            ui.write(evdev.ecodes.EV_KEY, key, 0)
        ui.syn()





class _processed_events:
    listen_events = []
    processed_events_setup = []

    class _processed_keyb_event:
        pressed_keys = []
        retranslate = True
        inject_keys = []
        run_command = []

        def __init__(self):
            self.pressed_keys = []
            self.retranslate = True
            self.inject_keys = []
            self.run_command = []

    def keys_as_string(self, keys=[]):
        # Сортируем отслеживаемые ключи и делаем из них строчку, по типу уникального читаемого ключа
        keys = sorted(keys)
        return ' '.join(keys)

    def find_strkey(self, verbose_active_keys):
        'Ищем быстрое вхождение в массив ключей событий'
        # Преобразуем полученные активные ключи в читабельный формат
        active_keys_str = []
        for verbose_key in verbose_active_keys:
            key = verbose_key[0]
            # print('key: %s ' % key)
            active_keys_str.append(key)
        strkey = self.keys_as_string(active_keys_str)
        # print('We find %s in %s' % (active_keys_str, self.listen_events))
        if strkey in self.listen_events:
            return strkey
        else:
            return False

    def clear(self):
        'Очищаем массивы отслеживаемых событий и массив ключей событий для быстрого поиска'
        self.listen_events = []
        self.processed_events_setup = []

    def add(self, pressed_keys='', retranslate=False, inject_keys='', run_command=''):
        # print('Add pressed_keys:', pressed_keys, 'retranslate:', retranslate,
        #       'inject_keys:', inject_keys, 'run_command:', run_command)

        # 1. Сортируем отслеживаемые ключи и делаем из них строчку, по типу уникального читаемого ключа
        pressed_keys_string = self.keys_as_string(pressed_keys.split())
        # print('pressed_keys_string: %s' % pressed_keys_string)
        # 2. Добавляем ключи в список отслеживаемых
        self.listen_events.append(pressed_keys_string)

        # print('self.listen_events: %s' % self.listen_events)

        # 3. Делаем класс обработки события и добавляем в массив обрабатываемых событий
        ev = self._processed_keyb_event()
        if inject_keys:
            ev.inject_keys = inject_keys.split()
            # print('ev.inject_keys: %s' % ev.inject_keys)
        ev.pressed_keys = pressed_keys_string  # Тут добавляем отсортированную строку по ключам
        # print('ev.pressed_keys: %s' % ev.pressed_keys)

        ev.retranslate = retranslate
        if run_command:
            ev.run_command = run_command.split()
        self.processed_events_setup.append(ev)
        # print('self.processed_events_setup: %s' % self.processed_events_setup)



    def proccess_event(self, strkey, ui, event_type, event_scancode, event_keystate):
        'Обрабатываем событие, которое ранее было найдено в списке ключей'
        print('We proccess "%s" event' % strkey)
        # Получаем событие из настроек
        found = False
        for event_setup in self.processed_events_setup:
            if event_setup.pressed_keys == strkey:
                # print('Found')
                found = True
                break
        if not found:
            return
        # print(event_setup)
        # Получен конфиг обработки текущего события
        if event_setup.retranslate:
            process.retranslate(ui, event_type, event_scancode, event_keystate)
        if event_setup.inject_keys:
            # print('We will inject keys: %s' % event_setup.inject_keys)
            process.keyb_event_inject(event_setup.inject_keys, ui)

        if event_setup.run_command:
            print('We will run command: %s' % event_setup.run_command)


    def __init__(self):
        self.listen_events = []
        self.processed_events_setup = []


class keyboard:
    name = ''
    address = ''
    retranslate_all = True
    dev = None
    processed_events = None

    def print_setup(self):
        # Печать текущих настроек в отладочных целях
        print()
        print('Config for "%s":' %
              self.name)
        print(' address: %s' % self.address)
        print(' retranslate_all: %s' % self.retranslate_all)
        print(' dev: %s' % self.dev)
        print(' listen_events: %s' % self.processed_events.listen_events)
        # print('processed_events_setup: %s' %
        #       self.processed_events.processed_events_setup)

    def __init__(self, name=name, address=address, retranslate_all=True):
        self.name = name
        self.address = address
        self.retranslate_all = retranslate_all
        self.processed_events = _processed_events()
        self.dev = InputDevice(address)

    # def set_processed_events(self, events):
    #     pass



def load_config(filename, keyboards=keyboards):
    with open(filename, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    for section in cfg:
        # print(section)
        keyboard_name = section
        for key in cfg[section]:
            value = cfg[section][key]
            # print('# key:', key, ', # value:',value)

            if key == 'device':
                device = value
                # We has name and device. Now initialize new
                # keyboard class:
                # new_keyboard.clear()
                new_keyboard = keyboard(keyboard_name, device)
            else:
                # Here is new keyboard event for handle
                pressed_keys = key
                # print('Found pressed_keys:', pressed_keys)
                inject_keys = None
                retranslate = False
                run_command = None
                if 'inject_keys' in value:
                    inject_keys = value['inject_keys']
                    # print('Found inject_keys:', inject_keys)
                if 'retranslate' in value:
                    retranslate = value['retranslate']
                    # print('Found retranslate:', retranslate)
                if 'run_command' in value:
                    run_command = value['run_command']
                    # print('Found run_command:', run_command)
                new_keyboard.processed_events.add(
                    pressed_keys=pressed_keys,
                    inject_keys=inject_keys,
                    retranslate=retranslate,
                    run_command=run_command
                )
        keyboards.append(new_keyboard)


    print('Config load successfully.')

    for keyb in keyboards:
        keyb.print_setup()



def grab_dev(keyboards):
    ui = UInput()

    home_keyb.print_setup()

    home_keyb.dev.grab()

    print('You can press keys to see it codes:')
    for event in home_keyb.dev.read_loop():
        event_handled = False
        if event.type == ecodes.EV_KEY:
            cur_event_data = categorize(event)
            # cur_active_keys = dev.active_keys()
            if cur_event_data.keystate in [1, 2]:  # Down and Hold events only
                # print('You Pressed the %s key, and currently active keys is: %s' % (cur_event_data.keycode, home_keyb.dev.active_keys(verbose=True) ) )

                strkey = home_keyb.processed_events.find_strkey(
                    home_keyb.dev.active_keys(verbose=True))
                if strkey:
                    event_handled = True
                    home_keyb.processed_events.proccess_event(strkey,
                                                              ui,
                                                              event.type,
                                                              cur_event_data.scancode,
                                                              cur_event_data.keystate)
                    # print('Found!')

                # В целях безопасности выходим при нажатии клавиш C или Q
                # Потом надо закомментировать, иначе скрипт будет регулярно отключаться
                # при наборе текста в других окнах.
                if cur_event_data.scancode in [ecodes.KEY_Q, ecodes.KEY_C]:
                    print('You press Q or C, and we quit now.')
                    break
            # print('cur_event_data: %s' % cur_event_data)
            # Here we decide - whether to skip the event further (whether to do inject)

            # Если событие не было из списка отлавливаемых, то возможно надо
            # ретранслировать это событие дальше, в зависимости от настроек
            # клавиатуры.
            if not event_handled:
                if home_keyb.retranslate_all:
                    # We decide to inject keyboard event:
                    ui.write(event.type,
                             cur_event_data.scancode,
                             cur_event_data.keystate)
                    ui.syn()

    home_keyb.dev.ungrab()
    ui.close()



def main():

    # Another way:
    #
    # import sys
    # parser = ...
    # if len(sys.argv[1:]) == 0:
    #     parser.print_help()
    #     # parser.print_usage() # for just the usage line
    #     parser.exit()
    # args = parser.parse_args()
    #

    parser = argparse.ArgumentParser(description="Long decription about program.")
    parser.add_argument("--config", type=str, help="Load config file")
    parser.add_argument("--grab", type=str,
                        help="Grab all events by defining keyboard, and show input codes. "
                             "Except C and Q keys, preserved for quit action. "
                             "Example: --grab /dev/input/eventXX")
    args = parser.parse_args()
    if args.config:
        print('Load config: %s' % args.config)
        # load_config("config_home.yml", keyboards)
        # grab_dev
    elif args.grab:
        print('Grab all events and show input keys for: %s' % args.grab)
        print('You can exit anytime by pressing Q or C.')
        # grab_dev
    else:
        print(parser.print_help())


if __name__ == '__main__':
    main()



