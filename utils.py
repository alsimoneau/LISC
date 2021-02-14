import numpy as np
import ccdproc
import rawpy
from astropy import units as u
from astropy.nddata import CCDData
import exiftool

def open_raw(fname):
    raw = rawpy.imread(fname)
    rgb = raw.postprocess(
        gamma = (1,1),
        output_bps = 16,
        no_auto_bright = True,
        user_flip = 0
    )
    with exiftool.ExifTool() as et:
        exif = et.get_metadata(fname)
    try:
        exposure = float(exif['MakerNotes:SonyExposureTime'])
    except KeyError:
        exposure = float(exif['EXIF:ExposureTime'])

    data = CCDData(rgb,unit=u.adu)
    data.header['exposure'] = exposure
    return data

def open_dark(fnames):
    pass

def substract_dark(data,dark):
    #ccdproc.substract_dark
    pass

def correct_flat(data,flat):
    #ccdproc.flat_correct
    pass

def cosmicray_removal(data):
    #ccdproc.cosmicray_lacosmic
    pass
