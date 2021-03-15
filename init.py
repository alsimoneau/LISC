#!/usr/bin/env python3
#
# LISC toolkit
# Folder initialisation
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: March 2021

import click
import os
import exiftool
from glob import glob
import pandas as pd
import yaml

@click.command()
@click.argument('folder_name', type=click.Path(exists=False), default='.')
def dir(folder_name):
    """Initialize calibration directory structure.

    FOLDER_NAME is the folder name the directory structure will be created into.
    If ommited, will create it in the current directory instead.
    """
    folders = [
        'FLATFIELD',
        'LINEARITY',
        'PHOTOMETRY'
    ]
    for fold_name in folders:
        os.makedirs(os.path.join(folder_name,fold_name,"DARKS"))
    os.makedirs(os.path.join(folder_name,"STARFIELD"))

    config  = ["# Config file for LISC calibration procedure"]
    config.append("device model: ")
    config.append("lens model: " )
    config.append("focainitl lenght: # in mm" )
    config.append("resolution: # [X, Y]")
    config.append("pixel size: # in µm")

    with open(os.path.join(folder_name,"config.ini"),'w') as f:
        f.write('\n'.join(config))

@click.command()
def init():
    """Initialize calibration procedure.

    Validate that datafiles are present and reads metadata to prepare
    for processing.
    """

    error = False

    # Validate LINEARITY
    #     EXP_i.arw
    #     Same for darks

    if not glob("LINEARITY/*_*.*"):
        print("ERROR: No linearity data.")
        error = True

    if not glob("LINEARITY/DARKS/*_*.*"):
        print("ERROR: No darks for linearity data.")
        error = True

    # Validate FLATFIELD
    #     image_X_Y.arw
    #     few darks

    if not glob("FLATFIELD/image_*_*.*"):
        print("ERROR: No flat field data.")
        error = True

    if not glob("FLATFIELD/DARKS/*.*"):
        print("ERROR: No darks for flat field data.")
        error = True

    # Validate PHOTOMETRY
    #     bunch of images and darks

    if not glob("PHOTOMETRY/*.*"):
        print("ERROR: No photometry data.")
        error = True

    if not glob("PHOTOMETRY/DARKS/*"):
        print("ERROR: No darks for photometry data.")
        error = True

    # Validate STARFIELD
    #     csv file with appropriate columns
    try:
        a = pd.read_csv("STARFIELD/starfield.csv")
    except:
        print("ERROR: Could not read starfield file.")
        error = True
    else:
        try:
            if not (a.columns == ["Name","X","Y","ALT","AZ"]).all():
                print("ERROR: Wrong columns name in starfield file.")
                error = True
        except ValueError:
            print("Starfield file is in the wrong format.")
            error = True

    # Read metadata
    if error:
        print("Error detected, aborting.")
    else:
        fname = glob("PHOTOMETRY/*.*")[0]

        with exiftool.ExifTool() as et:
            exif = et.get_metadata(fname)

        params = [
            f"camera: {exif['EXIF:Make']} {exif['EXIF:Model']}",
            f"height: {exif['MakerNotes:SonyImageHeightMax']}",
            f"width: {exif['MakerNotes:SonyImageWidthMax']}",
            f"lens: {exif['EXIF:LensModel']}",
            "focal_length: ----",
            "pixel_size: ---- # in µm"
        ]
        with open("params",'w') as f:
            f.write('\n'.join(params))

        print("Some information is missing.\n"
        "Please open the `params` file and complete as needed.")

    print("Done.")
