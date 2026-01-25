/**
 * Unit Tests for detail-pages.js - Utility Functions
 * 詳細ページユーティリティ関数のテスト
 */

const fs = require('fs');
const path = require('path');

// detail-pages.jsの最初の200行（ユーティリティ部分）を読み込み
const detailPagesCode = fs.readFileSync(
  path.join(__dirname, '../../../webui/detail-pages.js'),
  'utf8'
);

// 必要な部分のみを抽出
const utilsCode = detailPagesCode.split('\n').slice(0, 200).join('\n');

// API_BASEをモック
global.API_BASE = 'http://localhost:8000/api';

eval(utilsCode);

describe('Detail Pages - Loading Indicator', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="loadingIndicator" style="display: none;">Loading...</div>
    `;
  });

  describe('showLoading', () => {
    test('should display loading indicator', () => {
      showLoading();
      const loading = document.getElementById('loadingIndicator');
      expect(loading.style.display).toBe('flex');
    });

    test('should handle missing loading indicator gracefully', () => {
      document.body.innerHTML = '';
      expect(() => showLoading()).not.toThrow();
    });
  });

  describe('hideLoading', () => {
    test('should hide loading indicator', () => {
      const loading = document.getElementById('loadingIndicator');
      loading.style.display = 'flex';

      hideLoading();
      expect(loading.style.display).toBe('none');
    });

    test('should handle missing loading indicator gracefully', () => {
      document.body.innerHTML = '';
      expect(() => hideLoading()).not.toThrow();
    });
  });
});

describe('Detail Pages - Error Display', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="loadingIndicator" style="display: flex;">Loading...</div>
      <div id="errorMessage" style="display: none;">
        <span id="errorText"></span>
      </div>
    `;
  });

  describe('showError', () => {
    test('should display error message', () => {
      showError('Test error message');

      const errorEl = document.getElementById('errorMessage');
      const errorText = document.getElementById('errorText');

      expect(errorEl.style.display).toBe('block');
      expect(errorText.textContent).toBe('Test error message');
    });

    test('should hide loading indicator when showing error', () => {
      showError('Error occurred');

      const loading = document.getElementById('loadingIndicator');
      expect(loading.style.display).toBe('none');
    });

    test('should handle missing error elements gracefully', () => {
      document.body.innerHTML = '';
      expect(() => showError('Test')).not.toThrow();
    });

    test('should prevent XSS in error messages', () => {
      showError('<script>alert("XSS")</script>');

      const errorText = document.getElementById('errorText');
      expect(errorText.innerHTML).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
    });
  });

  describe('hideError', () => {
    test('should hide error message', () => {
      const errorEl = document.getElementById('errorMessage');
      errorEl.style.display = 'block';

      hideError();
      expect(errorEl.style.display).toBe('none');
    });

    test('should handle missing error element gracefully', () => {
      document.body.innerHTML = '';
      expect(() => hideError()).not.toThrow();
    });
  });
});

describe('Detail Pages - Date Formatting', () => {
  describe('formatDate', () => {
    test('should format date with time correctly', () => {
      const dateStr = '2024-01-15T10:30:00Z';
      const result = formatDate(dateStr);

      // 日本時間でフォーマットされる
      expect(result).toMatch(/2024\/01\/15/);
      expect(result).toMatch(/\d{2}:\d{2}/);
    });

    test('should return "N/A" for null', () => {
      expect(formatDate(null)).toBe('N/A');
    });

    test('should return "N/A" for undefined', () => {
      expect(formatDate(undefined)).toBe('N/A');
    });

    test('should return "N/A" for empty string', () => {
      expect(formatDate('')).toBe('N/A');
    });

    test('should handle different date formats', () => {
      const isoDate = '2024-03-20T15:45:30.000Z';
      const result = formatDate(isoDate);
      expect(result).toMatch(/2024\/03\/20/);
    });
  });

  describe('formatDateShort', () => {
    test('should format date without time', () => {
      const dateStr = '2024-01-15T10:30:00Z';
      const result = formatDateShort(dateStr);

      expect(result).toMatch(/2024\/01\/15/);
      expect(result).not.toMatch(/\d{2}:\d{2}/);
    });

    test('should return "N/A" for null', () => {
      expect(formatDateShort(null)).toBe('N/A');
    });

    test('should return "N/A" for undefined', () => {
      expect(formatDateShort(undefined)).toBe('N/A');
    });

    test('should return "N/A" for empty string', () => {
      expect(formatDateShort('')).toBe('N/A');
    });
  });
});

describe('Detail Pages - Scroll Utilities', () => {
  describe('scrollToTop', () => {
    test('should call window.scrollTo with correct parameters', () => {
      const scrollToSpy = jest.spyOn(window, 'scrollTo').mockImplementation();

      scrollToTop();

      expect(scrollToSpy).toHaveBeenCalledWith({
        top: 0,
        behavior: 'smooth'
      });

      scrollToSpy.mockRestore();
    });
  });
});

describe('Detail Pages - API Call', () => {
  beforeEach(() => {
    fetch.resetMocks();
    localStorage.clear();
    jest.spyOn(console, 'error').mockImplementation();
  });

  afterEach(() => {
    console.error.mockRestore();
  });

  test('should make successful API call', async () => {
    const mockData = { id: 1, title: 'Test' };
    fetch.mockResponseOnce(JSON.stringify(mockData));

    const result = await apiCall('/test-endpoint');

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/test-endpoint',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    );
    expect(result).toEqual(mockData);
  });

  test('should include authorization header when token exists', async () => {
    localStorage.setItem('access_token', 'test-token-123');
    fetch.mockResponseOnce(JSON.stringify({}));

    await apiCall('/protected');

    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token-123'
        })
      })
    );
  });

  test('should handle 401 unauthorized error', async () => {
    document.body.innerHTML = `
      <div id="loadingIndicator"></div>
      <div id="errorMessage"><span id="errorText"></span></div>
    `;

    fetch.mockResponseOnce('', { status: 401 });

    jest.useFakeTimers();
    const result = await apiCall('/protected');

    expect(result).toBeNull();
    expect(console.error).toHaveBeenCalledWith(
      expect.stringContaining('Unauthorized')
    );

    // 2秒後にリダイレクト
    jest.advanceTimersByTime(2000);
    expect(window.location.href).toBe('/login.html');

    jest.useRealTimers();
  });

  test('should handle POST request with body', async () => {
    fetch.mockResponseOnce(JSON.stringify({ success: true }));

    const postData = { name: 'Test', value: 123 };
    await apiCall('/create', {
      method: 'POST',
      body: JSON.stringify(postData)
    });

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/create',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(postData),
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    );
  });

  test('should handle network errors', async () => {
    fetch.mockReject(new Error('Network error'));

    const result = await apiCall('/test');

    expect(result).toBeNull();
  });

  test('should handle non-JSON error responses', async () => {
    fetch.mockResponseOnce('Plain text error', { status: 500 });

    const result = await apiCall('/error');

    expect(result).toBeNull();
  });

  test('should merge custom headers', async () => {
    fetch.mockResponseOnce(JSON.stringify({}));

    await apiCall('/test', {
      headers: {
        'X-Custom-Header': 'custom-value'
      }
    });

    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'X-Custom-Header': 'custom-value'
        })
      })
    );
  });
});
