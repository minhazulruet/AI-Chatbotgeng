// Global state management
let quizState = {
    quiz: null,
    currentQuestion: 0,
    userAnswers: [], // Array of selected answer indices
    timerInterval: null,
    timeRemaining: 0, // in seconds
    isSubmitted: false
};

/**
 * Validate form inputs and generate quiz
 */
async function generateQuiz() {
    const topic = document.getElementById('topicInput').value.trim();
    const numQuestions = parseInt(document.getElementById('numQuestionsInput').value);
    const difficulty = document.getElementById('difficultySelect').value;

    // Validation
    if (!topic) {
        showError('Please enter a topic');
        return;
    }

    if (topic.length < 2 || topic.length > 200) {
        showError('Topic must be between 2 and 200 characters');
        return;
    }

    if (isNaN(numQuestions) || numQuestions < 1 || numQuestions > 15) {
        showError('Number of questions must be between 1 and 15');
        return;
    }

    // Disable button
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;

    // Show loading screen
    showLoadingScreen();

    try {
        // Call backend API
        const response = await fetch(`${API_BASE_URL}/api/quiz/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({
                topic: topic,
                num_questions: numQuestions,
                difficulty: difficulty
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to generate quiz');
        }

        const data = await response.json();
        
        // Initialize quiz state
        quizState.quiz = data;
        quizState.currentQuestion = 0;
        quizState.userAnswers = new Array(data.num_questions).fill(null);
        quizState.isSubmitted = false;

        // Calculate timer (minutes per question based on difficulty)
        const minutesPerQuestion = {
            'Easy': 2,
            'Medium': 3,
            'Hard': 4
        }[difficulty] || 3;

        quizState.timeRemaining = data.num_questions * minutesPerQuestion * 60; // Convert to seconds

        // Hide loading screen and show quiz
        hideLoadingScreen();
        showQuizScreen();
        displayQuestion();
        updateSubmitButtonState(); // Initialize submit button state
        startTimer();

    } catch (error) {
        console.error('Error generating quiz:', error);
        hideLoadingScreen();
        const errorMsg = getErrorMessage(error);
        showError(errorMsg);
        btn.disabled = false;
    }
}

/**
 * Display current question
 */
function displayQuestion() {
    if (!quizState.quiz || quizState.currentQuestion >= quizState.quiz.questions.length) {
        return;
    }

    const question = quizState.quiz.questions[quizState.currentQuestion];
    const selectedAnswer = quizState.userAnswers[quizState.currentQuestion];
    const total = quizState.quiz.num_questions;
    const current = quizState.currentQuestion + 1;

    // Update progress
    document.getElementById('progressText').textContent = `Question ${current} of ${total}`;
    const progressPercent = (current / total) * 100;
    document.getElementById('progressFill').style.width = progressPercent + '%';

    // Update completion status
    const answered = quizState.userAnswers.filter(a => a !== null && a !== undefined).length;
    const completionEl = document.getElementById('completionStatus');
    if (completionEl) {
        completionEl.textContent = `${answered} / ${total} answered`;
    }

    // Build question HTML
    let optionsHtml = '';
    question.options.forEach((option, index) => {
        const isSelected = selectedAnswer === index;
        const selectedClass = isSelected ? 'selected' : '';
        const label = String.fromCharCode(65 + index); // A, B, C, D
        
        // Don't escape HTML - we want to preserve LaTeX
        optionsHtml += `
            <button class="option-button ${selectedClass}" onclick="selectAnswer(${index})" data-option-index="${index}">
                <span class="option-label">${label}.</span>
                <span class="option-text">${option}</span>
            </button>
        `;
    });

    const questionHtml = `
        <div class="question-container">
            <div class="question-number">Question ${current} of ${total}</div>
            <div class="question-text">${question.question}</div>
            <div class="options-list">
                ${optionsHtml}
            </div>
        </div>
    `;

    document.getElementById('questionArea').innerHTML = questionHtml;

    // Render math after a short delay to ensure DOM is updated
    if (window.MathJax && window.MathJax.typesetPromise) {
        setTimeout(() => {
            MathJax.typesetPromise([document.getElementById('questionArea')])
                .catch(err => console.log('MathJax error:', err));
        }, 50);
    }

    // Update navigation buttons
    updateNavigationButtons();
}

/**
 * Check if all questions are answered
 */
function areAllQuestionsAnswered() {
    return quizState.userAnswers.every(answer => answer !== null && answer !== undefined);
}

/**
 * Get count of unanswered questions
 */
function getUnansweredCount() {
    return quizState.userAnswers.filter(answer => answer === null || answer === undefined).length;
}

/**
 * Show warning message
 */
function showWarning(message) {
    // Create a simple warning div
    const warningDiv = document.createElement('div');
    warningDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff9800;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        font-size: 14px;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    warningDiv.textContent = '⚠️ ' + message;
    document.body.appendChild(warningDiv);
    
    // Remove after 4 seconds
    setTimeout(() => {
        warningDiv.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => warningDiv.remove(), 300);
    }, 4000);
}

/**
 * Select an answer
 */
function selectAnswer(optionIndex) {
    quizState.userAnswers[quizState.currentQuestion] = optionIndex;
    displayQuestion(); // Refresh to show selection
    updateSubmitButtonState(); // Update submit button state
}

/**
 * Update submit button state based on completion
 */
function updateSubmitButtonState() {
    if (!quizState.quiz) return;
    
    const submitBtn = document.getElementById('submitBtn');
    const allAnswered = areAllQuestionsAnswered();
    
    if (allAnswered) {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
        submitBtn.textContent = '✓ Submit Quiz (All Answered)';
    } else {
        const unanswered = getUnansweredCount();
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.5';
        submitBtn.style.cursor = 'not-allowed';
        submitBtn.textContent = `Submit Quiz (${unanswered} unanswered)`;
    }
}

/**
 * Navigate to next question
 */
function nextQuestion() {
    if (quizState.currentQuestion < quizState.quiz.num_questions - 1) {
        quizState.currentQuestion++;
        displayQuestion();
    }
}

/**
 * Navigate to previous question
 */
function previousQuestion() {
    if (quizState.currentQuestion > 0) {
        quizState.currentQuestion--;
        displayQuestion();
    }
}

/**
 * Update navigation button states
 */
function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const total = quizState.quiz.num_questions;
    const current = quizState.currentQuestion;

    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === total - 1;
}

/**
 * Start countdown timer
 */
function startTimer() {
    updateTimerDisplay();

    quizState.timerInterval = setInterval(() => {
        quizState.timeRemaining--;

        if (quizState.timeRemaining <= 0) {
            clearInterval(quizState.timerInterval);
            autoSubmitQuiz();
            return;
        }

        updateTimerDisplay();
    }, 1000);
}

/**
 * Update timer display with color coding
 */
function updateTimerDisplay() {
    const minutes = Math.floor(quizState.timeRemaining / 60);
    const seconds = quizState.timeRemaining % 60;
    const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    const timerEl = document.getElementById('timer');
    timerEl.textContent = timeStr;

    // Color coding based on remaining time
    const totalTime = quizState.quiz.num_questions * getTimerMultiplier() * 60;
    const percentRemaining = (quizState.timeRemaining / totalTime) * 100;

    timerEl.classList.remove('warning', 'critical');
    if (percentRemaining <= 10) {
        timerEl.classList.add('critical');
    } else if (percentRemaining <= 25) {
        timerEl.classList.add('warning');
    }
}

/**
 * Get timer multiplier based on difficulty
 */
function getTimerMultiplier() {
    const difficulty = quizState.quiz.difficulty;
    return {
        'Easy': 2,
        'Medium': 3,
        'Hard': 4
    }[difficulty] || 3;
}

/**
 * Auto-submit when time runs out
 */
function autoSubmitQuiz() {
    showError('Time is up! Submitting your quiz...');
    setTimeout(submitQuiz, 1500);
}

/**
 * Submit quiz for grading
 */
async function submitQuiz() {
    // Validate all questions are answered
    if (!areAllQuestionsAnswered()) {
        const unanswered = getUnansweredCount();
        showWarning(`Please answer all ${unanswered} remaining question(s) before submitting.`);
        return;
    }

    // Clear timer
    if (quizState.timerInterval) {
        clearInterval(quizState.timerInterval);
    }

    const submitBtn = document.getElementById('submitBtn');
    if (!submitBtn) {
        showError('Submit button not found');
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Submitting...';
    submitBtn.style.pointerEvents = 'auto';

    try {
        // Call backend grading endpoint
        const response = await fetch(`${API_BASE_URL}/api/quiz/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({
                quiz_id: quizState.quiz.quiz_id,
                answers: quizState.userAnswers
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to submit quiz');
        }

        const gradeData = await response.json();
        
        // Display results
        displayResults(gradeData);
        quizState.isSubmitted = true;

    } catch (error) {
        console.error('Error submitting quiz:', error);
        const errorMsg = getErrorMessage(error);
        console.error('Extracted error message:', errorMsg);
        showError(errorMsg);
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit Quiz →';
        submitBtn.style.pointerEvents = 'auto';
        updateSubmitButtonState();
    }
}

/**
 * Display results screen
 */
function displayResults(gradeData) {
    // Update score display
    const percent = Math.round(gradeData.score);
    document.getElementById('scoreDisplay').textContent = percent + '%';

    // Update grade badge with appropriate color
    const gradeBadge = document.getElementById('gradeBadge');
    gradeBadge.textContent = gradeData.grade;
    gradeBadge.classList.remove('excellent', 'good', 'fair', 'poor');
    
    if (gradeData.grade === 'A') {
        gradeBadge.classList.add('excellent');
    } else if (gradeData.grade === 'B' || gradeData.grade === 'C') {
        gradeBadge.classList.add(gradeData.grade === 'B' ? 'good' : 'fair');
    } else {
        gradeBadge.classList.add('poor');
    }

    // Update summary
    document.getElementById('correctCount').textContent = gradeData.correct;
    document.getElementById('totalCount').textContent = gradeData.total;
    document.getElementById('accuracyDisplay').textContent = percent + '%';
    document.getElementById('topicDisplay').textContent = gradeData.topic;

    // Build comprehensive review with full questions and options
    let reviewHtml = '';
    gradeData.breakdown.forEach((item, index) => {
        const isCorrect = item.correct;
        const correctClass = isCorrect ? 'correct' : 'incorrect';
        const status = isCorrect ? '✅' : '❌';
        
        const question = quizState.quiz.questions[index];
        const questionText = question.question;
        const options = question.options;
        const correctAnswerIndex = item.correct_answer;
        const userAnswerIndex = quizState.userAnswers[index];
        
        const correctAnswerOption = String.fromCharCode(65 + correctAnswerIndex); // A, B, C, D
        const correctAnswerText = options[correctAnswerIndex];
        
        const userAnswerOption = userAnswerIndex !== null ? String.fromCharCode(65 + userAnswerIndex) : '?';
        const userAnswerText = userAnswerIndex !== null ? options[userAnswerIndex] : 'Not answered';
        
        // Build options list
        let optionsHtml = '';
        options.forEach((option, optIdx) => {
            const optionLetter = String.fromCharCode(65 + optIdx);
            optionsHtml += `<div style="margin: 5px 0; padding-left: 15px;">• <strong>${optionLetter}.</strong> ${option}</div>`;
        });

        reviewHtml += `
            <div class="review-item ${correctClass}">
                <div style="margin-bottom: 12px; padding: 10px; background: #f5f5f5; border-radius: 4px; line-height: 1.5;">
                    <strong>Question ${index + 1}:</strong><br/>
                    ${questionText}
                </div>
                
                <div style="margin-bottom: 12px;">
                    <strong>Options:</strong>
                    ${optionsHtml}
                </div>
                
                <div style="margin-bottom: 8px; padding: 8px; background: #e3f2fd; border-left: 3px solid #2196f3; border-radius: 2px;">
                    <strong>Your answer:</strong> ${userAnswerOption}. ${userAnswerText}
                </div>
                
                ${!isCorrect ? `
                <div style="margin-bottom: 8px; padding: 8px; background: #e8f5e9; border-left: 3px solid #4caf50; border-radius: 2px;">
                    <strong>Correct answer:</strong> ${correctAnswerOption}. ${correctAnswerText}
                </div>
                ` : ''}
            </div>
        `;
    });

    document.getElementById('reviewList').innerHTML = reviewHtml;

    // Switch to results screen
    showResultsScreen_Screen();
}

/**
 * UI Screen switching functions
 */
function showFormScreen() {
    document.getElementById('formScreen').classList.add('active');
    document.getElementById('loadingScreen').classList.remove('active');
    document.getElementById('quizScreen').classList.remove('active');
    document.getElementById('resultsScreen').classList.remove('active');
}

function showLoadingScreen() {
    document.getElementById('formScreen').classList.remove('active');
    document.getElementById('loadingScreen').classList.add('active');
    document.getElementById('quizScreen').classList.remove('active');
    document.getElementById('resultsScreen').classList.remove('active');
}

function hideLoadingScreen() {
    document.getElementById('loadingScreen').classList.remove('active');
}

function showQuizScreen() {
    document.getElementById('formScreen').classList.remove('active');
    document.getElementById('loadingScreen').classList.remove('active');
    document.getElementById('quizScreen').classList.add('active');
    document.getElementById('resultsScreen').classList.remove('active');
}

function showResultsScreen_Screen() {
    document.getElementById('formScreen').classList.remove('active');
    document.getElementById('loadingScreen').classList.remove('active');
    document.getElementById('quizScreen').classList.remove('active');
    document.getElementById('resultsScreen').classList.add('active');
}

/**
 * Restart quiz - go back to form
 */
function restartQuiz() {
    // Clear state
    quizState = {
        quiz: null,
        currentQuestion: 0,
        userAnswers: [],
        timerInterval: null,
        timeRemaining: 0,
        isSubmitted: false
    };

    // Clear form
    document.getElementById('topicInput').value = '';
    document.getElementById('numQuestionsInput').value = '5';
    document.getElementById('difficultySelect').value = 'Medium';
    
    // Reset generate button state
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = false;
    generateBtn.innerHTML = 'Generate Quiz ✨';
    generateBtn.style.pointerEvents = 'auto';
    generateBtn.style.opacity = '1';

    // Switch back to form screen
    showFormScreen();

    // Focus on input
    setTimeout(() => {
        document.getElementById('topicInput').focus();
    }, 100);
}

/**
 * Go home
 */
function goHome() {
    window.location.href = 'index.html';
}

/**
 * Show error message (using simple alert for now, could be improved with toast)
 */
/**
 * Extract readable error message from various error formats
 */
function getErrorMessage(error) {
    if (!error) return 'An unknown error occurred';
    
    // If it's a string, return it
    if (typeof error === 'string') {
        return error;
    }
    
    // If it has a message property, use that
    if (error.message && typeof error.message === 'string') {
        return error.message;
    }
    
    // If it's an array (validation errors), join them
    if (Array.isArray(error)) {
        return error
            .map(e => {
                if (typeof e === 'string') return e;
                if (e && e.message) return e.message;
                if (e && typeof e === 'object') return JSON.stringify(e);
                return String(e);
            })
            .filter(e => e && e !== '[object Object]')
            .join(', ') || 'An error occurred';
    }
    
    // Try to stringify it (but avoid [object Object])
    try {
        const str = JSON.stringify(error);
        if (str === '{}' || str.includes('[object Object]')) {
            return String(error);
        }
        return str;
    } catch (e) {
        return String(error);
    }
}

/**
 * Show error message to user
 */
function showError(message) {
    const msg = getErrorMessage(message);
    alert('Error: ' + msg);
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
 * Get auth token from localStorage
 */
function getToken() {
    return localStorage.getItem('authToken') || '';
}

/**
 * Page load initialization
 */
document.addEventListener('DOMContentLoaded', function() {
    // Ensure form screen is visible on load
    showFormScreen();

    // Ensure button is enabled and clickable
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.style.pointerEvents = 'auto';
        generateBtn.style.opacity = '1';
    }

    // Set input constraints
    const numQuestionsInput = document.getElementById('numQuestionsInput');
    numQuestionsInput.addEventListener('change', function() {
        let value = parseInt(this.value);
        if (isNaN(value) || value < 1) value = 1;
        if (value > 15) value = 15;
        this.value = value;
    });

    // Focus on topic input on page load
    document.getElementById('topicInput').focus();
});

/**
 * Handle page unload - clear timer
 */
window.addEventListener('beforeunload', function() {
    if (quizState.timerInterval) {
        clearInterval(quizState.timerInterval);
    }
});
