from setuptools import find_packages, setup

VERSION = "0.0.0"

setup(
    name="ezyquant",
    version=VERSION,
    packages=find_packages(),
    python_requires=">=3.8.0",
    install_requires=["pandas>=1.4", "sqlalchemy>=1.4", "ta>=0.10"],
)
