"""
https://stackoverflow.com/questions/15944987/python-evdev-detect-device-unplugged
https://pyudev.readthedocs.io/en/latest/guide.html#monitoring-devices
"""

# import functools
import pyudev
import evdev

# from evdev import InputDevice
# from select import select

context = pyudev.Context()
# monitor = pyudev.Monitor.from_netlink(context)
# monitor.filter_by(subsystem='input')
# monitor.start()
#
# fds = {monitor.fileno(): monitor}
# finalizers = []

# print('List BLOCK devices:')
# for device in context.list_devices(subsystem='block'):
#     print('{0} ({1})'.format(device['DEVNAME'], device['DEVTYPE']))

plugged_devices = {
                    '/dev/input/event5': 'Logitech Mouse',
                    '/dev/input/event6': 'Logitech Keyboard',
                    }

print('List INPUT devices:')
for device in context.list_devices(subsystem='input'):
    dev_name = None
    dev_path = None
    suffix = ''
    if 'DEVNAME' in device:
        dev_name = device['DEVNAME']
        if dev_name in plugged_devices:
            suffix = ' (found in settings as %s)' % plugged_devices[dev_name]
        dev_path = ''
    else:
        dev_path = 'path=%s' % device['DEVPATH']

    if 'DEVNAME' in device:
        print('Device at %s %s %s' % (dev_name, dev_path, suffix))
    # for key in device:
    #     print(' %s: %s' % (key, device[key]))


print('Now start monitor..')

monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('input')
for device in iter(monitor.poll, None):
    # print('Событие с утройством %s' % device)
    suffix = ''
    if 'DEVNAME' in device:
        dev_name = device['DEVNAME']
        if dev_name in plugged_devices:
            suffix = ' (found in settings as %s)' % plugged_devices[dev_name]
        print('{0} input device {1}{2}'.format(device.action, dev_name, suffix))
        if format(device.action) == 'remove':
            '''
            ungrab_keyaboard()
            keyboard.enabled = false
            keyboard.dev = None
            keyboard.address = None
            
            '''
            pass
        if format(device.action) == 'add':
            ev_device = evdev.InputDevice(dev_name)
            print('  ev_device.name: %s' % ev_device.name)
            '''
            get capabilities
            get_type
            if name==name and type==type:
                grab_keyaboard()
            
            
            '''

    # if 'ID_FS_TYPE' in device:
    #     print('{0} partition {1}'.format(device.action, device.get('ID_FS_LABEL')))

