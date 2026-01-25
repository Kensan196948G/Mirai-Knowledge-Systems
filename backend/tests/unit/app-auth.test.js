/**
 * Unit Tests for app.js - Authentication & RBAC
 * 認証とロールベースアクセス制御のテスト
 */

const fs = require('fs');
const path = require('path');

// app.jsの最初の300行（認証とRBAC部分）を読み込み
const appCode = fs.readFileSync(
  path.join(__dirname, '../../../webui/app.js'),
  'utf8'
);

// 必要な部分のみを抽出（認証とRBAC関連）
const authRbacCode = appCode.split('\n').slice(0, 300).join('\n');

eval(authRbacCode);

describe('Authentication - checkAuth', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  test('should return true when token exists', () => {
    localStorage.setItem('access_token', 'valid-token-12345');

    const result = checkAuth();

    expect(result).toBe(true);
    expect(window.location.href).not.toBe('/login.html');
  });

  test('should redirect to login when no token', () => {
    const result = checkAuth();

    expect(result).toBe(false);
    expect(window.location.href).toBe('/login.html');
  });

  test('should log authentication check', () => {
    localStorage.setItem('access_token', 'test-token');

    checkAuth();

    expect(console.log).toHaveBeenCalledWith(
      '[AUTH] Checking authentication. Token exists:',
      'YES'
    );
  });
});

describe('Authentication - logout', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  test('should clear all auth tokens', () => {
    localStorage.setItem('access_token', 'token1');
    localStorage.setItem('refresh_token', 'token2');
    localStorage.setItem('user', '{"id": 1}');

    logout();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  test('should redirect to login page', () => {
    logout();

    expect(window.location.href).toBe('/login.html');
  });

  test('should log logout action', () => {
    logout();

    expect(console.log).toHaveBeenCalledWith('[AUTH] Logging out...');
  });
});

describe('Authentication - getCurrentUser', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.spyOn(console, 'error').mockImplementation();
  });

  afterEach(() => {
    console.error.mockRestore();
  });

  test('should return user object when valid JSON in localStorage', () => {
    const user = { id: 1, username: 'testuser', roles: ['admin'] };
    localStorage.setItem('user', JSON.stringify(user));

    const result = getCurrentUser();

    expect(result).toEqual(user);
  });

  test('should return null when no user in localStorage', () => {
    const result = getCurrentUser();

    expect(result).toBeNull();
  });

  test('should return null when invalid JSON', () => {
    localStorage.setItem('user', 'invalid-json{');

    const result = getCurrentUser();

    expect(result).toBeNull();
    expect(console.error).toHaveBeenCalled();
  });
});

describe('RBAC - checkPermission', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  test('should return false when no user', () => {
    const result = checkPermission('admin');
    expect(result).toBe(false);
  });

  test('should return true for admin role when user is admin', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'admin',
      roles: ['admin']
    }));

    const result = checkPermission('admin');
    expect(result).toBe(true);
  });

  test('should return true when user has higher role', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'admin',
      roles: ['admin']
    }));

    const result = checkPermission('partner');
    expect(result).toBe(true);
  });

  test('should return false when user has lower role', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 2,
      username: 'partner',
      roles: ['partner']
    }));

    const result = checkPermission('admin');
    expect(result).toBe(false);
  });

  test('should handle multiple roles correctly', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 3,
      username: 'manager',
      roles: ['partner', 'construction_manager']
    }));

    expect(checkPermission('partner')).toBe(true);
    expect(checkPermission('construction_manager')).toBe(true);
    expect(checkPermission('admin')).toBe(false);
  });

  test('should use highest role level for permission check', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 4,
      username: 'multiuser',
      roles: ['partner', 'quality_assurance', 'construction_manager']
    }));

    // 最高レベルは construction_manager (level 3)
    expect(checkPermission('quality_assurance')).toBe(true);
    expect(checkPermission('partner')).toBe(true);
  });
});

describe('RBAC - hasPermission', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('should return false when no user', () => {
    const result = hasPermission('write');
    expect(result).toBe(false);
  });

  test('should return true when user has wildcard permission', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'admin',
      permissions: ['*']
    }));

    expect(hasPermission('read')).toBe(true);
    expect(hasPermission('write')).toBe(true);
    expect(hasPermission('delete')).toBe(true);
  });

  test('should return true when user has specific permission', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 2,
      username: 'editor',
      permissions: ['read', 'write']
    }));

    expect(hasPermission('read')).toBe(true);
    expect(hasPermission('write')).toBe(true);
    expect(hasPermission('delete')).toBe(false);
  });

  test('should return false when user lacks permission', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 3,
      username: 'viewer',
      permissions: ['read']
    }));

    expect(hasPermission('write')).toBe(false);
  });
});

