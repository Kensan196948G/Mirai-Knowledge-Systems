/**
 * Unit Tests for actions.js
 * 共通アクション関数のテスト
 */

const fs = require('fs');
const path = require('path');

// loggerモック（actions.jsが使用）
// logger.logはconsole.logに転送することでjest.spyOn(console, 'log')で検証可能にする
global.logger = {
  error: (...args) => console.error(...args),
  warn: (...args) => console.warn(...args),
  info: (...args) => console.info(...args),
  log: (...args) => console.log(...args)
};

// テスト対象のファイルを読み込み
const actionsCode = fs.readFileSync(
  path.join(__dirname, '../../../webui/actions.js'),
  'utf8'
);

eval(actionsCode);

describe('Actions - Toast Notifications', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('showToast', () => {
    test('should create toast container if not exists', () => {
      showToast('Test message', 'info');

      const container = document.querySelector('.toast-container');
      expect(container).not.toBeNull();
      expect(document.body.contains(container)).toBe(true);
    });

    test('should create toast with correct message', () => {
      showToast('Hello World', 'success');

      const toast = document.querySelector('.toast');
      const message = toast.querySelector('.toast-message');
      expect(message.textContent).toBe('Hello World');
    });

    test('should apply correct type class', () => {
      showToast('Error message', 'error');

      const toast = document.querySelector('.toast');
      expect(toast.classList.contains('toast-error')).toBe(true);
    });

    test('should show correct icon for each type', () => {
      const types = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
      };

      Object.entries(types).forEach(([type, icon]) => {
        document.body.innerHTML = '';
        showToast('Test', type);
        const iconDiv = document.querySelector('.toast-icon');
        expect(iconDiv.textContent).toBe(icon);
      });
    });

    test('should add show class after timeout', () => {
      showToast('Test', 'info');
      const toast = document.querySelector('.toast');

      expect(toast.classList.contains('show')).toBe(false);

      jest.advanceTimersByTime(10);

      expect(toast.classList.contains('show')).toBe(true);
    });

    test('should remove toast after 3 seconds', () => {
      showToast('Test', 'info');
      const container = document.querySelector('.toast-container');

      expect(container.children.length).toBe(1);

      // 3秒経過
      jest.advanceTimersByTime(3000);
      const toast = document.querySelector('.toast');
      expect(toast.classList.contains('show')).toBe(false);

      // さらに300ms経過（アニメーション完了）
      jest.advanceTimersByTime(300);
      expect(document.querySelector('.toast')).toBeNull();
    });

    test('should remove container when empty', () => {
      showToast('Test', 'info');

      // 3.3秒経過（トースト削除まで）
      jest.advanceTimersByTime(3300);

      expect(document.querySelector('.toast-container')).toBeNull();
    });

    test('should prevent XSS in toast message', () => {
      showToast('<script>alert("XSS")</script>', 'info');
      const message = document.querySelector('.toast-message');
      expect(message.innerHTML).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
    });

    test('should reuse existing container for multiple toasts', () => {
      showToast('First', 'info');
      showToast('Second', 'success');

      const containers = document.querySelectorAll('.toast-container');
      expect(containers.length).toBe(1);

      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBe(2);
    });
  });
});

describe('Actions - Distribution', () => {
  beforeEach(() => {
    jest.spyOn(console, 'log').mockImplementation();
    // submitDistribution はconfirmダイアログを使うためモック（trueを返す）
    global.confirm = jest.fn(() => true);
  });

  afterEach(() => {
    console.log.mockRestore();
    delete global.confirm;
  });

  describe('submitDistribution', () => {
    test('should show success toast', () => {
      document.body.innerHTML = '';
      submitDistribution('sop', { id: 123, title: 'Test SOP' });

      const toast = document.querySelector('.toast');
      expect(toast).not.toBeNull();
      expect(toast.querySelector('.toast-message').textContent).toBe('配信申請を送信しました');
      expect(toast.classList.contains('toast-success')).toBe(true);
    });

    test('should log distribution data', () => {
      submitDistribution('manual', { id: 456 });

      expect(console.log).toHaveBeenCalledWith(
        '[ACTION] Distribution submitted:',
        'manual',
        { id: 456 }
      );
    });
  });
});

