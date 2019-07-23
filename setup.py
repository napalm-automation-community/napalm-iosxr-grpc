"""setup.py file."""
from setuptools import setup, find_packages

__author__ = "Mircea Ulinic <ping@mirceaulinic.net>"

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name="napalm-mos",
    version="2.4.1",
    packages=find_packages(),
    author="Mircea Ulinic",
    author_email="ping@mirceaulinic.net",
    description="Network Automation and Programmability Abstraction Layer with Multivendor support",
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    url="https://github.com/napalm-automation-community/napalm-iosxr-grpc",
    include_package_data=True,
    install_requires=reqs,
)