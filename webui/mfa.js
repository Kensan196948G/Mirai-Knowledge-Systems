/**
 * MFA (Multi-Factor Authentication) Support Functions
 * Mirai Knowledge Systems
 */

const API_BASE = window.location.origin;

/**
 * Setup MFA - Generate TOTP secret, QR code, and backup codes
 * @returns {Promise<Object>} Setup data with secret, qr_code_base64, and backup_codes
 */
async function setupMFA() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE}/api/v1/auth/mfa/setup`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'MFA setup failed');
    }

    return data;
}

/**
 * Verify MFA setup with TOTP code and enable MFA
 * @param {string} totpCode - 6-digit TOTP code
 * @returns {Promise<Object>} Success response
 */
async function verifyMFASetup(totpCode) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE}/api/v1/auth/mfa/enable`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: totpCode })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'MFA verification failed');
    }

    return data;
}

/**
 * Disable MFA (requires password and TOTP code)
 * @param {string} password - User password
 * @param {string} code - TOTP code or backup code
 * @returns {Promise<Object>} Success response
 */
async function disableMFA(password, code) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        throw new Error('Not authenticated');
    }

    const payload = {
        password: password,
        code: code
    };

    const response = await fetch(`${API_BASE}/api/v1/auth/mfa/disable`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'MFA disable failed');
    }

    return data;
}

/**
 * Login with MFA token and TOTP/backup code
 * @param {string} mfaToken - MFA temporary token from initial login
 * @param {string} code - TOTP code (6 digits) or backup code
 * @param {boolean} isBackupCode - True if using backup code instead of TOTP
 * @returns {Promise<Object>} Login response with access_token
 */
async function loginWithMFA(mfaToken, code, isBackupCode = false) {
    const payload = {
        mfa_token: mfaToken
    };

    if (isBackupCode) {
        payload.backup_code = code;
    } else {
        payload.code = code;
    }

    const response = await fetch(`${API_BASE}/api/v1/auth/login/mfa`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'MFA login failed');
    }

    // Store tokens
    if (data.success && data.data.access_token) {
        localStorage.setItem('access_token', data.data.access_token);
        localStorage.setItem('refresh_token', data.data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.data.user));

        // Store MFA status
        if (data.data.used_backup_code) {
            localStorage.setItem('mfa_backup_warning', 'true');
            localStorage.setItem('remaining_backup_codes', data.data.remaining_backup_codes);
        }
    }

    return data;
}

/**
 * Download backup codes as text file
 * @param {Array<string>} codes - Array of backup codes
 */
function downloadBackupCodesText(codes) {
    const content = [
        'Mirai Knowledge Systems',
        '2要素認証バックアップコード',
        '='.repeat(50),
        '',
        '各コードは1回のみ使用可能です。',
        '安全な場所に保管してください。',
        '',
        ...codes,
        '',
        `生成日時: ${new Date().toLocaleString('ja-JP')}`,
    ].join('\n');

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mks-backup-codes-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Regenerate backup codes
 * @param {string} totpCode - 6-digit TOTP code for verification
 * @returns {Promise<Object>} Response with new backup_codes
 */
async function regenerateBackupCodes(totpCode) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE}/api/v1/auth/mfa/backup-codes/regenerate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: totpCode })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Backup code regeneration failed');
    }

    return data;
}

/**
 * Get MFA status for current user
 * @returns {Promise<Object>} MFA status with mfa_enabled, remaining_backup_codes, etc.
 */
async function getMFAStatus() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE}/api/v1/auth/mfa/status`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to get MFA status');
    }

    return data;
}

/**
 * Request MFA recovery (sends recovery link via email)
 * @param {string} email - User email
 * @param {string} username - Username
 * @returns {Promise<Object>} Response
 */
async function requestMFARecovery(email, username) {
    const response = await fetch(`${API_BASE}/api/v1/auth/mfa/recovery`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, username })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'MFA recovery request failed');
    }

    return data;
}

/**
 * Display QR code in an element
 * @param {string} qrCodeBase64 - Base64-encoded PNG QR code
 * @param {HTMLElement} element - Target element to display QR code
 */
function displayQRCode(qrCodeBase64, element) {
    if (!element) {
        console.error('Target element not found');
        return;
    }

    const img = document.createElement('img');
    img.src = `data:image/png;base64,${qrCodeBase64}`;
    img.alt = 'QR Code for MFA Setup';
    img.style.maxWidth = '300px';

    element.textContent = '';
    element.appendChild(img);
}

/**
 * Format backup code for display (add dashes if not present)
 * @param {string} code - Backup code
 * @returns {string} Formatted code
 */
function formatBackupCode(code) {
    // Remove any existing dashes
    const clean = code.replace(/-/g, '');

    // Add dashes in XXXX-XXXX-XXXX format
    if (clean.length === 12) {
        return `${clean.slice(0, 4)}-${clean.slice(4, 8)}-${clean.slice(8, 12)}`;
    }

    return code;
}

/**
 * Validate TOTP code format
 * @param {string} code - TOTP code to validate
 * @returns {boolean} True if valid
 */
function isValidTOTPCode(code) {
    return /^\d{6}$/.test(code);
}

/**
 * Validate backup code format
 * @param {string} code - Backup code to validate
 * @returns {boolean} True if valid
 */
function isValidBackupCode(code) {
    const clean = code.replace(/-/g, '');
    return /^[A-Z0-9]{12}$/i.test(clean);
}

/**
 * Check if user should be warned about low backup codes
 * @param {number} remaining - Number of remaining backup codes
 * @returns {boolean} True if warning should be shown
 */
function shouldWarnLowBackupCodes(remaining) {
    return remaining > 0 && remaining <= 3;
}

/**
 * Display MFA countdown timer (for mfa_token expiration)
 * @param {number} expiresInSeconds - Seconds until expiration
 * @param {HTMLElement} element - Element to display countdown
 */
function displayMFACountdown(expiresInSeconds, element) {
    if (!element) return;

    let remaining = expiresInSeconds;

    const updateDisplay = () => {
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        element.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        if (remaining <= 60) {
            element.style.color = 'red';
        }

        if (remaining <= 0) {
            element.textContent = '期限切れ';
            clearInterval(interval);
        }

        remaining--;
    };

    updateDisplay();
    const interval = setInterval(updateDisplay, 1000);
}
