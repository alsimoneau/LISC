#!/usr/bin/env python3
#
# LISC toolkit
# Stellar photometry processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: March 2021

import click
import numpy as np
import pandas as pd
import rawpy
from glob import glob
import os
import exiftool
from utils import *

@click.command(name="photo")
def CLI_photometry():
    """Process frames for stellar photometry calibration.
    """
    photometry()
    print("Done.")

def photometry(r=10,initial=(2390,1642),drift_window=16):
    dark = open_clipped("PHOTOMETRY/DARKS/*")

    idx,idy = initial
    outs = pd.DataFrame(columns=["Filename","SAT","X","Y","R","G","B","sR","sG","sB","bR","bG","bB"])
    for i,fname in enumerate(sorted(glob_types(f"PHOTOMETRY/*"))):
        im = sub(open_raw(fname), dark)
        crop = im[idy-drift_window:idy+drift_window,idx-drift_window:idx+drift_window]
        y,x = np.where( np.sum(crop,2) == np.max(np.sum(crop,2)) )
        idx += x[0] - drift_window
        idy += y[0] - drift_window
        print(f"Found star at: {idx}, {idy}")

        star_mask = circle_mask(idx,idy,im.shape,r)
        star = np.sum(im[star_mask],0)
        bgnd_mask = circle_mask(idx,idy,im.shape,2*r) \
            & ~circle_mask(idx,idy,im.shape,1.5*r)
        bgnd = np.sum(im[bgnd_mask],0) * np.sum(star_mask) / np.sum(bgnd_mask)

        rad = star - bgnd

        outs.loc[i] = [
            fname[len("PHOTOMETRY/"):],
            (im[star_mask] > 60000).any(),
            idx, idy,
            *rad, *star, *bgnd
        ]

    outs.to_csv("photometry.csv")
