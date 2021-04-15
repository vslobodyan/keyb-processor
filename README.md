# Keyboard Processor

### Цели и задачи



### Описание возможностей



### Архитектура

| Нижний уровень | Средний уровень | Верхний уровень |
|--------|-------|---------|
| Пространство sudo | GNOME, Wayland / KDE / XFCE / etc. | Пространство пользователя |
| **keyb-processor**  перехватывает клавиатурные события с или создаёт нужные | --> | **keyb-processor executor** выполняет нужные команды |
| Использует конфиг устройств и перехватывает события до их попадания в графическую среду | сообщения что нужно делать отправляются на сокет | Слушает сокет и выполняет нужные команды используя плагины для конкретных DE|

### Скриншоты

keyb-processor с загруженным конфигом устройств:
![Скрин окна программы](https://raw.githubusercontent.com/vslobodyan/keyb-processor/master/screenshots/keyb_1.png "Скрин окна программы")

keyb-processor executor загрузил плагины и ждёт команды:
![Скрин окна программы](https://raw.githubusercontent.com/vslobodyan/keyb-processor/master/screenshots/exec_1.png "Скрин окна программы")


### Примеры листинга keyb-processor в режиме отслеживания событий

```
$ keyb-processor -c ./configs/work_gnome.yml
keyb-processor (keyboard and mouse events processor)
[sudo] пароль для xxxx: 

Initializing settings from the settings.yml file
Load config: ./configs/work_gnome.yml
Logitech G413 keyboard
Logitech G602 mouse
Razer Nostromo
Logitech Gaming Mouse G600
Notebook Keyboard
Configuration file "./configs/work_gnome.yml" successfully read
Start config change observer
watched_dir = ./configs
patterns = ./configs/work_gnome.yml
/home/vchs/Yandex.Disk/Settings/keyb-processor/processor.py:1203: DeprecationWarning: Please use InputDevice.path instead of InputDevice.fn
  plugged_devices.append((dev.name, _dev_type, dev.fn, dev))
plugged_devices:
  Lid Switch [] /dev/input/event0
  Sleep Button [] /dev/input/event1
  Power Button [] /dev/input/event2
  AT Translated Set 2 keyboard ['keyboard'] /dev/input/event3
  Logitech Gaming Mouse G600 ['mouse'] /dev/input/event4
  Logitech Gaming Mouse G600 Keyboard ['keyboard'] /dev/input/event5
  Logitech Gaming Mouse G600 [] /dev/input/event6
  Logitech G413 Carbon Mechanical Gaming Keyboard ['keyboard'] /dev/input/event7
  Logitech G413 Carbon Mechanical Gaming Keyboard ['keyboard'] /dev/input/event8
  Logitech G413 Carbon Mechanical Gaming Keyboard Consumer Control [] /dev/input/event9
  ETPS/2 Elantech Touchpad [] /dev/input/event10
  Video Bus [] /dev/input/event11
  Video Bus [] /dev/input/event12
  Asus Wireless Radio Control [] /dev/input/event13
  Asus WMI hotkeys [] /dev/input/event14
  PC Speaker [] /dev/input/event15
  USB2.0 HD UVC WebCam: USB2.0 HD [] /dev/input/event16
  HDA Intel HDMI HDMI/DP,pcm=3 [] /dev/input/event17
  HDA Intel HDMI HDMI/DP,pcm=7 [] /dev/input/event18
  HDA Intel HDMI HDMI/DP,pcm=8 [] /dev/input/event19
  HDA Intel HDMI HDMI/DP,pcm=9 [] /dev/input/event20
  HDA Intel HDMI HDMI/DP,pcm=10 [] /dev/input/event21
  HDA Intel PCH Mic [] /dev/input/event22
  HDA Intel PCH Headphone [] /dev/input/event23

Check plugged keyboards and set devices:
  Для клавиатуры Logitech G413 Carbon Mechanical Gaming Keyboard, keyboard ищем соответствующее подключенное устройство
  Нашли соответствующее устройство на /dev/input/event7 и включаем её.
  Для клавиатуры Logitech USB Receiver Keyboard, keyboard ищем соответствующее подключенное устройство
  Соответствующего устройства не нашли но будем ждать его подключения позднее.
  Для клавиатуры Razer Razer Nostromo, keyboard ищем соответствующее подключенное устройство
  Соответствующего устройства не нашли но будем ждать его подключения позднее.
  Для клавиатуры Logitech Gaming Mouse G600 Keyboard, keyboard ищем соответствующее подключенное устройство
  Нашли соответствующее устройство на /dev/input/event5 и включаем её.
  Для клавиатуры AT Translated Set 2 keyboard, keyboard ищем соответствующее подключенное устройство
  Нашли соответствующее устройство на /dev/input/event3 и включаем её.

Run monitor
Grab keyboards
```

### Примеры листинга keyb-processor в режиме executor

```
$ keyb-processor -e
keyb-processor (keyboard and mouse events processor)
Run executor service

Initializing settings from the settings.yml file

Path for plugins: /home/vchs/Yandex.Disk/Settings/keyb-processor/plugins/*.py
Founded plugins: ['xdotool', 'gnome', 'wmctrl']
Import plugins.xdotool module
Initiate "xdotool" plugin.
Import plugins.gnome module
Initiate "gnome" plugin.
Import plugins.wmctrl module
Initiate "wmctrl" plugin.

Available plugins:
  xdotool - Useful window management commands on Xorg using the xdotool.
	Functions:
	minimize - Minimize active window
  gnome - Useful commands for gnome windows and apps.
	Functions:
	raise - Raise window or run app. Parameters: COMMAND WINDOW_NAME (check name in "lg")
	close - Close active window
	minimize - Minimize active window
	lock - Lock screen
  wmctrl - Useful window management commands on Xorg using the wmctrl. Use "wmctrl -lx" to look names.
	Functions:
	raise - Raise first window with defined name or run app. Parameters: COMMAND WINDOW_NAME
	raise_all - Raise all windows with defined name or run app. Parameters: COMMAND WINDOW_NAME
	close - Close active window
Serving on ('127.0.0.1', 5001)
```



### Примеры листинга keyb-processor при выведении списка доступных устройств

```
$ keyb-processor -l
keyb-processor (keyboard and mouse events processor)
[sudo] пароль для xxxx: 
List of available devices:
   /dev/input/event0 "Lid Switch" 
   /dev/input/event1 "Sleep Button" 
   /dev/input/event2 "Power Button" 
   /dev/input/event3 "AT Translated Set 2 keyboard"  <-- KEYBOARD
   /dev/input/event4 "Logitech Gaming Mouse G600"  <-- MOUSE
   /dev/input/event5 "Logitech Gaming Mouse G600 Keyboard"  <-- KEYBOARD
   /dev/input/event6 "Logitech Gaming Mouse G600" 
   /dev/input/event7 "Logitech G413 Carbon Mechanical Gaming Keyboard"  <-- KEYBOARD
   /dev/input/event8 "Logitech G413 Carbon Mechanical Gaming Keyboard"  <-- KEYBOARD
   /dev/input/event9 "Logitech G413 Carbon Mechanical Gaming Keyboard Consumer Control" 
   /dev/input/event10 "ETPS/2 Elantech Touchpad" 
   /dev/input/event11 "Video Bus" 
   /dev/input/event12 "Video Bus" 
   /dev/input/event13 "Asus Wireless Radio Control" 
   /dev/input/event14 "Asus WMI hotkeys" 
   /dev/input/event15 "PC Speaker" 
   /dev/input/event16 "USB2.0 HD UVC WebCam: USB2.0 HD" 
   /dev/input/event17 "HDA Intel HDMI HDMI/DP,pcm=3" 
   /dev/input/event18 "HDA Intel HDMI HDMI/DP,pcm=7" 
   /dev/input/event19 "HDA Intel HDMI HDMI/DP,pcm=8" 
   /dev/input/event20 "HDA Intel HDMI HDMI/DP,pcm=9" 
   /dev/input/event21 "HDA Intel HDMI HDMI/DP,pcm=10" 
   /dev/input/event22 "HDA Intel PCH Mic" 
   /dev/input/event23 "HDA Intel PCH Headphone" 
   /dev/input/event24 "py-evdev-uinput"  <-- KEYBOARD
```