/**
 * @fileoverview セキュアなDOM操作ヘルパー関数 ESMモジュール版
 *
 * XSS脆弱性を防ぐため、innerHTML を使用せずDOM APIを使用。
 * webui/dom-helpers.js のESモジュール変換版。
 *
 * @module utils/dom-helpers
 * @version 2.0.0
 * @author Mirai Knowledge Systems
 */

import { logger } from '../core/logger.js';

// ============================================================
// Core - 基本DOM操作
// ============================================================

/**
 * HTMLエスケープ関数
 * @param {string} text - エスケープするテキスト
 * @returns {string} エスケープされたテキスト
 */
export function escapeHtml(text) {
  if (text == null) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

/**
 * 安全に要素を作成
 * @param {string} tag - HTMLタグ名
 * @param {Object} options - オプション
 * @param {string} [options.className] - クラス名
 * @param {string} [options.textContent] - テキストコンテンツ
 * @param {Object} [options.attributes] - 属性オブジェクト
 * @param {Object} [options.style] - スタイルオブジェクト
 * @param {Array<HTMLElement>} [options.children] - 子要素の配列
 * @returns {HTMLElement}
 */
export function createSecureElement(tag, options = {}) {
  const element = document.createElement(tag);

  if (options.className) {
    element.className = options.className;
  }

  if (options.textContent != null) {
    element.textContent = options.textContent;
  }

  if (options.attributes) {
    for (const [key, value] of Object.entries(options.attributes)) {
      element.setAttribute(key, value);
    }
  }

  if (options.style) {
    for (const [key, value] of Object.entries(options.style)) {
      element.style[key] = value;
    }
  }

  if (options.children) {
    for (const child of options.children) {
      if (child instanceof HTMLElement) {
        element.appendChild(child);
      }
    }
  }

  return element;
}

/**
 * 既存要素の内容を安全にクリアして新しい子要素を追加
 * @param {HTMLElement} parent - 親要素
 * @param {Array<HTMLElement>|HTMLElement} children - 子要素
 */
export function setSecureChildren(parent, children) {
  if (!parent) return;

  // 既存の子要素をクリア
  while (parent.firstChild) {
    parent.removeChild(parent.firstChild);
  }

  // 新しい子要素を追加
  if (Array.isArray(children)) {
    for (const child of children) {
      if (child instanceof HTMLElement) {
        parent.appendChild(child);
      }
    }
  } else if (children instanceof HTMLElement) {
    parent.appendChild(children);
  }
}

// ============================================================
// UI Components - UIコンポーネント作成
// ============================================================

/**
 * タグ要素を安全に作成
 * @param {string} tagText - タグテキスト
 * @returns {HTMLElement}
 */
export function createTagElement(tagText) {
  return createSecureElement('span', {
    className: 'tag',
    textContent: tagText
  });
}

/**
 * ピル要素を安全に作成
 * @param {string} pillText - ピルテキスト
 * @returns {HTMLElement}
 */
export function createPillElement(pillText) {
  return createSecureElement('div', {
    className: 'pill',
    textContent: pillText
  });
}

/**
 * ステータスドット付き要素を安全に作成
 * @param {string} text - テキスト
 * @param {string} [statusClass='active'] - ステータスクラス (active, is-ok, is-warn, is-hold)
 * @returns {HTMLElement}
 */
export function createStatusElement(text, statusClass = 'active') {
  const container = createSecureElement('div', {
    className: 'status-item'
  });

  const dot = createSecureElement('span', {
    className: `status-dot ${statusClass}`
  });

  const textSpan = createSecureElement('span', {
    textContent: text
  });

  container.appendChild(dot);
  container.appendChild(textSpan);

  return container;
}

/**
 * リンク要素を安全に作成
 * @param {string} href - リンク先URL
 * @param {string} text - リンクテキスト
 * @param {Object} [options] - オプション
 * @param {Object} [options.attributes] - 追加属性
 * @param {string} [options.className] - クラス名
 * @returns {HTMLElement}
 */
export function createLinkElement(href, text, options = {}) {
  return createSecureElement('a', {
    textContent: text,
    attributes: {
      href: href,
      ...options.attributes
    },
    className: options.className
  });
}

/**
 * テーブル行を安全に作成
 * @param {Array<string>} cells - セルの内容配列
 * @param {boolean} [isHeader=false] - ヘッダー行かどうか
 * @returns {HTMLElement}
 */
export function createTableRow(cells, isHeader = false) {
  const row = document.createElement('tr');
  const cellTag = isHeader ? 'th' : 'td';

  for (const cellContent of cells) {
    const cell = document.createElement(cellTag);
    cell.textContent = cellContent;
    row.appendChild(cell);
  }

  return row;
}

/**
 * HTML要素を含むテーブル行を安全に作成
 * @param {Array<string|HTMLElement>} cells - セルの内容配列（文字列またはHTML要素）
 * @param {boolean} [isHeader=false] - ヘッダー行かどうか
 * @returns {HTMLElement}
 */
export function createTableRowWithHTML(cells, isHeader = false) {
  const row = document.createElement('tr');
  const cellTag = isHeader ? 'th' : 'td';

  for (const cellContent of cells) {
    const cell = document.createElement(cellTag);

    if (typeof cellContent === 'string') {
      cell.textContent = cellContent;
    } else if (cellContent instanceof HTMLElement) {
      cell.appendChild(cellContent);
    }

    row.appendChild(cell);
  }

  return row;
}

/**
 * ドキュメントアイテム要素を安全に作成
 * @param {Object} item - アイテムデータ
 * @param {string} [item.id] - アイテムID
 * @param {string} [item.title] - タイトル
 * @param {string} [item.subtitle] - サブタイトル
 * @param {string} [item.description] - 説明
 * @param {string} detailPageUrl - 詳細ページURL
 * @returns {HTMLElement}
 */
export function createDocumentElement(item, detailPageUrl) {
  // IDパラメータを含む完全なURLを生成
  const fullUrl = item.id && !detailPageUrl.includes('?')
    ? `${detailPageUrl}?id=${item.id}`
    : detailPageUrl;

  const doc = createSecureElement('div', {
    className: 'document',
    attributes: {
      style: 'cursor: pointer;'
    }
  });

  doc.addEventListener('click', () => {
    window.location.href = fullUrl;
  });

  const titleLink = createLinkElement(fullUrl, item.title || '', {
    className: 'document-title'
  });
  const titleStrong = createSecureElement('strong');
  titleStrong.appendChild(titleLink);

  const smallText = createSecureElement('small', {
    textContent: item.subtitle || ''
  });

  const descDiv = createSecureElement('div', {
    textContent: item.description || ''
  });

  doc.appendChild(titleStrong);
  doc.appendChild(smallText);
  doc.appendChild(descDiv);

  return doc;
}

/**
 * コメント要素を安全に作成
 * @param {Object} comment - コメントデータ
 * @param {string} [comment.user] - ユーザー名
 * @param {string} [comment.author_name] - 著者名
 * @param {string} [comment.created_at] - 作成日時
 * @param {string} [comment.content] - コンテンツ
 * @param {number} [comment.likes] - いいね数
 * @returns {HTMLElement}
 */
export function createCommentElement(comment) {
  const commentDiv = createSecureElement('div', {
    className: 'comment-item',
    style: {
      padding: '15px',
      borderBottom: '1px solid #eee'
    }
  });

  const headerDiv = createSecureElement('div', {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '10px'
    }
  });

  const authorStrong = createSecureElement('strong', {
    textContent: comment.user || comment.author_name || 'Unknown'
  });

  const dateSmall = createSecureElement('small', {
    textContent: formatDateInternal(comment.created_at)
  });

  headerDiv.appendChild(authorStrong);
  headerDiv.appendChild(dateSmall);

  const contentDiv = createSecureElement('div', {
    textContent: comment.content
  });

  commentDiv.appendChild(headerDiv);
  commentDiv.appendChild(contentDiv);

  if (comment.likes) {
    const likesDiv = createSecureElement('div', {
      textContent: `\uD83D\uDC4D ${comment.likes}`,
      style: {
        marginTop: '8px',
        fontSize: '12px',
        color: '#888'
      }
    });
    commentDiv.appendChild(likesDiv);
  }

  return commentDiv;
}

