# NATO CPX ゲーム化ドキュメント レビュー（徹底的に厳しく）

作成日: 2026-03-09
対象: `docs/architecture.md`, `docs/game-rules.md`, `docs/cpx-reference/*`
前提: 本PJの目的を「NATOの軍事演習CPX（Command Post Exercise）をゲーム化すること」と解釈。

---

## 結論（要旨）

- 目的適合度: 55/100（未達）
- 合否: 不合格（CPX “相当”の骨格はあるが、NATO CPXの要点が欠落）
- 到達点: 「抽象的な作戦級戦闘ゲーム」の枠には達しているが、「NATO CPXの訓練様式・手順・成果物をゲームとして再現」する水準には到っていない。

---

## 重大ブロッカー（Blockers）

1) NATO標準の指揮・計画様式が欠落（必須）
- 指揮命令の形式が独自（`CommanderOrder` は Intent/Mission/Constraints/ROE…）で、NATOの5段構成（SMESC: Situation, Mission, Execution, Service Support, Command & Signal）やFRAGO、COPD/JOPPの手順化がない。
- 影響: CPXとしての「参謀プロセス」「命令循環」「正規の報告物」再現が不可能。

2) EXCON/ホワイトセル構造の未整備
- `excon_ai.py` 想定はあるが、ホワイトセル/レスポンスセル/コントロールセルの役割分担、MEL/MIL（Master Events/Inject List）運用、審判ルールが未定義。
- 影響: 訓練的イベント注入・審判の透明性・再現性が確立できない。

3) 報告様式・情報伝達の標準化不足
- `SITREP` はあるが、NATOの定型（SITREP, INTSUM, OPSUM, LOGSITREP, SALUTEなど）の項目粒度・用語統一がない。
- 影響: 情報の鮮度・確度・伝達遅延の管理と、訓練らしい業務フロー評価が困難。

4) 地理参照の不備（MGRS/座標系・フェーズライン未対応）
- データモデルは `x,y: Float` と擬似座標、テキスト地図はあるが、NATO運用で一般的なMGRS/グリッド、フェーズライン/境界、目標参照が未定義。
- 影響: 命令・報告・火力連携（ATO/ACO/FSCL等）の実務に即した表現ができない。

5) 多国籍・多階層C2未対応
- `side: player/enemy` 二値で、同盟/多国籍/下位部隊/上級司令部の多階層C2を表現できない。
- 影響: NATOらしい統合作戦・多国籍共同の本質が再現不能。

6) 「訓練評価」の設計がない
- 勝利条件は「殲滅/目標占領/膠着」中心。CPXでは訓練目標（T&EO/MOP/MOE）達成とAARが主。
- 影響: ゲームは成立してもCPXの教育目的が満たせない。

7) 審判（Adjudication）の根拠不足
- `game-rules.md` の判定要素は汎用的で、C2遅延、命令伝達・準備時間、交戦規定（ROE）、航空統制（ATO/ACO/エアスペース）、ターゲティング・プロセス等の手続を織り込めていない。
- 影響: CPXらしい「手続遵守の優位/違反の不利」が結果に反映されない。

8) ロジ/サステインメントの粒度不足
- 弾薬/燃料の3段階や「Interceptors/Precision Munitions」のカウンタはあるが、補給等級（Class I/III/V等）、回復/補充サイクル、MOT/補給路閉塞、MHE/補給拠点などの運用表現が足りない。
- 影響: 作戦継続可能性のコアがゲームに落ちない。

---

## 高優先の構造的ギャップ（High）

- ATO/ACO/エアスペース管理の不在（航空運用は判定表のみ）
- ターゲティング（JIPTL/NAI/TAI/ISRタスク）とFires統制（FSCL/CFZ/No-Fire Area）未定義
- EW/サイバー/情報作戦の役割と評価軸が曖昧
- 参謀業務（RFI/CCIR/PIR/IR）の循環が未導入
- シナリオ仕様の欠落（開始時のORBAT、地物、ルール適用セット、勝敗ではなく訓練目的の定義）
- 再現性・監査性（Seed付き判定、ログ、AAR自動収集）の欠落

---

## 現行ドキュメントの長所（認定）

- `Fog of War` の二層（真実/プレイヤービュー）設計は◎（CPXの出発点）
- `SITREP + テキストマップ`（`cpx-reference/excon-prompt-v4.1.md`）は状況把握を助ける良案
- 天候/時間/地形/資源の影響を明記（作戦級の基本）
- 上官命令の構造化（Intent/Constraints/ROE/Reporting）はCPX志向
- AARテンプレの試案あり

---

## 設計・データモデルへの具体的指摘

- `Game`: `current_date/time` あり → 時間管理は○。ただし「命令/報告/航空サイクル」等の複数時間軸を持てるよう、`planning_cycle`, `air_tasking_cycle`, `logistics_cycle` 等の導入を推奨。
- `Unit`: `side` が `player/enemy` 固定 → 多国籍対応のため `faction`（国/同盟/司令部）、`echelon`（軍/軍団/師/旅/大/中/小 等）を追加。
- `Order`: `order_level`（T/O/S）はあるが、NATOの命令書式（OPORD/FRAGO）を別テーブルで保持し、`SMESC`各節と紐づけること。
- 座標系: `x,y: Float` を最小限残しつつ、主参照は `MGRS` 文字列、`grid_ref_precision` を追加。フェーズライン/境界/エアスペースもエンティティ化。
- 情報: `intelligence` を情報源・鮮度・確度・RFI紐づけで正規化（報告連鎖を再現）。
- ログ: `adjudication_log` と `inject_log` を永続化し、AAR出力に流用。

