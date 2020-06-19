
def windspeed_check(value):
    """Check the windspeed value falls within reasonable limits.
        :param value: The windspeed value in knots.
        :return: True if the value falls with limits.
        :raise: ValueError if the value falls outside limits."""
    if 0 <= value < 500:
        return True
    else:
        raise ValueError(str(value) + ' windspeed value fails check')


def winddir_check(value):
    """Check the wind direction value falls within reasonable limits.
        :param value: The wind direction value in degrees.
        :return: True if the value falls with limits.
        :raise: ValueError if the value falls outside limits."""
    if 0 <= value <= 360:
        return True
    else:
        raise ValueError(str(value) + ' windspeed value fails check')