/**
 * 回答要素を安全に作成
 * @param {Object} answer - 回答データ
 * @param {string} [answer.expert_name] - エキスパート名
 * @param {string} [answer.user] - ユーザー名
 * @param {string} [answer.answered_at] - 回答日時
 * @param {string} [answer.created_at] - 作成日時
 * @param {string} [answer.content] - コンテンツ
 * @param {string} [answer.answer] - 回答内容
 * @param {number} [answer.likes] - いいね数
 * @param {number} [answer.helpful_count] - 参考になった数
 * @param {boolean} [isBestAnswer=false] - ベストアンサーかどうか
 * @returns {HTMLElement}
 */
export function createAnswerElement(answer, isBestAnswer = false) {
  const answerDiv = createSecureElement('div', {
    className: 'answer-item',
    style: {
      padding: '20px',
      marginBottom: '15px',
      backgroundColor: isBestAnswer ? '#f0f9ff' : '#fff',
      border: isBestAnswer ? '2px solid #0ea5e9' : '1px solid #e5e7eb',
      borderRadius: '8px'
    }
  });

  // ヘッダー
  const headerDiv = createSecureElement('div', {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '12px'
    }
  });

  const authorDiv = createSecureElement('div');
  const expertBadge = createSecureElement('span', {
    textContent: '専門家',
    style: {
      backgroundColor: '#0ea5e9',
      color: 'white',
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      marginRight: '8px'
    }
  });
  const expertName = createSecureElement('strong', {
    textContent: answer.expert_name || answer.user || 'Unknown'
  });

  authorDiv.appendChild(expertBadge);
  authorDiv.appendChild(expertName);

  const dateSmall = createSecureElement('small', {
    textContent: formatDateInternal(answer.answered_at || answer.created_at),
    style: { color: '#6b7280' }
  });

  headerDiv.appendChild(authorDiv);
  headerDiv.appendChild(dateSmall);

  // コンテンツ
  const contentDiv = createSecureElement('div', {
    textContent: answer.content || answer.answer,
    style: {
      lineHeight: '1.6',
      marginBottom: '12px'
    }
  });

  // フッター（いいね、ベストアンサーバッジ）
  const footerDiv = createSecureElement('div', {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: '12px'
    }
  });

  if (answer.likes || answer.helpful_count) {
    const likesSpan = createSecureElement('span', {
      textContent: `\uD83D\uDC4D 参考になった: ${answer.likes || answer.helpful_count}`,
      style: { fontSize: '13px', color: '#6b7280' }
    });
    footerDiv.appendChild(likesSpan);
  }

  if (isBestAnswer) {
    const bestBadge = createSecureElement('span', {
      textContent: '\u2713 ベストアンサー',
      style: {
        backgroundColor: '#10b981',
        color: 'white',
        padding: '4px 12px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 'bold'
      }
    });
    footerDiv.appendChild(bestBadge);
  }

  answerDiv.appendChild(headerDiv);
  answerDiv.appendChild(contentDiv);
  if (footerDiv.children.length > 0) {
    answerDiv.appendChild(footerDiv);
  }

  return answerDiv;
}

