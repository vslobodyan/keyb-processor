import socket
import sys
import keyb_settings



"""Исполнитель команд в пространстве клиента.
Запускается из-под клиента и ожидает от обработчика событий всех клавиатур указаний на выполнение команд.
Также возможны операции с окнами программ, запущенными у клиента.

Based on:
1. https://asyncio.readthedocs.io/en/latest/tcp_echo.html
"""

def Main():
    host = '127.0.0.1'
    port = 5001

    mySocket = socket.socket()
    mySocket.connect((host, port))

    message = ' '.join(sys.argv[1:])

    if message:
        mySocket.send(message.encode())
        data = mySocket.recv(1024).decode()

        print('Received from server: ' + data)

    # message = input(" -> ")

    # while message != 'q':
    #        mySocket.send(message.encode())
    #        data = mySocket.recv(1024).decode()
    #
    #        print ('Received from server: ' + data)
    #
    #        message = input(" -> ")

    mySocket.close()


if __name__ == '__main__':
    Main()
