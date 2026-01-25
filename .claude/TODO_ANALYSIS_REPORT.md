# TODO分析レポート

**作成日**: 2026-01-09
**調査対象**: webui/*.js, backend/*.py
**検出総数**: 13件（webui: 13件, backend: 0件）

---

## 📊 優先度別サマリー

| 優先度 | 件数 | 説明 | 対応方針 |
|--------|------|------|----------|
| **P0: 必須** | 0件 | 本番動作に影響 | 即時実装 |
| **P1: 重要** | 5件 | ユーザー体験向上 | 即時実装可能 |
| **P2: 改善** | 6件 | 将来的に実装 | Issue化/詳細化 |
| **P3: 不要** | 2件 | 重複・不要 | 削除 |

---

## 🔍 TODO詳細リスト

### P1: 重要（即時実装可能） - 5件

#### 1. [P1-1] ナレッジ詳細画面への遷移実装 ⚡
- **ファイル**: `webui/app.js:2276`
- **現在のコード**:
```javascript
function viewKnowledgeDetail(knowledgeId) {
  logger.log('[SIDEBAR] Viewing knowledge:', knowledgeId);
  showNotification(`ナレッジ詳細 ID:${knowledgeId} を表示します`, 'info');
  // TODO: 実際の詳細画面へ遷移
}
```
- **実装内容**: `window.location.href = \`search-detail.html?id=${knowledgeId}\`;`
- **理由**: 既に検索結果から詳細画面への遷移は実装済み（app.js:1773）。同じパターンを適用
- **所要時間**: 2分
- **優先度根拠**: お気に入りから詳細を開けないのはUX問題

#### 2. [P1-2] お気に入り削除処理のAPI連携 ⚡
- **ファイル**: `webui/app.js:2285`
- **現在のコード**:
```javascript
function removeFavorite(knowledgeId) {
  logger.log('[SIDEBAR] Removing favorite:', knowledgeId);
  showNotification('お気に入りから削除しました', 'success');
  // TODO: 実際の削除処理
  loadFavoriteKnowledge();
}
```
- **実装内容**: APIエンドポイント `/api/v1/favorites/<id>` DELETE呼び出し（バックエンド実装必要）
- **所要時間**: 15分（バックエンド含む）
- **優先度根拠**: お気に入り機能は動作しているが、削除がローカルのみ

#### 3. [P1-3] タグ検索機能の実装 ⚡
- **ファイル**: `webui/app.js:2295`
- **現在のコード**:
```javascript
function filterByTag(tagName) {
  logger.log('[SIDEBAR] Filtering by tag:', tagName);
  showNotification(`タグ「${tagName}」で検索します`, 'info');
  // TODO: タグ検索を実行
}
```
- **実装内容**: `loadKnowledge({ tags: tagName })` を呼び出し
- **理由**: 既にloadKnowledge関数はタグフィルタリングに対応済み
- **所要時間**: 3分
- **優先度根拠**: タグクラウドがあるのに機能しないのは不完全

#### 4. [P1-4] 承認処理のAPI連携 ⚡
- **ファイル**: `webui/app.js:1407`
- **現在のコード**:
```javascript
async function approveSelected() {
  if (!checkPermission('quality_assurance')) {
    showNotification('承認権限がありません。', 'error');
    return;
  }
  // TODO: 実際の承認処理をAPIで実行
  showNotification('承認処理を実行しました。', 'success');
  logger.log('[APPROVAL] Approved selected items');
  loadApprovals();
}
```
- **実装内容**: `/api/v1/approvals/<id>/approve` POST呼び出し（バックエンド実装必要）
- **所要時間**: 20分（バックエンド含む）
- **優先度根拠**: 承認フローはコア機能

#### 5. [P1-5] 却下処理のAPI連携 ⚡
- **ファイル**: `webui/app.js:1426`
- **現在のコード**:
```javascript
async function rejectSelected() {
  if (!checkPermission('quality_assurance')) {
    showNotification('却下権限がありません。', 'error');
    return;
  }
  const reason = prompt('却下理由を入力してください:');
  if (!reason) return;
  // TODO: 実際の却下処理をAPIで実行
  showNotification('却下処理を実行しました。', 'success');
  logger.log('[APPROVAL] Rejected selected items. Reason:', reason);
  loadApprovals();
}
```
- **実装内容**: `/api/v1/approvals/<id>/reject` POST呼び出し（バックエンド含む）
- **所要時間**: 20分（バックエンド含む）
- **優先度根拠**: 承認フローはコア機能

---

### P2: 改善（将来実装） - 6件

#### 6. [P2-1] 配信申請API実装（将来機能）
- **ファイル**: `webui/actions.js:73`
- **現在のコード**:
```javascript
function submitDistribution(type, data) {
  showToast('配信申請を送信しました', 'success');
  logger.log('[ACTION] Distribution submitted:', type, data);
  // TODO: 実際の配信申請APIを実装
}
```
- **対応方針**: GitHub Issue化（Phase D: 機能拡張）
- **理由**: 配信機能は将来的な拡張機能。現時点では必須ではない
- **備考**: Microsoft 365連携（SharePoint/OneDrive）と同時実装推奨

#### 7. [P2-2] 通知フィルタリング実装（将来機能）
- **ファイル**: `webui/app.js:1335`
- **現在のコード**:
```javascript
if (panel.id === 'notificationSidePanel') {
  // TODO: 通知のフィルタリング実装
}
```
- **対応方針**: GitHub Issue化
- **理由**: 通知機能は動作中。フィルタは利便性向上だが必須ではない
- **提案実装**: 通知タイプ別フィルタ（info/warning/error）、日付範囲フィルタ

#### 8. [P2-3] ナレッジ編集モーダル実装（将来機能）
- **ファイル**: `webui/app.js:1442`
- **現在のコード**:
```javascript
async function editKnowledge(knowledgeId, creatorId) {
  if (!canEdit(creatorId)) {
    showNotification('編集権限がありません。作成者または管理者のみ編集できます。', 'error');
    return;
  }
  // TODO: 編集モーダルを表示するか、編集画面へ遷移
  showNotification('編集画面へ遷移します: ' + knowledgeId, 'info');
  logger.log('[KNOWLEDGE] Editing knowledge:', knowledgeId);
}
```
- **対応方針**: GitHub Issue化
- **理由**: 編集機能はPUT APIが実装済み（/api/v1/knowledge/<id>）。UIが未実装
- **提案実装**: 新規作成モーダルを流用した編集専用モーダル

#### 9. [P2-4] Slack連携実装（Phase D機能）
- **ファイル**: `webui/detail-pages.js:2459`
- **現在のコード**:
```javascript
function shareBySlack() {
  showToast('Slack連携機能は準備中です', 'info');
  // TODO: 実際のSlack API連携を実装
}
```
- **対応方針**: GitHub Issue化（Phase D: 機能拡張）
- **理由**: 外部連携は将来的な拡張機能
- **備考**: Slack Webhook or Slack API利用

#### 10. [P2-5] Microsoft Teams連携実装（Phase D機能）
- **ファイル**: `webui/detail-pages.js:2467`
- **現在のコード**:
```javascript
function shareByTeams() {
  showToast('Teams連携機能は準備中です', 'info');
  // TODO: 実際のTeams API連携を実装
}
```
- **対応方針**: GitHub Issue化（Phase D: 機能拡張）
- **理由**: 外部連携は将来的な拡張機能
- **備考**: Microsoft Graph API利用

#### 11. [P2-6] 朝礼用サマリ生成（将来機能）
- **ファイル**: `webui/app.js:1463`
- **現在のコード**:
```javascript
function generateMorningSummary() {
  showNotification('朝礼用サマリを生成しています...', 'info');
  // TODO: 実装
}
```
- **対応方針**: GitHub Issue化
- **理由**: レポート機能は付加価値だが必須ではない
- **提案実装**: 前日の更新、未読通知、承認待ちをPDF/Excel出力

---

### P3: 不要（削除対象） - 2件

#### 12. [P3-1] ダッシュボード共有（重複実装）❌
- **ファイル**: `webui/app.js:1453`
- **現在のコード**:
```javascript
function shareDashboard() {
  showNotification('ダッシュボード共有リンクを生成しています...', 'info');
  // TODO: 実装
}
```
- **削除理由**: `actions.js:91` に同名関数が実装済み（prompt使用）
- **対応**: app.js内の重複関数を削除、actions.jsの実装を使用

#### 13. [P3-2] 配信申請（重複実装）❌
- **ファイル**: `webui/app.js:1468`
- **現在のコード**:
```javascript
function submitDistribution(type, data) {
  showNotification('配信申請を送信しています...', 'info');
  // TODO: 実装
}
```
- **削除理由**: `actions.js:69` に同名関数が実装済み
- **対応**: app.js内の重複関数を削除、actions.jsの実装を使用

---

## 📈 実装推奨度と影響度マトリクス

```
高影響 │ P1-4,P1-5       │ P2-3           │
      │ (承認/却下)      │ (編集UI)       │
      │                 │                │
影響度 │ P1-1,P1-3       │ P2-2,P2-6      │
      │ (詳細/タグ)      │ (フィルタ等)    │
      │                 │                │
低影響 │ P1-2            │ P2-1,P2-4,P2-5 │
      │ (お気に入り)     │ (外部連携)      │
      └─────────────────┴────────────────┘
        低工数          高工数
```

---

## 🎯 実装推奨順序

### フェーズ1: 即時実装（本日中） - 60分
1. **P3削除**: 重複関数削除（5分）
2. **P1-1**: 詳細画面遷移（2分）
3. **P1-3**: タグ検索（3分）
4. **P1-2**: お気に入り削除API（15分）
5. **P1-4**: 承認API（20分）
6. **P1-5**: 却下API（20分）

### フェーズ2: Issue化（30分）
- P2-1〜P2-6をGitHub Issueに登録
- テンプレート: `[Enhancement] <機能名>`
- ラベル: `Phase-D`, `enhancement`

---

## 📝 実装後の変更点

### 削除されるTODO: 13件
### 実装完了予定: 5件（P1）
### Issue化予定: 6件（P2）
### コード削減: 2関数（P3重複削除）

---

## 🚀 次のアクション

1. ✅ **P3削除**: app.js内の重複関数を削除
2. ✅ **P1実装**: 5件のTODOを実装してコメント削除
3. 📋 **Issue作成**: 6件のP2 TODOをGitHub Issueに登録
4. 📖 **ドキュメント更新**: CLAUDE.mdの既知の問題セクションを更新

---

## 📊 コード品質向上効果

- **TODOコメント削減**: 13件 → 0件（100%削減）
- **重複コード削減**: 2関数削除
- **実装完了機能**: 5機能
- **技術的負債整理**: Issue化により管理可能に

---

**作成者**: Claude Code Agent
**レビュー**: 推奨