/**
 * ベストアンサー表示要素を安全に作成
 * @param {Object} answer - ベストアンサーデータ
 * @returns {HTMLElement}
 */
export function createBestAnswerElement(answer) {
  return createAnswerElement(answer, true);
}

/**
 * エキスパート情報要素を安全に作成
 * @param {Object} expert - エキスパートデータ
 * @param {string} [expert.name] - 氏名
 * @param {string} [expert.specialty] - 専門分野
 * @param {string} [expert.organization] - 所属
 * @param {string} [expert.certification] - 資格
 * @returns {HTMLElement}
 */
export function createExpertInfoElement(expert) {
  const container = createSecureElement('div', {
    className: 'expert-info-card',
    style: {
      backgroundColor: '#f8fafc',
      padding: '20px',
      borderRadius: '8px',
      border: '1px solid #e2e8f0'
    }
  });

  const header = createSecureElement('h4', {
    textContent: '担当専門家',
    style: {
      marginTop: '0',
      marginBottom: '15px',
      color: '#1e293b',
      fontSize: '16px'
    }
  });

  const nameDiv = createSecureElement('div', {
    style: { marginBottom: '8px' }
  });
  const nameLabel = createSecureElement('strong', {
    textContent: '氏名: '
  });
  const nameValue = createSecureElement('span', {
    textContent: expert.name || 'Unknown'
  });
  nameDiv.appendChild(nameLabel);
  nameDiv.appendChild(nameValue);

  const specialtyDiv = createSecureElement('div', {
    style: { marginBottom: '8px' }
  });
  const specialtyLabel = createSecureElement('strong', {
    textContent: '専門分野: '
  });
  const specialtyValue = createSecureElement('span', {
    textContent: expert.specialty || '-'
  });
  specialtyDiv.appendChild(specialtyLabel);
  specialtyDiv.appendChild(specialtyValue);

  const orgDiv = createSecureElement('div', {
    style: { marginBottom: '8px' }
  });
  const orgLabel = createSecureElement('strong', {
    textContent: '所属: '
  });
  const orgValue = createSecureElement('span', {
    textContent: expert.organization || '-'
  });
  orgDiv.appendChild(orgLabel);
  orgDiv.appendChild(orgValue);

  if (expert.certification) {
    const certDiv = createSecureElement('div', {
      style: { marginBottom: '8px' }
    });
    const certLabel = createSecureElement('strong', {
      textContent: '資格: '
    });
    const certValue = createSecureElement('span', {
      textContent: expert.certification
    });
    certDiv.appendChild(certLabel);
    certDiv.appendChild(certValue);
    container.appendChild(header);
    container.appendChild(nameDiv);
    container.appendChild(specialtyDiv);
    container.appendChild(orgDiv);
    container.appendChild(certDiv);
  } else {
    container.appendChild(header);
    container.appendChild(nameDiv);
    container.appendChild(specialtyDiv);
    container.appendChild(orgDiv);
  }

  return container;
}

