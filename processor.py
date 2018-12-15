
"""
For correct work need modules:
1. python-evdev
2. python-yaml

Were helpful:
 1. https://python-evdev.readthedocs.io/en/latest/tutorial.html
 2. https://stackoverflow.com/questions/19732978/how-can-i-get-a-string-from-hid-device-in-python-with-evdev
 3. https://martin-thoma.com/configuration-files-in-python/
 4. https://stackoverflow.com/questions/22368458/how-to-make-argparse-print-usage-when-no-option-is-given-to-the-code/22368785
 5. https://asyncio.readthedocs.io/en/latest/tcp_echo.html
 6. https://stackoverflow.com/questions/31623194/asyncio-two-loops-for-different-i-o-tasks

"""

import evdev
from evdev import InputDevice, categorize, ecodes, UInput
import yaml
import argparse
import asyncio
import json

from settings import settings
from plugins import Plugins


keyboards = []

class asyn:
    loop = None

class active_modifiers:
    # Класс текущих модификаторов со всех клавиатур
    # Нужен для использования кросс-девайсных комбинаций.
    # Например: Alt на клавиатуре и кнопка G10 на мышке
    alt = False
    ctrl = False
    meta = False
    shift = False

    alts = [ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT]
    ctrls = [ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL]
    metas = [ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA]
    shifts = [ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT]

    def get(self):
        # Получаем массив текущих модификаторов для добавления в массив
        # событий для сравнения с отслеживаемыми переменными.
        pass

    def find_mods_and_change_state(self, scancode, state=True):
        if scancode in self.alts: self.alt = state
        if scancode in self.ctrls: self.ctrl = state
        if scancode in self.metas: self.meta = state
        if scancode in self.shifts: self.shift = state

    def update(self, cur_event_data):
        # Обновляем статусы модификаторов на основе текущего события
        if cur_event_data.keystate in [1, 2]:
            # Клавиша нажата или продолжает нажиматься
            self.find_mods_and_change_state(cur_event_data.scancode, state=True)
        else:
            # Клавиша отпущена
            self.find_mods_and_change_state(cur_event_data.scancode, state=False)


async def tcp_echo_client(message, loop):
    """Функция передачи команды на приемник в клиентской части системы."""
    reader, writer = await asyncio.open_connection(settings.host, settings.port,
                                                   loop=loop)
    print('Send to executioner: %r' % message)
    writer.write(message.encode())

    data = await reader.read(100)
    print('Received: %r' % data.decode())

    print('Close the socket')
    writer.close()


class process():
    """Обвязка функций, выполняемых при обработке событий."""

    def retranslate(ui, event_type, event_scancode, event_keystate):
    # If we decide to inject keyboard event:
        ui.write(event_type, event_scancode, event_keystate)
        # ui.syn()

    def keyb_event_inject(keyb_inputs, ui):
        print('We will inject keyb codes now: %s' % keyb_inputs)
        # Press
        for one_key_code in keyb_inputs:
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            key = evdev.ecodes.ecodes[one_key_code]
            ui.write(evdev.ecodes.EV_KEY, key, 1)
        # ui.syn()
        # Release
        for one_key_code in keyb_inputs:
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            key = evdev.ecodes.ecodes[one_key_code]
            ui.write(evdev.ecodes.EV_KEY, key, 0)
        # ui.syn()

    def send_command(command, plugin=None):
        # command = ["ls", "-l"]
        print('Prepare to send command: %s under plugin: %s' % (command, plugin))
        message_dict = {'key': settings.key,
                        'plugin': plugin,
                        'command': command,
                        }
        # if plugin:
        #     message_dict['plugin'] = plugin
        # serialized_dict = json.dumps(a_dict)
        message = json.dumps(message_dict)
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(tcp_echo_client(message, loop))
        # loop.close()
        # print('message: %s' % message)
        asyn.loop.create_task(tcp_echo_client(message, asyn.loop))



class _processed_events:
    """Класс обрабатываемых событий."""
    listen_events = []
    processed_events_setup = []

    class _processed_keyb_event:
        pressed_keys = []
        retranslate = True
        inject_keys = []
        plugin = None
        command = []

        def __init__(self):
            self.pressed_keys = []
            self.retranslate = True
            self.inject_keys = []
            self.plugin = None
            self.command = []

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

    def add(self, pressed_keys='', retranslate=False, inject_keys='', plugin=None, command=''):
        # print('Add pressed_keys:', pressed_keys, 'retranslate:', retranslate,
        #       'inject_keys:', inject_keys, 'plugin:', plugin, 'command:', command)

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
        ev.plugin = plugin
        if command:
            ev.command = command.split()
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

        if event_setup.command:
            # print('We will run command: %s' % event_setup.command)
            # try:
            process.send_command(event_setup.command, event_setup.plugin)
            # except Exception as ex:
            #     print('Что-то пошло не так:', ex)


    def __init__(self):
        self.listen_events = []
        self.processed_events_setup = []


class keyboard:
    """Одиночный класс клавиатуры с конфигом."""
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
        print()

    def __init__(self, name=name, address=address, retranslate_all=True):
        self.name = name
        self.address = address
        self.retranslate_all = retranslate_all
        self.processed_events = _processed_events()
        self.dev = InputDevice(address)

    # def set_processed_events(self, events):
    #     pass



