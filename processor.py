
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
import pyudev
from evdev import InputDevice, categorize, ecodes, UInput
import yaml
import argparse
import asyncio
import json
# import time
import os
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


from settings import settings
from plugins import Plugins




class app:
    ui = None
    keyboards = []
    devs_need_grab = []
    need_reload_config = False
    config_filename = None

# class asyn:
#     loop = None


class Active_modifiers:
    # Класс текущих модификаторов со всех клавиатур
    # Нужен для использования кросс-девайсных комбинаций.
    # Например: Alt на клавиатуре и кнопка G10 на мышке
    alt = False
    ctrl = False
    meta = False
    shift = False
    pressed = {}

    alts = [ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT]
    ctrls = [ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL]
    metas = [ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA]
    shifts = [ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT]
    _all = alts + ctrls + metas + shifts

    def get(self):
        # Получаем массив текущих модификаторов для добавления в массив
        # событий для сравнения с отслеживаемыми переменными.
        res = []
        if self.alt: res.append('ALT')
        if self.ctrl: res.append('CTRL')
        if self.meta: res.append('META')
        if self.shift: res.append('SHIFT')
        return res

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
            self.pressed[cur_event_data.scancode] = cur_event_data.keystate
        else:
            # Клавиша отпущена
            self.find_mods_and_change_state(cur_event_data.scancode, state=False)
            self.pressed.pop(cur_event_data.scancode, None)
        print('(after update) modifiers: alt %s, ctrl %s, meta %s, shift %s' % (self.alt, self.ctrl, self.meta, self.shift))
        print('(after update) pressed: %s' % self.pressed)


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

    # def transmit(ui, event_type, event_scancode, event_keystate):
    # # If we decide to inject keyboard event:
    #     ui.write(event_type, event_scancode, event_keystate)
    #     # ui.syn()

    def keyb_event_inject(grabbed_event_strkeys, keyb_inputs, ui):

        class My_event():
            keystate = 0
            scancode = 0

            def __init__(self, keystate=0, scancode=0):
                self.scancode = scancode
                self.keystate = keystate

        print('We will inject keyb codes now: %s' % keyb_inputs)
        # delay = 5/10000

        # if grabbed_event_strkeys:
        #     print('grabbed_event_strkeys[]: %s' % grabbed_event_strkeys.split())
        #     grabbed_keys = grabbed_event_strkeys.split()
        #     # Use reverse hack from https://stackoverflow.com/questions/5846004/unable-to-reverse-lists-in-python-getting-nonetype-as-list
        #     # instead of .reverse()
        #     grabbed_keys = grabbed_keys[::-1]
        #     # print('grabbed_keys after reverse(): %s' % grabbed_keys)
        #     print('Before this we need UP keys for this keyboard (reversed): %s' % grabbed_keys)
        #     for one_key in grabbed_keys:
        #         key = evdev.ecodes.ecodes[one_key]
        #
        #         print(' Force release %s' % key)
        #         ui.write(evdev.ecodes.EV_KEY, key, 0)
        #         if key in active_modifiers.pressed:
        #             my_event = My_event(keystate=0,scancode=key)
        #             active_modifiers.update(my_event)
        #             # active_modifiers.find_mods_and_change_state(key, False)
        #         # time.sleep(delay)
        #           await asyncio.sleep(1.0)

        if active_modifiers.pressed:
            print('Before this we need UP keys for global modifiers: %s' % active_modifiers.pressed)
            for one_key_code in active_modifiers.pressed:
                print(' Force release %s' % one_key_code)
                # state = active_modifiers.pressed[one_key_code]
                ui.write(evdev.ecodes.EV_KEY, one_key_code, 0)
                # Обновляем в статусе глобальных модификаторов, что данный модификатор больше не нажат
                my_event = My_event(keystate=0,scancode=one_key_code)
                # active_modifiers.find_mods_and_change_state(one_key_code, False)
                # time.sleep(delay)
                # await asyncio.sleep(1.0)
            # Обновляем статусы отжатых модификаторов
            for one_key_code in active_modifiers.pressed.copy():
                my_event = My_event(keystate=0, scancode=one_key_code)
                active_modifiers.update(my_event)

        # Press
        for one_key_code in keyb_inputs:
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            key = evdev.ecodes.ecodes[one_key_code]
            ui.write(evdev.ecodes.EV_KEY, key, 1)
            # time.sleep(delay)
            # await asyncio.sleep(1.0)
        # ui.syn()

        # Release
        for one_key_code in keyb_inputs:
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            key = evdev.ecodes.ecodes[one_key_code]
            ui.write(evdev.ecodes.EV_KEY, key, 0)
            # time.sleep(delay)
            # await asyncio.sleep(1.0)

        # print('Now we need DOWN keys for global modifiers: %s' % active_modifiers.pressed)
        # for one_key_code in active_modifiers.pressed:
        #     state = active_modifiers.pressed[one_key_code]
        #     ui.write(evdev.ecodes.EV_KEY, one_key_code, state)

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
        # asyn.loop.create_task(tcp_echo_client(message, asyn.loop))
        loop = asyncio.get_event_loop()
        loop.create_task(tcp_echo_client(message, loop))


