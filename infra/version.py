VERSION = (2, 0, 0)


def get_version_string() -> str:
    return ".".join(str(x) for x in VERSION)


