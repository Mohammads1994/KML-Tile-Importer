from pathlib import Path
from urllib.parse import unquote
import re
import xml.etree.ElementTree as ET
from .model import Tile, LOD, Bounds

NS = {'kml': 'http://earth.google.com/kml/2.1'}
NS22 = {'kml': 'http://www.opengis.net/kml/2.2'}


def _root(path):
    return ET.parse(path).getroot()


def _find(root, name):
    node = root.find(f'.//kml:{name}', NS)
    return node if node is not None else root.find(f'.//kml:{name}', NS22)


def _text(parent, name, default=None):
    if parent is None:
        return default
    node = parent.find(f'kml:{name}', NS)
    if node is None:
        node = parent.find(f'kml:{name}', NS22)
    return node.text if node is not None else default


def _float(parent, name):
    value = _text(parent, name)
    return float(value) if value is not None else None


def _bounds(root):
    box = _find(root, 'LatLonAltBox')
    return Bounds(
        north=_float(box, 'north'), south=_float(box, 'south'),
        east=_float(box, 'east'), west=_float(box, 'west'),
        min_altitude=_float(box, 'minAltitude'), max_altitude=_float(box, 'maxAltitude'),
    )


def _lod(root):
    return _find(root, 'Lod')


def _model(root, base):
    model = _find(root, 'Model')
    if model is None:
        return None
    link = model.find('kml:Link', NS)
    if link is None:
        link = model.find('kml:Link', NS22)
    href = _text(link, 'href') if link is not None else None
    if not href:
        return None
    href = unquote(href.split('#', 1)[0])
    dae = (base / href).resolve()
    loc = model.find('kml:Location', NS)
    if loc is None:
        loc = model.find('kml:Location', NS22)
    location = (_float(loc, 'longitude'), _float(loc, 'latitude'), _float(loc, 'altitude')) if loc is not None else None
    return dae, location


def _level_from_name(path: Path):
    m = re.search(r'_L(\d+)', path.stem, re.I)
    return int(m.group(1)) if m else 0


def parse_tile_kml(path: Path) -> tuple[Tile, list[Path]]:
    root = _root(path)
    bounds = _bounds(root)
    lnode = _lod(root)
    model = _model(root, path.parent)
    lods = []
    if model:
        dae, location = model
        lods.append(LOD(
            level=_level_from_name(path), kml_path=path.resolve(), dae_path=dae,
            min_lod_pixels=_float(lnode, 'minLodPixels'), max_lod_pixels=_float(lnode, 'maxLodPixels'),
            location=location, bounds=bounds))
    links = []
    for node in root.findall('.//kml:NetworkLink', NS) + root.findall('.//kml:NetworkLink', NS22):
        link = node.find('kml:Link', NS)
        if link is None:
            link = node.find('kml:Link', NS22)
        href = _text(link, 'href') if link is not None else None
        if href:
            href = unquote(href.split('#', 1)[0])
            child = (path.parent / href).resolve()
            if child.suffix.lower() == '.kml':
                links.append(child)
    tile_id = re.search(r'(\d+)', path.stem)
    tile = Tile(tile_id=tile_id.group(1) if tile_id else path.stem, root_kml=path.resolve(), lods=lods)
    return tile, links


def discover_tiles(master_kml: Path):
    master_kml = master_kml.resolve()
    root = _root(master_kml)
    candidates = []
    for node in root.findall('.//kml:NetworkLink', NS) + root.findall('.//kml:NetworkLink', NS22):
        link = node.find('kml:Link', NS)
        if link is None:
            link = node.find('kml:Link', NS22)
        href = _text(link, 'href') if link is not None else None
        if href:
            child = (master_kml.parent / unquote(href.split('#', 1)[0])).resolve()
            if child.suffix.lower() == '.kml' and child.exists():
                candidates.append(child)
    tiles = {}
    for tile_kml in candidates:
        tile, _ = parse_tile_kml(tile_kml)
        if not tile.lods:
            continue
        # Walk the nested LOD NetworkLinks.
        stack = [tile_kml]
        visited = set()
        all_lods = []
        while stack:
            current = stack.pop()
            if current in visited or not current.exists():
                continue
            visited.add(current)
            t, links = parse_tile_kml(current)
            all_lods.extend(t.lods)
            stack.extend(links)
        tile.lods = sorted({x.dae_path: x for x in all_lods}.values(), key=lambda x: x.level)
        tiles[tile.tile_id] = tile
    return tiles
