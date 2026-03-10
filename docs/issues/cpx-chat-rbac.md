# CPX-CHAT: ロール別チャット/EXCON告知チャンネル

### 背景
通知タイプに `CHAT_MESSAGE` があるが、API/WS/フロント未整備。BLUE/RED/WHITE/Observer別の情報流通が必要。

### 提案
- `POST /api/games/{id}/chat` （RBAC: 書込可否）＋ `GET /api/games/{id}/chat?since=...`
- `/ws/games/{id}` で `chat_message` を配信（役割別にルーム分離）。

### 受け入れ基準
- BLUE/REDの相互不可視、WHITEは全閲覧、Observerはread-only。
- 既読/未読やタイムスタンプの簡易サポート。
