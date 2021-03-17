#!/usr/bin/env python3
#
# LISC toolkit
# Linearity processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: March 2021

import click
import os
import numpy as np
import pandas as pd
from glob import glob
import exiftool
from utils import open_clipped as Open, sub, glob_types
import yaml

@click.command(name="lin")
def CLI_linearity():
    """Process frames for linearity calibration.
    """
    linearity()
    print("Done.")

def linearity(size=25):
    set_times = { int(fname.split(os.sep)[-1].split('_')[0]) for fname in glob("LINEARITY/*.*") }

    with open("params") as f:
        params = yaml.safe_load(f)
    Nx = params['width']
    Ny = params['height']
    mask = np.zeros((Ny,Nx),dtype=np.bool8)
    mask[Ny//2 - size: Ny//2 + size + 1, Nx//2 - size: Nx//2 + size + 1] = True

    data = []
    for ss in sorted(set_times):
        frame = Open(f"LINEARITY/{ss}_*")
        with exiftool.ExifTool() as et:
            exif = et.get_metadata(glob_types(f"LINEARITY/{ss}_*")[0])
        exp = exif['MakerNotes:SonyExposureTime2']
        dark = Open(f"LINEARITY/DARKS/{ss}_*")
        frame = sub(frame,dark)

        print(exp,*frame[mask].mean(0))
        data.append((exp,*frame[mask].mean(0)))

    pd.DataFrame(data,columns=["Exposure","R","G","B"]).to_csv("linearity.csv")