/**
 * 手順ステップ要素を安全に作成
 * @param {string|Object} step - ステップデータ（文字列またはオブジェクト）
 * @param {number} index - ステップ番号（0始まり）
 * @returns {HTMLElement}
 */
export function createStepElement(step, index) {
  const stepDiv = createSecureElement('div', {
    className: 'step-item',
    style: {
      display: 'flex',
      marginBottom: '15px',
      padding: '15px',
      backgroundColor: '#f9fafb',
      borderRadius: '6px'
    }
  });

  const stepNumber = createSecureElement('div', {
    textContent: `${index + 1}`,
    style: {
      minWidth: '32px',
      height: '32px',
      backgroundColor: '#3b82f6',
      color: 'white',
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 'bold',
      marginRight: '12px',
      flexShrink: '0'
    }
  });

  const stepContent = createSecureElement('div', {
    textContent: typeof step === 'string' ? step : (step.description || step.step || ''),
    style: {
      flex: '1',
      lineHeight: '1.6'
    }
  });

  stepDiv.appendChild(stepNumber);
  stepDiv.appendChild(stepContent);

  return stepDiv;
}

/**
 * チェックリストアイテム要素を安全に作成
 * @param {string|Object} item - チェックリストアイテム
 * @returns {HTMLElement}
 */
export function createChecklistElement(item) {
  const itemDiv = createSecureElement('div', {
    className: 'checklist-item',
    style: {
      display: 'flex',
      alignItems: 'start',
      padding: '10px',
      marginBottom: '8px',
      backgroundColor: '#fff',
      border: '1px solid #e5e7eb',
      borderRadius: '4px'
    }
  });

  const checkbox = createSecureElement('span', {
    textContent: '\u2610',
    style: {
      fontSize: '18px',
      marginRight: '10px',
      color: '#6b7280'
    }
  });

  const itemText = createSecureElement('span', {
    textContent: typeof item === 'string' ? item : (item.item || item.description || ''),
    style: {
      flex: '1',
      lineHeight: '1.5'
    }
  });

  itemDiv.appendChild(checkbox);
  itemDiv.appendChild(itemText);

  return itemDiv;
}

/**
 * 注意事項要素を安全に作成
 * @param {string|Object} warning - 注意事項データ
 * @returns {HTMLElement}
 */
export function createWarningElement(warning) {
  const warningDiv = createSecureElement('div', {
    className: 'warning-item',
    style: {
      display: 'flex',
      alignItems: 'start',
      padding: '12px',
      marginBottom: '10px',
      backgroundColor: '#fef3c7',
      border: '1px solid #fbbf24',
      borderRadius: '6px'
    }
  });

  const warningIcon = createSecureElement('span', {
    textContent: '\u26A0\uFE0F',
    style: {
      fontSize: '20px',
      marginRight: '10px',
      flexShrink: '0'
    }
  });

  const warningText = createSecureElement('span', {
    textContent: typeof warning === 'string' ? warning : (warning.warning || warning.message || ''),
    style: {
      flex: '1',
      lineHeight: '1.6',
      color: '#92400e'
    }
  });

  warningDiv.appendChild(warningIcon);
  warningDiv.appendChild(warningText);

  return warningDiv;
}

