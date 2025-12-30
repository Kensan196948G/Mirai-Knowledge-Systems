// ============================================================
// セキュアなDOM操作ヘルパー関数
// XSS脆弱性を防ぐため、innerHTML を使用せずDOM APIを使用
// ============================================================

/**
 * HTMLエスケープ関数
 * @param {string} text - エスケープするテキスト
 * @returns {string} エスケープされたテキスト
 */
function escapeHtml(text) {
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
 * @param {string} options.className - クラス名
 * @param {string} options.textContent - テキストコンテンツ
 * @param {Object} options.attributes - 属性オブジェクト
 * @param {Array<HTMLElement>} options.children - 子要素の配列
 * @returns {HTMLElement}
 */
function createSecureElement(tag, options = {}) {
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
function setSecureChildren(parent, children) {
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

/**
 * タグ要素を安全に作成
 * @param {string} tagText - タグテキスト
 * @returns {HTMLElement}
 */
function createTagElement(tagText) {
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
function createPillElement(pillText) {
  return createSecureElement('div', {
    className: 'pill',
    textContent: pillText
  });
}

/**
 * ステータスドット付き要素を安全に作成
 * @param {string} text - テキスト
 * @param {string} statusClass - ステータスクラス (active, is-ok, is-warn, is-hold)
 * @returns {HTMLElement}
 */
function createStatusElement(text, statusClass = 'active') {
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
 * @param {Object} options - オプション
 * @returns {HTMLElement}
 */
function createLinkElement(href, text, options = {}) {
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
 * @param {boolean} isHeader - ヘッダー行かどうか
 * @returns {HTMLElement}
 */
function createTableRow(cells, isHeader = false) {
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
 * ドキュメントアイテム要素を安全に作成
 * @param {Object} item - アイテムデータ
 * @param {string} detailPageUrl - 詳細ページURL
 * @returns {HTMLElement}
 */
function createDocumentElement(item, detailPageUrl) {
  const doc = createSecureElement('div', {
    className: 'document',
    attributes: {
      style: 'cursor: pointer;'
    }
  });

  doc.addEventListener('click', () => {
    window.location.href = detailPageUrl;
  });

  const titleLink = createLinkElement(detailPageUrl, item.title || '', {
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
 * @returns {HTMLElement}
 */
function createCommentElement(comment) {
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
    textContent: formatDate(comment.created_at)
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
      textContent: `👍 ${comment.likes}`,
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
 * 空のメッセージ要素を作成
 * @param {string} message - メッセージ
 * @returns {HTMLElement}
 */
function createEmptyMessage(message) {
  return createSecureElement('p', {
    textContent: message
  });
}

/**
 * エラーメッセージ要素を作成
 * @param {string} message - エラーメッセージ
 * @returns {HTMLElement}
 */
function createErrorMessage(message) {
  return createSecureElement('p', {
    textContent: message,
    style: {
      color: 'var(--danger)',
      padding: '10px'
    }
  });
}