class _processed_events:
    """Класс обрабатываемых событий."""
    listen_events = []
    processed_events_setup = []

    class _processed_keyb_event:
        pressed_keys = []
        # transmit = False
        inject_keys = []
        plugin = None
        command = []

        def __init__(self):
            self.pressed_keys = []
            # self.transmit = False
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
        # print('Получили строку для поиска ключей: %s' % strkey)
        # print('Массив слушаемых событий: %s' % self.listen_events)
        # print('We find %s in %s' % (active_keys_str, self.listen_events))
        if strkey in self.listen_events:
            return strkey
        else:
            return False

    def clear(self):
        'Очищаем массивы отслеживаемых событий и массив ключей событий для быстрого поиска'
        self.listen_events = []
        self.processed_events_setup = []

    def add(self, pressed_keys='', inject_keys='', plugin=None, command=''):
        # print('Add pressed_keys:', pressed_keys, 'transmit:', transmit,
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

        # ev.transmit = transmit
        ev.plugin = plugin
        if command:
            ev.command = command.split()
        self.processed_events_setup.append(ev)
        # print('self.processed_events_setup: %s' % self.processed_events_setup)



    def proccess_event(self, strkey, ui):
        'Обрабатываем событие, которое ранее было найдено в списке ключей'
        # Раньше использовались дополнительные параметры: , event_type, event_scancode, event_keystate
        print('We proccess "%s" event' % strkey)
        grabbed_event_strkeys = strkey
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
        if event_setup.inject_keys:
            # print('We will inject keys: %s' % event_setup.inject_keys)
            process.keyb_event_inject(grabbed_event_strkeys, event_setup.inject_keys, ui)

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
    dev_name = ''
    dev_type = ''
    transmit_all = True
    dev = None
    processed_events = None
    enabled = False

    def print_setup(self):
        # Печать текущих настроек в отладочных целях
        print()
        print('Config for "%s":' %
              self.name)
        print(' address: %s' % self.address)
        print(' transmit_all: %s' % self.transmit_all)
        print(' dev: %s' % self.dev)
        print(' listen_events: %s' % self.processed_events.listen_events)
        # print('processed_events_setup: %s' %
        #       self.processed_events.processed_events_setup)
        print()

    def __init__(self, name=name, dev_name=dev_name, dev_type=dev_type,transmit_all=True):
        #address=address,
        self.name = name
        # self.address = address
        self.dev_name = dev_name
        self.dev_type = dev_type
        self.transmit_all = transmit_all
        self.processed_events = _processed_events()
        # if address:
        #     # Устройство уже подключено
        #     self.dev = InputDevice(address)
        #     self.enabled = True
        # else:
        #     # Устройство возможно будет подключено позднее
        #     self.dev = None
        #     self.enabled = False

    # def set_processed_events(self, events):
    #     pass



