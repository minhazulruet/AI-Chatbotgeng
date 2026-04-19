// Chat Module - Frontend chat functionality with RAG-powered responses

let sessionId = null;
let currentTopK = 3;  // Number of context chunks to retrieve
let includeContext = true;  // Show context in responses

/**
 * Preprocess text to normalize LaTeX math delimiters
 * Converts: (( ... )) -> $$ ... $$
 * This ensures all math notation is recognized by MathJax
 */
function preprocessLatexDelimiters(text) {
    // Convert double parentheses (( ... )) to display math $$ ... $$
    text = text.replace(/\(\(\s*/g, '$$');
    text = text.replace(/\s*\)\)/g, '$$');
    return text;
}

/**
 * Send message to chatbot and display response
 */
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Disable input during processing
    input.disabled = true;
    
    try {
        // Add user message to UI
        addMessageToChat(message, 'user');
        input.value = '';
        
        // Show loading indicator
        showLoadingIndicator();
        
        // Send to API - now using new /api/chat/ask endpoint
        const response = await sendChatMessage(message, sessionId, currentTopK, includeContext);
        
        // Clear loading indicator
        hideLoadingIndicator();
        
        // Update session ID if new
        if (!sessionId) {
            sessionId = response.session_id;
            console.log('Session started:', sessionId);
        }
        
        // Add assistant response to UI with full information
        addDetailedMessageToChat(response);
        
        // Log response metadata
        console.log('Response Quality Score:', response.quality_score);
        console.log('Contexts Retrieved:', response.contexts_count);
        console.log('Agents Used:', response.agents_used);
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideLoadingIndicator();
        addMessageToChat(
            'Error: ' + (error.message || 'Could not send message. Please try again.'),
            'error'
        );
    } finally {
        input.disabled = false;
        input.focus();
    }
}

/**
 * Add a simple message to chat (user/error)
 */
function addMessageToChat(message, role) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = escapeHtml(message);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add detailed assistant response with context and metadata
 */
function addDetailedMessageToChat(response) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Main response container
    const responseDiv = document.createElement('div');
    responseDiv.className = 'message assistant detailed-response';
    
    // Explanation
    const explanationDiv = document.createElement('div');
    explanationDiv.className = 'explanation-content';
    const processedExplanation = preprocessLatexDelimiters(response.explanation || 'No response generated');
    explanationDiv.innerHTML = marked.parse(processedExplanation);
    responseDiv.appendChild(explanationDiv);
    
    chatMessages.appendChild(responseDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Trigger MathJax rendering for entire response (in case there are equations in metadata or elsewhere)
    if (window.MathJax) {
        MathJax.typesetPromise([responseDiv]).catch(err => console.log('MathJax error:', err));
    }
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message loading';
    loadingDiv.id = 'loadingIndicator';
    loadingDiv.innerHTML = '<span class="loading-dots">.</span>';
    
    // Animate dots
    let dots = 1;
    const interval = setInterval(() => {
        if (document.getElementById('loadingIndicator')) {
            dots = (dots % 3) + 1;
            document.querySelector('.loading-dots').textContent = '.'.repeat(dots);
        } else {
            clearInterval(interval);
        }
    }, 500);
    
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Clear chat history
 */
async function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        try {
            await clearChatHistory();
            document.getElementById('chatMessages').innerHTML = '';
            sessionId = null;
            alert('Chat history cleared');
        } catch (error) {
            console.error('Error clearing chat:', error);
            alert('Failed to clear chat history');
        }
    }
}

/**
 * Submit feedback on last response
 */
async function submitFeedback(rating) {
    const feedback = prompt(`Please provide additional feedback (optional):`);
    
    try {
        const messages = document.querySelectorAll('.message.user');
        const lastQuery = messages[messages.length - 1]?.textContent || 'Unknown query';
        
        await submitChatFeedback(sessionId, lastQuery, rating, feedback);
        alert('Thank you for your feedback!');
    } catch (error) {
        console.error('Error submitting feedback:', error);
        alert('Failed to submit feedback');
    }
}

/**
 * Toggle context display
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('messageInput');
    
    // Handle Enter key to send message
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        input.focus();
    }
    
    // Initialize session
    console.log('Chat module initialized');
});
