# PWA Requirements Specification - Mirai Knowledge Systems

**プロジェクト**: Mirai Knowledge Systems v1.3.0
**Phase**: D-5 - Progressive Web App Implementation
**作成日**: 2026-01-31
**ステータス**: 要件定義完了

---

## 1. エグゼクティブサマリー

### 1.1 背景とコンテキスト

**現状**:
- **システム**: Mirai Knowledge Systems v1.3.0
- **アーキテクチャ**: Flask 3.1.2 backend + Vanilla JavaScript frontend
- **ユーザー**: 300+名の同時接続ユーザー（建設現場）
- **ページ数**: 16 HTMLページ、約350KB JavaScript
- **現在の制限**:
  - ネットワーク依存の運用
  - オフラインでのSOP/規制情報アクセス不可
  - モバイルデバイス最適化不足
  - ホーム画面インストール機能なし

**ビジネス課題**:
建設現場では以下の問題が頻発:
- 不安定なネットワーク接続（山間部、地下工事）
- オフラインでの安全手順書へのアクセス需要
- 過酷な環境でのタブレット/スマートフォン使用
- 中央ナレッジリポジトリへのアクセス遅延

**解決策**: Progressive Web App（PWA）化により、オフライン優先の運用を実現し、既存のFlaskバックエンドとの完全統合を維持します。

### 1.2 戦略目標

1. **運用継続性**: ネットワーク状態に関わらず重要なナレッジへのアクセスを保証
2. **モバイル最適化**: デプロイコストなしでネイティブアプリ並みの体験を提供
3. **コスト効率**: iOS/Androidネイティブアプリ開発を回避（推定削減額: ¥15M+）
4. **迅速デプロイ**: 既存Web資産を活用し3週間で実装完了

### 1.3 成功指標

| 指標 | 現在 | 目標 | 測定方法 |
|------|------|------|----------|
| オフラインアクセス率 | 0% | 85%+ | SOP/規制情報のキャッシュ率 |
| モバイルロード時間 | 8-12s | <3s | Lighthouse Performance Score |
| インストール率 | 0% | 40%+ | アクティブユーザーのPWAインストール率 |
| ネットワーク障害回復 | 手動リフレッシュ | 自動 | Background Sync成功率 |
| PWAスコア（Lighthouse） | 0 | 90+ | 自動監査 |

---

## 2. ユーザーストーリーとシナリオ

### 2.1 主要ユーザーストーリー

**US-PWA-001: オフラインSOP閲覧（Critical）**
```
AS A 建設現場の作業員
I WANT 通信環境が悪い場所でもSOP・規制情報を閲覧したい
SO THAT 作業手順を確認して安全に作業を遂行できる

受け入れ基準:
- 過去に閲覧したSOP/規制情報はオフラインでアクセス可能
- オフライン状態が明確に表示される
- キャッシュされたコンテンツ一覧を確認できる
- ネットワーク復旧時に自動同期される
```

**US-PWA-002: ホーム画面インストール（High）**
```
AS A 現場監督
I WANT スマートフォンのホーム画面からアプリのように起動したい
SO THAT ブラウザのブックマークから探す手間を省ける

受け入れ基準:
- インストールプロンプトが適切なタイミングで表示される
- インストール後はブラウザUIなしで全画面表示
- アプリアイコンとスプラッシュ画面が表示される
- OSのアプリ切り替えに表示される
```

**US-PWA-003: バックグラウンド同期（Medium）**
```
AS A 品質保証担当
I WANT オフライン時に記録した監査結果を自動送信したい
SO THAT ネットワーク復旧を待たずに次の作業に移れる

受け入れ基準:
- オフライン時の入力データはローカルに保存される
- ネットワーク復旧時に自動的にサーバーへ送信される
- 送信待ちキューの状態を確認できる
- 送信失敗時はリトライされる
```

**US-PWA-004: プッシュ通知（Optional）**
```
AS A 安全衛生責任者
I WANT 重大事故情報をプッシュ通知で受け取りたい
SO THAT 即座に現場への注意喚起ができる

受け入れ基準:
- 緊急度「高」のナレッジ登録時にプッシュ通知
- 承認待ちアイテムの通知
- 通知設定のオン/オフが可能
```

### 2.2 エッジケースと制約条件

**制約C-001: HTTPS要件**
- Service WorkerはHTTPS環境でのみ動作
- 開発環境: localhostはHTTPでも許可
- 本番環境: 既存の自己署名証明書を活用（192.168.0.187:9443）

