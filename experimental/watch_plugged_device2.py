import pyudev
import asyncio

async def monitor_devices(self) -> None:
    monitor = pyudev.Monitor.from_netlink(self.__context)
    monitor.filter_by('usb')

    while True:
        device = monitor.poll(0)
        if device is None:
            await asyncio.sleep(1.0)
            continue

        device = Device(device)
        self.__options.print_very_verbose('{0.action} on {0.device_path}'.format(device))
        if device.action == "add":
            if self.__is_a_device_we_care_about(device):
                await self.device_added.fire(device)
        elif device.action == "remove":
            await self.device_removed.fire(device)
