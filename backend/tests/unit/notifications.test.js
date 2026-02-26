/**
 * Unit Tests for notifications.js
 * 通知システムのテスト
 */

const fs = require('fs');
const path = require('path');

// 依存する関数をモック
global.fetchAPI = jest.fn();
global.formatDate = jest.fn(date => date);

// loggerモック（notifications.jsが使用）
global.logger = {
  error: (...args) => console.error(...args),
  warn: (...args) => console.warn(...args),
  info: jest.fn(),
  log: jest.fn()
};

// テスト対象のファイルを読み込み
const notificationsCode = fs.readFileSync(
  path.join(__dirname, '../../../webui/notifications.js'),
  'utf8'
);

// setIntervalとaddEventListenerをスキップするため、一部を置き換え
const modifiedCode = notificationsCode
  .replace(/setInterval\([^)]+\);/g, '// setInterval skipped in tests')
  .replace(/document\.addEventListener\('DOMContentLoaded'[^}]+}\);/g, '// DOMContentLoaded skipped');

eval(modifiedCode);

describe('Notifications - Badge Management', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div class="notification-badge"></div>
    `;
  });

  describe('updateNotificationBadge', () => {
    test('should display badge with count when count > 0', () => {
      updateNotificationBadge(5);
      const badge = document.querySelector('.notification-badge');
      expect(badge.textContent).toBe('5');
      expect(badge.style.display).toBe('inline-block');
    });

    test('should display "99+" when count > 99', () => {
      updateNotificationBadge(150);
      const badge = document.querySelector('.notification-badge');
      expect(badge.textContent).toBe('99+');
      expect(badge.style.display).toBe('inline-block');
    });

    test('should hide badge when count is 0', () => {
      updateNotificationBadge(0);
      const badge = document.querySelector('.notification-badge');
      expect(badge.style.display).toBe('none');
    });

    test('should handle missing badge element gracefully', () => {
      document.body.innerHTML = '';
      expect(() => updateNotificationBadge(5)).not.toThrow();
    });
  });
});

describe('Notifications - Display', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div class="notifications-panel"></div>
    `;
    jest.clearAllMocks();
  });

  describe('displayNotifications', () => {
    test('should display "no notifications" message when empty', () => {
      displayNotifications([]);
      const panel = document.querySelector('.notifications-panel');
      expect(panel.querySelector('.no-notifications')).not.toBeNull();
      expect(panel.querySelector('.no-notifications').textContent).toBe('通知はありません');
    });

    test('should display notification items', () => {
      const notifications = [
        {
          id: 1,
          type: 'approval_required',
          title: 'Approval Needed',
          message: 'Please approve the document',
          created_at: '2024-01-15T10:00:00Z',
          is_read: false
        },
        {
          id: 2,
          type: 'approval_completed',
          title: 'Approved',
          message: 'Document was approved',
          created_at: '2024-01-14T09:00:00Z',
          is_read: true
        }
      ];

      displayNotifications(notifications);

      const panel = document.querySelector('.notifications-panel');
      const items = panel.querySelectorAll('.notification-item');

      expect(items.length).toBe(2);
      expect(items[0].querySelector('.notification-title').textContent).toBe('Approval Needed');
      expect(items[1].querySelector('.notification-title').textContent).toBe('Approved');
    });

    test('should mark unread notifications correctly', () => {
      const notifications = [
        {
          id: 1,
          type: 'approval_required',
          title: 'Unread Notification',
          message: 'This is unread',
          created_at: '2024-01-15T10:00:00Z',
          is_read: false
        }
      ];

      displayNotifications(notifications);

      const item = document.querySelector('.notification-item');
      expect(item.classList.contains('unread')).toBe(true);
      expect(item.querySelector('.unread-dot')).not.toBeNull();
    });

    test('should not show unread dot for read notifications', () => {
      const notifications = [
        {
          id: 1,
          type: 'approval_required',
          title: 'Read Notification',
          message: 'This is read',
          created_at: '2024-01-15T10:00:00Z',
          is_read: true
        }
      ];

      displayNotifications(notifications);

      const item = document.querySelector('.notification-item');
      expect(item.classList.contains('read')).toBe(true);
      expect(item.querySelector('.unread-dot')).toBeNull();
    });

    test('should prevent XSS in notification content', () => {
      const notifications = [
        {
          id: 1,
          type: 'approval_required',
          title: '<script>alert("XSS")</script>',
          message: '<img src=x onerror=alert("XSS")>',
          created_at: '2024-01-15T10:00:00Z',
          is_read: false
        }
      ];

      displayNotifications(notifications);

      const item = document.querySelector('.notification-item');
      const title = item.querySelector('.notification-title');
      const message = item.querySelector('.notification-message');

      // textContentを使用しているため、HTMLは実行されない
      expect(title.innerHTML).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
      expect(message.innerHTML).toBe('&lt;img src=x onerror=alert("XSS")&gt;');
    });

    test('should display correct icon for each notification type', () => {
      const notifications = [
        { id: 1, type: 'approval_required', title: 'T1', message: 'M1', created_at: '2024-01-15', is_read: false },
        { id: 2, type: 'approval_completed', title: 'T2', message: 'M2', created_at: '2024-01-15', is_read: false },
        { id: 3, type: 'incident_reported', title: 'T3', message: 'M3', created_at: '2024-01-15', is_read: false },
        { id: 4, type: 'consultation_answered', title: 'T4', message: 'M4', created_at: '2024-01-15', is_read: false },
        { id: 5, type: 'unknown_type', title: 'T5', message: 'M5', created_at: '2024-01-15', is_read: false }
      ];

      displayNotifications(notifications);

      const icons = document.querySelectorAll('.notification-icon');
      expect(icons[0].textContent).toBe('📋');
      expect(icons[1].textContent).toBe('✅');
      expect(icons[2].textContent).toBe('⚠️');
      expect(icons[3].textContent).toBe('💬');
      expect(icons[4].textContent).toBe('📢'); // default icon
    });
  });
});

