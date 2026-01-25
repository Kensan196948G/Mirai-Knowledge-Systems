# ワイヤーフレーム

## 目的
- 主要画面のレイアウトと情報量を検証し、視線導線を固定する

## 共通レイアウト
- 3カラム構成: 左サイドバー / メイン / 右レール
- ヘッダーにグローバルナビゲーションと主要アクションを配置
- 主要情報はメイン上段に集約、補助情報は右レールに配置

## ダッシュボード (index.html)
```
[Header]
  - Brand / Global Nav / Status Chips / CTA
[Hero]
  - Title + Summary
  - Primary Actions (3)
  - Search Bar + Filters
[Metrics]
  - 4 KPI Cards
[Main Panels]
  - Approval Flow / Weekly Actions
  - Monitoring / Risk Alerts
  - Tabs (Search / SOP / Incident)
  - Knowledge Flow / Regulation Check
[Right Rail]
  - Alert
  - Site Status
  - Map Snapshot
  - Activity Feed
  - Expert On Duty
```

## 詳細画面 (検索/SOP/法令/事故/相談)
```
[Header]
  - Global Nav / Status Chips / CTA
[Detail Hero]
  - Breadcrumb / Title
  - Meta Info / Tags / Actions
[Detail Grid]
  - Content Cards (Steps, Analysis, Tasks, References)
  - KPI/Progress/Timeline as needed
[Right Rail]
  - Alert / Review Status
  - Related Sites
  - Related Knowledge / Documents
```

## 詳細画面ごとの重点ブロック
- 検索結果詳細: 温度ログサマリ / 逸脱履歴 / 関連資料
- SOP詳細: 点検ステップ / 判定基準 / 改訂履歴
- 法令詳細: 改訂ポイント / 影響評価 / 周知スケジュール
- 事故詳細: タイムライン / 原因分析 / 是正措置
- 相談: 相談フォーム / 必要資料 / 回答テンプレ

## 配置ルール
- 緊急性の高い情報は右レールの上段
- KPI/進捗はメイン中段で一覧性を確保
- テーブルは詳細カード内に配置し、横スクロールは避ける

## 成功条件
- ダッシュボードの主要情報が1画面で把握できる
- 詳細画面で判断に必要な情報が1スクロール以内に集約される

## 変更履歴
| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-26 | 0.1 | 初版作成 | Codex |
