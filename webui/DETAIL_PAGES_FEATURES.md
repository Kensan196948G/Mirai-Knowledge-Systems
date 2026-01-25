# 詳細ページ共通機能実装完了

## 実装完了日
2025-12-28

## 実装された機能

### 1. PDF保存機能 ✅
**関数:** `downloadPDF(pageType)`

**動作:**
- ブラウザの印刷機能（window.print()）を呼び出してPDF保存
- pageType: 'incident', 'sop', 'knowledge', 'consult'
- ファイル名形式: `${pageType}-report-${YYYYMMDD}.pdf`
- 成功通知表示（showNotification統合済み）

**使用例:**
```html
<button onclick="downloadPDF('incident')">📥 PDF保存</button>
```

### 2. 共有モーダル機能 ✅

**実装された関数:**
- `shareKnowledge()` - ナレッジ共有
- `shareSOP()` - SOP共有
- `shareIncident()` - 事故レポート共有
- `shareConsult()` - 専門家相談共有
- `openShareModal()` - モーダル表示（共通処理）
- `closeShareModal()` - モーダル閉じる
- `copyShareUrl()` - URLクリップボードコピー
- `shareByEmail()` - メールで共有（mailto:）
- `shareBySlack()` - Slack共有（準備中）
- `shareByTeams()` - Teams共有（準備中）

**HTMLモーダル構造:**
```html
<div id="shareModal" class="modal">
  <div class="modal-content">
    <div class="modal-header">
      <h2>共有</h2>
      <button class="modal-close" onclick="closeShareModal()">&times;</button>
    </div>
    <div class="modal-body">
      <div class="field">
        <label>共有URL</label>
        <input type="text" id="shareUrl" readonly>
        <button onclick="copyShareUrl()">コピー</button>
      </div>
      <div class="field">
        <button onclick="shareByEmail()">📧 メール</button>
        <button onclick="shareBySlack()">💬 Slack</button>
        <button onclick="shareByTeams()">👥 Teams</button>
      </div>
    </div>
  </div>
</div>
```

**特徴:**
- 動的モーダル生成（HTMLに存在しない場合は自動作成）
- 現在のURLを自動取得
- クリップボードAPI対応（フォールバック: execCommand）
- モーダル外クリックで閉じる

### 3. 新規作成モーダル機能 ✅

#### 3-1. 事故レポート新規作成
**関数:**
- `openNewIncidentModal()` - モーダル表示
- `closeNewIncidentModal()` - モーダル閉じる
- `submitNewIncident(event)` - フォーム送信
- `createNewIncidentModal()` - 動的モーダル生成

