from setuptools import setup

setup(
    name='LISC',
    version='0.1.2',
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
        'astroscrappy@git+https://github.com/astropy/astroscrappy@master'
    ],
    entry_points='''
        [console_scripts]
        lisc=lisc.main:lisc
    ''',
)
