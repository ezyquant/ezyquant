from setuptools import find_packages, setup

NAME = "ezyquant"
VERSION = "0.1.1"

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(),
    python_requires=">=3.8.0",
    install_requires=["pandas>=1.4", "sqlalchemy>=1.4", "ta>=0.10", "XlsxWriter>=3.0"],
)
