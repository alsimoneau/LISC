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
import imageio

@click.command(name="calib")
@click.argument("cam_key")
@click.argument("images")
@click.argument("darks",nargs=-1)
@click.option('-f',"--format",type=click.Choice(['NPY', 'TIF'],
    case_sensitive=False),default="NPY",help="Converted file format. (Default: NPY)")
@click.option('-s',"--sigma",type=float,default=5,
    help="Standard deviation used for cosmicray filtering. (Default: 5)")
def CLI_calib(cam_key,images,darks,format,sigma):
    """Image calibration pipeline.

    CAM_KEY: Camera key for calibration. See the available options with `lisc list`.\n
    IMAGES: Image to convert. Altenatively, one can process multiple images by passing a string containing a wildcard.\n
    DARKS: Dark images to use for calibration.
    """
    calib(
        cam_key,
        glob(os.path.expanduser(images)),
        darks,
        fmt=format.lower(),
        sigclip=sigma
    )
    print("Done.")

def calib(cam_key,images,darks,fmt="npy",sigclip=5):
    datadir = os.path.expanduser(f"~/.LISC/{cam_key}/")
    lin_data = pd.read_csv(datadir+"linearity.csv")
    flat_data = np.load(datadir+"flatfield.npy")
    dark = open_clipped(darks)
    photo = np.loadtxt(datadir+"photometry.dat")

    for fname in images:
        print(f"Calibrating '{fname}'...")
        with exiftool.ExifTool() as et:
            exif = et.get_metadata(fname)
        exp = float(exif['MakerNotes:SonyExposureTime2'])

        im = cosmicray_removal(sub(open_raw(fname),dark),sigclip=sigclip)
        data = correct_flat(correct_linearity(im,lin_data),flat_data)
        data *= photo / exp

        if fmt=="npy":
            np.save(fname.rsplit('.',1)[0], data)
        elif fmt=="tif":
            imageio.imsave(fname.rsplit('.',1)[0]+".tif", data)
