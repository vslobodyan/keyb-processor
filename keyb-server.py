# https://shakeelosmani.wordpress.com/2015/04/13/python-3-socket-programming-example/
# https://github.com/meeuw/injectinput/blob/master/injectinput/injectinput.py

import socket

# need python-evdev in manjaro
import evdev
#import sys
#import time

#import subprocess


def keyb_inject(keyb_input):
    with evdev.UInput() as ui:
        escape = False

        print('We received codes: %s' % keyb_input)

        # Press
        for one_key_code in keyb_input:
            key = evdev.ecodes.ecodes['KEY_'+one_key_code.upper()]
            ui.write(evdev.ecodes.EV_KEY, key, 1)
        ui.syn()
        # Release
        for one_key_code in keyb_input:
            key = evdev.ecodes.ecodes['KEY_' + one_key_code.upper()]
            ui.write(evdev.ecodes.EV_KEY, key, 0)
        ui.syn()

        #time.sleep(.05)


def Main():
    host = "127.0.0.1"
    port = 5001
     
    mySocket = socket.socket()
    need_exit = False
    mySocket.bind((host,port))
    mySocket.listen(1)

    while not need_exit:
        conn, addr = mySocket.accept()
        print ("Connection from: " + str(addr))
        while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                if data=="q":
                    need_exit = True
                    break

                keyb_inject(data.split())

                print ("from connected  user: " + str(data))
             
                data = str(data).upper()
                print ("sending: " + str(data))
                conn.send(data.encode())
             
    conn.close()
     
if __name__ == '__main__':
    Main()
