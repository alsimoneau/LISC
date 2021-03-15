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

@click.command()
@click.argument('folder_name', type=click.Path(exists=False), default='.')
def init(folder_name):
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
    config.append("focal lenght: # in mm" )
    config.append("resolution: # [X, Y]")
    config.append("pixel size: # in µm")

    with open(os.path.join(folder_name,"config.ini"),'w') as f:
        f.write('\n'.join(config))
