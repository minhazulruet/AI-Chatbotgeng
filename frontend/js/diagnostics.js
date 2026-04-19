/**
 * Diagnostics Module
 * Handles diagnostic input, API calls, and response display
 */

// Session management
let currentSessionId = null;

/**
 * Initialize diagnostics module
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing diagnostics module...');
    
    // Setup form handler
    const form = document.getElementById('diagnosticForm');
    if (form) {
        form.addEventListener('submit', handleDiagnosticSubmit);
        form.addEventListener('reset', resetDiagnosticResults);
    }
    
    // Setup character counter
    const textarea = document.getElementById('inputText');
    if (textarea) {
        textarea.addEventListener('input', updateCharCount);
    }
    
    // Generate or retrieve session ID
    const storedSessionId = sessionStorage.getItem('diagnosticSessionId');
    if (storedSessionId) {
        currentSessionId = storedSessionId;
    } else {
        currentSessionId = `diag-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        sessionStorage.setItem('diagnosticSessionId', currentSessionId);
    }
    
    console.log('Diagnostics module initialized. Session ID:', currentSessionId);
});

/**
 * Update character count display
 */
function updateCharCount() {
    const textarea = document.getElementById('inputText');
    const count = textarea.value.length;
    document.getElementById('charCount').textContent = count;
}

/**
 * Fill textarea with example text
 */
function fillExample(text) {
    const textarea = document.getElementById('inputText');
    textarea.value = text;
    updateCharCount();
    textarea.focus();
}

/**
 * Handle diagnostic form submission
 */
async function handleDiagnosticSubmit(e) {
    e.preventDefault();
    
    const inputText = document.getElementById('inputText').value.trim();
    const submitBtn = document.getElementById('submitBtn');
    
    // Validation
    if (!inputText || inputText.length < 10) {
        alert('Please provide at least 10 characters describing your learning concern.');
        return;
    }
    
    // Disable submit button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = '🔄 Analyzing...';
    showDiagnosticsLoader();
    
    try {
        // Call diagnostic API
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_BASE_URL}/api/diagnostic/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                input_text: inputText,
                session_id: currentSessionId
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to analyze diagnostic input');
        }
        
        const result = await response.json();
        console.log('Diagnostic result:', result);
        
        // Display results
        displayDiagnosticResults(result);
        
    } catch (error) {
        console.error('Error:', error);
        displayError(error.message);
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Analyze My Learning';
    }
}

/**
 * Display diagnostic results
 */
function displayDiagnosticResults(result) {
    const resultsContent = document.getElementById('diagnosticsResultContent');
    
    let html = '';
    
    // Classification badge
    const classificationColor = getClassificationColor(result.classification);
    html += `
        <div class="classification-badge ${classificationColor}">
            📊 ${capitalize(result.classification)}
        </div>
    `;
    
    // Confidence score
    html += `
        <div style="margin-bottom: 20px;">
            <p style="margin: 0 0 5px 0; font-size: 0.95em; color: #666;">
                Analysis Confidence: ${(result.confidence * 100).toFixed(0)}%
            </p>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${result.confidence * 100}%"></div>
            </div>
        </div>
    `;
    
    // Check if canned response
    if (result.status === 'canned_response') {
        html += `
            <div class="canned-response">
                <strong>ℹ️ Note:</strong> ${result.canned_response}
            </div>
        `;
        resultsContent.innerHTML = html;
        return;
    }
    
    // Topics identified
    if (result.identified_topics && result.identified_topics.length > 0) {
        html += `
            <div style="margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0; color: #333; font-size: 1.1em;">📚 Identified Topics</h3>
                <ul class="topics-list">
        `;
        result.identified_topics.forEach(topic => {
            html += `<li>${topic}</li>`;
        });
        html += `
                </ul>
            </div>
        `;
    }
    
    // Main recommendation
    if (result.recommendation) {
        const rec = result.recommendation;
        
        html += `
            <div class="recommendation-section">
                <h3>🎯 Personalized Improvement Plan</h3>
        `;
        
        // Weakness identified
        html += `
            <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                <h4 style="margin: 0 0 8px 0; color: #333;">Identified Weakness</h4>
                <p style="margin: 0; color: #666;">${rec.weakness_identified}</p>
                <p style="margin: 5px 0 0 0; color: #999; font-size: 0.9em;"><strong>Root Cause:</strong> ${rec.root_cause}</p>
                <div style="margin-top: 10px;">
                    <span style="display: inline-block; padding: 4px 12px; background: ${getSeverityColor(rec.severity)}; border-radius: 4px; color: white; font-size: 0.85em; font-weight: 600;">
                        Severity: ${capitalize(rec.severity)}
                    </span>
                </div>
            </div>
        `;
        
        // Improvement steps
        if (rec.improvement_steps && rec.improvement_steps.length > 0) {
            html += `
                <h4 style="color: #333; margin-top: 20px; margin-bottom: 12px;">📋 Action Steps</h4>
            `;
            
            rec.improvement_steps.forEach(step => {
                html += `
                    <div class="improvement-step">
                        <h4>Step ${step.step}: ${step.title}</h4>
                        <p>${step.description}</p>
                `;
                
                if (step.resources && step.resources.length > 0) {
                    html += `<div class="resources">`;
                    html += `<strong>Resources:</strong> `;
                    html += step.resources.join(', ');
                    html += `</div>`;
                }
                
                if (step.estimated_time) {
                    html += `<p style="margin: 8px 0 0 0; font-size: 0.9em; color: #999;">⏱️ Time: ${step.estimated_time}</p>`;
                }
                
                html += `</div>`;
            });
        }
        
        // Study strategies
        if (rec.study_strategies && rec.study_strategies.length > 0) {
            html += `
                <h4 style="color: #333; margin-top: 20px; margin-bottom: 12px;">💡 Study Strategies</h4>
            `;
            
            rec.study_strategies.forEach(strategy => {
                html += `
                    <div class="strategy-card">
                        <h4>${strategy.strategy}</h4>
                        <p><strong>How it works:</strong> ${strategy.description}</p>
                        <p><strong>Implementation:</strong> ${strategy.implementation}</p>
                    </div>
                `;
            });
        }
        
        // Timeline and metrics
        if (rec.timeline || (rec.success_metrics && rec.success_metrics.length > 0)) {
            html += `
                <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 15px;">
            `;
            
            if (rec.timeline) {
                html += `
                    <p style="margin: 0 0 10px 0;">
                        <strong>⏰ Timeline for Improvement:</strong> ${rec.timeline}
                    </p>
                `;
            }
            
            if (rec.success_metrics && rec.success_metrics.length > 0) {
                html += `
                    <p style="margin: 0 0 5px 0; font-weight: 600;">✅ Success Metrics:</p>
                    <ul style="margin: 0; padding-left: 20px;">
                `;
                rec.success_metrics.forEach(metric => {
                    html += `<li>${metric}</li>`;
                });
                html += `
                    </ul>
                `;
            }
            
            html += `</div>`;
        }
        
        html += `</div>`;
    }
    
    // Related resources
    if (result.related_resources && result.related_resources.length > 0) {
        html += `
            <h3 style="color: #333; margin-top: 25px; margin-bottom: 15px;">🎓 Recommended Resources</h3>
            <div class="resources-grid">
        `;
        
        result.related_resources.forEach(resource => {
            const icon = resource.type === 'quiz' ? '❓' : 
                         resource.type === 'chat' ? '💬' : 
                         resource.type === 'flashcard' ? '🗂️' : '📚';
            
            html += `
                <div class="resource-card ${resource.type}" onclick="redirectToResource('${resource.link}')">
                    <h4>${icon} ${resource.title}</h4>
                    <p>${resource.description || 'Click to access'}</p>
                </div>
            `;
        });
        
        html += `</div>`;
    }
    
    // Feedback section
    html += `
        <div class="feedback-section">
            <p style="margin: 0 0 10px 0;">Was this diagnostic analysis helpful?</p>
            <div class="feedback-buttons">
                <button class="btn-feedback btn-helpful" onclick="submitFeedback(true)">👍 Yes, helpful!</button>
                <button class="btn-feedback btn-not-helpful" onclick="submitFeedback(false)">👎 Not helpful</button>
            </div>
        </div>
    `;
    
    resultsContent.innerHTML = html;
}

