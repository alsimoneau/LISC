from setuptools import find_packages, setup

import lisc

setup(
    name="LISC",
    version=lisc.__version__,
    description="Low Intensity Sensor Calibration",
    url="https://github.com/alsimoneau/lisc",
    author="Alexandre Simoneau",
    author_email="alsimoneau@gmail.com",
    liscence="MIT",
    packages=find_packages("."),
    zip_safe=False,
    install_requires=[
        "Click",
        "imageio",
        "joblib",
        "matplotlib",
        "numpy",
        "pandas",
        "progressbar2",
        "pyexiftool",
        "pyyaml",
        "rawpy",
        "requests",
        "scipy",
        "astroscrappy@git+https://github.com/astropy/astroscrappy@main",
    ],
    entry_points="""
        [console_scripts]
        lisc=lisc.main:main
    """,
)
