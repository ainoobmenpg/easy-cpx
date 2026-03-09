# Arcade CPX 再レビュー（ゲーム性最優先・徹底的に厳しく）

作成日: 2026-03-09（第2回）
対象: docs一式、frontend、backend（特に `backend/app/services/arcade_adjudication.py` / `api/routes.py`）
前提: 「ゲーム的CPX＝短時間・単純明快・ミリ感の味」を最優先。訓練厳密性よりも遊びやすさ重視。

---

## 結論（要旨）

- 目的適合度（ゲーム寄り）: 78/100（前回: 72）
- 合否: 条件付き合格のまま。コアループ実装は前進したが「仕様・UI・ルール・API」の食い違いが依然大きい。
- 評価: 2D6エンジン（ArcadeAdjudication）は◎。ただし、ドキュメントとフロント/ルーティングのズレが体験を崩している。

---

## 重大ブロッカー（要修正）

1) コマンド不整合（WAIT/STRIKE/SPECIAL）
- quick-ref: 6コマンドにSTRIKEを明記。
- game-rules(Arcade): WAITを記載、STRIKEなし。
- frontend: STRIKE→`order_type: 'special'`でPOST。
- arcade_adjudication: SPECIAL未対応（無効化される）。
→ 影響: ボタン1つが「押しても何も起きない」危険な罠。即修正必須。

2) 判定方式の齟齬（単一ロール vs 対抗ロール）
- quick-ref: 「Roll+Mod」1表でCRITICAL/…（単一ロールに読める）。
- arcade_adjudication: 攻撃側2D6+ATK vs 防御側2D6+DEF の対抗ロール（差分で判定）。
→ 影響: プレイヤーが結果を予見できない。どちらかに統一して明文化を。

3) 移動仕様の矛盾
- quick-ref: 地形別のCells/Turn（平地4/森林2…）。
- arcade_adjudication: ユニット種別ごとの`move`（例：歩兵2/戦車3）＋到達先タイルのコストのみ参照。
- architecture: 「Arcadeは1セル/手番」とも読める記述あり。
→ 影響: どれが正解か不明。UIの予測表示も破綻。仕様を「ユニット基準の移動値 ×（地形コスト）」に一本化推奨。

4) ユニット種別の不一致
- quick-ref: INF/ARM/ART/AD/RECON（5種）。
- game-rules(Arcade): +SUPPORTを含む6種。
- architecture: 「3種（歩・戦・砲）に簡略化」と記述。
- arcade_adjudication: 6種（SUPPORTあり）。
→ 影響: 参照元で数字が食い違う。ドキュメントを実装（6種）に合わせて統一。