class MyEventHandler(PatternMatchingEventHandler):
    def on_moved(self, event):
        super(MyEventHandler, self).on_moved(event)
        print("File %s was just moved" % event.src_path)
        app.need_reload_config = True

    def on_created(self, event):
        super(MyEventHandler, self).on_created(event)
        print("File %s was just created" % event.src_path)
        app.need_reload_config = True

    def on_deleted(self, event):
        super(MyEventHandler, self).on_deleted(event)
        print("File %s was just deleted" % event.src_path)
        app.need_reload_config = True

    def on_modified(self, event):
        super(MyEventHandler, self).on_modified(event)
        print("File %s was just modified" % event.src_path)
        app.need_reload_config = True


def start_config_change_observer(file_path):
    print('Start config change observer')
    watched_dir = os.path.split(file_path)[0]
    print('watched_dir = {watched_dir}'.format(watched_dir=watched_dir))
    patterns = [file_path]
    print('patterns = {patterns}'.format(patterns=', '.join(patterns)))
    event_handler = MyEventHandler(patterns=patterns)
    observer = Observer()
    observer.schedule(event_handler, watched_dir, recursive=True)
    observer.start()
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     observer.stop()
    # observer.join()



async def wait_for_reload_config():
    while True:
        if app.need_reload_config:
            print('Нужно перезагрузить конфиг')
            app.need_reload_config = False
            # load_config(app.config_filename, reload=True)
        await asyncio.sleep(0.3)



# def find_and_create_new_keyboard(keyboard_name, dev_name, dev_type):
#     # Поиск нужного устройства
#     device = ''
#     # print('Look for device:')
#     # print(' keyboard_name="%s"' % keyboard_name)
#     # print(' dev_name="%s"' % dev_name)
#     # print(' dev_type="%s"' % dev_type)
#
#     print('  Looking for device "%s" / %s' % (dev_name, dev_type))
#
#     raw_devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
#     devices = reversed(raw_devices)
#     # devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
#     # print(devices)
#     device = None
#     for dev in devices:
#         # print('dev: %s' % dev)
#         # print('compare "%s" and "%s"' % (dev_name, dev.name))
#         if dev_name == dev.name:
#             # print('Found name')
#             # Нашли устройство с нужным именем
#             capabilities = dev.capabilities(verbose=True)
#             _dev_type = get_dev_type(capabilities)
#             # print('_dev_type: %s' % _dev_type)
#             if dev_type in _dev_type:
#                 # Нашли нужное устройство с именем и нужным типом
#                 # print('Device was found: %s' % dev)
#                 device = dev.fn
#                 # print('Device was found as %s' % device)
#                 print('   found at %s' % device)
#                 break
#     new_keyboard = None
#     if device:
#         new_keyboard = keyboard(keyboard_name, device, dev_name, dev_type)
#     else:
#         # print('We cant find whese device!')
#         print('   device not found!')
#     if not device:
#         print('  Устройство не было найдено. Но конфиг загружен на будущее, и будет ждать подключения этого устройства.')
#     new_keyboard = keyboard(keyboard_name, device, dev_name, dev_type)
#
#     return new_keyboard





