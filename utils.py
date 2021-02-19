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
    #ccdproc.combine
    pass

def substract_dark(data,dark):
    #ccdproc.substract_dark
    pass

def correct_flat(data,flat):
    #ccdproc.flat_correct
    pass

def cosmicray_removal(image,**kwargs):
    if "sigclip" not in kwargs:
        kwargs['sigclip'] = 25
    if image.data.ndim == 3:
        new_data = np.stack( [
            ccdproc.cosmicray_lacosmic(image.data[:,:,i],**kwargs)[0] \
            for i in range(image.data.shape[2])
        ], axis=2 )
    else:
        new_data = ccdproc.cosmicray_lacosmic(image.data,**kwargs)[0]
    return CCDData(new_data,unit=u.adu)
