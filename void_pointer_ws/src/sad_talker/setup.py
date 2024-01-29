#!/usr/bin/env python3.8
from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup()
d["packages"] = ["sad_talker"]
d["package_dir"] = {"": "src"}
setup(**d)
