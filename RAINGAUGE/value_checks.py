
def rain_rate_check(value):
    """Check the rain rate value falls within reasonable limits.
        :param value: The rain rate value in mm/hr.
        :return: True if the value falls with limits.
        :raise: ValueError if the value falls outside limits."""
    if 0 <= value < 500:
        return True
    else:
        raise ValueError(str(value) + ' rain rate value fails check')
