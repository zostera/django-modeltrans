# Re-exported so type checkers load the module defining the manager class which
# modeltrans assigns to the managers of every translated model.
from .manager import MultilingualManager  # noqa: F401

__version__ = "0.10.2"
