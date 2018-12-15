"""Исполнитель команд в пространстве клиента.
Запускается из-под клиента и ожидает от обработчика событий всех клавиатур указаний на выполнение команд.
Также возможны операции с окнами программ, запущенными у клиента.

Were helpful:
1. https://asyncio.readthedocs.io/en/latest/tcp_echo.html
2. https://stackoverflow.com/questions/15190362/sending-a-dictionary-using-sockets-in-python
"""


import asyncio
import json
import subprocess

from settings import settings

import plugins



# Received '{"key": "TET&#$%Ssdfsdfdhggfdhgf78", "plugin": "gnome", "command": ["raise_or_run", "opera", "Opera"' from ('127.0.0.1', 57448)

# Send to executioner: '{"key": "TET&#$%Ssdfsdfdhggfdhgf78", "command": ["raise_or_run", "opera", "Opera"], "plugin": "gnome"}'
#
# Received '{"key": "TET&#$%Ssdfsdfdhggfdhgf78", "command": ["raise_or_run", "opera", "Opera"], "plugin": "gnome' from ('127.0.0.1', 57478)

def process_command(message):
    # 1. Разбор строки как словаря
    message_dict = json.loads(message)
    print('message_dict: %s' % message_dict)
    # 2. Проверка на безопасность
    if "key" in message_dict and message_dict["key"]==settings.key:
        print('Прошли проверку безопасности.')
        command = None
        # Проверка наличия команды
        if "command" in message_dict:
            command = message_dict["command"]
            # Уточнение типа команды
            if "plugin" in message_dict:
                plugin = message_dict["plugin"]
                if plugin:
                    print('Need plugin: %s' % plugin)
            # Запускаем указанную команду
            print('We will run next command: %s' % command)
            # subprocess.run(command)



async def handle_echo(reader, writer):
    # data = await reader.read(100)
    data = await reader.read(1024)

    message = data.decode()
    addr = writer.get_extra_info('peername')
    print("Received %r from %r" % (message, addr))
    process_command(message)
    answer = 'Done'
    print("Send: %r" % answer)
    writer.write(answer.encode())
    await writer.drain()

    # print("Close the client socket")
    writer.close()


def Main():
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_echo, settings.host, settings.port, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    Main()
