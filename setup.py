#!/usr/bin/env python3

import codecs
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
  try:
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
      return fp.read()
  except IOError:
    return ""


def find_version(*file_paths):
  version_file = read(*file_paths)
  version_match = re.search(
    r"^__version__ = ['\"]([^'\"]*)['\"]",
    version_file,
    re.M,
  )
  if version_match:
    return version_match.group(1)

  raise RuntimeError("Unable to find version string.")


def load_requirements():
  data = read("requirements.txt")
  return data.split("\n")


setup(
  name="disks",
  version=find_version("src", "disks", "__init__.py"),
  description="Display list of disks in the system",
  long_description="Display list of disks in the system",
  license='MIT',
  classifiers=[
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
  ],

  author='The storage developers',

  package_dir={"": "src"},
  packages=find_packages(
    where="src",
    exclude=["contrib", "docs", "tests*", "tasks"],
  ),
  install_requires=load_requirements(),
  entry_points={
    "console_scripts": [
      "disks=disks.disks:main",
      ],
  },
  zip_safe=True,
  python_requires='>=3.7',
)
