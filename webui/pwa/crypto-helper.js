/**
 * JWT Token Encryption Helper using Web Crypto API
 * Algorithm: AES-GCM (256-bit) + PBKDF2 Key Derivation
 *
 * Security Features:
 * - PBKDF2 with 100,000 iterations (OWASP recommended)
 * - AES-GCM 256-bit encryption
 * - Browser fingerprint-based key derivation
 * - Token expiration validation
 */
class CryptoHelper {
  constructor() {
    this.algorithm = 'AES-GCM';
    this.keyLength = 256;
    this.iterations = 100000; // PBKDF2 iterations (OWASP推奨)
    this.saltKey = 'mks-pwa-salt-v1'; // localStorage key for salt
  }

  /**
   * Generate or retrieve salt for PBKDF2
   */
  async getSalt() {
    let saltHex = localStorage.getItem(this.saltKey);

    if (!saltHex) {
      // Generate new 16-byte random salt
      const salt = crypto.getRandomValues(new Uint8Array(16));
      saltHex = Array.from(salt).map(b => b.toString(16).padStart(2, '0')).join('');
      localStorage.setItem(this.saltKey, saltHex);
    }

    return new Uint8Array(saltHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
  }

  /**
   * Derive encryption key using PBKDF2
   * Base material: User email + Browser fingerprint
   */
  async deriveKey() {
    const userEmail = localStorage.getItem('user_email') || 'anonymous';
    const browserFingerprint = await this.getBrowserFingerprint();
    const passphrase = `${userEmail}:${browserFingerprint}`;

    const salt = await this.getSalt();
    const encoder = new TextEncoder();

    // Import passphrase as base key
    const baseKey = await crypto.subtle.importKey(
      'raw',
      encoder.encode(passphrase),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    // Derive AES-GCM key
    const derivedKey = await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: this.iterations,
        hash: 'SHA-256'
      },
      baseKey,
      { name: this.algorithm, length: this.keyLength },
      true, // extractable
      ['encrypt', 'decrypt']
    );

    return derivedKey;
  }

  /**
   * Generate browser fingerprint (stable across sessions)
   */
  async getBrowserFingerprint() {
    const components = [
      navigator.userAgent,
      navigator.language,
      screen.width,
      screen.height,
      screen.colorDepth,
      new Date().getTimezoneOffset(),
      !!window.sessionStorage,
      !!window.localStorage
    ];

    const fingerprint = components.join('|');
    const encoder = new TextEncoder();
    const data = encoder.encode(fingerprint);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Encrypt JWT token
   * @param {string} token - JWT token to encrypt
   * @returns {Object} - {encrypted: Uint8Array, iv: Uint8Array}
   */
  async encrypt(token) {
    const key = await this.deriveKey();
    const iv = crypto.getRandomValues(new Uint8Array(12)); // GCM recommended: 96-bit IV

    const encoder = new TextEncoder();
    const encrypted = await crypto.subtle.encrypt(
      { name: this.algorithm, iv: iv },
      key,
      encoder.encode(token)
    );

    return {
      encrypted: Array.from(new Uint8Array(encrypted)),
      iv: Array.from(iv)
    };
  }

  /**
   * Decrypt JWT token
   * @param {Array} encryptedData - Encrypted token data
   * @param {Array} iv - Initialization vector
   * @returns {string} - Decrypted JWT token
   */
  async decrypt(encryptedData, iv) {
    const key = await this.deriveKey();

    try {
      const decrypted = await crypto.subtle.decrypt(
        { name: this.algorithm, iv: new Uint8Array(iv) },
        key,
        new Uint8Array(encryptedData)
      );

      const decoder = new TextDecoder();
      return decoder.decode(decrypted);
    } catch (error) {
      console.error('[CryptoHelper] Decryption failed:', error);
      throw new Error('Token decryption failed');
    }
  }

  /**
   * Validate token expiration
   * @param {string} token - JWT token
   * @returns {boolean} - true if valid, false if expired
   */
  validateTokenExpiration(token) {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return false;

      const payload = JSON.parse(atob(parts[1]));
      const exp = payload.exp;

      if (!exp) return true; // No expiration = valid

      const now = Math.floor(Date.now() / 1000);
      return now < exp;
    } catch (error) {
      console.error('[CryptoHelper] Token validation failed:', error);
      return false;
    }
  }

  /**
   * Rotate encryption key (3-month cycle, optional)
   */
  async rotateKey() {
    // Clear old salt, force new key derivation on next encrypt()
    localStorage.removeItem(this.saltKey);
    console.log('[CryptoHelper] Key rotation triggered');
  }
}

// Export
window.CryptoHelper = CryptoHelper;
