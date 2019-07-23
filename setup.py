"""setup.py file."""
from setuptools import setup, find_packages

__author__ = "Mircea Ulinic <ping@mirceaulinic.net>"

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name="napalm-iosxr-grpc",
    version="0.0.1a1",
    packages=find_packages(exclude=("test*",)),
    author="Mircea Ulinic",
    author_email="ping@mirceaulinic.net",
    description="Network Automation and Programmability Abstraction Layer with Multivendor support",
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    url="https://github.com/napalm-automation-community/napalm-iosxr-grpc",
    include_package_data=True,
    install_requires=reqs,
)