def load_config(filename):
    """Загрузка конфига и создание нужных классов для захватываемых
    устройств.
    """
    keyboards = [] # Начальная очистка списка клавиатур
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
                command = None
                if 'inject_keys' in value:
                    inject_keys = value['inject_keys']
                    # print('Found inject_keys:', inject_keys)
                if 'retranslate' in value:
                    retranslate = value['retranslate']
                    # print('Found retranslate:', retranslate)
                if 'plugin' in value:
                    plugin = value['plugin']
                if 'command' in value:
                    command = value['command']
                    # print('Found command:', command)
                new_keyboard.processed_events.add(
                    pressed_keys=pressed_keys,
                    inject_keys=inject_keys,
                    retranslate=retranslate,
                    plugin=plugin,
                    command=command
                )
        keyboards.append(new_keyboard)


    print('Config load successfully.')

    for keyb in keyboards:
        keyb.print_setup()

    return keyboards


def show_dev_list():
    """Выводим список доступных устройств."""
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print(device.path, device.name, device.phys)


def grab_and_show_inputs(dev_addr):
    """Захватываем устройство и выводим в консоль все события его кнопок.
    Если нажаты Q или C - выходим.
    """
    dev = InputDevice(dev_addr)
    print(dev)
    dev.grab()
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            cur_event_data = categorize(event)
            print(cur_event_data)
            if cur_event_data.keystate in [1, 2]:  # Down and Hold events only
                if cur_event_data.scancode in [ecodes.KEY_Q, ecodes.KEY_C]:
                    print('You press Q or C, and we quit now.')
                    break
    dev.ungrab()




def process_one_event_and_exit(keyboard, ui, event):
    event_handled = False
    if event.type == ecodes.EV_KEY:
        cur_event_data = categorize(event)
        # cur_active_keys = dev.active_keys()
        if cur_event_data.keystate in [1, 2]:  # Down and Hold events only
            print('You Pressed the %s key, and currently active keys is: %s' % (
            cur_event_data.keycode, keyboard.dev.active_keys(verbose=True)))
            # if cur_event_data.scancode in [ecodes.KEY_Q, ecodes.KEY_C]:
            #     print('You press Q or C, and we quit now.')
            #     return True

            strkey = keyboard.processed_events.find_strkey(
                keyboard.dev.active_keys(verbose=True))
            if strkey:
                # print('Found!')
                # return False

                event_handled = True
                keyboard.processed_events.proccess_event(strkey,
                                                         ui,
                                                         event.type,
                                                         cur_event_data.scancode,
                                                         cur_event_data.keystate)

        # Here we decide - whether to skip the event further (whether to do inject)

        # Если событие не было из списка отлавливаемых, то возможно надо
        # ретранслировать это событие дальше, в зависимости от настроек
        # клавиатуры.
        if not event_handled:
            if keyboard.retranslate_all:
                # We decide to inject keyboard event:
                ui.write(event.type,
                         cur_event_data.scancode,
                         cur_event_data.keystate)
                # ui.syn()
    return False


def grab_and_process_keyboards(keyboards):
    """Основная функция захвата и обработки клавиатурных событий."""
    # print('Keyboards for grab and process:')
    # for keyb in keyboards:
    #     print(' - %s' % keyb.name)

    ui = UInput()

    async def proccess_events(keyboard):
        # Асинхронная функция обработки событий
        async for event in keyboard.dev.async_read_loop():

            # print(keyboard.dev.path, evdev.categorize(event), sep=': ')

            exit_now = process_one_event_and_exit(keyboard, ui, event)
            # После обработки события происходит синхронизация ввода.
            # Возможно, уже записаны новые коды ввода:
            # новая комбинация или просто ретрансляция вводимого.
            ui.syn()
            if exit_now:
                exit()


    for keyboard in keyboards:
        keyboard.dev.grab()
        asyncio.ensure_future(proccess_events(keyboard))

    asyn.loop = asyncio.get_event_loop()
    asyn.loop.run_forever()

    for keyboard in keyboards:
        # keyboard.dev.ungrab()
        pass

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

    parser = argparse.ArgumentParser(description="Warning: most function need sudo! "
                                                 "Long decription about program.")

    parser.add_argument("-i", "--install", action="store_true", help="Install parent script to system")

    parser.add_argument("-c", "--config", type=str, help="Load config file")

    parser.add_argument("-l", "--list", action="store_true", help="Show list of available devices.")

    parser.add_argument("-p", "--plugins", action="store_true", help="List of plugins and their available functions.")


    parser.add_argument("-e", "--exec", action="store_true", help="Run local executor service. Will execute commands from userspace.")

    parser.add_argument("-g", "--grab", type=str,
                        help="Grab all events by defining keyboard, and show input codes. "
                             "Except C and Q keys, preserved for quit action. "
                             "Example: --grab /dev/input/eventXX")
    args = parser.parse_args()
    if args.config:
        print('Load config: %s' % args.config)
        keyboards = load_config(args.config)
        # print('keyboards: %s' % keyboards)
        grab_and_process_keyboards(keyboards)
    elif args.list:
        print('Show list of available devices.')
        show_dev_list()
    elif args.plugins:
        plugins = Plugins()
    elif args.grab:
        print('Grab all events and show input keys for %s device.' % args.grab)
        print('You can exit anytime by pressing Q or C.')
        dev_addr = args.grab
        grab_and_show_inputs(dev_addr)
    else:
        print(parser.print_help())
        plugins = Plugins()


if __name__ == '__main__':
    main()



