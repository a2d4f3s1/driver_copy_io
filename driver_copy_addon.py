bl_info = {
    "name": "Driver Copy IO",
    "author": "moteki",
    "version": (2, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Tool > Driver Copy",
    "description": "Copy/Paste drivers via JSON using full path",
    "category": "Animation",
    "license": "GPL-3.0-or-later",
}

import bpy
import json
import re
import os
from bpy.props import StringProperty, BoolProperty
from bpy.types import Panel, Operator, PropertyGroup

try:
    # パッケージとしてインポートされた場合
    from . import driver_core as core
except ImportError:
    # 直接実行された場合
    import driver_core as core


# =============================================================================
# Utility Functions
# =============================================================================

def get_blend_directory():
    """blendファイルのディレクトリを取得（未保存の場合は空文字）"""
    blend_path = bpy.data.filepath
    if blend_path:
        return os.path.dirname(blend_path) + os.sep
    return ""


def check_driver_validity(driver):
    """
    ドライバーの変数が有効かチェックし、無効なものをリストで返す

    Returns:
        list of (var_name, error_message)
    """
    invalid = []
    for var in driver.variables:
        for target in var.targets:
            # ターゲットIDが未設定
            if target.id is None:
                invalid.append((var.name, "Target ID not set"))
                continue

            # data_pathが設定されている場合、有効性をチェック
            if target.data_path:
                try:
                    target.id.path_resolve(target.data_path)
                except (ValueError, AttributeError):
                    invalid.append((var.name, f"Invalid path: {target.data_path}"))

            # ボーンターゲットのチェック（SINGLE_PROP以外の場合）
            if hasattr(target, 'bone_target') and target.bone_target:
                if hasattr(target.id, 'pose') and target.id.pose:
                    bone_names = [b.name for b in target.id.pose.bones]
                    if target.bone_target not in bone_names:
                        invalid.append((var.name, f"Bone not found: {target.bone_target}"))

    return invalid


# =============================================================================
# Path Parser (Addon-specific)
# =============================================================================

def parse_full_path(full_path: str):
    """
    フルパスを解析してID datablock、data_path、indexを返す

    Examples:
        bpy.data.objects["Cube"].location[0]
        bpy.data.scenes["Scene"]["custom_prop"]
        bpy.data.materials["Material"].node_tree.nodes["Principled BSDF"].inputs[0].default_value

    Returns:
        (id_datablock, data_path, array_index) or raises ValueError
    """
    # bpy.data.{collection}["{name}"] or bpy.data.{collection}['{name}']
    pattern = r'^bpy\.data\.(\w+)\[(["\'])(.+?)\2\]\.?(.*)$'
    match = re.match(pattern, full_path)

    if not match:
        raise ValueError(f"Invalid path format: {full_path}\nExpected: bpy.data.{{collection}}[\"{{name}}\"].{{property}}")

    collection_name = match.group(1)
    id_name = match.group(3)
    data_path = match.group(4)

    # Get collection
    if not hasattr(bpy.data, collection_name):
        raise ValueError(f"Unknown collection: bpy.data.{collection_name}")

    collection = getattr(bpy.data, collection_name)

    # Get ID datablock
    id_data = collection.get(id_name)
    if id_data is None:
        raise ValueError(f"Not found: bpy.data.{collection_name}[\"{id_name}\"]")

    # Parse array index from end of data_path
    array_index = -1
    index_match = re.search(r'\[(\d+)\]$', data_path)
    if index_match:
        array_index = int(index_match.group(1))
        data_path = data_path[:index_match.start()]

    # Handle empty data_path (custom property on ID itself)
    if not data_path:
        raise ValueError(f"No property path specified after ID")

    return id_data, data_path, array_index


# =============================================================================
# Properties
# =============================================================================

class DriverCopyProperties(PropertyGroup):
    export_path: StringProperty(
        name="Export Path",
        description='Full path (e.g. bpy.data.objects["Cube"].location[0])',
        default=""
    )
    import_path: StringProperty(
        name="Import Path",
        description='Full path for import target',
        default=""
    )
    overwrite: BoolProperty(
        name="Overwrite",
        description="Overwrite existing driver",
        default=True
    )
    clipboard: StringProperty(
        name="Clipboard",
        default=""
    )


# =============================================================================
# Operators
# =============================================================================

class DRIVERCOPY_OT_copy(Operator):
    bl_idname = "drivercopy.copy_to_clipboard"
    bl_label = "Copy"
    bl_description = "Copy driver to clipboard"

    def execute(self, context):
        props = context.scene.driver_copy_props

        try:
            id_data, data_path, array_index = parse_full_path(props.export_path)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        fc = core.get_fcurve_with_driver(id_data, data_path, array_index)
        if not fc:
            self.report({'ERROR'}, f"No driver found at: {props.export_path}")
            return {'CANCELLED'}

        try:
            data = core.serialize_fcurve_driver(fc, id_data)
            props.clipboard = json.dumps(data, indent=2, ensure_ascii=False)
            self.report({'INFO'}, f"Copied: {data_path}[{fc.array_index}]")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


class DRIVERCOPY_OT_paste(Operator):
    bl_idname = "drivercopy.paste_from_clipboard"
    bl_label = "Paste"
    bl_description = "Paste driver from clipboard"

    def execute(self, context):
        props = context.scene.driver_copy_props

        if not props.clipboard:
            self.report({'ERROR'}, "Clipboard empty")
            return {'CANCELLED'}

        try:
            id_data, data_path, array_index = parse_full_path(props.import_path)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        try:
            data = json.loads(props.clipboard)

            # Use index from path, fallback to JSON
            if array_index < 0:
                array_index = data.get('array_index', 0)

            # data_path をオーバーライド（入力パスを使用）
            data['data_path'] = data_path
            data['array_index'] = array_index

            core.apply_driver_to_id(id_data, data, props.overwrite)

            # ペースト後にドライバーの有効性をチェック
            fc = core.get_fcurve_with_driver(id_data, data_path, array_index)
            if fc and fc.driver:
                invalid_vars = check_driver_validity(fc.driver)
                if invalid_vars:
                    # 無効な変数があれば警告を出力
                    warnings = ", ".join([f"{name}: {msg}" for name, msg in invalid_vars])
                    self.report({'WARNING'}, f"Pasted with invalid refs: {warnings}")
                else:
                    self.report({'INFO'}, f"Pasted to: {data_path}[{array_index}]")
            else:
                self.report({'INFO'}, f"Pasted to: {data_path}[{array_index}]")

        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


class DRIVERCOPY_OT_export_file(Operator):
    bl_idname = "drivercopy.export_to_file"
    bl_label = "Save"
    bl_description = "Save driver to JSON file"

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    def invoke(self, context, event):
        props = context.scene.driver_copy_props
        # blendファイルのディレクトリを初期ディレクトリに設定
        blend_dir = get_blend_directory()
        # デフォルトファイル名を生成
        try:
            id_data, data_path, array_index = parse_full_path(props.export_path)
            # パス内の特殊文字を置換
            safe_path = data_path.replace('.', '_').replace('[', '_').replace(']', '').replace('"', '')
            if array_index >= 0:
                filename = f"driver_{id_data.name}_{safe_path}_{array_index}.json"
            else:
                filename = f"driver_{id_data.name}_{safe_path}.json"
        except:
            filename = "driver.json"
        self.filepath = blend_dir + filename
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        props = context.scene.driver_copy_props

        try:
            id_data, data_path, array_index = parse_full_path(props.export_path)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        fc = core.get_fcurve_with_driver(id_data, data_path, array_index)
        if not fc:
            self.report({'ERROR'}, "No driver found")
            return {'CANCELLED'}

        try:
            data = core.serialize_fcurve_driver(fc, id_data)
            filepath = self.filepath
            if not filepath.endswith('.json'):
                filepath += '.json'
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.report({'INFO'}, f"Saved: {filepath}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


class DRIVERCOPY_OT_import_file(Operator):
    bl_idname = "drivercopy.import_from_file"
    bl_label = "Load"
    bl_description = "Load driver JSON to clipboard"

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    def invoke(self, context, event):
        # blendファイルのディレクトリを初期ディレクトリに設定
        self.filepath = get_blend_directory()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        props = context.scene.driver_copy_props

        # ファイルをクリップボードに読み込むだけ（Copyと同様の動作）
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            props.clipboard = json.dumps(data, indent=2, ensure_ascii=False)
            self.report({'INFO'}, f"Loaded to clipboard: {self.filepath}")

        except json.JSONDecodeError as e:
            self.report({'ERROR'}, f"Invalid JSON: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


class DRIVERCOPY_OT_show_clipboard(Operator):
    bl_idname = "drivercopy.show_clipboard"
    bl_label = "View JSON"
    bl_description = "Show clipboard content"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        props = context.scene.driver_copy_props
        layout = self.layout
        if props.clipboard:
            box = layout.box()
            for line in props.clipboard.split('\n')[:30]:
                box.label(text=line)
        else:
            layout.label(text="Empty")


# =============================================================================
# Panel
# =============================================================================

class DRIVERCOPY_PT_panel(Panel):
    bl_label = "Driver Copy"
    bl_idname = "DRIVERCOPY_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        props = context.scene.driver_copy_props

        # Export
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        box.prop(props, "export_path", text="")
        row = box.row(align=True)
        row.operator("drivercopy.export_to_file", icon='FILE_TICK')
        row.operator("drivercopy.copy_to_clipboard", icon='COPYDOWN')

        # Import
        box = layout.box()
        box.label(text="Import", icon='IMPORT')
        box.prop(props, "import_path", text="")
        box.prop(props, "overwrite")
        row = box.row(align=True)
        row.operator("drivercopy.import_from_file", icon='FILE_FOLDER')
        row.operator("drivercopy.paste_from_clipboard", icon='PASTEDOWN')

        # Clipboard status
        row = layout.row()
        row.label(text="Clipboard:" + (" Ready" if props.clipboard else " Empty"))
        if props.clipboard:
            row.operator("drivercopy.show_clipboard", text="", icon='TEXT')


# =============================================================================
# Registration
# =============================================================================

classes = [
    DriverCopyProperties,
    DRIVERCOPY_OT_copy,
    DRIVERCOPY_OT_paste,
    DRIVERCOPY_OT_export_file,
    DRIVERCOPY_OT_import_file,
    DRIVERCOPY_OT_show_clipboard,
    DRIVERCOPY_PT_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.driver_copy_props = bpy.props.PointerProperty(type=DriverCopyProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.driver_copy_props


if __name__ == "__main__":
    register()
