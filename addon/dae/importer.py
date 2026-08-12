from pathlib import Path
import bpy


def import_dae(path: Path):
    op = getattr(getattr(bpy.ops, 'wm', None), 'collada_import', None)
    if op is None:
        raise RuntimeError(
            'No Blender COLLADA importer is available. v0.1 targets Blender 4.4. '
            'A Blender 5.x backend (e.g. AssetKit) should be added here.'
        )
    before = set(bpy.data.objects)
    result = op(filepath=str(path))
    if 'FINISHED' not in result:
        raise RuntimeError(f'COLLADA import failed for {path}')
    return [obj for obj in bpy.data.objects if obj not in before]