5) マップサイズとシナリオの乖離
- architecture: Arcadeは固定12×8。
- docs/scenarios/*: 50×40, 60×50, 70×50など大型（シミュ向け）。
→ 影響: Arcadeとの互換がない。各シナリオに「Arcade版（12×8）」の配置と勝利条件を併記すべき。

6) API/ルーティング未接続
- 追加された`/turn/commit`はシミュ用`RuleEngine`を呼ぶ。Arcade用`ArcadeAdjudication`を使うエンドポイントがない。
→ 影響: Arcadeとして遊べない。`/arcade/turn/commit`（もしくは`/turn/commit`が`game_mode`を見て分岐）を早急に。

7) Victory Pointsの未実装
- quick-ref: 「Points: 10 pts/unit destroyed」記載。
- 実装: 加点やスコア表示なし。
→ 影響: Arcadeの“気持ち良いスコアリング”が効かない。スコアとスター評価を導入。

---

## 改善点（高優先）

- STRIKEの定義を最小コストで実装
  - 仕様: `order_type: special`をArcadeで受理し「攻撃ロール+2、使用後にcan_attack=False（次ターンまで）」
  - コスト: ゲーム側`strike_tokens`（Gameに整数）を導入（初期2〜3）。0なら失敗。
  - UI: ボタンに残数バッジ。ツールチップで効果説明。

- 判定方式の統一（ドキュメント優先）
  - 対抗ロール方式を採用（現実装に合わせる）。
  - quick-refの「2D6表」を「差分テーブル」に差し替え（diff≤-3=CF, -2=F, -1/0=P, +1=S, +2=G, ≥+3=C）。

- 移動の一貫仕様
  - 「ユニットmove値（2〜4） ×（目的タイルの地形コスト）」で可否判定。
  - quick-refの「地形別Cells/Turn」は削除し、ユニット表の`MOVE`に一本化。
  - UIで「到達可否」を色（到達=緑/部分=黄/不可=赤）でプレビュー。

- シナリオのArcade版を追加
  - `docs/scenarios/*`に「Arcadeセクション」を新設（12×8配置、初期STRIKE残数、勝利点、所要ターン6〜8）。
  - 既存の大判マップはSimulation用として残す。

- Victory Points / 星評価
  - 破壊=10pt、主要目標=+15、達成ターン短縮ボーナス=+X、STRIKE未使用ボーナス=+Y。
  - ターン終了時に加点カードをSITREP内に表示、最終スコアに星1〜3を付与。

- イベントデッキの実戦投入
  - arcade_adjudication内で「1ターン1枚/20%」の抽選→`event_deck.py`適用。
  - 修正値は`attack/defense/movement`のいずれか±1/1ターン程度に限定し、可視化する。

- 敵AIの最低限行動
  - 隣接攻撃>前進>防御の優先度。ターゲットは最も弱い/VP近いユニット。
  - これがないと“置物”になり、ゲーム感が損なわれる。

---

## ドキュメント整合性チェック（差異の指摘）

- quick-ref.md vs game-rules.md vs architecture.md vs 実装
  - [NG] コマンド: STRIKEの有無が不一致（実装なし）。
  - [NG] 判定: 単一ロール表と対抗ロールの混在。
  - [NG] 移動: 地形固定表とユニットMOVE値の混在。
  - [NG] ユニット種: 3/5/6種が混在（実装は6）。
  - [NG] マップ: 12×8と大判マップが混在（モード未明示）。
  - [NG] 得点: quick-refのみ、実装/API/UIは未対応。

→ 対応: quick-refを唯一の「Arcadeプレイヤー向け仕様書」に格上げし、他ドキュは参照・付録化。数表・閾値はquick-refをソース・オブ・トゥルースに。

---

## 実装ギャップ（コード観点）

- `/turn/commit`がArcade未対応 → `Game.game_mode`で分岐し、Arcadeなら`ArcadeAdjudication.adjudicate_turn()`を呼ぶ。
- `frontend`のArcadeボタン→`/api/orders`投げっぱなし → Arcadeは即時/一括処理の`/turn/commit`（あるいは`/arcade/turn/commit`）に統一。
- SPECIAL未実装 → `ArcadeAdjudication`に`resolve_strike()`追加、または`resolve_attack()`内でフラグ処理。
- Victory Points → `Game`に`score`フィールド（INT）。攻撃結果や目標達成で加点、SITREPに表示。
- Fog of War(Arcade) → 最低限「隣接セルのみ可視」を導入（非可視ユニットはUIで半透明/不表示）。

---

## バランス速報（初期所感）

- 現行の対抗ロール閾値は“出目ブレ”依存が強く、連敗・連勝が出やすい。
- 攻撃>防御の基礎値（ATK/DEF）差を+1〜+2に抑え、イベント修正±1で手触りを作るのが無難。
- 目安分布（突破30/維持50/押し返20）を狙うなら、同格対戦で`diff=+1`付近にプレイヤーが乗りやすい調整が必要。

---

## 48時間以内の修正TODO（Issue対応案）

- Fix-1: `/turn/commit`で`game_mode`分岐 → Arcadeなら`ArcadeAdjudication.adjudicate_turn()`
- Fix-2: frontendのArcadeボタンを`/turn/commit`に変更（ユニットIDと簡易命令を配列で送る）
- Fix-3: SPECIAL=STRIKE実装（+2攻撃、次ターン攻撃不可、残数消費）
- Fix-4: quick-refを対抗ロール基準に修正、6種ユニットとMOVE表を統一
- Fix-5: `docs/scenarios/*`へArcade版（12×8）を追記し、VP/STRIKE残数も定義
- Fix-6: SITREPカードに「ターン加点/累計スコア」を表示

---

## 総評

Arcadeエンジンが入って“遊べる核”は出来た。ただし、仕様と実装・UIのつなぎが崩れており、初見プレイヤーには不親切。まずは「STRIKEの実働」「/turn/commitのArcade対応」「quick-refの唯一仕様化」を一気に片付けること。そこまで通れば、30分完走の“気持ち良いミリごっこ”は実現できる。
