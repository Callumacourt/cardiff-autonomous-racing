"""Configuration dataclasses for cone mapper."""
from dataclasses import dataclass

@dataclass
class GlobalMapConfig:
    """Configuration for persistent global map."""
    confidence_threshold: float = 0.7
    min_detections: int = 3
    duplicate_radius_m: float = 1.5

@dataclass
class LocalBufferConfig:
    """Configuration for local cone buffer."""
    max_size: int = 200
    max_age_sec: float = 6.0
    confidence_decay_rate: float = 0.04
    matching_radius_m: float = 2.0
    
@dataclass
class MapperConfig:
    """Main mapper configuration."""
    global_map: GlobalMapConfig = GlobalMapConfig()
    local_buffer: LocalBufferConfig = LocalBufferConfig()
    local_view_radius_m: float = 20.0
    max_coordinate_bound: float = 50.0