**制約C-002: ストレージ制限**
- Cache Storage: 約50MB（ブラウザ依存）
- IndexedDB: 約50MB-250MB（ブラウザ依存）
- 古いキャッシュのLRU（Least Recently Used）削除戦略が必須

**制約C-003: Safari制限**
- Push Notifications: iOS Safari 16.4+で限定サポート
- Background Sync: iOS Safariでは未サポート（段階的拡張）
- Service Worker: Safari 11.1+でサポート

---

## 3. 機能要件

### 3.1 オフライン機能（Priority: CRITICAL）

**FR-PWA-001: Service Workerインストール**
- Service Workerの登録とライフサイクル管理
- 更新検知（24時間ごと）とリフレッシュプロンプト
- エラーハンドリングとフォールバック

**FR-PWA-002: 静的アセットキャッシュ**
- 対象: HTML, CSS, JavaScript, 画像, フォント
- 戦略: Cache First（キャッシュ優先）
- 有効期限: 7日間
- バージョン管理: `v1.3.0-cache-{timestamp}`

**FR-PWA-003: APIレスポンスキャッシュ**
- 対象エンドポイント:
  - `/api/knowledge`（検索結果）
  - `/api/sop/{id}`（SOP詳細）
  - `/api/regulations`（規制情報）
  - `/api/notifications`（通知一覧）
- 戦略: Network First with Cache Fallback
- 有効期限: 1時間（検索結果）、24時間（詳細ページ）

**FR-PWA-004: オフラインフォールバックページ**
- ネットワーク不可時の専用オフラインページ
- キャッシュ済みコンテンツへのナビゲーション
- オフライン状態の明確な表示

### 3.2 インストール体験（Priority: HIGH）

**FR-PWA-005: Web App Manifest**
- アプリ名、アイコン、テーマカラー定義
- Standalone表示モード
- スプラッシュ画面設定
- ショートカット定義

**FR-PWA-006: インストールプロンプトUI**
- 初回訪問から2分後、または3ページ閲覧後に表示
- ユーザーが「後で」を選択した場合は7日間非表示
- 設定パネルから再表示可能

### 3.3 バックグラウンド同期（Priority: MEDIUM）

**FR-PWA-007: Background Sync登録**
- 新規ナレッジ登録
- 専門家相談の送信
- 承認/却下アクション
- 通知既読ステータス

**FR-PWA-008: 同期キュー管理**
- IndexedDBによるpending queue管理
- リトライロジック（指数バックオフ: 1s, 2s, 4s, 8s, 16s）
- 最大リトライ回数: 5回
- 失敗時のユーザー通知

### 3.4 パフォーマンス最適化（Priority: HIGH）

**FR-PWA-009: リソースヒント**
- preconnect, dns-prefetch
- preload（重要なJS/CSS）
- 画像のlazy loading

**FR-PWA-010: コード分割**
- Critical CSSのインライン化
- JavaScriptの遅延ロード
- 画像のlazy loading

---

## 4. 非機能要件

### 4.1 パフォーマンス要件

| 指標 | 目標 | 測定ツール |
|------|------|-----------|
| First Contentful Paint (FCP) | <1.5s | Lighthouse |
| Largest Contentful Paint (LCP) | <2.5s | Lighthouse |
| Time to Interactive (TTI) | <3.5s | Lighthouse |
| Total Blocking Time (TBT) | <200ms | Lighthouse |
| Cumulative Layout Shift (CLS) | <0.1 | Lighthouse |
| PWAスコア | 90+ | Lighthouse |
| キャッシュヒット率 | 70%+ | Service Worker Metrics |

### 4.2 互換性要件

**デスクトップブラウザ**:
- Chrome 90+ ✅
- Edge 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅

**モバイルブラウザ**:
- Chrome Android 90+ ✅
- Safari iOS 14+ ✅（制限付き）
- Samsung Internet 14+ ✅

**デバイスサポート**:
- Viewport: 320px - 2560px
- タッチターゲット: 最小 44x44px
- オフラインストレージ: 最低 50MB

### 4.3 セキュリティ要件

**SEC-PWA-001: HTTPS強制**
- 本番環境ではHTTPS必須
- HTTP→HTTPSリダイレクト
- HSTSヘッダー設定

**SEC-PWA-002: トークンセキュリティ**
- JWTトークンのIndexedDB暗号化保存
- トークン有効期限の厳格な管理
- Refresh tokenのローテーション

**SEC-PWA-003: Content Security Policy**
```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' https://cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  img-src 'self' data: https:;
  connect-src 'self' https://192.168.0.187:9443;
  worker-src 'self';
```

### 4.4 アクセシビリティ要件

