from setuptools import setup

setup(
    name='LISC',
    version='0.1.001',
    py_modules=['main'],
    install_requires=[
        'Click',
        'numpy',
        'matplotlib',
        'pyexiftool',
        'rawpy'
    ],
    entry_points='''
        [console_scripts]
        lisc=main:lisc
    ''',
)