describe('Notifications - API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    document.body.innerHTML = `
      <div class="notification-badge"></div>
      <div class="notifications-panel"></div>
    `;
  });

  describe('loadUnreadNotificationCount', () => {
    test('should fetch and update unread count', async () => {
      fetchAPI.mockResolvedValueOnce({
        success: true,
        data: { unread_count: 7 }
      });

      await loadUnreadNotificationCount();

      expect(fetchAPI).toHaveBeenCalledWith('/notifications/unread/count');
      const badge = document.querySelector('.notification-badge');
      expect(badge.textContent).toBe('7');
    });

    test('should handle API errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      fetchAPI.mockRejectedValueOnce(new Error('Network error'));

      await loadUnreadNotificationCount();

      expect(consoleError).toHaveBeenCalled();
      consoleError.mockRestore();
    });
  });

  describe('loadNotifications', () => {
    test('should fetch all notifications when status is null', async () => {
      fetchAPI.mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { unread_count: 0 }
      });

      await loadNotifications();

      expect(fetchAPI).toHaveBeenCalledWith('/notifications');
    });

    test('should fetch filtered notifications by status', async () => {
      fetchAPI.mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { unread_count: 0 }
      });

      await loadNotifications('unread');

      expect(fetchAPI).toHaveBeenCalledWith('/notifications?status=unread');
    });
  });

  describe('markNotificationAsRead', () => {
    test('should mark notification as read via API', async () => {
      fetchAPI.mockResolvedValueOnce({ success: true });
      fetchAPI.mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { unread_count: 0 }
      });

      await markNotificationAsRead(123);

      expect(fetchAPI).toHaveBeenCalledWith('/notifications/123/read', { method: 'PUT' });
    });

    test('should handle errors when marking as read', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      fetchAPI.mockRejectedValueOnce(new Error('API error'));

      await markNotificationAsRead(123);

      expect(consoleError).toHaveBeenCalled();
      consoleError.mockRestore();
    });
  });
});

describe('Notifications - Utility Functions', () => {
  describe('formatRelativeTime', () => {
    beforeEach(() => {
      // 固定日時を設定（2024-01-15 12:00:00）
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2024-01-15T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test('should return "たった今" for very recent time', () => {
      const justNow = new Date('2024-01-15T11:59:45Z').toISOString();
      expect(formatRelativeTime(justNow)).toBe('たった今');
    });

    test('should return minutes ago for recent time', () => {
      const fiveMinutesAgo = new Date('2024-01-15T11:55:00Z').toISOString();
      expect(formatRelativeTime(fiveMinutesAgo)).toBe('5分前');
    });

    test('should return hours ago for time within 24 hours', () => {
      const threeHoursAgo = new Date('2024-01-15T09:00:00Z').toISOString();
      expect(formatRelativeTime(threeHoursAgo)).toBe('3時間前');
    });

    test('should return days ago for time within a week', () => {
      const twoDaysAgo = new Date('2024-01-13T12:00:00Z').toISOString();
      expect(formatRelativeTime(twoDaysAgo)).toBe('2日前');
    });
  });

  describe('escapeHtml', () => {
    test('should escape HTML special characters', () => {
      expect(escapeHtml('<script>alert("XSS")</script>')).toBe('&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;');
    });

    test('should handle null and undefined', () => {
      expect(escapeHtml(null)).toBe('');
      expect(escapeHtml(undefined)).toBe('');
    });
  });
});

describe('Notifications - Panel Toggle', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div class="notifications-panel" style="display: none;"></div>
    `;
    jest.clearAllMocks();
  });

  describe('toggleNotificationPanel', () => {
    test('should show panel when hidden', async () => {
      fetchAPI.mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { unread_count: 0 }
      });

      toggleNotificationPanel();

      const panel = document.querySelector('.notifications-panel');
      expect(panel.style.display).toBe('block');
      expect(fetchAPI).toHaveBeenCalledWith('/notifications');
    });

    test('should hide panel when visible', () => {
      const panel = document.querySelector('.notifications-panel');
      panel.style.display = 'block';

      toggleNotificationPanel();

      expect(panel.style.display).toBe('none');
    });

    test('should handle missing panel gracefully', () => {
      document.body.innerHTML = '';
      expect(() => toggleNotificationPanel()).not.toThrow();
    });
  });
});
