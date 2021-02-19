import numpy as np
import ccdproc
import rawpy
from astropy import units as u
from astropy.nddata import CCDData
import exiftool

def open_raw(fname, normalize=False):
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

    if normalize:
        rgb /= 2**16 - 1

    data = CCDData(rgb,unit=u.adu)
    data.header['exposure'] = exposure * u.s
    return data

def open_dark(fnames):
    frames = [ open_raw(fname) for fname in fnames ]
    if frames[0].data.ndim == 3:
        dark = np.stack( [
            ccdproc.combine([f[:,:,i] for f in frames], sigma_clip=True) \
            for i in range(3)
        ], axis=2 )
        dark = CCDData(dark,unit=u.adu)
        dark.header = frames[0].header
    else:
        dark = ccdproc.combine(frames, sigma_clip=True)
    return dark

def subtract_dark(data,dark):
    return ccdproc.subtract_dark(
        data, dark,
        data_exposure = data.header['exposure'],
        dark_exposure = dark.header['exposure']
    )

def correct_flat(data,flat):
    return ccdproc.flat_correct(data,flat)

def cosmicray_removal(image,**kwargs):
    if "sigclip" not in kwargs:
        kwargs['sigclip'] = 25
    if image.data.ndim == 3:
        new_data = np.stack( [
            ccdproc.cosmicray_lacosmic(image.data[:,:,i],**kwargs)[0] \
            for i in range(3)
        ], axis=2 )
    else:
        new_data = ccdproc.cosmicray_lacosmic(image.data,**kwargs)[0]
    new_data = CCDData(new_data,unit=u.adu)
    new_data.header = image.header
    return new_data
