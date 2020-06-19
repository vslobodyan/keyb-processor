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

from plugins import Plugins


class Executor:
    plugins = None

    def process_command(self, message):
        # 1. Разбор строки как словаря
        message_dict = json.loads(message)
        print('message_dict: %s' % message_dict)
        # 2. Проверка на безопасность
        if "key" in message_dict and message_dict["key"] == settings.key:
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
                if plugin:
                    plugin_command = command[0]
                    plugin_args = command[1:]
                    if plugin in self.plugins.available:
                        # Плагин есть в загруженных
                        if plugin_command in self.plugins.available[plugin].functions.available:
                            # Run function
                            self.plugins.available[plugin].functions.available[plugin_command].func(plugin_args)

                        else:
                            print('Function "%s" not found in that plugin.' % plugin_command)
                    else:
                        print('Plugin "%s" not found.' % plugin)
                else:
                    # Если команда не требует плагина - просто выполняем её.
                    subprocess.run(command)

    def __init__(self):
        self.plugins = Plugins()
        self.plugins.print()


async def handle_echo(reader, writer):
    # data = await reader.read(100)
    data = await reader.read(1024)

    message = data.decode()
    addr = writer.get_extra_info('peername')
    print("\nReceived %r from %r" % (message, addr))
    executor.process_command(message)
    answer = 'Done'
    print("\nSend: %r" % answer)
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
    executor = Executor()
    Main()
