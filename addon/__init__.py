bl_info = {
    'name': 'KML Tile Importer',
    'author': 'BIM project',
    'version': (0, 1, 0),
    'blender': (4, 4, 0),
    'location': 'Properties > Scene > KML Tile Importer',
    'description': 'Import geographically positioned KML/DAE tiles with tile selection.',
    'category': 'Import-Export',
}

import bpy
from .ui.panel import CLASSES


def register():
    for cls in CLASSES: bpy.utils.register_class(cls)
    bpy.types.Scene.kml_tile_importer = bpy.props.PointerProperty(type=CLASSES[1])


def unregister():
    del bpy.types.Scene.kml_tile_importer
    for cls in reversed(CLASSES): bpy.utils.unregister_class(cls)

if __name__ == '__main__': register()
