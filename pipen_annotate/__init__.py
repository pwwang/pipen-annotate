from .annotate import annotate
from .sections import Section

__version__ = "1.0.5"

# backward compatibility
version = __version__

__all__ = ["annotate", "Section", "version", "__version__"]
