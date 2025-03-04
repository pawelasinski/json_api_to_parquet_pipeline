import os


def get_date_path_directories(base_path: str, year: int, month: int, day: int) -> str:
    """Constructs a directory path using the provided base path and date components.

    Args:
        base_path: The root directory where date-based dirs will be stored.
        year: The year component.
        month: The month component.
        day: The day component.

    Returns:
        The constructed directory path in the
            `{base_path}/year={year}/month={month}/day={day}` format.

    """
    return os.path.join(base_path, f"year={year}", f"month={month}", f"day={day}")
