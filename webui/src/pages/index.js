/**
 * @fileoverview ページモジュール集約エクスポート v2.0.0
 * @module pages/index
 * @description Phase F-4: webui/src/pages/ 配下の全モジュールを集約してエクスポート
 *
 * 使用方法:
 *   import { loadKnowledgeDetail, loadSOPDetail } from './src/pages/index.js';
 *
 * または個別モジュールから直接インポート:
 *   import { loadKnowledgeDetail } from './src/pages/knowledge-detail.js';
 */

// 共通ページレンダリング
export * from './page-renderer.js';

// ナレッジ詳細 (search-detail.html)
export * from './knowledge-detail.js';

// SOP詳細 (sop-detail.html)
export * from './sop-detail.js';

// 事故レポート詳細 (incident-detail.html)
export * from './incident-detail.js';

// 専門家相談詳細 (expert-consult.html)
export * from './consultation-detail.js';

// 専門家詳細 (expert-detail.html) - スタブ
export * from './expert-detail.js';

// 法令詳細 (law-detail.html) - スタブ
export * from './law-detail.js';

// 承認詳細 (approval-detail.html) - スタブ
export * from './approval-detail.js';
