# =============================================================================
# Driver Copy Utility - Text Editor Launcher
# =============================================================================
"""
Blenderテキストエディタから直接実行するランチャー

使用方法:
    1. このファイル (_run.py) をテキストエディタで開く（Open）
       ※ 新規作成してコピペではなく、ファイルとして開くこと
    2. [Run Script] で実行
    3. Sidebar (N) > Tool > Driver Copy

解除:
    bpy.ops.driver.unregister_standalone()
"""

import bpy
import sys
import os


def get_script_dir():
    """スクリプトのディレクトリを取得"""

    # 方法1: __file__ から取得（外部から実行時）
    try:
        if '__file__' in dir() and __file__:
            return os.path.dirname(os.path.abspath(__file__))
    except:
        pass

    # 方法2: テキストエディタのファイルパスから取得
    try:
        text = bpy.context.space_data.text
        if text and text.filepath:
            return os.path.dirname(os.path.abspath(text.filepath))
    except:
        pass

    # 方法3: 現在のテキストブロックを名前で探す
    for text in bpy.data.texts:
        if text.filepath and text.name.startswith('_run'):
            return os.path.dirname(os.path.abspath(text.filepath))

    return None


def setup_path():
    """モジュールパスをセットアップ"""
    script_dir = get_script_dir()

    if not script_dir:
        raise RuntimeError(
            "スクリプトのパスが取得できません。\n"
            "テキストエディタで Text > Open からファイルを開いてください。\n"
            "（新規作成してコピペではダメです）"
        )

    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    print(f"Driver Copy: Script dir = {script_dir}")
    return script_dir


# パスをセットアップ
setup_path()

# 既存モジュールをリロード（再実行時のため）
for mod_name in ['driver_schema', 'driver_core', 'driver_copy_addon']:
    if mod_name in sys.modules:
        del sys.modules[mod_name]

# モジュールをインポート
import driver_copy_addon


# アンレジスタ用オペレーター
class DRIVER_OT_unregister_standalone(bpy.types.Operator):
    bl_idname = "driver.unregister_standalone"
    bl_label = "Unregister Driver Copy"
    bl_description = "Unregister the standalone Driver Copy panel"

    def execute(self, context):
        unregister()
        self.report({'INFO'}, "Driver Copy panel unregistered")
        return {'FINISHED'}


_registered = False


def register():
    global _registered
    if _registered:
        print("Driver Copy: Already registered")
        return

    driver_copy_addon.register()
    bpy.utils.register_class(DRIVER_OT_unregister_standalone)
    _registered = True
    print("Driver Copy: Registered")


def unregister():
    global _registered
    if not _registered:
        return

    try:
        bpy.utils.unregister_class(DRIVER_OT_unregister_standalone)
    except:
        pass
    driver_copy_addon.unregister()
    _registered = False
    print("Driver Copy: Unregistered")


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
