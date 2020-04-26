"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="CircuitPython_SPS30",
    description="CircuitPython driver for Sensiron's SPS30 Particulate Matter sensor",
    url="https://github.com/Jacksonbaker323/CircuitPython_SPS30",
    author="Jackson Baker",
    author_email="Jackson@jacksonbaker.net",
    install_requires=["adafruit-circuitpython-busdevice"],
    license="GPLv3",
    keywords="sensiron sps30 hardware micropython circuitpython",
    py_modules=["sensiron_sps30"],
)
