#!/usr/bin/env python3
#
# LISC toolkit
# Image calibration
#
# Author : Alexandre Simoneau
#
# Created: March 2021
# Edited: April 2021

import click
import numpy as np
import pandas as pd
from glob import glob
import os
import exiftool
from utils import *

@click.command(name="calib")
@click.argument("cam_key")
@click.argument("images")
@click.argument("darks",nargs=-1)
def CLI_calib(cam_key,images,darks):
    """Image calibration.
    """
    calib(cam_key,glob(os.path.expanduser(images)),darks)
    print("Done.")

# TODO: Add cosmicray parameters to CLI
def calib(cam_key,images,darks):
    datadir = os.path.expanduser(f"~/.LISC/{cam_key}/")
    lin_data = pd.read_csv(datadir+"linearity.csv")
    flat_data = np.load(datadir+"flatfield.npy")
    dark = open_clipped(darks)
    photo = np.loadtxt(datadir+"photometry.dat")

    for fname in images:
        with exiftool.ExifTool() as et:
            exif = et.get_metadata(fname)
        exp = float(exif['MakerNotes:SonyExposureTime2'])

        im = cosmicray_removal(sub(open_raw(fname),dark))
        data = correct_flat(correct_linearity(im,lin_data),flat_data)
        data *= photo / exp

        np.save(fname.rsplit('.',1)[0], data)
