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
from glob import glob
import exiftool
from utils import open_clipped as Open
from utils import sub

@click.command(name="linearity")
def CLI_linearity():
    """Process frames for linearity calibration.
    """
    linearity()
    print("Done.")

def linearity():
    set_times = { int(fname.split(os.sep)[-1].split('_')[0]) for fname in glob("LINEARITY/*.*") }

    data = []
    for ss in sorted(set_times):
        frame = Open(glob(f"LINEARITY/{ss}_*"))
        with exiftool.ExifTool() as et:
            exif = et.get_metadata(glob(f"LINEARITY/{ss}_*")[0])
        exp = exif['MakerNotes:SonyExposureTime2']
        dark = Open(glob(f"LINEARITY/DARKS/{ss}_*"))
        frame = sub(frame,dark)

        print(exp,*frame.mean((0,1)))
        data.append((exp,*frame.mean((0,1))))

    pd.DataFrame(data,columns=["Exposure","R","G","B"]).to_csv("linearity.csv")
