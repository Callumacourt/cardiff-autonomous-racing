"""Cone color constants and type definitions."""
from enum import IntEnum

class ConeColor(IntEnum):
    """Cone color labels."""
    BLUE = 0
    YELLOW = 1
    ORANGE = 2

# RViz color mappings (RGB)
CONE_COLORS_RGB = {
    ConeColor.BLUE: (0.0, 0.0, 1.0),
    ConeColor.YELLOW: (1.0, 1.0, 0.0),
    ConeColor.ORANGE: (1.0, 0.5, 0.0),
}