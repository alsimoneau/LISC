import numpy as np
import ccdproc
import rawpy
from astropy import units as u
from astropy.nddata import CCDData
from astropy.stats import sigma_clipped_stats
import exiftool
import tables

def open_raw(fname, normalize=False):
    print(fname)
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

    #data = CCDData(rgb,unit=u.adu)
    #data.header['exposure'] = exposure * u.s
    return rgb

def open_multiple(fnames,filename):
    for i,fname in enumerate(fnames):
        rgb = open_raw(fname)
        if i == 0:
            shape = (0,) + rgb.shape
            f = tables.open_file(filename,mode='w')
            arr = f.create_earray(f.root,'data',obj=np.zeros(shape))
        arr.append(rgb[None])
    return f,arr

def open_mean(fnames):
    frames = np.array([ open_raw(fname) for fname in fnames ])
    return sigma_clipped_stats(frames,axis=0)

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
