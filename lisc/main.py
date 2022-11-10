#!/usr/bin/env python3

import os
from glob import glob
from importlib import import_module

import click

import lisc.calib


@click.group()
@click.version_option(lisc.__version__, prog_name="LISC toolkit")
def main():
    r"""Low Intensity Sensor Calibration toolkit.

    See 'lisc COMMAND --help' to read about specific subcommand.
    """
    pass  # Entry point


functions = (
    (".init", "dir"),
    (".init", "init"),
    (".init", "save"),
    (".init", "list"),
    (".processing", "perc"),
)

for module_name, method in functions:
    module = import_module(module_name, package="lisc")
    main.add_command(getattr(module, method))


@main.command(name="calib")
@click.argument("cam_key")
@click.argument("images")
@click.argument("darks", nargs=-1)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["NPY", "TIF"], case_sensitive=False),
    default="NPY",
    help="Converted file format. (Default: NPY)",
)
@click.option(
    "-s",
    "--sigma",
    type=float,
    default=5,
    help="Standard deviation used for cosmicray filtering. (Default: 5)",
)
def calib(cam_key, images, darks, format, sigma):
    """Image calibration pipeline.

    CAM_KEY: Camera key for calibration. See the available options with `lisc
    list`.\n
    IMAGES: Image to convert. Altenatively, one can process multiple images by
    passing a string containing a wildcard.\n
    DARKS: Dark images to use for calibration.
    """
    lisc.calib.calib(
        cam_key,
        glob(os.path.expanduser(images)),
        darks,
        fmt=format.lower(),
        sigclip=sigma,
    )
    print("Done.")


@main.command(name="flat")
def flatfield():
    """Process frames for flat field calibration."""
    lisc.calib.flatfield()
    print("Done.")


@main.command(name="lin")
@click.option(
    "-s",
    "--size",
    type=int,
    default=50,
    help="Size of the window to process. (Default: 50)",
)
def linearity(size):
    """Process frames for linearity calibration."""
    lisc.calib.linearity(size)
    print("Done.")


@main.command(name="photo")
@click.option("-r", "--radius", type=float, default=50)
@click.option("-w", "--drift-window", type=int, default=200)
def photometry(radius, drift_window):
    """Process frames for stellar photometry calibration.

    Integrates the stellar flux using a disk of radius RADIUS pixels.
    The star used is identified by it's ID in the Yale Bright Star Catalog.
    """

    lisc.calib.photometry(r=radius, drift_window=drift_window)
    print("Done.")


@main.command(name="geo")
def starfield():
    """Process frames for star field calibration."""
    lisc.calib.starfield()
    print("Done.")
