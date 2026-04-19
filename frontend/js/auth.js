// Frontend Authentication Module

const AUTH_TOKEN_KEY = 'authToken';
const REFRESH_TOKEN_KEY = 'refreshToken';
const USER_INFO_KEY = 'userInfo';

// ==================== Authentication Functions ====================

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
function isAuthenticated() {
    return localStorage.getItem(AUTH_TOKEN_KEY) !== null;
}

/**
 * Get stored authentication token
 * @returns {string|null}
 */
function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Get stored user info
 * @returns {object|null}
 */
function getUserInfo() {
    const userInfo = localStorage.getItem(USER_INFO_KEY);
    return userInfo ? JSON.parse(userInfo) : null;
}

/**
 * Store authentication tokens and user info
 * @param {string} accessToken
 * @param {string} refreshToken
 * @param {object} userProfile
 */
function storeAuthData(accessToken, refreshToken, userProfile) {
    localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(userProfile));
}

/**
 * Clear authentication data
 */
function clearAuthData() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_INFO_KEY);
}

/**
 * Verify if token is valid by calling backend
 * @returns {Promise<boolean>}
 */
async function verifyToken() {
    const token = getAuthToken();
    if (!token) return false;

    try {
        const response = await makeRequest('/api/auth/verify', 'GET', null, token);
        return response.success || response.user_id;
    } catch (error) {
        console.error('Token verification failed:', error);
        return false;
    }
}

// ==================== Signup ====================

/**
 * Validate email format and domain
 * @param {string} email
 * @returns {boolean}
 */
function validateEmail(email) {
    const pattern = /^[a-zA-Z0-9._%+-]+@student\.qu\.edu\.qa$/;
    return pattern.test(email);
}

/**
 * Validate password strength
 * @param {string} password
 * @returns {object} {isValid: boolean, checks: {length, upper, lower, digit}}
 */
function validatePasswordStrength(password) {
    const checks = {
        length: password.length >= 8,
        upper: /[A-Z]/.test(password),
        lower: /[a-z]/.test(password),
        digit: /\d/.test(password)
    };
    
    const isValid = checks.length && checks.upper && checks.lower && checks.digit;
    return { isValid, checks };
}

/**
 * Update password requirement indicators
 * @param {object} checks
 */
function updatePasswordRequirements(checks) {
    updateRequirementCheck('lengthCheck', checks.length);
    updateRequirementCheck('upperCheck', checks.upper);
    updateRequirementCheck('lowerCheck', checks.lower);
    updateRequirementCheck('digitCheck', checks.digit);
}

/**
 * Update individual requirement check
 * @param {string} elementId
 * @param {boolean} isMet
 */
function updateRequirementCheck(elementId, isMet) {
    const element = document.getElementById(elementId);
    if (element) {
        if (isMet) {
            element.classList.add('met');
            element.textContent = '✓';
        } else {
            element.classList.remove('met');
            element.textContent = '✗';
        }
    }
}

/**
 * Show message in UI
 * @param {string} message
 * @param {string} type 'success' or 'error'
 */
function showMessage(message, type = 'error') {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.className = type === 'success' ? 'success-message' : 'error-message';
        
        // Create close button for error messages
        let content = message;
        if (type === 'error') {
            content = `<div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <button type="button" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 1.2rem; padding: 0;" onclick="this.parentElement.parentElement.style.display='none';">×</button>
            </div>`;
        }
        
        messageDiv.innerHTML = content;
        messageDiv.style.display = 'block';
        
        // Auto-hide success messages only
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 2000);
        }
    }
}

/**
 * Show loading state
 * @param {boolean} isLoading
 */
function setLoading(isLoading) {
    const loadingDiv = document.getElementById('loading');
    const submitBtn = document.getElementById('submitBtn');
    
    if (loadingDiv) {
        loadingDiv.style.display = isLoading ? 'block' : 'none';
    }
    if (submitBtn) {
        submitBtn.disabled = isLoading;
    }
}

/**
 * Handle signup form submission
 * @param {Event} event
 */
async function handleSignup(event) {
    event.preventDefault();
    setLoading(true);

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const department = document.getElementById('department').value.trim();
    const rollId = document.getElementById('rollId').value.trim();

    // Validate email
    if (!validateEmail(email)) {
        showMessage('Please use a valid @student.qu.edu.qa email address', 'error');
        setLoading(false);
        return;
    }

    // Validate password strength
    const { isValid: isPasswordValid } = validatePasswordStrength(password);
    if (!isPasswordValid) {
        showMessage('Password must contain uppercase, lowercase, and digits, and be at least 8 characters', 'error');
        setLoading(false);
        return;
    }

    // Check if passwords match
    if (password !== confirmPassword) {
        showMessage('Passwords do not match', 'error');
        setLoading(false);
        return;
    }

    try {
        const response = await signup(name, email, password, department, rollId);
        
        if (response.success) {
            showMessage('Sign up successful! Redirecting to login...', 'success');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showMessage(response.message || 'Signup failed', 'error');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showMessage('An error occurred during signup', 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Handle login form submission
 * @param {Event} event
 */
async function handleLogin(event) {
    event.preventDefault();
    setLoading(true);

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    try {
        const response = await login(email, password);
        
        if (response.success) {
            storeAuthData(
                response.access_token,
                response.refresh_token,
                {
                    user_id: response.user_id,
                    email: response.email,
                    ...response.user_profile
                }
            );
            showMessage('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        } else {
            showMessage(response.message || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('An error occurred during login', 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Handle logout
 */
async function handleLogout() {
    const token = getAuthToken();
    
    try {
        await makeRequest('/api/auth/logout', 'POST', null, token);
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        clearAuthData();
        window.location.href = 'login.html';
    }
}

// ==================== Page Initialization ====================

/**
 * Check authentication on page load and redirect if needed
 */
async function checkAuthentication() {
    if (window.location.pathname.includes('login.html') || 
        window.location.pathname.includes('signup.html') ||
        window.location.pathname.includes('index.html')) {
        
        if (window.location.pathname.includes('index.html')) {
            // Index page requires authentication
            const isAuth = isAuthenticated();
            const isValid = isAuth ? await verifyToken() : false;
            
            if (!isAuth || !isValid) {
                clearAuthData();
                window.location.href = 'login.html';
                return;
            }
        } else if (isAuthenticated() && (window.location.pathname.includes('login.html') || 
                                         window.location.pathname.includes('signup.html'))) {
            // If already logged in, redirect away from auth pages
            const isValid = await verifyToken();
            if (isValid) {
                window.location.href = 'index.html';
            }
        }
    }
}

/**
 * Set up password validation listeners on signup page
 */
function setupPasswordValidation() {
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const { checks } = validatePasswordStrength(this.value);
            updatePasswordRequirements(checks);
        });
    }
}

/**
 * Initialize page on load
 */
document.addEventListener('DOMContentLoaded', async function() {
    setupPasswordValidation();
    await checkAuthentication();
});
