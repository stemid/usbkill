#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# This is USBKill, based on usbkill by Hephaestos and forked by Stefan Midjich
# into this tool. 
# 
# Please see README.md for more info.

__version__ = "1.0"

import re
import subprocess
import platform
import os, sys, signal
from time import sleep
from datetime import datetime
from ConfigParser import SafeConfigParser, DuplicateSectionError
from argparse import ArgumentParser
from json import loads as jsonloads
from logging import handlers, Formatter, getLogger, StreamHandler

current_platform = platform.system()

# Darwin specific library
if 'DARWIN' in current_platform.upper():
    import plistlib

# We compile this function beforehand for efficiency.
DEVICE_RE = [ re.compile(".+ID\s(?P<id>\w+:\w+)"), re.compile("0x([0-9a-z]{4})") ]

config_files = [
    '/etc/usbkill.conf', 
    './usbkill.conf'
]
config = SafeConfigParser({
    'log_maxsize': '20971520',
    'log_file': '',
    'log_format': '%(asctime)s %(filename)s[%(levelname)s]: %(message)s',
    'log_maxcopies': '2',
    'log_level': 'ERROR',
    'do_sync': 'True',
    'kill_commands': '[]',
    'shutdown': 'True',
    'sleep_time': '0.25',
    'whitelist': '[]',
    'duplicate_check': 'True'
})
config.read(config_files)

# It is required to add this section in memory if the config file does not exist
try:
    config.add_section('usbkill')
except DuplicateSectionError as e:
    pass

# https://docs.python.org/2/library/logging.html#levels
loglevels = {
    'CRITICAL': 50,
    'ERROR': 40,
    'WARNING': 30,
    'INFO': 20,
    'DEBUG': 10,
    'NOTSET': 0
}

# Setup logging
log = getLogger(__name__)
formatter = Formatter(config.get('usbkill', 'log_format', raw = True))

# Add stdout handler
handler = StreamHandler(
    stream = sys.stdout
)
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(loglevels[config.get('usbkill', 'log_level')])

# Add additional handler for file
if config.get('usbkill', 'log_file') is not '':
    handler = handlers.RotatingFileHandler(
        config.get('usbkill', 'log_file'),
        maxBytes = config.getint('usbkill', 'log_maxsize'),
        backupCount = config.getint('usbkill', 'log_maxcopies')
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)

# Log current USB state
def logusb():
    if 'DARWIN' in current_platform.upper():
        usboutput = subprocess.check_output("system_profiler SPUSBDataType", shell=True)
    else:
        usboutput = subprocess.check_output("lsusb", shell=True)

    log.info(usboutput)

# Kills the computer
def kill_computer():
    # Log usb device status
    logusb()
    
    # Sync the filesystem to save recent changes
    if config.get('usbkill', 'do_sync') is 'True':
        log.info('Syncing filesystem')
        os.system("sync")

    # Execute kill commands in order.
    for command in jsonloads(config.get('usbkill', 'kill_commands').strip()):
        log.info('Executing command: {0}'.format(command))
        os.system(command)
        
    if config.get('usbkill', 'shutdown') is 'True':
        # Finally poweroff computer immediately
        if 'DARWIN' in current_platform.upper():
            # OS X (Darwin) - Will halt ungracefully, without signaling apps
            os.system("killall Finder && killall loginwindow && halt -q")
        elif 'BSD' in current_platform.upper():
            # BSD-based systems - Will shutdown
            os.system("shutdown -h now")
        else:
            # Linux-based systems - Will shutdown
            os.system("poweroff -f")
    else:
        log.info('Not shutting down computer, exiting...')
        
    # Exit the process to prevent executing twice (or more) all commands
    sys.exit(0)