**フォーム項目:**
- タイトル（必須）
- 発生日時（必須）- datetime-local
- 発生場所（必須）
- 重大度（必須）- 低/中/高/重大
- 事故内容（必須）- textarea
- 写真・資料 - file input（複数可、image/*,.pdf）

**データ処理:**
- localStorageに保存
- 新規IDを自動生成
- タイムライン自動生成
- 作成後、新規レポートページに遷移

#### 3-2. 専門家相談新規作成
**関数:**
- `openNewConsultationModal()` - モーダル表示
- `closeNewConsultationModal()` - モーダル閉じる
- `submitNewConsultation(event)` - フォーム送信
- `createNewConsultationModal()` - 動的モーダル生成

**フォーム項目:**
- 質問タイトル（必須）
- カテゴリ（必須）- 構造設計/施工管理/品質管理/安全管理/環境対策/地盤技術
- 優先度（必須）- 通常/高/緊急
- 質問内容（必須）- textarea（8行）
- 添付ファイル - file input（複数可、image/*,.pdf,.xlsx,.dwg）

**データ処理:**
- APIに送信（POST /consultations）
- エラーハンドリング
- 成功通知後、ページリロード

### 4. トースト通知システム統合 ✅

**使用例:**
```javascript
showNotification('操作が完了しました', 'success');  // 成功
showNotification('エラーが発生しました', 'error');    // エラー
showNotification('処理中...', 'info');               // 情報
showNotification('警告メッセージ', 'warning');        // 警告
```

**統合箇所:**
- PDF保存成功/失敗
- URL コピー成功
- メール共有開始
- 事故レポート作成/更新
- 専門家相談投稿

### 5. その他の共通機能 ✅

**actions.jsに追加された関数:**
- `updateIncidentStatus()` - ステータス更新モーダル表示
- `closeStatusModal()` - ステータスモーダル閉じる
- `editIncident()` - 事故レポート編集
- `editConsult()` - 専門家相談編集
- `closeConsult()` - 相談クローズ
- `toggleFollow()` - フォロー切り替え
- `resetAnswerForm()` - 回答フォームリセット
- `closeAnswerDetailModal()` - 回答詳細モーダル閉じる
- `selectBestAnswer()` - ベストアンサー選択
- `startRecord()` - SOP編集記録開始
- `cancelRecord()` - 記録キャンセル

## ファイル構成

### 実装ファイル
1. **detail-pages.js** - メイン実装（新規追加: 約500行）
   - PDF保存機能
   - 共有機能（モーダル動的生成含む）
   - 新規作成モーダル（事故レポート/専門家相談）

2. **actions.js** - アクション関数（追加: 約130行）
   - イベントハンドラー
   - モーダル制御
   - フォーム処理

3. **incident-detail.html** - 事故レポート詳細ページ
   - 共有モーダルコメント追加

4. **expert-consult.html** - 専門家相談詳細ページ
   - 共有モーダルコメント追加
   - 新規作成モーダルコメント追加

### 既存統合
- **app.js** - showNotification関数（既存）
- **styles.css** - モーダルスタイル（既存）

## 使用方法

### HTML内での呼び出し
```html
<!-- PDF保存 -->
<button class="cta ghost" onclick="downloadPDF('incident')">
  📥 PDF保存
</button>

<!-- 共有 -->
<button class="cta ghost" onclick="shareIncident()">
  🔗 共有
</button>

<!-- 新規作成（事故レポート） -->
<button class="cta" onclick="openNewIncidentModal()">
  新規作成
</button>

<!-- 新規作成（専門家相談） -->
<button class="cta" onclick="submitNewConsultation()">
  新規相談
</button>
```

### JavaScript内での呼び出し
```javascript
// PDF保存
downloadPDF('sop');

// 共有モーダル表示
shareSOP();

// URLコピー
copyShareUrl();

// メール共有
shareByEmail();
```

## エラーハンドリング

すべての機能にエラーハンドリングを実装：
- try-catchブロック
- エラー通知（showNotification）
- コンソールログ出力
- ユーザーフレンドリーなメッセージ

## 動作確認済み機能

✅ PDF保存（印刷ダイアログ表示）
✅ 共有モーダル表示
✅ URLコピー（クリップボードAPI）
✅ メール共有（mailto:）
✅ Slack/Teams共有準備中メッセージ
✅ 事故レポート新規作成モーダル
✅ 専門家相談新規作成モーダル
✅ フォームバリデーション
✅ localStorage連携
✅ 通知統合

## 今後の拡張ポイント

1. **PDF生成強化**
   - jsPDF/html2canvasを使用した高度なPDF生成
   - カスタムレイアウト
   - 自動ダウンロード

2. **Slack/Teams連携**
   - Webhook統合
   - OAuth認証
   - メッセージカスタマイズ

3. **ファイルアップロード**
   - プログレス表示
   - プレビュー機能
   - サイズ制限チェック

4. **リアルタイム通知**
   - WebSocket統合
   - プッシュ通知
   - バックグラウンド同期

## テスト方法

1. ブラウザでdetail-pages.jsを読み込む
2. 各詳細ページ（incident-detail.html、expert-consult.html）にアクセス
3. サイドバーの「PDF保存」「共有」ボタンをクリック
4. ヘッダーの「新規作成」ボタンをクリック
5. フォーム入力して送信
6. 通知が表示されることを確認

## 注意事項

- モーダルは動的に生成されるため、HTMLに存在しなくても動作する
- localStorageにデータが存在しない場合は適切なエラーメッセージを表示
- すべての関数はグローバルスコープに登録済み（window.関数名）
- ブラウザの印刷機能を使用するため、ページスタイルが印刷に最適化されている必要がある
