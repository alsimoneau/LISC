#!/usr/bin/env python3
#
# LISC toolkit
# Linearity processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: February 2021

import click

@click.command(name="linearity")
def CLI_linearity():
    """Process frames for linearity calibration.
    """
    linearity()

def linearity():
    pass
