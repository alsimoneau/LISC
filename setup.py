from setuptools import setup

setup(
    name='LISC',
    version='0.1.1',
    description="Low Intensity Sensor Calibration",
    author="Alexandre Simoneau",
    py_modules=[
        'main',
        'linearity',
        'flatfield',
        'photometry',
        'init'
        'utils'],
    install_requires=[
        'Click',
        'numpy',
        'matplotlib',
        'pyexiftool',
        'rawpy',
        'astroscrappy@git+https://github.com/astropy/astroscrappy@master',
        'ccdproc',
        'pyyaml'
    ],
    entry_points='''
        [console_scripts]
        lisc=main:lisc
    ''',
)