/**
 * タイムラインイベント要素を安全に作成
 * @param {Object} event - イベントデータ
 * @param {string} [event.time] - 時刻文字列
 * @param {string} [event.timestamp] - タイムスタンプ
 * @param {string} [event.description] - 説明
 * @param {string} [event.event] - イベント名
 * @returns {HTMLElement}
 */
export function createTimelineElement(event) {
  const eventDiv = createSecureElement('div', {
    className: 'timeline-item',
    style: {
      display: 'flex',
      marginBottom: '20px',
      position: 'relative',
      paddingLeft: '30px'
    }
  });

  const timelineDot = createSecureElement('div', {
    style: {
      position: 'absolute',
      left: '0',
      top: '4px',
      width: '12px',
      height: '12px',
      backgroundColor: '#3b82f6',
      borderRadius: '50%',
      border: '2px solid #fff',
      boxShadow: '0 0 0 2px #3b82f6'
    }
  });

  const contentDiv = createSecureElement('div', {
    style: { flex: '1' }
  });

  const timeDiv = createSecureElement('div', {
    textContent: event.time || formatDateInternal(event.timestamp),
    style: {
      fontSize: '13px',
      color: '#6b7280',
      marginBottom: '4px',
      fontWeight: '600'
    }
  });

  const descDiv = createSecureElement('div', {
    textContent: event.description || event.event || '',
    style: {
      lineHeight: '1.5',
      color: '#1f2937'
    }
  });

  contentDiv.appendChild(timeDiv);
  contentDiv.appendChild(descDiv);
  eventDiv.appendChild(timelineDot);
  eventDiv.appendChild(contentDiv);

  return eventDiv;
}

/**
 * 添付ファイル要素を安全に作成
 * @param {Object} file - ファイルデータ
 * @param {string} [file.filename] - ファイル名
 * @param {string} [file.name] - ファイル名（代替）
 * @param {string} [file.size] - ファイルサイズ
 * @param {string} [file.url] - ファイルURL
 * @returns {HTMLElement}
 */
export function createAttachmentElement(file) {
  const fileDiv = createSecureElement('div', {
    className: 'attachment-item',
    style: {
      display: 'flex',
      alignItems: 'center',
      padding: '12px',
      marginBottom: '8px',
      backgroundColor: '#f9fafb',
      border: '1px solid #e5e7eb',
      borderRadius: '6px',
      cursor: 'pointer',
      transition: 'background-color 0.2s'
    }
  });

  fileDiv.addEventListener('mouseenter', () => {
    fileDiv.style.backgroundColor = '#f3f4f6';
  });

  fileDiv.addEventListener('mouseleave', () => {
    fileDiv.style.backgroundColor = '#f9fafb';
  });

  const fileIcon = createSecureElement('span', {
    textContent: '\uD83D\uDCCE',
    style: {
      fontSize: '20px',
      marginRight: '10px'
    }
  });

  const fileInfo = createSecureElement('div', {
    style: { flex: '1' }
  });

  const fileName = createSecureElement('div', {
    textContent: file.filename || file.name || 'ファイル',
    style: {
      fontWeight: '500',
      color: '#1f2937',
      marginBottom: '4px'
    }
  });

  const fileSize = createSecureElement('div', {
    textContent: file.size || '',
    style: {
      fontSize: '12px',
      color: '#6b7280'
    }
  });

  fileInfo.appendChild(fileName);
  if (file.size) {
    fileInfo.appendChild(fileSize);
  }

  if (file.url) {
    fileDiv.addEventListener('click', () => {
      window.open(file.url, '_blank');
    });
  }

  fileDiv.appendChild(fileIcon);
  fileDiv.appendChild(fileInfo);

  return fileDiv;
}

/**
 * ステータス履歴要素を安全に作成
 * @param {Object} item - 履歴アイテム
 * @param {string} [item.status] - ステータス
 * @param {string} [item.updated_by] - 更新者
 * @param {string} [item.user] - ユーザー名
 * @param {string} [item.updated_at] - 更新日時
 * @param {string} [item.date] - 日付
 * @returns {HTMLElement}
 */
