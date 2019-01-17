"""
$ loginctl
$ loginctl list-sessions --no-legend
показывает кто залогинен и на какой консоли

$ sudo fgconsole
7

$ cat /sys/class/tty/tty0/active
tty8


Показать консоли и юзеров
$ loginctl list-sessions --no-legend

- Состояние консоли
- $ loginctl show-session -p State c2
- State=active
- $ loginctl show-session -p State 7
- State=online
- Не дает ничего нужного.

"""

# 1. Детектим изменения в логе иксов или lightdm

# 2. При изменениях в логе проверяем какая сейчас консоль активна и смотрим какой юзер на ней.

# 3. Если юзер отличается от прописанного в конфиге - отключаем обработку сигналов и все их пропускаем.
# Иначе - наоборот, включаем обработку сигналов в соответствии с конфигом.

