try:
    from .calib import calib
    from .flatfield import flatfield
    from .linearity import linearity
    from .photometry import photometry
    from .starfield import starfield
except ModuleNotFoundError:
    pass

__version__ = "0.2.1"
