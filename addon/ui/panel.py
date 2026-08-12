import bpy
from bpy.types import Panel
from ..kml.parser import discover_tiles
from ..geo.transform import enu_offset
from ..dae.importer import import_dae
from ..blender.scene import ensure_collection, move_objects_to_collection
from pathlib import Path

TILE_CACHE = {}

def _props():
    return bpy.context.scene.kml_tile_importer


class KMLTileItem(bpy.types.PropertyGroup):
    tile_id: bpy.props.StringProperty(name='Tile')
    selected: bpy.props.BoolProperty(default=False)


class KMLTileSettings(bpy.types.PropertyGroup):
    master_kml: bpy.props.StringProperty(name='Master KML', subtype='FILE_PATH')
    tiles: bpy.props.CollectionProperty(type=KMLTileItem)
    origin_mode: bpy.props.EnumProperty(
        name='Origin', items=[('FIRST', 'First selected tile', ''), ('ZERO', 'KML origin', '')], default='FIRST')
    import_highest: bpy.props.BoolProperty(name='Highest available LOD', default=True)


class KML_OT_Discover(bpy.types.Operator):
    bl_idname = 'kml_tile.discover'
    bl_label = 'Discover Tiles'
    bl_description = 'Read the master KML and discover first-level tiles'

    def execute(self, context):
        s = _props()
        path = Path(bpy.path.abspath(s.master_kml))
        if not path.exists():
            self.report({'ERROR'}, 'Master KML does not exist')
            return {'CANCELLED'}
        try:
            tiles = discover_tiles(path)
        except Exception as exc:
            self.report({'ERROR'}, f'KML parse failed: {exc}')
            return {'CANCELLED'}
        s.tiles.clear()
        for tid in sorted(tiles, key=lambda x: int(x) if x.isdigit() else x):
            item = s.tiles.add()
            item.tile_id = tid
            item.selected = False
        TILE_CACHE.clear(); TILE_CACHE.update({tid: str(t.root_kml) for tid, t in tiles.items()})
        self.report({'INFO'}, f'Discovered {len(tiles)} tiles')
        return {'FINISHED'}


class KML_OT_SelectAll(bpy.types.Operator):
    bl_idname = 'kml_tile.select_all'
    bl_label = 'Select All'
    def execute(self, context):
        for t in _props().tiles: t.selected = True
        return {'FINISHED'}


class KML_OT_SelectNone(bpy.types.Operator):
    bl_idname = 'kml_tile.select_none'
    bl_label = 'Select None'
    def execute(self, context):
        for t in _props().tiles: t.selected = False
        return {'FINISHED'}


class KML_OT_Import(bpy.types.Operator):
    bl_idname = 'kml_tile.import_selected'
    bl_label = 'Import Selected Tiles'
    bl_description = 'Import the highest available LOD for selected tiles'

    def execute(self, context):
        s = _props()
        cache = TILE_CACHE
        selected = [x.tile_id for x in s.tiles if x.selected]
        if not selected:
            self.report({'ERROR'}, 'Select at least one tile')
            return {'CANCELLED'}
        from ..kml.parser import parse_tile_kml
        tile_objs = []
        origin = None
        root_coll = ensure_collection('KML_Tiles')
        for tid in selected:
            root = Path(cache.get(tid, ''))
            if not root.exists():
                self.report({'WARNING'}, f'Tile {tid} KML not found')
                continue
            tile, _ = parse_tile_kml(root)
            # Re-discover nested LODs.
            # parse_tile_kml(root) gives base; manually walk links.
            stack = [root]; visited=set(); lods=[]
            while stack:
                p=stack.pop()
                if p in visited or not p.exists(): continue
                visited.add(p)
                t, links=parse_tile_kml(p); lods.extend(t.lods); stack.extend(links)
            tile.lods = sorted({x.dae_path:x for x in lods}.values(), key=lambda x:x.level)
            lod = tile.highest_lod
            if lod is None or not lod.dae_path.exists():
                self.report({'WARNING'}, f'Tile {tid}: no available DAE')
                continue
            if origin is None and lod.location:
                origin = lod.location
            tile_objs.append((tile, lod))
        if origin is None:
            self.report({'ERROR'}, 'No valid tile location found')
            return {'CANCELLED'}
        for tile, lod in tile_objs:
            tile_coll = ensure_collection(f'TILE_{tile.tile_id}', root_coll)
            lod_coll = ensure_collection(f'LOD_{lod.level:02d}', tile_coll)
            imported = import_dae(lod.dae_path)
            move_objects_to_collection(imported, lod_coll)
            lon, lat, alt = lod.location
            x,y,z = enu_offset(lon,lat,alt,*origin)
            for obj in imported:
                obj.location.x += x; obj.location.y += y; obj.location.z += z
            tile_coll['tile_id'] = tile.tile_id
            tile_coll['source_kml'] = str(tile.root_kml)
            tile_coll['source_dae'] = str(lod.dae_path)
            tile_coll['longitude'] = lon; tile_coll['latitude'] = lat; tile_coll['altitude'] = alt
            tile_coll['origin_longitude'] = origin[0]; tile_coll['origin_latitude'] = origin[1]; tile_coll['origin_altitude'] = origin[2]
            tile_coll['coordinate_system'] = 'Local ENU: X=East, Y=North, Z=Up'
            tile_coll['north_preserved'] = True
            lod_coll['lod_level'] = lod.level
            lod_coll['min_lod_pixels'] = lod.min_lod_pixels if lod.min_lod_pixels is not None else -1
            lod_coll['max_lod_pixels'] = lod.max_lod_pixels if lod.max_lod_pixels is not None else -1
        self.report({'INFO'}, f'Imported {len(tile_objs)} tile(s)')
        return {'FINISHED'}


class KML_PT_Panel(Panel):
    bl_label = 'KML Tile Importer'
    bl_idname = 'KML_PT_tile_importer'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'SCENE'
    def draw(self, context):
        layout=self.layout; s=_props()
        layout.prop(s,'master_kml')
        layout.operator('kml_tile.discover', icon='FILE_FOLDER')
        if s.tiles:
            row=layout.row(align=True); row.operator('kml_tile.select_all'); row.operator('kml_tile.select_none')
            for t in s.tiles:
                layout.prop(t,'selected',text=t.tile_id)
            layout.prop(s,'origin_mode')
            layout.prop(s,'import_highest')
            layout.operator('kml_tile.import_selected', icon='IMPORT')


CLASSES=(KMLTileItem,KMLTileSettings,KML_OT_Discover,KML_OT_SelectAll,KML_OT_SelectNone,KML_OT_Import,KML_PT_Panel)
