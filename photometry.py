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
from utils import open_clipped, open_raw, sub

@click.command(name="photometry")
def CLI_photometry():
    """Process frames for stellar photometry calibration.
    """
    photometry()
    print("Done.")

def photometry(N=10):
    dark = open_clipped("PHOTOMETRY/DARKS/*")

    outs = pd.DataFrame(columns=["Filename","X","Y","R","G","B"])
    for i,fname in enumerate(sorted(glob(f"PHOTOMETRY/*.*"))):
        im = sub(open_raw(fname), dark)
        idy, idx = np.where( np.sum(im,2) == np.max(np.sum(im,2)) )
        idx, idy = idx[0], idy[0]
        print(f"Found star at: {idx}, {idy}")
        rad = np.sum( im[idy-N:idy+N,idx-N:idx+N], (0,1) ) - \
            np.sum( im[idy-N:idy+N,idx-(3*N):idx-N], (0,1) )
        outs.loc[i] = [fname[len("PHOTOMETRY/"):], idx, idy, *rad]

    outs.to_csv("photometry.csv")
