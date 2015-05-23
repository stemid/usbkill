# USBKill

A tool that shuts down your computer if USB devices change, for example if you unplug or plug-in a device. 

## Run

    sudo python usbkill.py

## Depends on

  * Python 2.7

## Installation

    python setup.py install

## Configuration

Sample configuration file with defaults filled in.

    [usbkill]
    log_maxsize: 20971520
    log_file: 
    log_format: %(asctime)s %(filename)s[%(levelname)s]: %(message)s
    log_maxcopies: 2
    log_level: ERROR
    do_sync: True
    kill_commands: []
    shutdown: True
    sleep_time: 0.25
    whitelist: []
    duplicate_check: True

See `python usbkill.py --help` for more info. 

# Fork info

This is a fork of [https://github.com/hephaest0s/usbkill](usbkill) by hephaest0s. 

I've kept most of the features so please do check the original README, but here is a list of changes. 

  * Depends on argparse instead of doing its own parsing of sys.argv
  * No Python3 support with ConfigParse (KISS: not necessary)
  * Depends on logger instead of implementing its own solution
  * No shredding of logs or data supported (KISS: should be handled separately)
  * Added ability to reload configuration file when SIGUSR1 is received
  * Limited the configuration files to ./usbkill.conf and /etc/usbkill.conf (KISS)
  * Added option to skip duplicate USB IDs checking (only to resolve the original issue I had on F21 and Ubuntu 14)


# Contact

Stefan Midjich (contact me through github)
