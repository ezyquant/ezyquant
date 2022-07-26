from setuptools import find_packages, setup

NAME = "ezyquant"
VERSION = "0.1.4"

setup(
    name=NAME,
    packages=find_packages(include=["ezyquant", "ezyquant.*"]),
    version=VERSION,
    description="Powerful backtest python library for Thai stocks",
    long_description="Powerful backtest python library for Thai stocks",
    author="Fintech (Thailand) Company Limited",
    author_email="admin@fintech.co.th",
    url="https://github.com/ezyquant/ezyquant",
    maintainer="Fintech (Thailand) Company Limited",
    maintainer_email="admin@fintech.co.th",
    install_requires=["pandas>=1.4", "sqlalchemy>=1.4", "ta>=0.10", "XlsxWriter>=3.0"],
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
        "Source": "https://github.com/bukosabino/ta",
    },
)
