# Issue #64: 内部用エンドポイントが無認証で公開されている

- 作成日: 2026-03-09
- 種別: Security / Data Exposure
- 優先度: Critical

## 事象
`backend/app/api/routes.py` の `/api/internal/games/{game_id}/true-state` および `/api/internal/games/{game_id}/units` は「FOR AUTHORIZED USE ONLY」とコメントされていますが、実際には FastAPI の標準依存関係だけで公開されており、認証やロール判定が一切ありません。任意のクライアントが HTTP GET を叩くだけで Fog of War を無視した完全なゲーム状態（敵位置・補給・地形シードまで含む）を取得できます。citebackend/app/api/routes.py:320-379

## 影響
- 対人戦や観戦を考慮した場合、敵のユニット配置・ステータスが丸見えになる。
- `terrain_data` や `map_width`/`map_height` まで返るため、今後シナリオが非公開情報を含むと知財漏えいに直結。
- ゲーム外部からの簡単なスクリプトでも悪用可能。WAF や API Gateway を通してもアプリ側で許可している限り防げない。

## 対応案
1. 認証レイヤーを導入（例: FastAPI の `Depends(get_current_user)` + JWT/OAuth）。
2. 最低限でも環境変数フラグ（`ENABLE_INTERNAL_ENDPOINTS=false`）でデプロイ時に無効化。
3. 管理用途が必要ならば、API Key チェックまたは IP allowlist を追加し、ログにも監査証跡を残す。
4. ドキュメント上も「ローカルデバッグ専用、デプロイでは無効化必須」と明記。

## 完了条件
- 外部クライアントが無認証で `/api/internal/...` を叩いても 401/403 になる、もしくはエンドポイント自体が提供されない。
- FastAPI ルーターとドキュメントが新しい認可フローを説明している。
- セキュリティレビューで再度検証した際にデータ漏えいが発生しない。