- WCAG 2.1 Level AA準拠
- スクリーンリーダー対応
- キーボードナビゲーション
- 適切なARIAラベル

---

## 5. 受け入れ基準

### 5.1 Phase 1: PWA基盤（Week 1）

**AC-P1-001: Service Worker登録**
- [ ] Service Workerが正常に登録される
- [ ] 開発環境（localhost:5200）で動作確認
- [ ] 本番環境（192.168.0.187:9443）で動作確認
- [ ] Service Workerの更新検知が機能する

**AC-P1-002: Manifestインストール**
- [ ] manifest.jsonが正しく読み込まれる
- [ ] Android Chromeでインストールプロンプト表示
- [ ] iOS Safariで「ホーム画面に追加」が機能
- [ ] アプリアイコンとスプラッシュ画面が表示

### 5.2 Phase 2: キャッシュ戦略（Week 2）

**AC-P2-001: 静的アセットキャッシュ**
- [ ] HTML/CSS/JSがCache Firstで配信される
- [ ] 2回目以降のページロードが1秒未満
- [ ] オフライン時にキャッシュから表示される

**AC-P2-002: APIレスポンスキャッシュ**
- [ ] 検索結果がNetwork Firstでキャッシュされる
- [ ] SOP詳細が24時間キャッシュされる
- [ ] オフライン時にキャッシュから表示される
- [ ] オフライン状態が明確に表示される

### 5.3 Phase 3: UI最適化（Week 3）

**AC-P3-001: レスポンシブデザイン**
- [ ] 320px〜2560pxで表示崩れなし
- [ ] タッチ操作の最適化（44x44pxターゲット）
- [ ] ハンバーガーメニューの実装

**AC-P3-002: パフォーマンス最適化**
- [ ] Lighthouse PWA Score 90+
- [ ] FCP <1.5s, LCP <2.5s, TTI <3.5s
- [ ] Total JavaScript <500KB（gzip）

---

## 6. リスク分析と緩和策

### 6.1 技術的リスク

| リスク | 影響 | 確率 | 緩和策 |
|--------|------|------|--------|
| Safari PWA制限による機能不全 | Medium | High | 段階的拡張戦略（Push通知はオプション） |
| Cache Storage容量超過 | High | Medium | LRU削除 + 最大50MBキャップ |
| Service Worker更新失敗 | High | Low | 強制更新機能 + skipWaiting() |
| トークン暗号化の性能劣化 | Low | Medium | Web Crypto API + IndexedDB最適化 |
| 既存JSファイルの肥大化 | Medium | High | Code splitting + lazy loading |

### 6.2 運用リスク

| リスク | 影響 | 確率 | 緩和策 |
|--------|------|------|--------|
| ユーザーの混乱（オフライン動作） | Medium | Medium | 明確なオフライン表示 + ヘルプガイド |
| バックグラウンド同期の失敗通知 | Low | Low | リトライ + 管理画面での確認機能 |
| HTTPS証明書の期限切れ | High | Low | 90日前アラート + 自動更新検討 |

---

## 7. スコープ外（Phase D-5）

以下はPhase D-5では実装せず、将来のフェーズで検討:
- Push Notifications（Safari制限のためPhase D-5.1で検討）
- WebRTCによるP2Pデータ同期
- WebAssemblyによるPDFレンダリング高速化
- Geolocationによる現場自動判別
- Camera APIによる写真アップロード最適化

---

## 8. 用語集

| 用語 | 定義 |
|------|------|
| Service Worker | ブラウザがバックグラウンドで実行するスクリプト。ネットワークリクエストのプロキシとして機能 |
| Cache First | キャッシュを優先し、ない場合のみネットワークから取得する戦略 |
| Network First | ネットワークを優先し、失敗時のみキャッシュから取得する戦略 |
| Stale-While-Revalidate | キャッシュを返しつつ、バックグラウンドで更新する戦略 |
| Background Sync | オフライン時の操作をキューイングし、接続回復時に自動実行する仕組み |
| IndexedDB | ブラウザ内の大容量構造化データストレージ |
| skipWaiting() | 新しいService Workerを即座にアクティブ化する命令 |
| Lighthouse | Google提供のWebパフォーマンス監査ツール |

---

## 9. 承認

| 役割 | 氏名 | 承認日 | 署名 |
|------|------|--------|------|
| spec-planner | Claude Sonnet 4.5 | 2026-01-31 | ✅ |
| arch-reviewer | （承認待ち） | - | ⏳ |
| プロジェクトマネージャー | （承認待ち） | - | ⏳ |

---

**次のステップ**: arch-reviewerによる設計レビュー → 承認後、code-implementerによる実装開始
