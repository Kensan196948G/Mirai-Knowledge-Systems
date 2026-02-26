/**
 * AuthManager Unit Tests
 * Mirai Knowledge Systems v1.5.0
 *
 * Jest unit tests for core/auth.js
 */

import { AuthManager, authManager } from '../core/auth.js';
import stateManager from '../core/state-manager.js';

describe('AuthManager', () => {
  beforeEach(() => {
    // Clear state before each test
    stateManager.clearState();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Authentication Status', () => {
    test('should check if user is authenticated', () => {
      stateManager.setState('isAuthenticated', false);
      expect(authManager.isAuthenticated()).toBe(false);

      stateManager.setState('isAuthenticated', true);
      expect(authManager.isAuthenticated()).toBe(true);
    });

    test('should return false when authentication state is undefined', () => {
      stateManager.setState('isAuthenticated', undefined);
      expect(authManager.isAuthenticated()).toBe(false);
    });
  });

  describe('Permission Checking', () => {
    test('should check permission correctly', () => {
      stateManager.setState('userPermissions', ['knowledge.read', 'knowledge.create']);
      expect(authManager.checkPermission('knowledge.read')).toBe(true);
      expect(authManager.checkPermission('knowledge.delete')).toBe(false);
    });

    test('should grant all permissions for wildcard', () => {
      stateManager.setState('userPermissions', ['*']);
      expect(authManager.checkPermission('any.permission')).toBe(true);
    });

    test('should return false when permissions are empty', () => {
      stateManager.setState('userPermissions', []);
      expect(authManager.checkPermission('knowledge.read')).toBe(false);
    });

    test('should handle null permissions', () => {
      stateManager.setState('userPermissions', null);
      expect(authManager.checkPermission('knowledge.read')).toBe(false);
    });
  });

  describe('Multiple Permissions Checking', () => {
    test('should check if user has any of the permissions', () => {
      stateManager.setState('userPermissions', ['knowledge.read']);
      expect(authManager.hasAnyPermission(['knowledge.read', 'knowledge.write'])).toBe(true);
      expect(authManager.hasAnyPermission(['knowledge.write', 'knowledge.delete'])).toBe(false);
    });

    test('should check if user has all of the permissions', () => {
      stateManager.setState('userPermissions', ['knowledge.read', 'knowledge.write', 'knowledge.delete']);
      expect(authManager.hasAllPermissions(['knowledge.read', 'knowledge.write'])).toBe(true);
      expect(authManager.hasAllPermissions(['knowledge.read', 'knowledge.admin'])).toBe(false);
    });

    test('should handle empty permission arrays', () => {
      stateManager.setState('userPermissions', ['knowledge.read']);
      expect(authManager.hasAnyPermission([])).toBe(false);
      expect(authManager.hasAllPermissions([])).toBe(true); // Empty set is subset of any set
    });
  });

  describe('Role Checking', () => {
    test('should check role correctly', () => {
      stateManager.setState('userRoles', ['admin', 'manager']);
      expect(authManager.hasRole('admin')).toBe(true);
      expect(authManager.hasRole('user')).toBe(false);
    });

    test('should return false when roles are empty', () => {
      stateManager.setState('userRoles', []);
      expect(authManager.hasRole('admin')).toBe(false);
    });

    test('should handle null roles', () => {
      stateManager.setState('userRoles', null);
      expect(authManager.hasRole('admin')).toBe(false);
    });
  });

  describe('Multiple Roles Checking', () => {
    test('should check if user has any of the roles', () => {
      stateManager.setState('userRoles', ['manager']);
      expect(authManager.hasAnyRole(['admin', 'manager'])).toBe(true);
      expect(authManager.hasAnyRole(['admin', 'supervisor'])).toBe(false);
    });

    test('should check if user has all of the roles', () => {
      stateManager.setState('userRoles', ['admin', 'manager', 'supervisor']);
      expect(authManager.hasAllRoles(['admin', 'manager'])).toBe(true);
      expect(authManager.hasAllRoles(['admin', 'user'])).toBe(false);
    });
  });

  describe('Token Management', () => {
    test('should get access token from localStorage', () => {
      localStorage.setItem('access_token', 'test-token-123');
      expect(authManager.getAccessToken()).toBe('test-token-123');
    });

    test('should return null when access token is not set', () => {
      expect(authManager.getAccessToken()).toBeNull();
    });

    test('should set access token to localStorage', () => {
      authManager.setAccessToken('new-token-456');
      expect(localStorage.getItem('access_token')).toBe('new-token-456');
    });

    test('should remove access token from localStorage', () => {
      localStorage.setItem('access_token', 'test-token');
      authManager.removeAccessToken();
      expect(localStorage.getItem('access_token')).toBeNull();
    });
  });

  describe('Refresh Token Management', () => {
    test('should get refresh token from localStorage', () => {
      localStorage.setItem('refresh_token', 'refresh-test-123');
      expect(authManager.getRefreshToken()).toBe('refresh-test-123');
    });

    test('should set refresh token to localStorage', () => {
      authManager.setRefreshToken('new-refresh-456');
      expect(localStorage.getItem('refresh_token')).toBe('new-refresh-456');
    });

    test('should remove refresh token from localStorage', () => {
      localStorage.setItem('refresh_token', 'test-refresh');
      authManager.removeRefreshToken();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('Logout', () => {
    test('should clear all authentication data on logout', () => {
      // Setup authenticated state
      stateManager.setCurrentUser({ id: 1, username: 'test' });
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('refresh_token', 'test-refresh');

      // Logout
      authManager.logout();

      // Verify cleanup
      expect(stateManager.getCurrentUser()).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('User Information', () => {
    test('should get current user', () => {
      const user = { id: 1, username: 'testuser' };
      stateManager.setCurrentUser(user);
      expect(authManager.getCurrentUser()).toEqual(user);
    });

    test('should get user permissions', () => {
      stateManager.setState('userPermissions', ['read', 'write']);
      expect(authManager.getUserPermissions()).toEqual(['read', 'write']);
    });

    test('should get user roles', () => {
      stateManager.setState('userRoles', ['admin', 'manager']);
      expect(authManager.getUserRoles()).toEqual(['admin', 'manager']);
    });
  });
});

describe('Global AuthManager Instance', () => {
  test('should be available globally', () => {
    expect(authManager).toBeDefined();
    expect(authManager).toBeInstanceOf(AuthManager);
  });

  test('should be available on window object', () => {
    expect(window.authManager).toBeDefined();
    expect(window.AuthManager).toBeDefined();
  });
});
