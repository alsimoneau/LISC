#!/usr/bin/env python3
#
# LISC toolkit
# Folder initialisation
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: April 2021

import inspect
import os
import shutil
from glob import glob

import click
import exiftool
import pandas as pd
import yaml


@click.command()
@click.argument("folder_name", type=click.Path(exists=False), default=".")
def dir(folder_name):
    """Initialize calibration directory structure.

    FOLDER_NAME is the folder name the directory structure will be created into.
    If ommited, will create it in the current directory instead.
    """
    folders = ["FLATFIELD", "LINEARITY", "PHOTOMETRY"]
    for fold_name in folders:
        os.makedirs(os.path.join(folder_name, fold_name, "DARKS"))
    os.makedirs(os.path.join(folder_name, "STARFIELD"))

    txt = [
        "star_id: 0           # Star's ID in the Yale Bright Star Catalog",
        "star_position: [0,0] # Initial star position in pixels (X,Y)",
        "theta: 90            # Zenith angle of the star [deg]",
        "aod: 1.0             # Aerosol optical depth",
        "alpha: 1.0           # Angstrom coefficient",
        "pressure: 101.3      # Air pressure [kPa]",
        "altitude: 0          # Altitude of the measurement site [m]",
        "altitude_aod: 0      # Altitude of the AERONET station used [m]",
        "altitude_pressure: 0 # Altitude of the site where the pressure was measured [m]",
    ]

    with open("PHOTOMETRY/photometry.params", "w") as f:
        f.write("\n".join(txt))


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
            if not (a.columns == ["Name", "X", "Y", "ALT", "AZ"]).all():
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
            f"camera_reference_name: ----",
            f"camera: {exif['EXIF:Make']} {exif['EXIF:Model']}",
            f"height: {exif['MakerNotes:SonyImageHeightMax']}",
            f"width: {exif['MakerNotes:SonyImageWidthMax']}",
            f"lens: {exif['EXIF:LensModel']}",
            "focal_length: ----",
            "pixel_size: ---- # in µm",
        ]
        with open("params", "w") as f:
            f.write("\n".join(params))

        print(
            "Some information is missing.\n"
            "Please open the `params` file and complete as needed."
        )

        print("Done.")


@click.command()
def save():
    "Saves calibration files"
    datafiles = [
        "params",
        "geometry.npy",
        "linearity.csv",
        "flatfield.npy",
        "flat_weight.npy",
        "photometry.csv",
        "photometry.dat",
    ]

    error = False
    for fname in datafiles:
        if not os.path.isfile(fname):
            print(f"ERROR: {fname} is missing")
            error = True

    if error:
        print("Error detected, aborting.")
        return ()

    with open("params") as f:
        params = yaml.safe_load(f)
    cam_key = params["camera_reference_name"]

    datadir = os.path.expanduser(f"~/.LISC/{cam_key}/")

    if os.path.isdir(datadir):
        flag = input(f"Data for {cam_key} already found, overwrite ? [Y/n] ")
        if len(flag) > 1 and flag[0] in "Nn":
            print("Aborting.")
            return ()
        shutil.rmtree(datadir)

    print("Creating " + datadir)
    os.makedirs(datadir)
    for fname in datafiles:
        shutil.copy(fname, datadir + fname)

    print("Done.")


@click.command()
def list():
    "List calibrated cameras"

    for param_file in glob(os.path.expanduser("~/.LISC/*/params")):
        with open(param_file) as f:
            params = yaml.safe_load(f)

        print(
            f"{params['camera_reference_name']}\n"
            f"   Camera body: {params['camera']}\n"
            f"    Lens model: {params['lens']}\n"
        )
