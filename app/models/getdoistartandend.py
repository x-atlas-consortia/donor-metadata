from models.appconfig import AppConfig
def getdoistartandend() -> tuple:
    """
    Calculates the start and end points of a donor DOI processing run.
    :return: a tuple with the start and end ordinal positions in the sorted list of donor ids.

    """
    cfg = AppConfig()
    start = int(cfg.getfield(key='DOI_START'))
    batch = int(cfg.getfield(key='DOI_BATCH'))
    if start < 0:
        start = 0
        end = batch
    else:
        end = start + batch

    return start, end