describe('Actions - Revision Proposal', () => {
  beforeEach(() => {
    jest.spyOn(console, 'log').mockImplementation();
    global.prompt = jest.fn();
    global.alert = jest.fn();
  });

  afterEach(() => {
    console.log.mockRestore();
    global.prompt.mockRestore();
    global.alert.mockRestore();
  });

  describe('proposeRevision', () => {
    test('should prompt user for revision reason', () => {
      global.prompt.mockReturnValue('Outdated information');

      proposeRevision('sop');

      expect(global.prompt).toHaveBeenCalledWith(
        expect.stringContaining('改訂理由を入力してください')
      );
    });

    test('should alert confirmation when reason provided', () => {
      global.prompt.mockReturnValue('Need to update process');

      proposeRevision('manual');

      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('改訂提案を受け付けました')
      );
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('Need to update process')
      );
    });

    test('should log revision proposal', () => {
      global.prompt.mockReturnValue('Update required');

      proposeRevision('law');

      expect(console.log).toHaveBeenCalledWith(
        '[ACTION] Revision proposed:',
        'law',
        'Update required'
      );
    });

    test('should do nothing when user cancels', () => {
      global.prompt.mockReturnValue(null);

      proposeRevision('sop');

      expect(global.alert).not.toHaveBeenCalled();
      expect(console.log).not.toHaveBeenCalled();
    });

    test('should do nothing when empty reason provided', () => {
      global.prompt.mockReturnValue('');

      proposeRevision('sop');

      expect(global.alert).not.toHaveBeenCalled();
      expect(console.log).not.toHaveBeenCalled();
    });
  });
});

describe('Actions - Dashboard Sharing', () => {
  beforeEach(() => {
    jest.spyOn(console, 'log').mockImplementation();
    global.prompt = jest.fn();
    global.alert = jest.fn();
  });

  afterEach(() => {
    console.log.mockRestore();
    global.prompt.mockRestore();
    global.alert.mockRestore();
  });

  describe('shareDashboard', () => {
    test('should prompt for recipient emails', () => {
      global.prompt.mockReturnValue('user1@example.com, user2@example.com');

      shareDashboard();

      expect(global.prompt).toHaveBeenCalledWith(
        expect.stringContaining('共有先のメールアドレスを入力してください')
      );
    });

    test('should alert confirmation with recipients', () => {
      const recipients = 'admin@example.com';
      global.prompt.mockReturnValue(recipients);

      shareDashboard();

      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('ダッシュボードを共有しました')
      );
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining(recipients)
      );
    });

    test('should log share action', () => {
      const recipients = 'test@example.com';
      global.prompt.mockReturnValue(recipients);

      shareDashboard();

      expect(console.log).toHaveBeenCalledWith(
        '[ACTION] Dashboard shared to:',
        recipients
      );
    });

    test('should do nothing when user cancels', () => {
      global.prompt.mockReturnValue(null);

      shareDashboard();

      expect(global.alert).not.toHaveBeenCalled();
      expect(console.log).not.toHaveBeenCalled();
    });
  });
});

describe('Actions - Window Object Integration', () => {
  test('showToast should be available on window object', () => {
    expect(window.showToast).toBeDefined();
    expect(typeof window.showToast).toBe('function');
  });

  test('window.showToast should work correctly', () => {
    document.body.innerHTML = '';
    window.showToast('Global test', 'info');

    const toast = document.querySelector('.toast');
    expect(toast).not.toBeNull();
    expect(toast.querySelector('.toast-message').textContent).toBe('Global test');
  });
});
