from pcdsdevices.beam_stats import LCLS, BeamStats


def global_devices():
    """
    Instantiates information devices shared across LCLS.
    """
    return dict(
        beam_stats=BeamStats(),
        lcls=LCLS()
        )


global_device_docs = {
    'beam_stats': 'Summary of the most important beam statistics.',
    'lcls': 'Collection of all upstream x-ray diagnostics.',
    }