export function createStatusHistoryElement(item) {
  const historyDiv = createSecureElement('div', {
    className: 'status-history-item',
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '12px',
      marginBottom: '8px',
      backgroundColor: '#f9fafb',
      borderRadius: '6px'
    }
  });

  const leftDiv = createSecureElement('div');

  const statusSpan = createSecureElement('span', {
    textContent: item.status || '',
    style: {
      fontWeight: '600',
      color: '#1f2937',
      marginRight: '8px'
    }
  });

  const userSpan = createSecureElement('span', {
    textContent: `（${item.updated_by || item.user || ''}）`,
    style: {
      fontSize: '13px',
      color: '#6b7280'
    }
  });

  leftDiv.appendChild(statusSpan);
  leftDiv.appendChild(userSpan);

  const dateSpan = createSecureElement('span', {
    textContent: formatDateInternal(item.updated_at || item.date),
    style: {
      fontSize: '13px',
      color: '#6b7280'
    }
  });

  historyDiv.appendChild(leftDiv);
  historyDiv.appendChild(dateSpan);

  return historyDiv;
}

/**
 * 承認フロー要素を安全に作成
 * @param {Object} flowItem - 承認フローアイテム
 * @param {string|number} [flowItem.step] - ステップ番号
 * @param {string} [flowItem.status] - ステータス
 * @param {string} [flowItem.role] - 役割
 * @param {string} [flowItem.approver] - 承認者
 * @returns {HTMLElement}
 */
export function createApprovalFlowElement(flowItem) {
  const flowDiv = createSecureElement('div', {
    className: 'approval-step',
    style: {
      display: 'flex',
      alignItems: 'center',
      padding: '15px',
      marginBottom: '10px',
      backgroundColor: '#fff',
      border: '1px solid #e5e7eb',
      borderRadius: '8px'
    }
  });

  const stepNumber = createSecureElement('div', {
    textContent: `${flowItem.step || ''}`,
    style: {
      minWidth: '40px',
      height: '40px',
      backgroundColor: flowItem.status === '承認済み' ? '#10b981' : '#e5e7eb',
      color: flowItem.status === '承認済み' ? 'white' : '#6b7280',
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 'bold',
      marginRight: '15px'
    }
  });

  const contentDiv = createSecureElement('div', {
    style: { flex: '1' }
  });

  const roleDiv = createSecureElement('div', {
    textContent: flowItem.role || '',
    style: {
      fontWeight: '600',
      marginBottom: '4px',
      color: '#1f2937'
    }
  });

  const approverDiv = createSecureElement('div', {
    textContent: flowItem.approver || '未設定',
    style: {
      fontSize: '14px',
      color: '#6b7280'
    }
  });

  contentDiv.appendChild(roleDiv);
  contentDiv.appendChild(approverDiv);

  const statusBadge = createSecureElement('span', {
    textContent: flowItem.status || '未承認',
    style: {
      padding: '4px 12px',
      borderRadius: '12px',
      fontSize: '12px',
      fontWeight: '600',
      backgroundColor: flowItem.status === '承認済み' ? '#d1fae5' : '#fef3c7',
      color: flowItem.status === '承認済み' ? '#065f46' : '#92400e'
    }
  });

  flowDiv.appendChild(stepNumber);
  flowDiv.appendChild(contentDiv);
  flowDiv.appendChild(statusBadge);

  return flowDiv;
}

/**
 * メタ情報要素を安全に作成（汎用）
 * @param {Object} data - データオブジェクト
 * @param {Array<{label: string, key: string, formatter?: Function}>} fields - フィールド定義配列
 * @returns {HTMLElement}
 */
export function createMetaInfoElement(data, fields) {
  const container = createSecureElement('div', {
    className: 'meta-info',
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '12px',
      padding: '15px',
      backgroundColor: '#f8fafc',
      borderRadius: '8px'
    }
  });

  for (const field of fields) {
    const fieldDiv = createSecureElement('div');

    const label = createSecureElement('div', {
      textContent: field.label,
      style: {
        fontSize: '12px',
        color: '#6b7280',
        marginBottom: '4px',
        fontWeight: '600'
      }
    });

    const value = field.formatter
      ? field.formatter(data[field.key])
      : (data[field.key] || '-');

    const valueDiv = createSecureElement('div', {
      textContent: value,
      style: {
        fontSize: '14px',
        color: '#1f2937',
        fontWeight: '500'
      }
    });

    fieldDiv.appendChild(label);
    fieldDiv.appendChild(valueDiv);
    container.appendChild(fieldDiv);
  }

  return container;
}

// ============================================================
// Messages - メッセージ表示
// ============================================================

