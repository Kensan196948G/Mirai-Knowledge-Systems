/**
 * APIClient Unit Tests
 * Mirai Knowledge Systems v1.5.0
 *
 * Jest unit tests for api/client.js
 */

import { APIClient, apiClient } from '../api/client.js';

describe('APIClient', () => {
  let client;

  beforeEach(() => {
    client = new APIClient();
    localStorage.clear();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
    localStorage.clear();
  });

  describe('Initialization', () => {
    test('should initialize with default base URL', () => {
      expect(client.baseURL).toBe('http://localhost/api/v1');
    });

    test('should initialize with custom base URL', () => {
      const customClient = new APIClient('https://api.example.com');
      expect(customClient.baseURL).toBe('https://api.example.com');
    });
  });

  describe('Request Headers', () => {
    test('should add Content-Type header for JSON', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await client.request('/test', { method: 'POST', body: { data: 'test' } });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    test('should add authorization header when token exists', async () => {
      localStorage.setItem('access_token', 'test-token-123');
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await client.request('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token-123'
          })
        })
      );
    });

    test('should not add authorization header when token is missing', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await client.request('/test');

      const fetchCall = global.fetch.mock.calls[0][1];
      expect(fetchCall.headers['Authorization']).toBeUndefined();
    });

    test('should merge custom headers with default headers', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await client.request('/test', {
        headers: { 'X-Custom-Header': 'custom-value' }
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Custom-Header': 'custom-value'
          })
        })
      );
    });
  });

  describe('HTTP Methods', () => {
    test('should make GET request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' })
      });

      const result = await client.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual({ data: 'test' });
    });

    test('should make POST request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      const data = { name: 'test' };
      await client.post('/test', data);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data)
        })
      );
    });

    test('should make PUT request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      const data = { id: 1, name: 'updated' };
      await client.put('/test/1', data);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(data)
        })
      );
    });

    test('should make PATCH request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      const data = { name: 'patched' };
      await client.patch('/test/1', data);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/1'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(data)
        })
      );
    });

    test('should make DELETE request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await client.delete('/test/1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/1'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('Error Handling', () => {
    test('should handle HTTP errors', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ error: 'Resource not found' })
      });

      await expect(client.get('/test')).rejects.toThrow();
    });

    test('should handle network errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(client.get('/test')).rejects.toThrow('Network error');
    });

    test('should handle 401 Unauthorized and clear tokens', async () => {
      localStorage.setItem('access_token', 'expired-token');
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ error: 'Unauthorized' })
      });

      await expect(client.get('/test')).rejects.toThrow();
      expect(localStorage.getItem('access_token')).toBeNull();
    });

    test('should handle JSON parse errors', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      await expect(client.get('/test')).rejects.toThrow('Invalid JSON');
    });
  });

  describe('Query Parameters', () => {
    test('should append query parameters to URL', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' })
      });

      await client.get('/test', { params: { page: 1, limit: 10 } });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('page=1'),
        expect.any(Object)
      );
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=10'),
        expect.any(Object)
      );
    });

    test('should handle existing query parameters in URL', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' })
      });

      await client.get('/test?existing=value', { params: { new: 'param' } });

      const url = global.fetch.mock.calls[0][0];
      expect(url).toContain('existing=value');
      expect(url).toContain('new=param');
    });
  });

  describe('Response Processing', () => {
    test('should parse JSON response', async () => {
      const responseData = { data: 'test', success: true };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => responseData
      });

      const result = await client.get('/test');
      expect(result).toEqual(responseData);
    });

    test('should handle empty response', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => null
      });

      const result = await client.get('/test');
      expect(result).toBeNull();
    });
  });

  describe('Request Timeout', () => {
    test('should abort request on timeout', async () => {
      jest.useFakeTimers();

      const mockAbort = jest.fn();
      global.AbortController = jest.fn(() => ({
        signal: {},
        abort: mockAbort
      }));

      global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      const requestPromise = client.request('/test', { timeout: 5000 });

      jest.advanceTimersByTime(5000);

      await expect(requestPromise).rejects.toThrow();
      expect(mockAbort).toHaveBeenCalled();

      jest.useRealTimers();
    });
  });
});

describe('Global APIClient Instance', () => {
  test('should be available globally', () => {
    expect(apiClient).toBeDefined();
    expect(apiClient).toBeInstanceOf(APIClient);
  });

  test('should be available on window object', () => {
    expect(window.apiClient).toBeDefined();
    expect(window.APIClient).toBeDefined();
  });
});
