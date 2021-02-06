#!/usr/bin/env python3

import click
from importlib import import_module

@click.group()
@click.version_option("0.1.001",prog_name="LISC toolkit")
def lisc():
    r"""Low Intensity Sensor Calibration toolkit.

    See 'lisc COMMAND --help' to read about specific subcommand.
    """
    pass # Entry point

# functions = (
# )
#
# for module_name,method in functions:
#     module = import_module(module_name)
#     lisc.add_command(getattr(module,method))
