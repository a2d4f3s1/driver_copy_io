# =============================================================================
# Driver Schema - JSON Schema Definitions and Type Mappings
# =============================================================================
"""
ドライバのJSONスキーマ定義と型マッピング

他プロジェクトでの使用例:
    from driver_schema import DRIVER_JSON_VERSION, ID_TYPE_MAP, COLLECTION_NAME_MAP
"""

# JSONスキーマバージョン
DRIVER_JSON_VERSION = 2

# -----------------------------------------------------------------------------
# Type Mappings
# -----------------------------------------------------------------------------

# Blenderクラス名 → id_type (ドライバ変数のターゲット用)
ID_TYPE_MAP = {
    'Object': 'OBJECT',
    'Mesh': 'MESH',
    'Curve': 'CURVE',
    'Armature': 'ARMATURE',
    'Light': 'LIGHT',
    'Camera': 'CAMERA',
    'Material': 'MATERIAL',
    'NodeTree': 'NODETREE',
    'Scene': 'SCENE',
    'World': 'WORLD',
    'Collection': 'COLLECTION',
    'Action': 'ACTION',
    'Key': 'KEY',
    'Texture': 'TEXTURE',
    'Image': 'IMAGE',
    'ParticleSettings': 'PARTICLE',
    'GreasePencil': 'GPENCIL',
    'FreestyleLineStyle': 'LINESTYLE',
}

# Blenderクラス名 → bpy.dataコレクション名
COLLECTION_NAME_MAP = {
    'Object': 'objects',
    'Mesh': 'meshes',
    'Curve': 'curves',
    'Armature': 'armatures',
    'Light': 'lights',
    'Camera': 'cameras',
    'Material': 'materials',
    'NodeTree': 'node_groups',
    'Scene': 'scenes',
    'World': 'worlds',
    'Collection': 'collections',
    'Action': 'actions',
    'Key': 'shape_keys',
    'Texture': 'textures',
    'Image': 'images',
    'ParticleSettings': 'particles',
    'GreasePencil': 'grease_pencils',
    'FreestyleLineStyle': 'linestyles',
}

# id_type → bpy.dataコレクション名 (逆引き用)
TYPE_TO_COLLECTION_MAP = {
    'OBJECT': 'objects',
    'MESH': 'meshes',
    'CURVE': 'curves',
    'ARMATURE': 'armatures',
    'LIGHT': 'lights',
    'CAMERA': 'cameras',
    'MATERIAL': 'materials',
    'NODETREE': 'node_groups',
    'SCENE': 'scenes',
    'WORLD': 'worlds',
    'COLLECTION': 'collections',
    'ACTION': 'actions',
    'KEY': 'shape_keys',
    'TEXTURE': 'textures',
    'IMAGE': 'images',
    'PARTICLE': 'particles',
    'GPENCIL': 'grease_pencils',
    'LINESTYLE': 'linestyles',
}

# -----------------------------------------------------------------------------
# JSON Schema Documentation
# -----------------------------------------------------------------------------
"""
Driver JSON Schema (version 2):

{
    "version": 2,
    "source": {
        "id_name": "ObjectName",
        "id_type": "OBJECT",
        "id_collection": "objects"
    },
    "data_path": "location",
    "array_index": 0,
    "driver": {
        "type": "SCRIPTED",
        "expression": "var * 2",
        "use_self": false,
        "variables": [
            {
                "name": "var",
                "type": "TRANSFORMS",
                "targets": [
                    {
                        "id_name": "Cube",
                        "id_type": "OBJECT",
                        "id_collection": "objects",
                        "data_path": "",
                        "bone_target": "",
                        "transform_type": "LOC_X",
                        "transform_space": "WORLD_SPACE",
                        "rotation_mode": "AUTO"
                    }
                ]
            }
        ]
    },
    "extrapolation": "CONSTANT",
    "mute": false
}
"""