/**
 * 空のメッセージ要素を作成
 * @param {string} message - メッセージ
 * @returns {HTMLElement}
 */
export function createEmptyMessage(message) {
  return createSecureElement('p', {
    textContent: message
  });
}

/**
 * エラーメッセージ要素を作成
 * @param {string} message - エラーメッセージ
 * @returns {HTMLElement}
 */
export function createErrorMessage(message) {
  return createSecureElement('p', {
    textContent: message,
    style: {
      color: 'var(--danger)',
      padding: '10px'
    }
  });
}

// ============================================================
// Utilities - ユーティリティ関数
// ============================================================

/**
 * 日付文字列をフォーマット（内部使用）
 * @private
 * @param {string} dateString - 日付文字列
 * @returns {string} フォーマット済み日付 or 'Invalid Date'
 */
function formatDateInternal(dateString) {
  if (!dateString) return 'Invalid Date';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Invalid Date';
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric', month: '2-digit', day: '2-digit'
  });
}

/**
 * テキストを指定文字数で切り詰める
 * @param {string} text - テキスト
 * @param {number} maxLength - 最大文字数
 * @returns {string} 切り詰めたテキスト
 */
export function truncateText(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + '...';
}

// ============================================================
// MKSApp.DOM Namespace - セキュアなDOM操作ヘルパー（ESM版）
// ============================================================

/**
 * MKSApp.DOM Namespace オブジェクト
 * 後方互換性のため window.MKSApp.DOM を維持
 */
const DOMHelpers = {
  // Core
  escapeHtml,
  createSecureElement,
  setSecureChildren,
  truncateText,

  // Components
  Components: {
    createTag: createTagElement,
    createPill: createPillElement,
    createStatus: createStatusElement,
    createLink: createLinkElement,
    createTableRow: createTableRow,
    createTableRowWithHTML: createTableRowWithHTML,
    createDocument: createDocumentElement,
    createComment: createCommentElement,
    createAnswer: createAnswerElement,
    createBestAnswer: createBestAnswerElement,
    createExpertInfo: createExpertInfoElement,
    createStep: createStepElement,
    createChecklist: createChecklistElement,
    createWarning: createWarningElement,
    createTimeline: createTimelineElement,
    createAttachment: createAttachmentElement,
    createStatusHistory: createStatusHistoryElement,
    createApprovalFlow: createApprovalFlowElement,
    createMetaInfo: createMetaInfoElement
  },

  // Messages
  Messages: {
    createEmpty: createEmptyMessage,
    createError: createErrorMessage
  }
};

// ============================================================
// 後方互換性レイヤー - window.* グローバルエイリアス維持
// ============================================================
if (typeof window !== 'undefined') {
  // MKSApp.DOM Namespace
  if (typeof window.MKSApp === 'undefined') {
    window.MKSApp = {};
  }
  window.MKSApp.DOM = DOMHelpers;

  // window.DOMHelpers - フラットアクセス
  window.DOMHelpers = DOMHelpers;

  // 既存コードが直接参照する個別グローバル関数
  window.escapeHtml = escapeHtml;
  window.createSecureElement = createSecureElement;
  window.setSecureChildren = setSecureChildren;
  window.truncateText = truncateText;
  window.createTagElement = createTagElement;
  window.createPillElement = createPillElement;
  window.createStatusElement = createStatusElement;
  window.createLinkElement = createLinkElement;
  window.createTableRow = createTableRow;
  window.createTableRowWithHTML = createTableRowWithHTML;
  window.createDocumentElement = createDocumentElement;
  window.createCommentElement = createCommentElement;
  window.createAnswerElement = createAnswerElement;
  window.createBestAnswerElement = createBestAnswerElement;
  window.createExpertInfoElement = createExpertInfoElement;
  window.createStepElement = createStepElement;
  window.createChecklistElement = createChecklistElement;
  window.createWarningElement = createWarningElement;
  window.createTimelineElement = createTimelineElement;
  window.createAttachmentElement = createAttachmentElement;
  window.createStatusHistoryElement = createStatusHistoryElement;
  window.createApprovalFlowElement = createApprovalFlowElement;
  window.createMetaInfoElement = createMetaInfoElement;
  window.createEmptyMessage = createEmptyMessage;
  window.createErrorMessage = createErrorMessage;

  logger.info('[DOMHelpers] ESM module loaded. MKSApp.DOM namespace initialized.');
}

export default DOMHelpers;
