#!/usr/bin/env python3
#
# LISC toolkit
# Image calibration
#
# Author : Alexandre Simoneau
#
# Created: March 2021
# Edited: March 2021

import click
from utils import *

@click.command(name="calib")
def CLI_process():
    """Image calibration.
    """
    calib()
    print("Done.")

def calib(fname):
  pass