/**
 * Get color for classification badge
 */
function getClassificationColor(classification) {
    const colors = {
        'weakness': 'badge-weakness',
        'confusion': 'badge-confusion',
        'progression': 'badge-progression',
        'irrelevant': 'badge-irrelevant'
    };
    return colors[classification] || 'badge-weakness';
}

/**
 * Get color for severity
 */
function getSeverityColor(severity) {
    const colors = {
        'low': '#28a745',
        'medium': '#ffc107',
        'high': '#dc3545'
    };
    return colors[severity] || '#007bff';
}

/**
 * Capitalize first letter
 */
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Display error message
 */
function displayError(message) {
    const resultsContent = document.getElementById('diagnosticsResultContent');
    resultsContent.innerHTML = `
        <div class="error-message">
            <strong>❌ Error:</strong> ${message}
        </div>
    `;
}

function showDiagnosticsLoader() {
    const resultsContent = document.getElementById('diagnosticsResultContent');
    resultsContent.innerHTML = `
        <div class="loading-indicator diagnostics-loader">
            <div class="spinner"></div>
            <p>Analyzing your learning concern...</p>
            <small>This may take a few seconds.</small>
        </div>
    `;
    resultsContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function resetDiagnosticResults() {
    const resultsContent = document.getElementById('diagnosticsResultContent');
    if (!resultsContent) return;
    resultsContent.innerHTML = `
        <p class="results-placeholder">
            Submit your learning concern to see personalized recommendations below.
        </p>
    `;
    updateCharCount();
}

/**
 * Redirect to resource
 */
function redirectToResource(link) {
    if (link.startsWith('http')) {
        window.open(link, '_blank');
    } else {
        window.location.href = link;
    }
}

/**
 * Submit feedback on diagnostic
 */
async function submitFeedback(helpful) {
    try {
        const token = localStorage.getItem('authToken');
        const feedbackText = helpful ? 'Recommendations were helpful' : 'Recommendations were not helpful';
        
        const response = await fetch(`${API_BASE_URL}/api/diagnostic/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                feedback_text: feedbackText,
                helpful: helpful
            })
        });
        
        if (response.ok) {
            alert('Thank you for your feedback! 🙏');
        } else {
            console.error('Failed to submit feedback');
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
    }
}

/**
 * Load diagnostic history
 */
async function loadDiagnosticHistory() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_BASE_URL}/api/diagnostic/history/${currentSessionId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const history = await response.json();
            console.log('Diagnostic history:', history);
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}
