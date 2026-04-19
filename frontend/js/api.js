// API Service Module - Common utilities for API interactions

// Dynamically determine API base URL
const API_BASE_URL = (() => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // In development (localhost), use port 10000 (FastAPI default)
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return `${protocol}//localhost:10000`;
    }
    
    // In production (Render, etc.), use same domain
    return `${protocol}//${window.location.host}`;
})();

console.log('API Base URL:', API_BASE_URL);

async function makeRequest(endpoint, method = 'GET', data = null, token = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    // Add authorization header if token is provided
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        // Check if response is ok or handle specific status codes
        if (response.status === 401) {
            // Token expired or invalid, clear auth data
            localStorage.removeItem('authToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userInfo');
            window.location.href = 'login.html';
            throw new Error('Session expired. Please login again.');
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ==================== Authentication API ====================

/**
 * Sign up a new user
 * @param {string} name
 * @param {string} email
 * @param {string} password
 * @param {string} department
 * @param {string} rollId
 * @returns {Promise}
 */
async function signup(name, email, password, department, rollId) {
    return makeRequest('/api/auth/signup', 'POST', {
        name,
        email,
        password,
        department,
        roll_id: rollId
    });
}

/**
 * Login user
 * @param {string} email
 * @param {string} password
 * @returns {Promise}
 */
async function login(email, password) {
    return makeRequest('/api/auth/login', 'POST', {
        email,
        password
    });
}

// ==================== Chat API ====================

/**
 * Send a message to the RAG-powered chatbot
 * @param {string} message - User question or message
 * @param {string} sessionId - Optional session ID for tracking conversation
 * @param {number} topK - Number of context chunks to retrieve (1-5, default: 3)
 * @param {boolean} includeContext - Include retrieved context in response (default: true)
 * @returns {Promise}
 */
async function sendChatMessage(message, sessionId = null, topK = 3, includeContext = true) {
    return makeRequest('/api/chat/ask', 'POST', {
        message,
        session_id: sessionId,
        top_k: topK,
        include_context: includeContext
    });
}

/**
 * Get conversation history for a session
 * @param {string} sessionId - Session ID
 * @returns {Promise}
 */
async function getConversationHistory(sessionId) {
    return makeRequest(`/api/chat/conversation-history/${sessionId}`, 'GET');
}

/**
 * Clear conversation history
 * @returns {Promise}
 */
async function clearChatHistory() {
    return makeRequest('/api/chat/clear-history', 'POST', {});
}

/**
 * Submit feedback on a chat response
 * @param {string} sessionId - Session ID
 * @param {string} query - The original query
 * @param {number} rating - Rating 1-5
 * @param {string} feedback - Optional feedback text
 * @returns {Promise}
 */
async function submitChatFeedback(sessionId, query, rating, feedback = null) {
    return makeRequest('/api/chat/feedback', 'POST', {
        session_id: sessionId,
        query,
        rating,
        feedback
    });
}

// ==================== Quiz API ====================

async function getQuiz() {
    const token = localStorage.getItem('authToken');
    return makeRequest('/api/quiz/get', 'GET', null, token);
}

async function submitQuizAnswer(quizId, answers) {
    const token = localStorage.getItem('authToken');
    return makeRequest('/api/quiz/submit', 'POST', {
        quiz_id: quizId,
        answers
    }, token);
}

// ==================== Flashcards API ====================

async function getFlashcards(category = null) {
    const token = localStorage.getItem('authToken');
    const endpoint = category ? `/api/flashcards?category=${category}` : '/api/flashcards';
    return makeRequest(endpoint, 'GET', null, token);
}

// ==================== Diagnostics API ====================

/**
 * Analyze diagnostic input
 * @param {string} inputText - Student's learning concern
 * @param {string} sessionId - Optional session ID
 * @returns {Promise}
 */
async function analyzeDiagnostic(inputText, sessionId = null) {
    const token = localStorage.getItem('authToken');
    return makeRequest('/api/diagnostic/analyze', 'POST', {
        input_text: inputText,
        session_id: sessionId
    }, token);
}

/**
 * Get diagnostic history for a session
 * @param {string} sessionId - Session ID
 * @returns {Promise}
 */
async function getDiagnosticHistory(sessionId) {
    const token = localStorage.getItem('authToken');
    return makeRequest(`/api/diagnostic/history/${sessionId}`, 'GET', null, token);
}

/**
 * Submit feedback on diagnostic
 * @param {string} sessionId - Session ID
 * @param {string} feedbackText - Feedback text
 * @param {boolean} helpful - Whether recommendation was helpful
 * @returns {Promise}
 */
async function submitDiagnosticFeedback(sessionId, feedbackText, helpful) {
    const token = localStorage.getItem('authToken');
    return makeRequest('/api/diagnostic/feedback', 'POST', {
        session_id: sessionId,
        feedback_text: feedbackText,
        helpful
    }, token);
}
