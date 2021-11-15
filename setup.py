from setuptools import setup
import lisc

setup(
    name='LISC',
    version=lisc.__version__,
    description="Low Intensity Sensor Calibration",
    url="https://github.com/alsimoneau/lisc",
    author="Alexandre Simoneau",
    author_email="alsimoneau@gmail.com",
    liscence="MIT",
    packages=['lisc'],
    zip_safe=False,
    install_requires=[
        'Click',
        'numpy',
        'matplotlib',
        'pyyaml',
        'pandas',
        'scipy',
        'pyexiftool',
        'rawpy',
        'imageio',
        'requests',
        'progressbar2',
        'astroscrappy@git+https://github.com/astropy/astroscrappy@master'
    ],
    entry_points='''
        [console_scripts]
        lisc=lisc.main:lisc
    ''',
)
