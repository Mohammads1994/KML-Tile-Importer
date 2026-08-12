from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class Bounds:
    north: Optional[float] = None
    south: Optional[float] = None
    east: Optional[float] = None
    west: Optional[float] = None
    min_altitude: Optional[float] = None
    max_altitude: Optional[float] = None

@dataclass
class LOD:
    level: int
    kml_path: Path
    dae_path: Path
    min_lod_pixels: Optional[float] = None
    max_lod_pixels: Optional[float] = None
    location: tuple[float, float, float] | None = None
    bounds: Bounds = field(default_factory=Bounds)

@dataclass
class Tile:
    tile_id: str
    root_kml: Path
    lods: list[LOD] = field(default_factory=list)

    @property
    def highest_lod(self) -> Optional[LOD]:
        return max(self.lods, key=lambda x: x.level, default=None)
