#!/usr/bin/env python3
#
# LISC toolkit
# Image calibration
#
# Author : Alexandre Simoneau
#
# Created: March 2021
# Edited: March 2021

import click
import numpy as np
import pandas as pd
from glob import glob
import os
from utils import *

@click.command(name="calib")
@click.argument("images")
@click.argument("darks",required=True,nargs=-1)
def CLI_calib(images,darks):
    """Image calibration.
    """
    calib(glob(os.path.expanduser(images)),darks)
    print("Done.")

def calib(images,darks):
    lin_data = pd.read_csv("linearity.csv")
    flat_data = np.load("flatfield.npy")
    dark = open_clipped(darks)
    photo = np.loadtxt("photometry.dat")

    for fname in images:
        im = cosmicray_removal(sub(open_raw(fname),dark))
        data = correct_flat(correct_linearity(im,lin_data),flat_data)
        data *= photo

        np.save(fname.rsplit('.',1)[0], data)
