# from evdev import *
import evdev

dev_addr = '/dev/input/event12'

ui = evdev.UInput()

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
    ui.write_event(event)
    ui.syn()

ui.close()
dev.ungrab()


# ev = InputEvent(1334414993, 274296, ecodes.EV_KEY, ecodes.KEY_A, 1)
# with UInput() as ui:
#     ui.write_event(ev)
#     ui.syn()


#
# ui = UInput()
#
# # accepts only KEY_* events by default
# ui.write(e.EV_KEY, e.KEY_A, 1)  # KEY_A down
# ui.write(e.EV_KEY, e.KEY_A, 0)  # KEY_A up
# ui.syn()
#
# ui.close()