# Use OS X system_profiler (native and 60% faster than lsusb port)
def lsusb_darwin():
    df = subprocess.check_output(
        "system_profiler SPUSBDataType -xml -detailLevel mini", 
        shell=True
    )
    df = plistlib.readPlistFromString(df)

    def check_inside(result, devices):
        # Do not take devices with Built-in_Device=Yes
        try:
            result["Built-in_Device"]
        except KeyError:
            # Check if vendor_id/product_id is available for this one
            try:
                assert "vendor_id" in result and "product_id" in result
                # Append to the list of devices
                devices.append(DEVICE_RE[1].findall(result["vendor_id"])[0] + ':' + DEVICE_RE[1].findall(result["product_id"])[0])
            except AssertionError: {}
        
        # Check if there are items inside
        try:
            for result_deep in result["_items"]:
                # Check what's inside the _items array
                check_inside(result_deep, devices)
                    
        except KeyError: {}
        
    # Run the loop
    devices = []
    for result in df[0]["_items"]:
        check_inside(result, devices)
    return devices
    
def lsusb():
    # A Python version of the command 'lsusb' that returns a list of connected usbids
    if 'DARWIN' in current_platform.upper():
        # Use OS X system_profiler (native and 60% faster than lsusb port)
        return lsusb_darwin()
    else:
        # Use lsusb on linux and bsd
        return DEVICE_RE[0].findall(subprocess.check_output("lsusb", shell=True).decode('utf-8').strip())

def reload_handler(signum, frame):
    log.info('Reload signal received, reloading configuration...')
    try:
        config.read(config_files)
    except Exception as e:
        log.error('Failed reloading configuration: {0}'.format(str(e)))
    else:
        log.info('Reloaded configuration')

def exit_handler(signum, frame):
    log.info('Exit signal received, exiting...')
    sys.exit(0)

def main():
    parser = ArgumentParser(
        description = ('USBKill is meant to shutdown the system if USB devices '
                       'change'),
        epilog = 'fork of USBKill by Stefan Midjich'
    )

    parser.add_argument(
        '-S', '--no-shutdown',
        action = 'store_false',
        default = True,
        dest = 'shutdown',
        help = 'do not shutdown the computer, test run'
    )

    parser.add_argument(
        '-D', '--no-duplicate-check',
        action = 'store_false',
        default = True,
        dest = 'duplicate_check',
        help = 'Do not check for duplicate usb IDs'
    )

    parser.add_argument(
        '-d', '--debug',
        action = 'store_true',
        default = False,
        dest = 'debug',
        help = 'Debug output'
    )

    args = parser.parse_args()

    if not os.geteuid() == 0:
        log.error('Must be root')
        sys.exit(1)

    # Register handlers for clean exit of program
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, ]:
        signal.signal(sig, exit_handler)

    signal.signal(signal.SIGUSR1, reload_handler)

    if not args.shutdown:
        config.set('usbkill', 'shutdown', 'False')

    if not args.duplicate_check:
        config.set('usbkill', 'duplicate_check', 'False')

    if args.debug:
        config.set('usbkill', 'log_level', 'DEBUG')
        log.setLevel(loglevels[config.get('usbkill', 'log_level')])
    
    # Start main loop
    start_devices = lsusb()
    acceptable_devices = set(
        start_devices + jsonloads(config.get('usbkill', 'whitelist').strip())
    )

    log.info('Patrolling USB ports every {0} seconds'.format(
        config.getfloat('usbkill', 'sleep_time')
    ))
    logusb()

    while True:
        current_devices = lsusb()

        # Check that no usbids are connected twice.
        # Two devices with same usbid implies a usbid copy attack
        if config.get('usbkill', 'duplicate_check') is 'True':
            if not len(current_devices) == len(set(current_devices)):
                log.debug('Found duplicate USB IDs')
                kill_computer()

        # Check that all current devices are in the set of acceptable devices
        for device in current_devices:
            if device not in acceptable_devices:
                log.debug('Found unacceptable USB device')
                kill_computer()

        # Check that all start devices are still present in current devices
        for device in start_devices:
            if device not in current_devices:
                log.debug('Found discrepancy in current usb device list')
                kill_computer()

        sleep(config.getfloat('usbkill', 'sleep_time'))

if __name__== "__main__":
    main()
