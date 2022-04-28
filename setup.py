from setuptools import find_packages, setup

VERSION = "0.0.1"


def requirements(path):
    with open(path, "r") as f:
        return f.read().splitlines()


setup(
    name="ezyquant",
    version=VERSION,
    packages=find_packages(),
    python_requires=">=3.6.0",
    install_requires=requirements("requirements.txt"),
)
