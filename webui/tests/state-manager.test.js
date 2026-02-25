/**
 * StateManager Unit Tests
 * Mirai Knowledge Systems v1.5.0
 *
 * Jest unit tests for core/state-manager.js
 */

import { StateManager, stateManager } from '../core/state-manager.js';

describe('StateManager', () => {
  let testManager;

  beforeEach(() => {
    testManager = new StateManager();
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('State Management', () => {
    test('should set and get state', () => {
      testManager.setState('testKey', 'testValue');
      expect(testManager.getState('testKey')).toBe('testValue');
    });

    test('should get all state when key is not provided', () => {
      testManager.setState('key1', 'value1');
      testManager.setState('key2', 'value2');
      const allState = testManager.getState();
      expect(allState.key1).toBe('value1');
      expect(allState.key2).toBe('value2');
    });

    test('should return a copy of state, not a reference', () => {
      testManager.setState('key', 'value');
      const state1 = testManager.getState();
      state1.key = 'modified';
      const state2 = testManager.getState();
      expect(state2.key).toBe('value');
    });
  });

  describe('Observer Pattern', () => {
    test('should notify observers on state change', () => {
      const observer = jest.fn();
      testManager.subscribe(observer);
      testManager.setState('test', 'value');

      expect(observer).toHaveBeenCalledWith({
        key: 'test',
        oldValue: undefined,
        newValue: 'value'
      });
    });

    test('should support multiple observers', () => {
      const observer1 = jest.fn();
      const observer2 = jest.fn();
      testManager.subscribe(observer1);
      testManager.subscribe(observer2);

      testManager.setState('test', 'value');

      expect(observer1).toHaveBeenCalled();
      expect(observer2).toHaveBeenCalled();
    });

    test('should unsubscribe observer', () => {
      const observer = jest.fn();
      testManager.subscribe(observer);
      testManager.unsubscribe(observer);
      testManager.setState('test', 'value');

      expect(observer).not.toHaveBeenCalled();
    });

    test('should throw error for non-function observer', () => {
      expect(() => {
        testManager.subscribe('not a function');
      }).toThrow(TypeError);
    });

    test('should handle observer errors gracefully', () => {
      const errorObserver = jest.fn(() => {
        throw new Error('Observer error');
      });
      const normalObserver = jest.fn();

      testManager.subscribe(errorObserver);
      testManager.subscribe(normalObserver);

      // Should not throw, but continue to notify other observers
      expect(() => {
        testManager.setState('test', 'value');
      }).not.toThrow();

      expect(normalObserver).toHaveBeenCalled();
    });
  });

  describe('Current User Management', () => {
    test('should set and get current user', () => {
      const user = { id: 1, username: 'testuser', roles: ['user'], permissions: ['read'] };
      testManager.setCurrentUser(user);
      expect(testManager.getCurrentUser()).toEqual(user);
    });

    test('should update authentication state when user is set', () => {
      const user = { id: 1, username: 'testuser' };
      testManager.setCurrentUser(user);
      expect(testManager.getState('isAuthenticated')).toBe(true);
    });

    test('should clear authentication state when user is null', () => {
      testManager.setCurrentUser(null);
      expect(testManager.getState('isAuthenticated')).toBe(false);
      expect(testManager.getState('userPermissions')).toEqual([]);
      expect(testManager.getState('userRoles')).toEqual([]);
    });

    test('should extract permissions from user object', () => {
      const user = { id: 1, username: 'testuser', permissions: ['read', 'write'] };
      testManager.setCurrentUser(user);
      expect(testManager.getState('userPermissions')).toEqual(['read', 'write']);
    });

    test('should extract roles from user object', () => {
      const user = { id: 1, username: 'testuser', roles: ['admin', 'manager'] };
      testManager.setCurrentUser(user);
      expect(testManager.getState('userRoles')).toEqual(['admin', 'manager']);
    });
  });

  describe('Permission Checking', () => {
    test('should check permission correctly', () => {
      testManager.setState('userPermissions', ['read', 'write']);
      expect(testManager.hasPermission('read')).toBe(true);
      expect(testManager.hasPermission('delete')).toBe(false);
    });

    test('should grant all permissions for wildcard', () => {
      testManager.setState('userPermissions', ['*']);
      expect(testManager.hasPermission('anything')).toBe(true);
    });
  });

  describe('Role Checking', () => {
    test('should check role correctly', () => {
      testManager.setState('userRoles', ['admin', 'manager']);
      expect(testManager.hasRole('admin')).toBe(true);
      expect(testManager.hasRole('user')).toBe(false);
    });
  });

  describe('State Persistence', () => {
    test('should persist state to localStorage', () => {
      testManager.setState('testKey', 'testValue');
      const storedValue = localStorage.getItem('mks_state_testKey');
      expect(JSON.parse(storedValue)).toBe('testValue');
    });

    test('should not persist sensitive data in production', () => {
      testManager.setConfig('isProduction', true);
      testManager.setCurrentUser({ id: 1, username: 'test' });

      const storedUser = localStorage.getItem('mks_state_currentUser');
      expect(storedUser).toBeNull();
    });

    test('should restore state from localStorage', () => {
      localStorage.setItem('mks_state_testKey', JSON.stringify('testValue'));
      testManager.restoreState();
      expect(testManager.getState('testKey')).toBe('testValue');
    });
  });

  describe('State Clearing', () => {
    test('should clear all state except appConfig', () => {
      testManager.setState('currentUser', { id: 1 });
      testManager.setState('testKey', 'testValue');
      testManager.clearState();

      expect(testManager.getCurrentUser()).toBeNull();
      expect(testManager.getState('isAuthenticated')).toBe(false);
      expect(testManager.getState('appConfig')).toBeDefined();
    });

    test('should remove localStorage items on clear', () => {
      testManager.setState('testKey', 'testValue');
      testManager.clearState();

      const storedValue = localStorage.getItem('mks_state_testKey');
      expect(storedValue).toBeNull();
    });
  });

  describe('App Config Management', () => {
    test('should get config value', () => {
      expect(testManager.getConfig('apiBase')).toBe('http://localhost/api/v1');
    });

    test('should set config value', () => {
      testManager.setConfig('customKey', 'customValue');
      expect(testManager.getConfig('customKey')).toBe('customValue');
    });

    test('should get all config when key is not provided', () => {
      const config = testManager.getConfig();
      expect(config).toHaveProperty('apiBase');
      expect(config).toHaveProperty('isProduction');
    });
  });
});

describe('Global StateManager Instance', () => {
  test('should be available globally', () => {
    expect(stateManager).toBeDefined();
    expect(stateManager).toBeInstanceOf(StateManager);
  });

  test('should have getCurrentUser as window function', () => {
    expect(typeof window.getCurrentUser).toBe('function');
  });
});
