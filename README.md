# Driver Copy Utility

オブジェクト間でドライバーをJSON形式でコピー＆ペーストできるBlenderアドオン。

<p align="center">
  <img src="docs/driver_copy_io_image_001.jpg" width="800">
</p>

## 機能

- **ドライバーのコピー/ペースト** - クリップボード経由で他のプロパティにドライバーを複製
- **JSON保存/読込** - ファイルにエクスポートしてバックアップや共有が可能
- **フルパス対応** - `bpy.data.objects["Name"].property` 形式で正確に指定

<p align="center">
  <img src="docs/driver_copy_io_image_002.jpg" width="800">
</p>

## インストール

### Blender 4.2以降
1. Extensionをダウンロード
2. 編集 > プリファレンス > エクステンションを入手 > ディスクからインストール
3. ダウンロードしたフォルダまたはzipを選択

### Blender 4.1以前
1. 編集 > プリファレンス > アドオン > インストール
2. `driver_copy_addon.py` を選択
3. 「Animation: Driver Copy Utility」を有効化

## 使い方

1. パネルを開く: **3Dビュー > サイドバー (N) > ツール > Driver Copy**
2. コピー元のパスを入力（例: `bpy.data.objects["Cube"].location[0]`）
3. **Copy** をクリック
4. コピー先のパスを入力
5. **Paste** をクリック

### パス形式

```
bpy.data.objects["オブジェクト名"].property[index]
bpy.data.materials["マテリアル名"].node_tree.nodes["ノード名"].inputs[0].default_value
bpy.data.scenes["シーン名"]["カスタムプロパティ名"]
```

## ライセンス

GPL-3.0-or-later
