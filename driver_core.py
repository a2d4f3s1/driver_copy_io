# =============================================================================
# Driver Core - Serialization / Deserialization Functions
# =============================================================================
"""
ドライバのシリアライズ・デシリアライズ処理

他プロジェクトでの使用例:
    from driver_core import serialize_fcurve_driver, deserialize_driver

    # ドライバをJSONに変換
    fc = get_fcurve_with_driver(obj, "location", 0)
    data = serialize_fcurve_driver(fc, obj)

    # JSONからドライバを復元
    new_fc = obj.driver_add("location", 0)
    deserialize_driver(new_fc.driver, data['driver'])
"""

import bpy

try:
    # パッケージとしてインポートされた場合
    from . import driver_schema as schema
except ImportError:
    # 直接実行された場合
    import driver_schema as schema


# =============================================================================
# Utility Functions
# =============================================================================

def get_id_type(id_data) -> str:
    """ID datablockからid_typeを取得"""
    type_name = id_data.__class__.__name__
    return schema.ID_TYPE_MAP.get(type_name, 'OBJECT')


def get_collection_name(id_data) -> str:
    """ID datablockからコレクション名を取得"""
    type_name = id_data.__class__.__name__
    return schema.COLLECTION_NAME_MAP.get(type_name, 'objects')


def get_fcurve_with_driver(id_data, data_path: str, index: int = -1):
    """
    指定されたdata_pathとindexに一致するドライバFCurveを取得

    Args:
        id_data: ID datablock (Object, Material, etc.)
        data_path: プロパティパス (例: "location", "modifiers[\"Array\"].count")
        index: 配列インデックス (-1 で任意)

    Returns:
        FCurve or None
    """
    if not id_data.animation_data or not id_data.animation_data.drivers:
        return None
    for fc in id_data.animation_data.drivers:
        if fc.data_path == data_path:
            if index == -1 or fc.array_index == index:
                return fc
    return None


def resolve_id(id_name: str, id_type: str = None, id_collection: str = None):
    """
    名前とタイプからID datablockを解決

    Args:
        id_name: ID名
        id_type: ID type (例: "OBJECT", "MESH")
        id_collection: コレクション名 (例: "objects", "meshes") - 優先

    Returns:
        ID datablock or None
    """
    if not id_name:
        return None

    # コレクション名で検索 (より確実)
    if id_collection and hasattr(bpy.data, id_collection):
        collection = getattr(bpy.data, id_collection)
        result = collection.get(id_name)
        if result:
            return result

    # id_typeで検索 (フォールバック)
    if id_type:
        collection_name = schema.TYPE_TO_COLLECTION_MAP.get(id_type)
        if collection_name and hasattr(bpy.data, collection_name):
            collection = getattr(bpy.data, collection_name)
            return collection.get(id_name)

    return None


# =============================================================================
# Serialization Functions
# =============================================================================

def serialize_driver_target(target) -> dict:
    """ドライバ変数のターゲットをシリアライズ"""
    data = {
        'id_name': target.id.name if target.id else None,
        'id_type': target.id_type,
        'id_collection': get_collection_name(target.id) if target.id else None,
        'data_path': target.data_path,
        'bone_target': target.bone_target,
        'transform_type': target.transform_type,
        'transform_space': target.transform_space,
        'rotation_mode': target.rotation_mode,
    }
    if target.id and target.id.library:
        data['id_library'] = target.id.library.filepath
    return data


def serialize_driver_variable(var) -> dict:
    """ドライバ変数をシリアライズ"""
    return {
        'name': var.name,
        'type': var.type,
        'targets': [serialize_driver_target(t) for t in var.targets],
    }


def serialize_driver(driver) -> dict:
    """ドライバをシリアライズ"""
    return {
        'type': driver.type,
        'expression': driver.expression,
        'use_self': driver.use_self,
        'variables': [serialize_driver_variable(v) for v in driver.variables],
    }


def serialize_fcurve_driver(fc, id_data) -> dict:
    """
    FCurveドライバを完全なJSON用辞書にシリアライズ

    Args:
        fc: ドライバを持つFCurve
        id_data: FCurveが属するID datablock

    Returns:
        JSON用辞書
    """
    if not fc.driver:
        raise ValueError("FCurve has no driver")
    return {
        'version': schema.DRIVER_JSON_VERSION,
        'source': {
            'id_name': id_data.name,
            'id_type': get_id_type(id_data),
            'id_collection': get_collection_name(id_data),
        },
        'data_path': fc.data_path,
        'array_index': fc.array_index,
        'driver': serialize_driver(fc.driver),
        'extrapolation': fc.extrapolation,
        'mute': fc.mute,
    }


