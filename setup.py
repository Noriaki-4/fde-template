"""Setup configuration for FDE Template"""

from setuptools import find_packages, setup

setup(
    name="fde-template",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "fde=cli.fde_cli:cli",
        ],
    },
    python_requires=">=3.11",
)
