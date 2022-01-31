#!/usr/bin/env python3

from importlib import import_module

import click

import lisc


@click.group()
@click.version_option(lisc.__version__, prog_name="LISC toolkit")
def lisc():
    r"""Low Intensity Sensor Calibration toolkit.

    See 'lisc COMMAND --help' to read about specific subcommand.
    """
    pass  # Entry point


functions = (
    (".linearity", "CLI_linearity"),
    (".flatfield", "CLI_flatfield"),
    (".photometry", "CLI_photometry"),
    (".starfield", "CLI_starfield"),
    (".calib", "CLI_calib"),
    (".init", "dir"),
    (".init", "init"),
    (".init", "save"),
    (".init", "list"),
)

for module_name, method in functions:
    module = import_module(module_name, package="lisc")
    lisc.add_command(getattr(module, method))