---

## ルール/審判（Adjudication）の批評

- 成功/部分/失敗の三値は単純すぎる。CPXでは「手続遵守」「準備時間」「C2/ISR/兵站の整合」が結果を左右するため、判定前提のチェックリスト化が必要。
- 例: 攻勢判定は以下の最低条件を要求
  - ISR整合（NAI/TAI監視、PIR消化率）
  - Fires整合（SEAD、TOT、Danger Close許容、FSCLと整合）
  - Maneuver整合（軸/フェーズライン/予備/後続）
  - Sustainment整合（Class III/V所要・補給回数・輸送計画）
  - C2整合（同期マトリクス、通信計画、遅延/断の確率）
- これらが閾値未達の場合、実力差があっても「部分成功止まり」に倒す審判方針がCPX的。

---

## EXCON/イベント運用

- `excon-prompt-v4.1.md` は良い叩き台。ただしMEL/MILが未整備。イベントに「目的・注入条件・観察項目・想定反応・評価ポイント」を付与し、難易度調整を可能にすること。
- 参謀行動を促すため、定常Inject（RFI回答遅延、上官の優先変更、物流寸断、非戦闘員流入、空域制限変更等）を周期注入。

---

## 報告/様式の標準化（最低限）

- SITREP（標準項目）、INTSUM、OPSUM、LOGSITREP、FRAGOフォーマットを`docs/`配下で定義し、`/api/games/{id}/sitrep`等の返却スキーマと一致させる。
- 敵情報はSALUTE（Size, Activity, Location[MGRS], Unit/Uniform, Time, Equipment）で表現。推定/未確認はタグ化。

---

## ゲーム化（Game Design）観点

- 勝利条件を「訓練達成度」に置換（例: CCIRへの対応率、ROE遵守、損耗対効果、目標達成の時間内率）。
- スコアは「計画・同期・持続・情報・交戦」の5軸合成。AARで定量提示。
- UIは「計画（OPORD/FRAGO編集）」「同期（時間-効果マトリクス）」「状況（SITREP/INTSUM/マップ）」「持続（補給ダッシュボード）」の4タブ構成が望ましい。

---

## 10日以内の優先ロードマップ（提案）

Day 1-2: 仕様ドキュメント整備
- `docs/nato/opord.md`（SMESCフォーマット）
- `docs/nato/reports.md`（SITREP/INTSUM/LOGSITREP/FRAGOテンプレ）
- `docs/nato/airspace-fires.md`（ATO/ACO、FSCL/No-Fire等の最小ルール）

Day 3-4: データモデル改修案
- `MGRS`導入、`faction/echelon` 追加、`opord`/`frago`テーブル設計案を`architecture.md`に追記

Day 5-6: Adjudication v1.5
- 前提チェック（ISR/Fire/Sustainment/C2）を通過しない攻撃は自動で成功上限を「部分成功」に制限
- 低確率イベントはMEL/MILに一本化

Day 7: 報告系APIスキーマ
- `/sitrep`, `/intsum`, `/opsum`, `/logsitrep` の返却JSON雛形

Day 8: AAR/スコアリング
- MOP/MOE指標とAAR出力のドラフト（`cpx-reference` に雛形）

Day 9-10: 最小シナリオ
- NATO準拠の開始資料（ORBAT、MGRSマップ、上官OPORD、CCIR、ROE）を`docs/scenarios/`に追加

---

## クリティカル修正指示（短期）

- 表記: 目的文の「PCX」は「CPX」に統一（正式: Command Post Exercise）。
- `game-rules.md`: 勝利条件章に「訓練達成度（T&EO/MOP/MOE）」を追加。
- `architecture.md`: Data Modelsに `MGRS`/`faction`/`echelon`/`opord_id`/`frago_id` を追記、APIに `/reports/*` 群を追加。
- `cpx-reference/excon-prompt-v4.1.md`: MEL/MILセクション、SALUTE準拠の敵情報表現、AARの評価指標を増補。

---

## 最終評価

- 現状は「作戦級の抽象ゲームとしては有望」だが、「NATO CPXの訓練様式をゲームとして体験・評価できる」状態には未達。
- 上記ブロッカー（特にSMESC/EXCON構造/MGRS/報告様式）を潰せば、CPXゲーム化としての核が立つ。まずは「手続（プロセス）を結果に直結させる審判」に着手すべき。

---

### 付録：最小OPORD（SMESC）雛形（ドラフト）

- Situation: 概況/敵情/友軍/民生/地形天候/想定
- Mission: 任務（5W+H, Time/MGRS参照）
- Execution: 作戦構想/主攻補助/フェーズ/協同/COA/リスク/ROE
- Service Support: 補給/医療/回収/輸送/補充/補給所/MOT
- Command & Signal: 指揮系統/位置/通信計画/周波数/暗号/認証

（本雛形は`docs/nato/opord.md`へ分離推奨）
