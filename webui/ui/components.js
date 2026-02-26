/**
 * UI Components - Re-export Entry Point
 * Mirai Knowledge Systems - Phase E-1
 *
 * このファイルは components-basic.js と components-advanced.js の
 * 再エクスポートエントリーポイントです。
 *
 * Week 3でリファクタリング実施（BI-001対応）:
 * - 旧 components.js (498行) → 3分割
 * - dom-utils.js (150行)
 * - components-basic.js (277行)
 * - components-advanced.js (106行)
 *
 * 既存コードとの互換性維持のため、このファイルで全エクスポートを再公開。
 *
 * @version 1.5.0
 * @date 2026-02-16
 */

// 基本コンポーネント（Button, Card, Alert）
export { Button, Card, Alert } from './components-basic.js';

// 高度コンポーネント（List, Table）
export { List, Table } from './components-advanced.js';

// DOM操作ヘルパー
export { DOMHelper } from './dom-utils.js';

// デフォルトエクスポート（すべてを含むオブジェクト）
import { Button, Card, Alert } from './components-basic.js';
import { List, Table } from './components-advanced.js';
import { DOMHelper } from './dom-utils.js';

export default {
  DOMHelper,
  Button,
  Card,
  Alert,
  List,
  Table
};