describe('RBAC - canEdit', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('should return false when no user', () => {
    const result = canEdit('creator123');
    expect(result).toBe(false);
  });

  test('should return true when user is admin', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'admin',
      roles: ['admin']
    }));

    expect(canEdit('other-user')).toBe(true);
  });

  test('should return true when user is the creator by ID', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 100,
      username: 'creator',
      roles: ['partner']
    }));

    expect(canEdit(100)).toBe(true);
  });

  test('should return true when user is the creator by username', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 200,
      username: 'myusername',
      roles: ['partner']
    }));

    expect(canEdit('myusername')).toBe(true);
  });

  test('should return false when user is neither creator nor admin', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 300,
      username: 'otheruser',
      roles: ['partner']
    }));

    expect(canEdit('creator123')).toBe(false);
    expect(canEdit(999)).toBe(false);
  });
});

describe('RBAC - applyRBACUI', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    localStorage.clear();
    jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  test('should hide elements with data-permission when user lacks permission', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'viewer',
      permissions: ['read']
    }));

    document.body.innerHTML = `
      <button data-permission="write">Edit</button>
      <button data-permission="read">View</button>
    `;

    applyRBACUI();

    const editBtn = document.querySelector('[data-permission="write"]');
    const viewBtn = document.querySelector('[data-permission="read"]');

    expect(editBtn.classList.contains('permission-hidden')).toBe(true);
    expect(viewBtn.classList.contains('permission-hidden')).toBe(false);
  });

  test('should hide elements with data-role when user lacks role', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'partner',
      roles: ['partner']
    }));

    document.body.innerHTML = `
      <div data-role="admin">Admin Only</div>
      <div data-role="partner">Partner Access</div>
      <div data-role="admin,quality_assurance">Multi-role</div>
    `;

    applyRBACUI();

    const adminDiv = document.querySelector('[data-role="admin"]');
    const partnerDiv = document.querySelector('[data-role="partner"]');
    const multiDiv = document.querySelector('[data-role="admin,quality_assurance"]');

    expect(adminDiv.classList.contains('permission-hidden')).toBe(true);
    expect(partnerDiv.classList.contains('permission-hidden')).toBe(false);
    expect(multiDiv.classList.contains('permission-hidden')).toBe(true);
  });

  test('should hide elements with data-required-role based on role hierarchy', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'qa',
      roles: ['quality_assurance']
    }));

    document.body.innerHTML = `
      <div data-required-role="partner">Partner Level</div>
      <div data-required-role="quality_assurance">QA Level</div>
      <div data-required-role="admin">Admin Level</div>
    `;

    applyRBACUI();

    const partnerDiv = document.querySelector('[data-required-role="partner"]');
    const qaDiv = document.querySelector('[data-required-role="quality_assurance"]');
    const adminDiv = document.querySelector('[data-required-role="admin"]');

    expect(partnerDiv.classList.contains('permission-hidden')).toBe(false);
    expect(qaDiv.classList.contains('permission-hidden')).toBe(false);
    expect(adminDiv.classList.contains('permission-hidden')).toBe(true);
  });

  test('should hide elements with data-creator when user is not creator or admin', () => {
    localStorage.setItem('user', JSON.stringify({
      id: 100,
      username: 'user100',
      roles: ['partner']
    }));

    document.body.innerHTML = `
      <button data-creator="100">My Content Edit</button>
      <button data-creator="200">Other User Content Edit</button>
    `;

    applyRBACUI();

    const myEdit = document.querySelector('[data-creator="100"]');
    const otherEdit = document.querySelector('[data-creator="200"]');

    expect(myEdit.classList.contains('permission-hidden')).toBe(false);
    expect(otherEdit.classList.contains('permission-hidden')).toBe(true);
  });

  test('should do nothing when no user is logged in', () => {
    document.body.innerHTML = `
      <div data-permission="write">Should not be touched</div>
    `;

    applyRBACUI();

    const div = document.querySelector('[data-permission="write"]');
    expect(div.classList.contains('permission-hidden')).toBe(false);
  });
});

describe('RBAC - Role Hierarchy Constants', () => {
  test('should have correct role hierarchy levels', () => {
    expect(ROLE_HIERARCHY.partner).toBe(1);
    expect(ROLE_HIERARCHY.quality_assurance).toBe(2);
    expect(ROLE_HIERARCHY.construction_manager).toBe(3);
    expect(ROLE_HIERARCHY.admin).toBe(4);
  });

  test('role levels should be in ascending order', () => {
    expect(ROLE_HIERARCHY.partner).toBeLessThan(ROLE_HIERARCHY.quality_assurance);
    expect(ROLE_HIERARCHY.quality_assurance).toBeLessThan(ROLE_HIERARCHY.construction_manager);
    expect(ROLE_HIERARCHY.construction_manager).toBeLessThan(ROLE_HIERARCHY.admin);
  });
});