def serialize_all_drivers(id_data) -> dict:
    """
    ID datablockの全ドライバをシリアライズ

    Args:
        id_data: ID datablock

    Returns:
        全ドライバを含む辞書
    """
    if not id_data.animation_data or not id_data.animation_data.drivers:
        return {
            'version': schema.DRIVER_JSON_VERSION,
            'source_name': id_data.name,
            'source_type': get_id_type(id_data),
            'source_collection': get_collection_name(id_data),
            'drivers': []
        }

    drivers = []
    for fc in id_data.animation_data.drivers:
        drivers.append(serialize_fcurve_driver(fc, id_data))

    return {
        'version': schema.DRIVER_JSON_VERSION,
        'source_name': id_data.name,
        'source_type': get_id_type(id_data),
        'source_collection': get_collection_name(id_data),
        'drivers': drivers
    }


# =============================================================================
# Deserialization Functions
# =============================================================================

def deserialize_driver_target(target, data: dict):
    """辞書からドライバターゲットを復元"""
    # id を設定すれば id_type は自動で決まる (id_type は read-only)
    target.id = resolve_id(
        data['id_name'],
        data.get('id_type'),
        data.get('id_collection')
    )
    target.data_path = data.get('data_path', '')
    target.bone_target = data.get('bone_target', '')

    # variable type によっては設定不可な属性がある
    try:
        target.transform_type = data['transform_type']
    except:
        pass
    try:
        target.transform_space = data['transform_space']
    except:
        pass
    try:
        target.rotation_mode = data['rotation_mode']
    except:
        pass


def deserialize_driver_variable(driver, data: dict):
    """辞書からドライバ変数を復元"""
    var = driver.variables.new()
    var.name = data['name']
    var.type = data['type']
    for i, target_data in enumerate(data['targets']):
        if i < len(var.targets):
            deserialize_driver_target(var.targets[i], target_data)
    return var


def deserialize_driver(driver, data: dict):
    """辞書からドライバを復元"""
    driver.type = data['type']
    driver.expression = data['expression']
    driver.use_self = data.get('use_self', False)

    # 既存の変数をクリア
    while driver.variables:
        driver.variables.remove(driver.variables[0])

    for var_data in data['variables']:
        deserialize_driver_variable(driver, var_data)


def apply_driver_to_id(id_data, data: dict, overwrite: bool = True):
    """
    辞書データからドライバをID datablockに適用

    Args:
        id_data: 対象のID datablock
        data: serialize_fcurve_driver()の戻り値
        overwrite: 既存ドライバを上書きするか

    Returns:
        作成されたFCurve
    """
    data_path = data['data_path']
    array_index = data.get('array_index', 0)

    if not id_data.animation_data:
        id_data.animation_data_create()

    # 既存ドライバのチェック
    existing = get_fcurve_with_driver(id_data, data_path, array_index)
    if existing:
        if overwrite:
            id_data.animation_data.drivers.remove(existing)
        else:
            raise ValueError(f"Driver already exists at {data_path}[{array_index}]")

    # ドライバを追加
    try:
        fc = id_data.driver_add(data_path, array_index)
        if isinstance(fc, list):
            fc = fc[0]
    except TypeError:
        fc = id_data.driver_add(data_path)
        if isinstance(fc, list):
            fc = fc[0]

    fc.extrapolation = data.get('extrapolation', 'CONSTANT')
    fc.mute = data.get('mute', False)
    deserialize_driver(fc.driver, data['driver'])

    return fc


def apply_all_drivers_to_id(id_data, data: dict, overwrite: bool = True):
    """
    serialize_all_drivers()の結果をID datablockに適用

    Args:
        id_data: 対象のID datablock
        data: serialize_all_drivers()の戻り値
        overwrite: 既存ドライバを上書きするか

    Returns:
        作成されたFCurveのリスト
    """
    results = []
    for driver_data in data.get('drivers', []):
        fc = apply_driver_to_id(id_data, driver_data, overwrite)
        results.append(fc)
    return results
