#!/usr/bin/env python3

import os

import click
import imageio
import numpy as np
import pandas as pd

import lisc.utils


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "-p",
    "--percentile",
    default=[100, 99, 95, 90],
    type=float,
    multiple=True,
    help="The percentile value to extract. Can be specified multiple times.",
)
def perc(filename, percentile):
    """Extract percentile from images"""
    percentile = np.asarray(sorted(percentile, reverse=True))
    if np.all(percentile < 1):
        print("WARNING: All percentiles below 1. Expected to be in [0:100].")

    try:
        im = lisc.utils.open_raw(filename)
    except TypeError as err:
        try:
            im = imageio.imread(filename)
        except OSError:
            raise err

    perc = np.percentile(im, percentile, (0, 1))

    if len(perc) == 1:
        print(f"R = {perc[0,0]:.2g}    G = {perc[0,1]:.2g}    B = {perc[0,2]:.2g}")
    else:
        print(pd.DataFrame(perc, index=percentile, columns=["R", "G", "B"]))


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.argument("weights", nargs=3, type=float, default=[1 / 3, 1 / 3, 1 / 3])
def gray(filename, weights):
    im = imageio.imread(filename)
    gr = np.dot(im, weights)
    name, ext = os.path.splitext(filename)
    imageio.imwrite("".join([name, "_gr", ext]), gr)
