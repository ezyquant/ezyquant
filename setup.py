import re

from setuptools import find_packages, setup

NAME = "ezyquant"

VERSIONFILE = "ezyquant/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(
    name=NAME,
    packages=find_packages(include=["ezyquant", "ezyquant.*"]),
    version=verstr,
    description="Powerful backtest python library for Thai stocks",
    long_description="Powerful backtest python library for Thai stocks",
    author="Fintech (Thailand) Company Limited",
    author_email="admin@fintech.co.th",
    url="https://doc.ezyquant.com/",
    maintainer="Fintech (Thailand) Company Limited",
    maintainer_email="admin@fintech.co.th",
    python_requires=">=3.8.6",
    install_requires=[
        "pandas>=1.3",
        "sqlalchemy>=1.4",
        "psycopg2-binary>=2.9",
        "ta>=0.10",
        "XlsxWriter>=3.0",
        "typing_extensions>=4.4",
    ],
    license="The MIT License (MIT)",
    classifiers=[
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    project_urls={
        "Documentation": "https://doc.ezyquant.com/",
        "Bug Reports": "https://github.com/ezyquant/ezyquant/issues",
        "Source": "https://github.com/ezyquant/ezyquant",
    },
)
