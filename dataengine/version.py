# Store the version here so:
# 1) we don't load dependencies by storing it in __init__.py
# 2) we can import it in setup.py for the same reason
# 3) we can import it into your module module
__version_info__ = (0, 0, 92)
__version__ = '.'.join(map(str, __version_info__))