def load_config(filename, reload=False):
    """Загрузка конфига и создание нужных классов для захватываемых
    устройств.
    """
    # app.keyboards

    if not reload:
        # У нас первый запуск загрузки конфига. Запускаем отслеживание изменений файла
        start_config_change_observer(filename)

    cfg_keyboards = [] # Начальная очистка списка клавиатур из конфига
    with open(filename, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    for section in cfg:
        # print(section)
        keyboard_name = section
        dev_name = ''
        dev_type = ''
        keyboard_was_created = False

        for key in cfg[section]:
            value = cfg[section][key]
            # print('# key:', key, ', # value:',value)

            if key == 'device':
                pass
                # device = value
                # We has name and device. Now initialize new
                # keyboard class:
                # new_keyboard.clear()
                # new_keyboard = keyboard(keyboard_name, device)
                pass
            elif key == 'name':
                dev_name = value
            elif key == 'capabilities':
                dev_type = value
            else:
                if not keyboard_was_created:
                    # Создаем новую клавиатуру после того, как загружены все необходимые параметры
                    # new_keyboard = find_and_create_new_keyboard(keyboard_name, dev_name, dev_type)
                    new_keyboard = keyboard(keyboard_name, dev_name, dev_type)
                    keyboard_was_created = True
                    # if not new_keyboard:
                    #     # Клавиатуры не нашли. Выходим из обработки данной секции
                    #     break

                # Here is new keyboard event for handle
                pressed_keys = key
                # print('Found pressed_keys:', pressed_keys)
                inject_keys = None
                plugin = None
                command = None
                if 'inject_keys' in value:
                    inject_keys = value['inject_keys']
                    # print('Found inject_keys:', inject_keys)
                if 'plugin' in value:
                    plugin = value['plugin']
                if 'command' in value:
                    command = value['command']
                    # print('Found command:', command)
                new_keyboard.processed_events.add(
                    pressed_keys=pressed_keys,
                    inject_keys=inject_keys,
                    plugin=plugin,
                    command=command
                )
        if new_keyboard:
            cfg_keyboards.append(new_keyboard)


    print('Config load successfully.')

    for keyb in cfg_keyboards:
        keyb.print_setup()

    app.keyboards = cfg_keyboards



def get_dev_type(capabilities):
    """Определяем, к какому типу вероятно относится данное устройство.
    Возвращаем массив вида ['mouse', 'keyboard'] """

    ev_key=('EV_KEY', 1)
    ev_rel=('EV_REL', 2)
    key_esc=('KEY_ESC', 1)
    res = []

    if ev_rel in capabilities:
        # 'EV_REL' --> mouse
        res.append('mouse')
        # print('  (mouse)')
        # print('  capabilities look like MOUSE')
    if ev_key in capabilities and key_esc in capabilities[ev_key]:
        res.append('keyboard')
        # print('keys:', capabilities[ev_key])
        # and 'KEY_ESC' in capabilities[('EV_KEY', 1)]
        #   'BTN_MOUSE' / 'BTN_LEFT' --> mouse
        #   'KEY_ESC' --> keyboard
        # print('  (keyboard)')
        # print('  capabilities look like KEYBOARD')
    return res


def show_dev_list():
    """Выводим список доступных устройств."""
    raw_devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    devices = reversed(raw_devices)
    # devices = [evdev.InputDevice(path) for path in evdev.list_devices()]


    for device in devices:
        # print(' %s' % device)
        # Дальше получаем его capabilities
        capabilities = device.capabilities(verbose=True)
        # print('capabilities: %s' % capabilities)
        # for key in capabilities:
        #     print('  key', key)
            # for subkey in capabilities[key]:
            #     print('    subkey', subkey)
        dev_type = get_dev_type(capabilities)
        if not dev_type:
            str_type = ''
        else:
            str_type='(%s)' % ', '.join(dev_type)
        # print(device.path, device.name, device.phys)
        print(device.fn, '"%s" %s' % (device.name, str_type))



def grab_and_show_inputs(dev_addr):
    """Захватываем устройство и выводим в консоль все события его кнопок.
    Если нажаты Q или C - выходим.
    """
    dev = InputDevice(dev_addr)
    print(dev)
    print('Getting LED states:')
    print(dev.leds(verbose=True))
    print('Listing device capabilities:')
    capabilities = dev.capabilities(verbose=True)
    print(capabilities)
    print()
    print('Now press any key to see its code or Ctrl+Q / Ctrl+C to quit programm:')
    dev.grab()
    for event in dev.read_loop():
        cur_event_data = categorize(event)
        print(cur_event_data)
        # print(event)
        if event.type == ecodes.EV_KEY:
            cur_event_data = categorize(event)
            # print('cur_event_data: %s' % cur_event_data)
            if cur_event_data.keystate in [1, 2]:  # Down and Hold events only
                if cur_event_data.scancode in [ecodes.KEY_Q, ecodes.KEY_C]:
                    print('You press Q or C, and we quit now.')
                    break
    dev.ungrab()




def process_one_event_and_exit(keyboard, ui, event):
    event_handled = False
    # single_meta_press = False
    if event.type == ecodes.EV_KEY:
        cur_event_data = categorize(event)
        # cur_active_keys = dev.active_keys()
        # Переводим инфу о нажатых клавишах в понятный формат
        active_keys = keyboard.dev.active_keys()
        verbose_active_keys = keyboard.dev.active_keys(verbose=True)
        print()
        print('Событие: %s (активные клавиши: %s)' % (cur_event_data.keycode, verbose_active_keys))

        # Глотаем нажатия META-клавиши до нажатия другой значащей клавиши
        # if 'META' in cur_event_data.keycode and not verbose_active_keys and cur_event_data.keystate in [1, 2]:
        #     # single_meta_press = True
        #     print('Это просто нажатие META-клавиши. Его можно проглотить.')

        # # Проверяем, не избыточное ли отжатие модификатора это
        # if cur_event_data.scancode in active_modifiers._all and cur_event_data.keystate == 0:
        #     unreleased_mod = False
        #     all_active_mods = active_modifiers.get()
        #     print('all_active_mods: %s' % all_active_mods)
        #     print('cur_event_data.scancode: %s' % cur_event_data.scancode)
        #     print('cur_event_data.keycode: %s' % cur_event_data.keycode)
        #     for active_mod in all_active_mods:
        #         if active_mod in cur_event_data.keycode:
        #             unreleased_mod = True
        #     if not unreleased_mod:
        #         print('Нашли избыточное отжатие модификатора. Отбрасываем его.')
        #         event_handled = True

        # print('cur_event_data.keycode="%s"' % cur_event_data.keycode)
        # print('active_modifiers._all=%s' % active_modifiers._all)
        # Проверяем - не модификатор ли нажат
        if cur_event_data.scancode in active_modifiers._all and not event_handled:
            # print('It\'s modifier key: %s' % cur_event_data.keycode)
            active_modifiers.update(cur_event_data)

        # Check for double event modifier and sign key combination, like from self-programming Logitech devices: G602, G600 etc.
        double_event_mod_and_sign_keys = False
        # if cur_event_data.keystate in [1, 2]:  # Down and Hold events only
        #     if cur_event_data.scancode in active_modifiers._all:
        #         """ Если нажат модификатор, проверяем - не идет ли с ним
        #         в паре с того-же устройства сразу другое значимое событие,
        #         как это происходит с Logitech G602 """
        #         double_event_mod_and_sign_keys = False
        #         for one_key_rec in verbose_active_keys:
        #             if one_key_rec[1] not in active_modifiers._all:
        #                 double_event_mod_and_sign_keys = True
        #
        #
        #         if double_event_mod_and_sign_keys:
        #             print('Was pressed modifier, but in combination with sign key. Like double action from programming device. Drop it.')
        #             event_handled = True
        #
        #     # Если нажат модификатор и идет другое событие с утройства - игнорируем его

            # Дальше обрабатываем только нажатия
        if cur_event_data.keystate in [1, 2] and not double_event_mod_and_sign_keys:  # Down and Hold events only

            global_modifiers = active_modifiers.get()
            print('You Pressed the %s key, active keys from this device is: %s, and global modifiers: %s' % (
                            cur_event_data.keycode,
                            verbose_active_keys,
                            global_modifiers))
            # Собираем читабельный массив нажатых клавиш с клавиатуры
            verb_keys = []
            for a_key in active_keys:
                verb_keys.append(ecodes.KEY[a_key])
            # Ищем глобальные модификаторы, которых нет в текущих событиях с клавиатуры
            also_pressed_modifiers = {}
            for modifier in global_modifiers:
                # print(' global modifier: %s' % modifier)
                new_mod = True
                for verb_key in verb_keys:
                    if modifier in verb_key:
                        new_mod = False
                if new_mod:
                    # print('  Global modifier was also pressed: %s' % modifier)
                    also_pressed_modifiers[modifier] = True

            # print('-'*20)
            # print('also_pressed_modifiers: %s' % also_pressed_modifiers)

            combinations_events_search = []
            combinations_events_search.append(verbose_active_keys)
            for also_mod in also_pressed_modifiers:
                new_comb=[(also_mod, 0)]+verbose_active_keys
                # print('new_comb: %s' % new_comb)
                combinations_events_search.append(new_comb)
            # print('combinations_events_search: %s' % combinations_events_search)

            for combination in combinations_events_search:
                # Перебираем комбинации и ищем их в слушаемых событиях
                strkey = keyboard.processed_events.find_strkey(combination)
                if strkey:
                    # print('Found!')
                    # return False
                    event_handled = True
                    keyboard.processed_events.proccess_event(strkey, ui)
                    # Раньше использовались дополнительные параметры:
                    # event.type,
                    # cur_event_data.scancode,
                    # cur_event_data.keystate
        # Here we decide - whether to skip the event further (whether to do inject)

        # Если событие не было из списка отлавливаемых, то возможно надо
        # ретранслировать это событие дальше, в зависимости от настроек
        # клавиатуры.
        if not event_handled:
            if keyboard.transmit_all:
                # We decide to inject keyboard event:
                print('Transmit %s, %s' % (cur_event_data.keycode, cur_event_data.keystate))
                ui.write(event.type,
                         cur_event_data.scancode,
                         cur_event_data.keystate)
                # ui.syn()
    else:
        #All non-key events
        ui.write_event(event)

    return False




async def proccess_events(keyboard):
    # Асинхронная функция обработки событий
    try:
        async for event in keyboard.dev.async_read_loop():

            # print(keyboard.dev.path, evdev.categorize(event), sep=': ')

            exit_now = process_one_event_and_exit(keyboard, app.ui, event)
            # После обработки события происходит синхронизация ввода.
            # Возможно, уже записаны новые коды ввода:
            # новая комбинация или просто ретрансляция вводимого.
            app.ui.syn()
            if exit_now:
                exit()
    except OSError:
        print('Проблемы с обработкой сигналов с утройства %s (%s, %s).'% (keyboard.address,
                                                                          keyboard.dev_name,
                                                                          keyboard.dev_type))
        print('Останавливаем цикл их обработки' )
        keyboard.enabled = False


def grab_and_process_keyboard(keyboard, create_task=False):
    """Функция захвата и обработки событий одной клавиатуры"""
    if keyboard.enabled:
        # Если клавиатура включена, то у неё должен быть адрес и прикрепленное устройство
        keyboard.dev.grab()
        asyncio.ensure_future(proccess_events(keyboard))
    else:
        # А иначе это конфиг на будущее, ожидающий подключения устройства позднее.
        pass

    # if not create_task:
    #     asyncio.ensure_future(proccess_events(keyboard))
    # else:
    #     loop = asyncio.get_event_loop()
    #     loop.create_task(proccess_events(keyboard))


# def grab_plugged_keyboard():
#     pass




def get_configured_keyboard(keyb_address=None, keyb_name=None, keyb_type=None):
    print('Look up for configured device like %s "%s", %s' %
          (keyb_address,
           keyb_name,
           keyb_type))
    found_keyboard = None
    for keyboard in app.keyboards:
        # Сравниваем имя и тип устройства
        # print('  Compare with config for %s "%s", %s, enabled: %s' %
        #       (keyboard.address,
        #        keyboard.dev_name,
        #        keyboard.dev_type,
        #        keyboard.enabled))
        if keyb_address:
            # Сравниваем по одному адресу
            if keyb_address == keyboard.address:
                found_keyboard = keyboard
                break
        elif keyb_name == keyboard.dev_name and keyboard.dev_type in keyb_type:
            # Нашли нужное устройство с именем и нужным типом
            found_keyboard = keyboard
            # print(' Found')
            break
    return found_keyboard



def devices_observer_event(action, device):
    """
    1. Получили событие с подключением-отключением устройства.
    2. Опознаем устройства - входят ли в конфиг.
    3. Включаем захват для сконфигурированных.
    """
    # print('Событие %s с устройством %s' % (action, device))

    if 'DEVNAME' in device:
        dev_name = device['DEVNAME']
        print('Monitor devices: {0} input device {1}'.format(action, dev_name))

        if format(action) == 'add':
            conf_keyboard = None
            ev_device = None
            try:
                ev_device = evdev.InputDevice(dev_name)
                keyb_name = ev_device.name
            except:
                print('Устройство не является evdev.InputDevice')

            if ev_device:
                capabilities = ev_device.capabilities(verbose=True)
                keyb_type = get_dev_type(capabilities)
                conf_keyboard = get_configured_keyboard(keyb_name=keyb_name,
                                                        keyb_type=keyb_type)

            if conf_keyboard and not conf_keyboard.enabled:
                print('  For this device events will be grabbed again.')
                # Обновляем параметры сконфигурированной клавиатуры
                conf_keyboard.enabled = True
                conf_keyboard.address = dev_name
                conf_keyboard.dev = ev_device
                # Запускаем захват событий клавиатуры
                # grab_and_process_keyboard(conf_keyboard)
                # keyboard.dev.grab()
                # asyncio.ensure_future(proccess_events(keyboard))
                # loop = asyncio.get_event_loop()
                # app.loop_forever.create_task(proccess_events(conf_keyboard))
                # asyn.loop.create_task(proccess_events(keyboard))
                # asyncio.set_event_loop(loop)
                # loop.create_task(proccess_events(conf_keyboard))

                app.devs_need_grab.append(conf_keyboard)
                print('  Добавили в массив устройств к захвату')

                # new_loop = False
                # try:
                #     loop = asyncio.get_event_loop()
                #     grab_and_process_keyboard(conf_keyboard)
                #     print('Подключили к существующей петле Asyncio')
                # except RuntimeError:
                #     print('Создаем новую петлю Asyncio')
                #     loop = asyncio.new_event_loop()
                #     asyncio.set_event_loop(loop)
                #     new_loop = True
                # if new_loop:
                #     # future = loop.create_task(proccess_events(keyboard))
                #     print('Запускаем в новой петле')
                #     # grab_and_process_keyboard(conf_keyboard)
                #     loop.run_forever()
                #     # keyboard.dev.grab()
                #     # asyncio.ensure_future(proccess_events(keyboard))
                #     loop.run_until_complete(proccess_events(keyboard))
                #     print('Петля запущена')

                # grab_and_process_keyboard(conf_keyboard)
                # loop.run_forever()
                # loop.run_until_complete()

                # try:
                #     loop = asyncio.get_event_loop()
                #     grab_and_process_keyboard(conf_keyboard)
                #     print('Подключили к существующей петле Asyncio')
                # except RuntimeError:
                #     print('Создаем новую петлю Asyncio')
                #     loop = asyncio.new_event_loop()
                #     asyncio.set_event_loop(loop)
                #     grab_and_process_keyboard(conf_keyboard)
                #     print('Запустили в новой петле')
                #     loop.run_forever()

        if format(action) == 'remove':
            conf_keyboard = get_configured_keyboard(keyb_address=dev_name)
            if conf_keyboard:
                print('  Выключаем конфиг отключенного устройства.')
                conf_keyboard.enabled = False


async def wait_for_new_devices():
    while True:
        if app.devs_need_grab:
            print('Есть устройства для захвата')
            keyboard = app.devs_need_grab.pop()
            print('Grab keyboard: %s' % keyboard.name)
            grab_and_process_keyboard(keyboard, create_task=True)
        await asyncio.sleep(0.2)


# loop = asyncio.get_event_loop()
# app.loop_forever.create_task(proccess_events(conf_keyboard))


def grab_and_process_keyboards(keyboards):
    """Основная функция захвата и обработки клавиатурных событий."""
    # print('Keyboards for grab and process:')
    # for keyb in keyboards:
    #     print(' - %s' % keyb.name)
    app.ui = UInput()

    print('Run monitor')
    # asyncio.ensure_future(monitor_devices())
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('input')
    observer = pyudev.MonitorObserver(monitor, devices_observer_event)
    observer.start()

    print('Grab keyboards')
    for keyboard in keyboards:
        # keyboard.dev.grab()
        # asyncio.ensure_future(proccess_events(keyboard))
        grab_and_process_keyboard(keyboard)

    # Функция в этом потоке, которая будет подключать граббинг с утройств
    asyncio.ensure_future(wait_for_new_devices())
    # Отслеживаем сообщение о необходимости обновить конфиг
    asyncio.ensure_future(wait_for_reload_config())

    # Начинаем мониторить подключаемые-отключаемые устройства
    # asyncio.ensure_future(monitor_devices())
    # asyncio.create_task(monitor_devices())

    loop = asyncio.get_event_loop()
    # asyn.loop.create_task(monitor_devices())
    loop.run_forever()

    for keyboard in keyboards:
        keyboard.dev.ungrab()

    app.ui.close()


def check_plugged_keyboard_and_set_device(keyboard, plugged_devices, set_enabled=True):
    # Проверяем, подключена ли такая клавиатура
    print('  Для клавиатуры %s, %s ищем соответствующее подключенное устройство' % (keyboard.dev_name, keyboard.dev_type))
    # Если подключена - прикрепляем к ней соответствующее устройство и включаем её
    for plug_dev in plugged_devices:
        dev_name, dev_type, address, dev = plug_dev
        if keyboard.dev_name == dev_name and keyboard.dev_type in dev_type:
            # print('    Нашли соответствующее устройство %s %s %s' % (dev_name, dev_type, address))
            print('  Нашли соответствующее устройство на %s и включаем её.' % address)
            keyboard.dev = dev
            keyboard.address = address
            keyboard.enabled = True
            break
    if not keyboard.enabled:
        print('  Соответствующего устройства не нашли но будем ждать его подключения позднее.')


def get_plugged_devices_array():
    plugged_devices = []
    raw_devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    devices = reversed(raw_devices)
    for dev in devices:
        # print('dev: %s' % dev)
        capabilities = dev.capabilities(verbose=True)
        _dev_type = get_dev_type(capabilities)
        plugged_devices.append((dev.name, _dev_type, dev.fn, dev))
    return plugged_devices # (dev_name, dev_type, address, dev)


def check_plugged_keyboards_and_set_devices(keyboards):
    """Проверяем подключенные клавиатуры и прикрепляем к классам соответствующие устройства"""
    plugged_devices = get_plugged_devices_array()
    print('plugged_devices:')
    for plug_dev in plugged_devices:
        dev_name, dev_type, address, dev = plug_dev
        print('  %s %s %s' % (dev_name, dev_type, address))
    print()

    print('Check plugged keyboards and set devices:')
    for keyboard in keyboards:
        check_plugged_keyboard_and_set_device(keyboard, plugged_devices)
    print()


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

    parser.add_argument("-l", "--list", action="store_true", help="Show list of available devices:")

    parser.add_argument("-p", "--plugins", action="store_true", help="List of plugins and their available functions.")


    parser.add_argument("-e", "--exec", action="store_true", help="Run local executor service. Will execute commands from userspace.")

    parser.add_argument("-g", "--grab", type=str,
                        help="Listing device capabilities. Grab all its events and show information like input codes, mouse moves etc."
                             "Except C and Q keys, preserved for quit action. "
                             "Example: --grab /dev/input/eventXX")
    args = parser.parse_args()
    if args.config:
        print('Load config: %s' % args.config)
        app.config_filename = args.config
        load_config(args.config)
        # print('keyboards: %s' % keyboards)
        check_plugged_keyboards_and_set_devices(app.keyboards)
        grab_and_process_keyboards(app.keyboards)
    elif args.list:
        print('Show list of available devices.')
        show_dev_list()
    elif args.plugins:
        plugins = Plugins()
        plugins.print()
    elif args.grab:
        print('Grab all events and show input keys for %s device.' % args.grab)
        print('You can exit anytime by pressing Q or C.')
        dev_addr = args.grab
        grab_and_show_inputs(dev_addr)
    else:
        print(parser.print_help())
        plugins = Plugins()
        plugins.print()


if __name__ == '__main__':
    active_modifiers = Active_modifiers()

    main()



