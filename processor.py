
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
import yaml
import argparse
import asyncio
import json
import time
import os
import datetime
import traceback

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


from settings import Settings
from plugins import Plugins


class app:
    name = 'keyb-processor'
    # ui = None
    keyboards = []
    devs_need_grab = []
    need_reload_config = False
    config_filename = None
    ui_suffix = 'kbdprocessor'

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
    abstract_list = ['ALT', 'CTRL', 'SHIFT', 'META']

    alts = [evdev.ecodes.KEY_LEFTALT, evdev.ecodes.KEY_RIGHTALT]
    ctrls = [evdev.ecodes.KEY_LEFTCTRL, evdev.ecodes.KEY_RIGHTCTRL]
    metas = [evdev.ecodes.KEY_LEFTMETA, evdev.ecodes.KEY_RIGHTMETA]
    shifts = [evdev.ecodes.KEY_LEFTSHIFT, evdev.ecodes.KEY_RIGHTSHIFT]
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
        # print('(after update) modifiers: alt %s, ctrl %s, meta %s, shift %s' % (self.alt, self.ctrl, self.meta, self.shift))
        # print('(after update) pressed: %s' % self.pressed)


async def tcp_echo_client(message, loop):
    """Функция передачи команды на приемник в клиентской части системы."""
    reader, writer = await asyncio.open_connection(app.settings.host, app.settings.port,
                                                   loop=loop)
    print('Send to executioner: %r' % message)
    writer.write(message.encode())

    data = await reader.read(100)
    # print('Received: %r' % data.decode())

    # print('Close the socket')
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

        # Минимально необходимая пауза для стабильной работы и определения нажатий в системе, например в Gnome/Wayland
        pause = 0.01

        # def write_event(key_code, event_type):
        #     if event_type:
        #         event = "Inject press"
        #     else:
        #         event = "Inject release"
        #
        #     print('%s %s' % (event, one_key_code))
        #     key = evdev.ecodes.ecodes[key_code]
        #     ev = evdev.InputEvent(0, 0, evdev.ecodes.EV_KEY, key, event_type)
        #     ui.write_event(ev)
        #     time.sleep(pause)
        #     ui.syn()

        def write_key(key_code, event_type):
            if event_type:
                event = "Inject press"
            else:
                event = "Inject release"

            print('%s %s' % (event, one_key_code))
            key = evdev.ecodes.ecodes[key_code]
            ui.write(evdev.ecodes.EV_KEY, key, event_type)
            time.sleep(pause)
            ui.syn()


        print('We will inject keyb codes now: %s' % keyb_inputs)
        # Пауза между нажатиями, экспериментальным путём определил что это минимально достаточное расстояние между
        # нажатиями, чтобы система, в частности Gnome/Wayland, определяли соседние события как раздельные.

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
                write_key(one_key_code, 0)
                # state = active_modifiers.pressed[one_key_code]
                # ui.write(evdev.ecodes.EV_KEY, one_key_code, 0)
                # Обновляем в статусе глобальных модификаторов, что данный модификатор больше не нажат
                my_event = My_event(keystate=0,scancode=one_key_code)
                # active_modifiers.find_mods_and_change_state(one_key_code, False)
                time.sleep(pause)
                # await asyncio.sleep(pause) // outside async function
            # Обновляем статусы отжатых модификаторов
            for one_key_code in active_modifiers.pressed.copy():
                my_event = My_event(keystate=0, scancode=one_key_code)
                active_modifiers.update(my_event)

        # Press
        for one_key_code in keyb_inputs:
            write_key(one_key_code, 1)
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            # key = evdev.ecodes.ecodes[one_key_code]
            # ui.write(evdev.ecodes.EV_KEY, key, 1)
            # time.sleep(pause)
            # await asyncio.sleep(pause) // outside async function
        # ui.syn()

        # Release
        for one_key_code in keyb_inputs:
            write_key(one_key_code, 0)
            # key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            # key = evdev.ecodes.ecodes[one_key_code]
            # ui.write(evdev.ecodes.EV_KEY, key, 0)
            # time.sleep(pause)
            # await asyncio.sleep(pause) // outside async function

        # print('Now we need DOWN keys for global modifiers: %s' % active_modifiers.pressed)
        # for one_key_code in active_modifiers.pressed:
        #     state = active_modifiers.pressed[one_key_code]
        #     ui.write(evdev.ecodes.EV_KEY, one_key_code, state)

        # ui.syn()

    def send_command(command, plugin=None):
        # command = ["ls", "-l"]
        print('Prepare to send command: %s under plugin: %s' % (command, plugin))
        message_dict = {'key': app.settings.key,
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
        # print(' Получили строку для поиска ключей: %s' % strkey)
        # print('Массив слушаемых событий: %s' % self.listen_events)
        # print('We find %s in %s' % (active_keys_str, self.listen_events))
        if strkey in self.listen_events:
            # print(' Нашли')
            return strkey
        else:
            # print(' Не нашли')
            return False

    def clear(self):
        'Очищаем массивы отслеживаемых событий и массив ключей событий для быстрого поиска'
        self.listen_events = []
        self.processed_events_setup = []

    def add(self, pressed_keys='', inject_keys='', plugin=None, command=''):
        # print('Add pressed_keys:', pressed_keys,
        #       'inject_keys:', inject_keys, 'plugin:', plugin, 'command:', command)
        # 'transmit:', transmit,

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
            import shlex
            ev.command = shlex.split(command)

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



class Significant_events:
    """Класс для работы с накапливаемым краткосрочным массивом значимых событий с устройства. Например, анализ движения колёсика дополнительного скроллинга для определения - каким образом реагировать на сделанное пользователем движение или жест."""
    timeout = 100
    accepted = []

    class event:
        time=None
        type=None
        value=None

    def time_for_receiving_has_expired(self, time=None):
        # Время ожидания новых событий для добавления в очередь вышло
        if not time:
            time = datetime.datetime.now()
        len_accept = len(self.accepted)
        diff_time_mili = 0

        if len_accept>0:
            diff_time = time - self.accepted[len_accept-1].time
            diff_time_mili = int(diff_time.total_seconds()*1000)
        if diff_time_mili>self.timeout:
            # print('У события слишком большая разница по времени. Анализируем полученный массив принятых событий.')
            # self.print()
            # self.accepted = []
            # print('Очищаем массив принятых событий')
            return True
        else:
            # Ещё есть время для новых событий в этой очереди
            return False

    # def check(self, time=None):
    #     # print('Check sig events')
    #
    #     len_accept = len(self.accepted)
    #     diff_time_mili = 0
    #
    #     if len_accept>0:
    #         diff_time = time - self.accepted[len_accept-1].time
    #         diff_time_mili = int(diff_time.total_seconds()*1000)
    #     if diff_time_mili>self.timeout:
    #         print('У события слишком большая разница по времени. Анализируем полученный массив принятых событий.')
    #         self.print()
    #         self.accepted = []
    #         print('Очищаем массив принятых событий')
    #         return False
    #     else:
    #         # print('Разница по времени с предыдущим событием: %s' % diff_time_mili)
    #         return True


    def print(self):
        print('Массив accepted в данный момент:')
        for one_event in self.accepted:
            print('  event: %s, %s, %s' % (one_event.time, one_event.type, one_event.value) )


    def add(self, time=None, type=None, value=None):

        if not self.time_for_receiving_has_expired(time=time):
        # len_accept = len(self.accepted)
        # diff_time_mili = 0

        # if len_accept>0:
            # diff_time = time - self.accepted[len_accept-1].time
            # diff_time_mili = int(diff_time.total_seconds()*1000)
        # if diff_time_mili>self.timeout:
            # print('У события слишком большая разница по времени. Анализируем полученный массив принятых событий.')
            # self.print()
            # self.accepted = []
            # print('Очищаем массив принятых событий')
        # else:
            # print('Добавляем значимое событие. Разница по времени с предыдущим: %s' % diff_time_mili)
            new_event = self.event()
            new_event.time = time
            new_event.type = type
            new_event.value = value
            self.accepted.append(new_event)
            # print('Added new event: %s, %s, %s' % (new_event.time, new_event.type, new_event.value))



class Keyboard:
    """Одиночный класс клавиатуры с конфигом."""
    name = ''
    address = ''
    dev_name = ''
    dev_type = ''
    transmit_all = True
    dev = None
    task = None
    processed_events = None
    enabled = False
    ui = None
    significant_events = Significant_events()

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

    def __init__(self, name=name, dev_name=None, dev_type=None,transmit_all=True):
        #address=address,
        # print('Нужно создать новую клавиатуру:')
        # print(' name: %s, dev_name: %s, dev_type: %s' % (name, dev_name, dev_type))
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



async def check_significant_events_and_react():
    while True:
        # Обходим активные "клавиатуры"
        for keyboard in app.keyboards:
            if keyboard.enabled:
                # Проверяем наличие значимых событий у каждой
                if keyboard.significant_events.accepted:
                    # Проверяем - истёк ли таймаут для какой-то очереди
                    if keyboard.significant_events.time_for_receiving_has_expired():
                        # Если истёк - сообщаем о том что получили мета-событие и на него надо реагировать
                        sig_events_str = []
                        sig_events_dict = {}
                        for event in keyboard.significant_events.accepted:
                            sig_events_str.append((event.type, event.value))
                            # Формируем словарь типов с массивами значимых событий (типа группировка)
                            if not event.type in sig_events_dict:
                                sig_events_dict[event.type] = []
                            sig_events_dict[event.type].append(str(event.value))
                        print('.. Обнаружен законченный массив принятых событий у устройства %s: %s' % (
                        keyboard.name, sig_events_str))
                        print('.. sig_events_dict: %s' % sig_events_dict)
                        for one_type in sig_events_dict:
                            keys = []
                            for key in sig_events_dict[one_type]:
                                # Проводим обработку значений, чтобы если от устройства пришли повышенные значения мы их разложили в единицы
                                for ind in range(0, abs(int(key))):
                                    if int(key)>0: mini_key = '1'
                                    else: mini_key = '-1'
                                    keys.append(mini_key)
                            print('keys: %s' % keys)
                            strkey = one_type + ':' + ','.join(keys)
                            print('.. strkey: %s' % strkey)
                            # print('.. keyboard.processed_events.listen_events: %s' % keyboard.processed_events.listen_events)
                            if strkey in keyboard.processed_events.listen_events:
                                print('.. Это событие есть в конфиге.')
                                keyboard.processed_events.proccess_event(strkey, keyboard.ui)
                        # print('.. Таймаут принятия новых событий вышел - фиксируем, обрабатываем, очищаем очередь.')
                        # Очищаем массив принятых событий для данного устройства
                        keyboard.significant_events.accepted = []

        await asyncio.sleep(0.05)




async def wait_for_reload_config():
    while True:
        if app.need_reload_config:
            print('Нужно перезагрузить конфиг')
            app.need_reload_config = False
            new_keyboards = load_config(app.config_filename)
            compare_loaded_and_new_keyboards(new_keyboards)
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


def get_configured_keyboard(keyboards, name=None, address=None, dev_name=None, dev_type=None):
    # print('Look up for configured device like "%s" %s "%s", %s' %
    #       (name,
    #        address,
    #        dev_name,
    #        dev_type))
    found_keyboard = None
    for keyboard in keyboards:
        # Сравниваем имя и тип устройства
        # print('  Compare with config for %s "%s", %s, enabled: %s' %
        #       (keyboard.address,
        #        keyboard.dev_name,
        #        keyboard.dev_type,
        #        keyboard.enabled))
        if name:
            # Сравниваем по одному названию класса клавиатуры/её секции в конфиге
            if name == keyboard.name:
                found_keyboard = keyboard
                break
        if address:
            # Сравниваем по одному адресу
            if address == keyboard.address:
                found_keyboard = keyboard
                break
        elif dev_name == keyboard.dev_name and keyboard.dev_type in dev_type:
            # Нашли нужное устройство с именем и нужным типом
            found_keyboard = keyboard
            # print(' Found')
            break
    return found_keyboard


def compare_loaded_and_new_keyboards(new_keyboards):
    print('Анализируем изменения между работающим конфигом клавиатур и новым:')

    need_delete_keyboards = []

    # Поиск клавиатур в памяти, которых нет в новом конфиге, и которые надо стереть.
    for i in range(0, len(app.keyboards)):
        exist_keyboard = app.keyboards[i]
        new_keyboard = get_configured_keyboard(new_keyboards, name=exist_keyboard.name)
        if not new_keyboard:
            print('- В конфиге отсутствует клавиатура "%s". Её надо освободить и удалить в памяти программы.' % exist_keyboard.name)
            ungrab_and_release_keyboard(exist_keyboard)
            app.keyboards[i] = None
            need_delete_keyboards.append(i)
    # Удаление пустых ячеек в массиве загруженных клавиатур
    for i in need_delete_keyboards:
        del app.keyboards[i]


    # Поиск новыйх клавиатур и изменений в имеющихся
    for new_keyboard in new_keyboards:
        # if app.ui_suffix in new_keyboard.name:
            # print('У нас новая подключенное виртуальное устройство, созданное %s: %s. Пропускаем его.' % (app.ui_suffix, new_keyboard.name) )
            # continue
        keyboard_was_changed = False
        need_regrab = False
        exist_keyboard = get_configured_keyboard(app.keyboards, name=new_keyboard.name)
        if exist_keyboard:
            print('- Клавиатура "%s" уже есть в памяти програмы.' % new_keyboard.name)

            if not exist_keyboard.dev_name == new_keyboard.dev_name or not exist_keyboard.dev_type == new_keyboard.dev_type:
                print('   Изменилось имя/тип клавиатуры с %s/%s' % (exist_keyboard.dev_name, exist_keyboard.dev_type))
                print('   на %s/%s' % (new_keyboard.dev_name, new_keyboard.dev_type))
                keyboard_was_changed = True

                print('  Выполняем освобождение устройства и цикла перехвата событий и ищем новое устройство для захвата.')
                ungrab_and_release_keyboard(exist_keyboard)

                exist_keyboard.dev_name = new_keyboard.dev_name
                exist_keyboard.dev_type = new_keyboard.dev_type

                check_plugged_keyboards_and_set_devices([exist_keyboard])
                grab_and_process_keyboard(exist_keyboard)

            # Сравниванием конфиги отлавливаемых событий и действий между загруженным и новым
            exist_events = exist_keyboard.processed_events.listen_events.copy()
            new_events = new_keyboard.processed_events.listen_events.copy()

            events_was_changed = False
            actions_was_changed = False

            if not exist_events == new_events:
                events_was_changed = True
                keyboard_was_changed = True
                print('   Был изменен массив событий, обрабатываемых этой клавиатурой.')

            if not events_was_changed:
                # События не были изменены, но могли быть изменены действия, связанные с ними
                # Сравниваем массивы классов в обработчиках событий этих клавиатур
                for i in range(0, len(exist_keyboard.processed_events.processed_events_setup)):
                    exist_processed_event = exist_keyboard.processed_events.processed_events_setup[i]
                    new_processed_event = new_keyboard.processed_events.processed_events_setup[i]
                    if not exist_processed_event.pressed_keys == new_processed_event.pressed_keys:
                        actions_was_changed = True
                    if not exist_processed_event.inject_keys == new_processed_event.inject_keys:
                        actions_was_changed = True
                    if not exist_processed_event.plugin == new_processed_event.plugin:
                        actions_was_changed = True
                    if not exist_processed_event.command == new_processed_event.command:
                        actions_was_changed = True

                    if actions_was_changed:
                        keyboard_was_changed = True
                        print('   Был изменен массив действий, который вызываются событиями с этой клавиатуры.')
                        break

            if events_was_changed or actions_was_changed:
                exist_keyboard.processed_events.listen_events = new_keyboard.processed_events.listen_events.copy()
                # Перезагружаем классы обработчиков клавиатуры
                exist_keyboard.processed_events.processed_events_setup = new_keyboard.processed_events.processed_events_setup.copy()
                print('   --> Обновляем кэш событий и класс событий и действий для этой клавиатуры.')

                # exist_keyboard.print_setup()

            if not keyboard_was_changed:
                print('   В обновленном конфиге клавиатура осталась без изменений.')

        else:
            # not exist_keyboard
            print('- В конфиге обнаружена новая клавиатура "%s". Её надо добавить к имеющимся.' % new_keyboard.name)
            app.keyboards.append(new_keyboard)
            check_plugged_keyboards_and_set_devices([new_keyboard])
            grab_and_process_keyboard(new_keyboard)


def load_yml_file(filename):
    # with open(filename, 'r') as ymlfile:    <-- а вот это опасный вариант
    #     cfg = yaml.load(ymlfile)

    # Используем безопасную загрузку конфига, чтобы там не оказалось ничего исполняемого
    with open(filename, 'r') as ymlfile:
        try:
            cfg = yaml.safe_load(ymlfile)
        except yaml.YAMLError as exc:
            print(exc)
            exit()
    return cfg


def add_event_to_keyboard_settings(key, value, new_keyboard):
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
    
def load_keyboard_section(cfg_key_values, new_keyboard):
    include_cfgs = [] # Массив включаемых конфигов для данного устройства
    
    for key in cfg_key_values:
        value = cfg_key_values[key]
        # print('# key:', key, ', # value:',value)
        if key == 'include':
            print('Встретили инструкцию на добавление настройки из файла %s' % value)
            include_cfgs.append(load_yml_file(value))
        elif key == 'name':
            new_keyboard.dev_name = value
        elif key == 'capabilities':
            new_keyboard.dev_type = value
        else:
            add_event_to_keyboard_settings(key, value, new_keyboard)

    # Если встретили include и загрузили эти конфиги
    for one_include_cfg in include_cfgs:
        # Выполняем рекурсивную загрузку этих секций
        load_keyboard_section(one_include_cfg, new_keyboard)
    

def load_config(filename):
    """Загрузка конфига и создание нужных классов для захватываемых
    устройств.
    """
    #print('filename[0]:', filename[0])
    if filename[0] not in ['.', '/', '\\']:
        full_filename = './configs/%s.yml' % filename
        print('В качестве файла конфигурации было указано сокращённое имя (алиас) "%s". Разворачиваю его в полноценный путь: %s' % (filename,full_filename))
        filename = full_filename
        app.config_filename = filename
    
    cfg_keyboards = [] # Начальная очистка списка клавиатур из конфига

    cfg = load_yml_file(filename)

    # # with open(filename, 'r') as ymlfile:    <-- а вот это опасный вариант
    # #     cfg = yaml.load(ymlfile)
    #
    # # Используем безопасную загрузку конфига, чтобы там не оказалось ничего исполняемого
    # with open(filename, 'r') as ymlfile:
    #     try:
    #         cfg = yaml.safe_load(ymlfile)
    #     except yaml.YAMLError as exc:
    #         print(exc)
    #         exit()

    for section in cfg:
        print(section)
        keyboard_name = section
        # Создаем клавиатуру только с именем. Остальное добавляем позже
        new_keyboard = Keyboard(name=keyboard_name)

        load_keyboard_section(cfg[section], new_keyboard)
        
        #for key in cfg[section]:
            #value = cfg[section][key]
            ## print('# key:', key, ', # value:',value)
            #if key == 'include':
                #print('Встретили инструкцию на добавление настройки из файла %s' % value)
                #include_cfgs.append(load_yml_file(value))
            #elif key == 'name':
                #new_keyboard.dev_name = value
            #elif key == 'capabilities':
                #new_keyboard.dev_type = value
            #else:
                #add_event_to_keyboard_settings(key, value, new_keyboard)
                ### Here is new keyboard event for handle
                ##pressed_keys = key
                ### print('Found pressed_keys:', pressed_keys)
                ##inject_keys = None
                ##plugin = None
                ##command = None
                ##if 'inject_keys' in value:
                    ##inject_keys = value['inject_keys']
                    ### print('Found inject_keys:', inject_keys)
                ##if 'plugin' in value:
                    ##plugin = value['plugin']
                ##if 'command' in value:
                    ##command = value['command']
                    ### print('Found command:', command)
                ##new_keyboard.processed_events.add(
                    ##pressed_keys=pressed_keys,
                    ##inject_keys=inject_keys,
                    ##plugin=plugin,
                    ##command=command
                ##)
        
        cfg_keyboards.append(new_keyboard)

    print('Configuration file "%s" successfully read' % filename)

    # for keyb in cfg_keyboards:
    #     keyb.print_setup()
    #
    # for keyboard in cfg_keyboards:
    #     print('In cfg_keyboards:')
    #     print(' keyboard: %s, dev_name: %s, dev_type: %s' % (keyboard, keyboard.dev_name, keyboard.dev_type))
    #     print('-'*20)

    return cfg_keyboards


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
            str_type=' <-- %s' % ', '.join(dev_type)
            str_type = str_type.upper()
        # print(device.path, device.name, device.phys)
        # print(device.fn, '"%s" %s' % (device.name, str_type))
        print('  ', device.path, '"%s" %s' % (device.name, str_type))



def grab_and_show_inputs(dev_addr):
    """Захватываем устройство и выводим в консоль все события его кнопок.
    Если нажаты Q или C - выходим.
    """
    # from evdev import UInput
    # ui = UInput()

    dev = evdev.InputDevice(dev_addr)
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
        cur_event_data = evdev.categorize(event)
        print(cur_event_data)
        # print(event)
        if event.type == evdev.ecodes.EV_KEY:
            cur_event_data = evdev.categorize(event)
            # print('cur_event_data: %s' % cur_event_data)
            if cur_event_data.keystate in [1, 2]:  # Down and Hold events only
                if cur_event_data.scancode in [evdev.ecodes.KEY_Q, evdev.ecodes.KEY_C]:
                    print('You press Q or C, and we quit now.')
                    break
        # Прокидываем событие с клавиатуры дальше в систему
        # dev.write_event(event)
        # ui.write_event(event)
        # ui.syn()

    # ui.close()
    dev.ungrab()




def process_one_event_and_exit(keyboard, ui, event):
    event_handled = False
    # single_meta_press = False

    cur_event_data = evdev.categorize(event)
    time_now = datetime.datetime.now()
    # keyboard.significant_events.check(time_now)
    
    if event.type == evdev.ecodes.EV_REL:
        # События колёсика
        # print('У нас событие колёсика или перемещения мышки')
        if event.code == evdev.ecodes.REL_HWHEEL:
            print('%s У нас событие горизонтального колёсика. Value: %s' % (time_now, event.value))

            # keyboard.significant_events.add(time=time_now, type=evdev.ecodes.REL_HWHEEL, value=event.value)
            keyboard.significant_events.add(time=time_now, type='REL_HWHEEL', value=event.value)

    
    if event.type == evdev.ecodes.EV_KEY:
        # cur_event_data = evdev.categorize(event)
        # cur_active_keys = dev.active_keys()
        # Переводим инфу о нажатых клавишах в понятный формат
        active_keys = keyboard.dev.active_keys()
        verbose_active_keys_raw = keyboard.dev.active_keys(verbose=True)

        # verbose_active_keys = keyboard.dev.active_keys(verbose=True)
        verbose_active_keys = []
        
        # Проверка на кривые коды клавиш и исправление этого
        for one_rec in verbose_active_keys_raw:
            k_name,k_code = one_rec
            # print('one_rec: %s, %s' % (k_name,k_code))
            if '?' in k_name:
                # print('Найден ? в записи. Замещаем на код.')
                k_name = '_%s' % k_code
            verbose_active_keys.append((k_name, k_code))
        # print('Результирующий verbose_active_keys: %s' % verbose_active_keys)
        
        # print()
        print('Событие: %s (активные клавиши: %s)' % (cur_event_data.keycode, verbose_active_keys))
        # print('Все активные клавиши: %s' % active_keys)

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
            print('It\'s modifier key: %s' % cur_event_data.keycode)
            active_modifiers.update(cur_event_data)

        # Check for double event modifier and sign key combination, like from self-programming Logitech devices: G602, G600 etc.
        # double_event_mod_and_sign_keys = False
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
        if cur_event_data.keystate in [1, 2]:  # Down and Hold events only
            #   and not double_event_mod_and_sign_keys

            global_modifiers = active_modifiers.get()
            print('You Pressed the %s, active keys from this (%s) device is: %s, global modifiers: %s' % (
                            cur_event_data.keycode,
                            keyboard.name,
                            verbose_active_keys,
                            global_modifiers))
            # Собираем читабельный массив нажатых клавиш с клавиатуры
            verb_keys = []
            for a_key in active_keys:
                # print('a_key: %s' % a_key)
                try:
                    verb_keys.append(evdev.ecodes.KEY[a_key])
                except:
                    code_key = '_%s' % a_key
                    # Тут происходит ошибка при добавлении нажатых на мышке клавиш
                    print('Ошибка при добавлении клавиши в массив. Замещаем кодом клавиши: %s' % code_key)
                    verb_keys.append(code_key)
                    
            # print('verb_keys: %s' % verb_keys)
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

            # Для случая одной нажатой клавиши или нескольких нажатых клавиш с одного устройства- просто обрабатываем их, собрав в массив

            # Если активен глобальный модификатор:
            # 1. проверяем, не из-за модификатора с устройства он активен
            # 2. если глобальный модификатор отдельно - собираем комбинацию только с ним конкретно (LEFTALT/RIGHTALT) и затем добавляем с его общим варианто (ALT)

            # print('verbose_active_keys: %s' % verbose_active_keys)
            # combinations_events_search = []
            # combinations_events_search.append(verbose_active_keys)

            variations_pressed_combination = []

            pressed_combination = verbose_active_keys

            for also_mod in also_pressed_modifiers:
                # new_comb=[(also_mod, 0)]+verbose_active_keys
                # print('new_comb: %s' % new_comb)
                # combinations_events_search.append(new_comb)
                pressed_combination.append((also_mod, 0))

            # Добавляем основную нажатую комбинацию с устройства + модификаторы с других
            variations_pressed_combination.append(pressed_combination)

            # print('combinations_events_search: %s' % combinations_events_search)
            # print('pressed_combination: %s' % pressed_combination)

            # Дальше надо добавить измененную комбинацию с утройства на абстрактные ALT / SHIFT / META / CTRL
            abstract_pressed_combination = []
            for one_key in pressed_combination:
                abstract_pressed_combination.append(one_key[0])

            # print('abstract_pressed_combination: %s' % abstract_pressed_combination)

            # abstract_pressed_combination = pressed_combination.copy()
            get_abstract_pressed_combination = False

            # print('abstract_pressed_combination: %s' % abstract_pressed_combination)
            for i in range(0, len(abstract_pressed_combination)):
                # print('i=%s' % i)
                one_key = abstract_pressed_combination[i]
                # print('one_key: %s' % one_key)
                # one_key = abstract_pressed_combination[i]
                # print('one_key: %s' % abstract_pressed_combination[i])

                for mod in active_modifiers.abstract_list:
                    # print('look for mod: %s' % mod)
                    # Ищем такой модификатор в строке и меняем его на абстрактный
                    if mod in one_key:
                        abstract_pressed_combination[i] = mod
                        # print('after replace one_key abstract_pressed_combination= %s' % abstract_pressed_combination)
                        get_abstract_pressed_combination = True

            # Добавляем цифру к элементам, как при обработке событий
            for i in range(0, len(abstract_pressed_combination)):
                abstract_pressed_combination[i] = (abstract_pressed_combination[i], 0)

            if get_abstract_pressed_combination:
                # print('abstract_pressed_combination: %s' % abstract_pressed_combination)
                variations_pressed_combination.append(abstract_pressed_combination)

            # print('variations_pressed_combination: %s' % variations_pressed_combination)

            for combination in variations_pressed_combination:
                # Перебираем комбинации и ищем их в слушаемых событиях
                print('Для комбинации "%s" ищем назначение в конфиге' % combination)
                strkey = keyboard.processed_events.find_strkey(combination)
                if strkey:
                    # print('Нашли: %s' % strkey)
                    # return False
                    event_handled = True
                    keyboard.processed_events.proccess_event(strkey, ui)
                    break
                    # Раньше использовались дополнительные параметры:
                    # event.type,
                    # cur_event_data.scancode,
                    # cur_event_data.keystate
                # else:
                    # print('Не нашли. Конфига для комбинации нет.')

            # print('Для комбинации "%s" ищем ...' % combination)

        # Here we decide - whether to skip the event further (whether to do inject)

        # # Если событие не было из списка отлавливаемых, то возможно надо
        # # ретранслировать это событие дальше, в зависимости от настроек
        # # клавиатуры.
        # if not event_handled:
            # if keyboard.transmit_all:
                # # We decide to inject keyboard event:
                # # print('Transmit %s, %s' % (cur_event_data.keycode, cur_event_data.keystate))
                # ui.write(event.type,
                         # cur_event_data.scancode,
                         # cur_event_data.keystate)
                # # ui.syn()
    # else:
        # #All non-key events
        # ui.write_event(event)
        
    if not event_handled:
        # Все не-кнопочные события и кнопочные, которые не перехвачены/обработаны
        # print('Событие не обработано и транслируется дальше')
        ui.write_event(event)
    else:
        # print('Событие было обработано и не выводится в поток виртуального устройства')
        pass
    
    return False




async def proccess_events(keyboard):
    # Асинхронная функция обработки событий
    try:
        async for event in keyboard.dev.async_read_loop():

            # print(keyboard.dev.path, evdev.categorize(event), sep=': ')

            # exit_now = process_one_event_and_exit(keyboard, app.ui, event)
            exit_now = process_one_event_and_exit(keyboard, keyboard.ui, event)
            # После обработки события происходит синхронизация ввода.
            # Возможно, уже записаны новые коды ввода:
            # новая комбинация или просто ретрансляция вводимого.
            # app.ui.syn()
            keyboard.ui.syn()
            if exit_now:
                exit()
    except OSError:
        print('Проблемы с обработкой сигналов с утройства %s (%s, %s).'% (keyboard.address,
                                                                          keyboard.dev_name,
                                                                          keyboard.dev_type))
        print('Останавливаем цикл их обработки' )
        keyboard.enabled = False
    # except Exception as e: print(e)
    except Exception:
        traceback.print_exc()
        

def ungrab_and_release_keyboard(keyboard):
    """Освобождаем захват устройства, выключаем класс и заканчиваем цикл ожидания сигналов."""
    print('  Освобождаем захват устройства, выключаем класс и заканчиваем цикл ожидания сигналов.')
    keyboard.enabled = False
    if keyboard.ui:
        keyboard.ui.close()
    if keyboard.dev:
        keyboard.dev.ungrab()
        keyboard.dev = None
    print('  Надо убить процесс отлова событий в loop')
    if keyboard.task and not keyboard.task.cancelled():
        keyboard.task.cancel()
        keyboard.task = None


def make_uinput_dev(keyboard):
    """Функция создания UInput на основе данного реального девайса"""
    print('Делаем виртуальное устройство ввода:', keyboard.name, keyboard.dev, keyboard.address)
    dev = evdev.InputDevice(keyboard.address)
    keyboard.ui = evdev.UInput.from_device(dev, name=keyboard.name+' ' + app.ui_suffix)


def grab_and_process_keyboard(keyboard):
    """Функция захвата и обработки событий одной клавиатуры"""
    if keyboard.enabled:
        # Если клавиатура включена, то у неё должен быть адрес и прикрепленное устройство
        make_uinput_dev(keyboard)
        keyboard.dev.grab()
        # asyncio.ensure_future(proccess_events(keyboard))
        keyb_task = asyncio.ensure_future(proccess_events(keyboard))
        keyboard.task = keyb_task
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
                conf_keyboard = get_configured_keyboard(app.keyboards, 
                                                        dev_name=keyb_name,
                                                        dev_type=keyb_type)

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
            conf_keyboard = get_configured_keyboard(app.keyboards, address=dev_name)
            if conf_keyboard:
                print('  Выключаем конфиг отключенного устройства.')
                conf_keyboard.enabled = False


async def wait_for_new_devices():
    while True:
        if app.devs_need_grab:
            print('Есть устройства для захвата')
            keyboard = app.devs_need_grab.pop()
            print('Grab keyboard: %s' % keyboard.name)
            grab_and_process_keyboard(keyboard)
        await asyncio.sleep(0.2)


# loop = asyncio.get_event_loop()
# app.loop_forever.create_task(proccess_events(conf_keyboard))


def grab_and_process_keyboards(keyboards):
    """Основная функция захвата и обработки клавиатурных событий."""
    # print('Keyboards for grab and process:')
    # for keyb in keyboards:
    #     print(' - %s' % keyb.name)
    # app.ui = evdev.UInput()

    # Кусок кода более не актуален - все устройства работают со своими собственными UI
    # for keyboard in keyboards:
        # if keyboard.enabled:
            # print('Найдена включённая клавиатура, на основе которой сделаем виртуальное устройство ввода:', keyboard.name, keyboard.dev, keyboard.address)
            # dev = evdev.InputDevice(keyboard.address)
            # app.ui = evdev.UInput.from_device(dev, name='kbdprocessor')
            # break
    # else:
        # app.ui = evdev.UInput()

    # dev_addr = '/dev/input/event8'
    # dev = evdev.InputDevice(keyboard.address)
    # app.ui = evdev.UInput.from_device(dev, name='kbdprocessor')


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
    # Отслеживаем накопленные значимые события у устройств и реагируем на них
    asyncio.ensure_future(check_significant_events_and_react())

    # Начинаем мониторить подключаемые-отключаемые устройства
    # asyncio.ensure_future(monitor_devices())
    # asyncio.create_task(monitor_devices())

    loop = asyncio.get_event_loop()
    # asyn.loop.create_task(monitor_devices())
    loop.run_forever()

    for keyboard in keyboards:
        # keyboard.dev.ungrab()
        ungrab_and_release_keyboard(keyboard)

    # app.ui.close()


def check_plugged_keyboard_and_set_device(keyboard, plugged_devices, set_enabled=True):
    # Проверяем, подключена ли такая клавиатура
    print('  Для клавиатуры %s, %s ищем соответствующее подключенное устройство' % (keyboard.dev_name, keyboard.dev_type))
    # Если подключена - прикрепляем к ней соответствующее устройство и включаем её
    for plug_dev in plugged_devices:
        dev_name, dev_type, address, dev = plug_dev
        if keyboard.dev_name == dev_name and keyboard.dev_type in dev_type:
            # print('    Нашли соответствующее устройство %s %s %s' % (dev_name, dev_type, address))
            print('    Нашли соответствующее устройство на %s и включаем её.' % address)
            keyboard.dev = dev
            keyboard.address = address
            keyboard.enabled = True
            break
    if not keyboard.enabled:
        print('    Соответствующего устройства не нашли но будем ждать его подключения позднее.')


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
        # print(' keyboard: %s, dev_name: %s, dev_type: %s' % (keyboard, keyboard.dev_name, keyboard.dev_type ))
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

    parser = argparse.ArgumentParser(description="Description about program. "
                                                 "Long decription about program.")

    parser.add_argument("-c", "--config", type=str, help="Load config file. You can use shortname like 'gnome'. We will use configs from ./configs folder. Usage: %s -c gnome" % app.name)

    parser.add_argument("-i", "--install", action="store_true", help="Make link /usr/local/bin/keyb-processor and /usr/local/bin/kp -> main script. Needs SUDO.")

    parser.add_argument("-l", "--list", action="store_true", help="Show list of available devices:")

    parser.add_argument("-p", "--plugins", action="store_true", help="List of plugins and their available functions.")


    parser.add_argument("-e", "--exec", action="store_true", help="Run local executor service. Will execute commands from userspace.")

    parser.add_argument("-g", "--grab", type=str,
                        help="Listing device capabilities. Grab all its events and show information like input codes, mouse moves etc. Needs SUDO. "
                             "Except C and Q keys, preserved for quit action. "
                             "Example: --grab /dev/input/eventXX")
    args = parser.parse_args()
    if args.config:
        app.settings = Settings()
        print('Load config: %s' % args.config)
        app.config_filename = args.config
        # Запускаем отслеживание изменений файла конфига
        app.keyboards = load_config(app.config_filename)
        # print('keyboards: %s' % keyboards)

        # for keyboard in app.keyboards:
        #     print('After load config in app.keyboards:')
        #     print(' keyboard: %s, dev_name: %s, dev_type: %s' % (keyboard, keyboard.dev_name, keyboard.dev_type))
        #     print('-'*20)

        #start_config_change_observer(args.config)
        start_config_change_observer(app.config_filename)
        check_plugged_keyboards_and_set_devices(app.keyboards)
        grab_and_process_keyboards(app.keyboards)
    elif args.list:
        print('List of available devices:')
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
        # print(parser.print_help())
        parser.print_help()
        plugins = Plugins()
        plugins.print()


if __name__ == '__main__':
    active_modifiers = Active_modifiers()

    main()



