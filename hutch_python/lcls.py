from pcdsdevices.beam_stats import LCLS, BeamStats


def global_devices():
    """
    Instantiates information devices shared across LCLS.
    """
    return dict(
        beam_stats=BeamStats(),
        lcls=LCLS()
        )
