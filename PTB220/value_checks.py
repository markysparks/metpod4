def pressure_check(value):
    """Check the pressure value falls within reasonable limits.
    :param value: The pressure value in hectopascals (hPa).
    :return: True if the value falls with limits.
    :raise: ValueError if the value falls outside limits."""
    if 800 < value < 1200:
        return True
    else:
        raise ValueError(str(value) + ' pressure value fails check')


def tendency_check(value):
    """Check the pressure tendency value falls within reasonable limits.
    For this check a value of None is acceptable since this parameter is
    not immediately available from the supplying sensor.
        :param value: The pressure tendency value in hectopascals (hPa).
        :return: True if the value falls with limits.
        :raise: ValueError if the value falls outside limits."""
    if value is None or -50 < value < 50:
        return True
    else:
        raise ValueError(str(value) + ' tendency value fails check')


def trend_check(value):
    """Check the pressure trend value falls within reasonable limits.
    For this check a value of None is acceptable since this parameter is
    not immediately available from the supplying sensor.
        :param value: The pressure trend value WMO code 0-9.
        :return: True if the value falls with limits.
        :raise: ValueError if the value falls outside limits."""
    if value is None or 0 <= value <= 9:
        return True
    else:
        raise ValueError(str(value) + ' trend value fails check')

