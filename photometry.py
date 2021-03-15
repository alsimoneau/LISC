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

    tots = []
    #star = np.zeros((2*N,2*N,3))
    #bg = np.zeros((2*N,2*N,3))
    for fname in sorted(glob(f"PHOTOMETRY/*.*")):
        im = sub(open_raw(fname), dark)
        idy, idx = np.where( np.sum(im,2) == np.max(np.sum(im,2)) )
        idx, idy = idx[0], idy[0]
        print(f"Found star at: {idx}, {idy}")
        tots.append(
            np.sum( im[idy-N:idy+N,idx-N:idx+N], (0,1) ) -
            np.sum( im[idy-N:idy+N,idx-(3*N):idx-N], (0,1) )
        )
        #star += im[idy-N:idy+N,idx-N:idx+N]
        #bg += im[idy-N:idy+N,idx-(3*N):idx-N]

    np.savetxt("integrated",tots)
    #np.save("star",star)
    #np.save("background",bg)
