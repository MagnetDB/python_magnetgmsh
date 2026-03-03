import logging

logger = logging.getLogger(__name__)


def flatten(S: list) -> list:
    """
    flatten list of list
    """
    from pandas.core.common import flatten as pd_flatten

    flattened = list(pd_flatten(S))

    # Check for duplicates
    if len(flattened) != len(set(flattened)):
        duplicates = [item for item in set(flattened) if flattened.count(item) > 1]
        logger.warning(f"Duplicates found in flattened list: {duplicates}")

    return flattened
