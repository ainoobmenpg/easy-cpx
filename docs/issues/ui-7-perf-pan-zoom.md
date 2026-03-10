# UI-7: パン/ズームのパフォーマンス最適化

### 背景
- `didPan`/`isPanning` で工夫済みだが、再描画が多い。CSS transform で `g` を丸ごと移動し、rAFでスロットルする。

### 対応
- パン時は state 更新をrAFで1フレームに集約。ズームはSVG `viewBox`/`transform` 併用で拡縮。

### 完了条件
- 低スペック環境でもドラッグがカクつかない（目安: 60fps近傍）。
