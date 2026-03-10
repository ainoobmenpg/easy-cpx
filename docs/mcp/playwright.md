# Playwright MCP セットアップと使い方

このプロジェクトで Playwright MCP (Model Context Protocol) を使うための最小セットアップを行いました。Codex CLI からそのまま使えます。

## 前提
- macOS / Node.js 18+（本環境は Node 22 で確認）
- Codex CLI を利用（このリポジトリは `~/.codex/config.toml` で trusted 登録済み）

## セットアップ内容（2026-03-10）
- Codex の MCP 設定に Playwright MCP を追加：
  - `~/.codex/config.toml` に以下を追記済み
    ```toml
    [mcp_servers.playwright]
    command = "npx"
    args = [
      "@playwright/mcp@latest",
      "--output-dir",
      "${REPO}/.playwright-mcp",
      "--console-level",
      "warning"
    ]
    ```
    - `${REPO}` はローカルパスに解決済み（例: `/Users/<YOU>/GitHub/easy-cpx`）。
  - MCP の出力（スナップショット/ログ等）は `.playwright-mcp/` に保存され、`.gitignore` 済み。

> 備考: ブラウザバイナリは初回起動時に自動ダウンロードされます。必要であれば `npx @playwright/mcp@latest --browser chrome` などでチャンネル指定可能。

## 使い方（Codex）
- チャットで Playwright MCP ツールを使う指示を出すだけで起動されます。
- 明示的にスモーク確認したい場合：
  - `npx -y @playwright/mcp@latest --help` でヘルプが表示されれば OK。
  - ログは `.playwright-mcp/` に出力されます。

## 便利オプション（必要に応じて）
- ヘッドレス実行: `--headless`
- ブラウザ指定: `--browser chrome|firefox|webkit|msedge`
- 追跡保存: `--save-trace` / 動画保存: `--save-video=1280x720`
- セッション永続化: 既定は永続。一次セッションで十分なら `--isolated` を付与
- 出力先変更: `--output-dir path/to/dir`

## セキュリティ注意
- `--allowed-origins` / `--blocked-origins` を使うとネットワーク許可/遮断を細かく制御できます。
- ローカルファイルアクセスを厳しくする場合は既定（ワークスペース外禁止）を維持。緩める時のみ `--allow-unrestricted-file-access`。

## トラブルシュート
- 初回起動で時間がかかる: ブラウザのダウンロード中。完了後は高速化します。
- 既存 Chrome プロファイルを使いたい: `--browser chrome`（既定は Playwright 管理プロファイル）。
- `EACCES` や権限エラー: `.playwright-mcp/` の書き込み権限を確認。

## 参考
- Microsoft Playwright MCP: https://github.com/microsoft/playwright-mcp
