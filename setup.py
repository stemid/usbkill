import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "USBKill",
    version = "1.0",
    author = "Stefan Midjich",
    author_email = "swehack@gmail.com",
    description = ("A tool that shuts down your computer if USB devices"
                   " change"),
    license = "GPLv3",
    keywords = "usb shutdown privacy",
    url = "https://github.com/stemid/usbkill",
    packages = find_packages(),
    scripts = ['usbkill.py'],
    entry_points = {
        'console_scripts': [
            'usbkill = usbkill:main'
        ]
    },
    long_description = read('README.md'),
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
