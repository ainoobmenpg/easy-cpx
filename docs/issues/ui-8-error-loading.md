# UI-8: エラーハンドリング/ローディングの標準化

### 症状
- 画面ごとにエラー表示がバラバラ。Toast/EmptyState/Skeletonの標準化が必要。

### 対応
- 共通 `useToast()`/`<Skeleton/>` を作成。`/games` `/scenarios` `/game` の失敗時挙動を統一。

### 完了条件
- 失敗時に原因/対処がすぐ分かり、Fallbackが一貫。
