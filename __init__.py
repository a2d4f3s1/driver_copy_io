# =============================================================================
# Driver Copy Utility - Blender Add-on Package Entry Point
# =============================================================================
"""
Driver Copy Utility

ドライバのコピー/ペースト/ファイル入出力を行うBlenderアドオン

インストール方法:
    1. driver_copy_io フォルダをzipに圧縮
    2. Blender > Edit > Preferences > Add-ons > Install
    3. zipファイルを選択してインストール
    4. "Animation: Driver Copy Utility" を有効化

使用方法:
    3D View > Sidebar (N) > Tool > Driver Copy
"""

bl_info = {
    "name": "Driver Copy Utility",
    "author": "moteki",
    "version": (2, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Tool > Driver Copy",
    "description": "Copy/Paste drivers via JSON using full path",
    "category": "Animation",
    "license": "GPL-3.0-or-later",
}

from . import driver_copy_addon


def register():
    driver_copy_addon.register()


def unregister():
    driver_copy_addon.unregister()


if __name__ == "__main__":
    register()
