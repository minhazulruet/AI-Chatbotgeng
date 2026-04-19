// Global state for flashcard system
let flashcardState = {
    deck: null,
    currentCard: 0,
    isFlipped: false
};

/**
 * Validate form inputs and generate flashcards
 */
async function generateFlashcards() {
    const topic = document.getElementById('topicInput').value.trim();
    const numCards = parseInt(document.getElementById('numCardsInput').value);

    // Validation
    if (!topic) {
        showWarning('Please enter a topic');
        return;
    }

    if (topic.length < 2 || topic.length > 200) {
        showWarning('Topic must be between 2 and 200 characters');
        return;
    }

    if (isNaN(numCards) || numCards < 2 || numCards > 20) {
        showWarning('Number of cards must be between 2 and 20');
        return;
    }

    // Disable button
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;

    // Show loading screen
    showLoadingScreen();

    try {
        // Call backend API
        const response = await fetch(`${API_BASE_URL}/api/flashcard/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({
                topic: topic,
                num_cards: numCards
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to generate flashcards');
        }

        const data = await response.json();
        
        // Initialize flashcard state
        flashcardState.deck = data;
        flashcardState.currentCard = 0;
        flashcardState.isFlipped = false;

        // Hide loading screen and show flashcard
        hideLoadingScreen();
        showFlashcardScreen();
        displayFlashcard();

    } catch (error) {
        console.error('Error generating flashcards:', error);
        hideLoadingScreen();
        const errorMsg = getErrorMessage(error);
        showWarning(errorMsg);
    } finally {
        btn.disabled = false;
    }
}

/**
 * Display current flashcard (initially showing only term)
 */
function displayFlashcard() {
    if (!flashcardState.deck || flashcardState.currentCard >= flashcardState.deck.cards.length) {
        return;
    }

    const card = flashcardState.deck.cards[flashcardState.currentCard];
    
    // Update progress
    const current = flashcardState.currentCard + 1;
    const total = flashcardState.deck.num_cards;
    document.getElementById('progressText').textContent = `Card ${current} of ${total}`;

    // Update card display
    document.getElementById('categoryLabel').textContent = card.category.toUpperCase();
    document.getElementById('termDisplay').textContent = card.term;
    document.getElementById('definitionDisplay').textContent = card.definition;
    document.getElementById('exampleDisplay').textContent = card.example;

    // Hide definition and example by default (reset flip state)
    flashcardState.isFlipped = false;
    document.getElementById('definitionDisplay').classList.remove('visible');
    document.getElementById('exampleSection').classList.remove('visible');

    // Update button states
    document.getElementById('prevBtn').disabled = current === 1;
    document.getElementById('nextBtn').disabled = current === total;

    // Trigger MathJax to render any LaTeX
    if (window.MathJax) {
        MathJax.typesetPromise([document.getElementById('termDisplay'), document.getElementById('definitionDisplay')])
            .catch(err => console.log('MathJax error:', err));
    }
}

/**
 * Toggle card flip - reveals definition and example
 */
function toggleFlip() {
    const definitionDisplay = document.getElementById('definitionDisplay');
    const exampleSection = document.getElementById('exampleSection');
    const display = document.getElementById('flashcardDisplay');

    flashcardState.isFlipped = !flashcardState.isFlipped;

    if (flashcardState.isFlipped) {
        definitionDisplay.classList.add('visible');
        exampleSection.classList.add('visible');
        display.classList.add('flipped');
    } else {
        definitionDisplay.classList.remove('visible');
        exampleSection.classList.remove('visible');
        display.classList.remove('flipped');
    }
}

/**
 * Navigate to next card
 */
function nextCard() {
    if (flashcardState.currentCard < flashcardState.deck.cards.length - 1) {
        flashcardState.currentCard++;
        displayFlashcard();
    }
}

/**
 * Navigate to previous card
 */
function previousCard() {
    if (flashcardState.currentCard > 0) {
        flashcardState.currentCard--;
        displayFlashcard();
    }
}

/**
 * Show summary of all cards
 */
function displayAllCards() {
    if (!flashcardState.deck) return;

    const cardsList = document.getElementById('cardsList');
    let html = '';

    flashcardState.deck.cards.forEach((card, index) => {
        html += `
            <div class="summary-card">
                <div class="summary-card-term">${index + 1}. ${card.term}</div>
                <div class="summary-card-def"><strong>Definition:</strong> ${card.definition}</div>
                <div class="summary-card-example"><strong>Example:</strong> ${card.example}</div>
            </div>
        `;
    });

    cardsList.innerHTML = html;

    // Update topic
    document.getElementById('summaryTopic').textContent = `${flashcardState.deck.topic} (${flashcardState.deck.num_cards} cards)`;
}

/**
 * UI Screen switching functions
 */
function showFormScreen() {
    document.getElementById('formScreen').classList.add('active');
    document.getElementById('loadingScreen').classList.remove('active');
    document.getElementById('flashcardScreen').classList.remove('active');
    document.getElementById('summaryScreen').classList.remove('active');
}

function showLoadingScreen() {
    document.getElementById('formScreen').classList.add('active');
    document.getElementById('loadingScreen').classList.add('active');
    document.getElementById('flashcardScreen').classList.remove('active');
    document.getElementById('summaryScreen').classList.remove('active');
    document.getElementById('loadingScreen').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideLoadingScreen() {
    document.getElementById('loadingScreen').classList.remove('active');
}

function showFlashcardScreen() {
    document.getElementById('formScreen').classList.add('active');
    document.getElementById('loadingScreen').classList.remove('active');
    document.getElementById('flashcardScreen').classList.add('active');
    document.getElementById('summaryScreen').classList.remove('active');
    document.getElementById('flashcardScreen').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showSummaryScreen() {
    displayAllCards();
    document.getElementById('formScreen').classList.add('active');
    document.getElementById('loadingScreen').classList.remove('active');
    document.getElementById('flashcardScreen').classList.remove('active');
    document.getElementById('summaryScreen').classList.add('active');
    document.getElementById('summaryScreen').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Restart - go back to form
 */
function restartFlashcards() {
    // Clear state
    flashcardState = {
        deck: null,
        currentCard: 0,
        exampleRevealed: false
    };

    // Clear form
    document.getElementById('topicInput').value = '';
    document.getElementById('numCardsInput').value = '5';
    
    // Reset button state
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = false;
    generateBtn.innerHTML = 'Generate Flashcards ✨';

    // Switch back to form screen
    showFormScreen();

    // Focus on input
    setTimeout(() => {
        document.getElementById('topicInput').focus();
    }, 100);
}

/**
 * Extract readable error message from various error formats
 */
function getErrorMessage(error) {
    if (!error) return 'An unknown error occurred';
    
    if (typeof error === 'string') {
        return error;
    }
    
    if (error.message && typeof error.message === 'string') {
        return error.message;
    }
    
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
 * Get auth token from localStorage
 */
function getToken() {
    return localStorage.getItem('authToken') || '';
}

/**
 * Show warning message to user
 */
function showWarning(message) {
    const msg = getErrorMessage(message);
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

/**
 * Page load initialization
 */
document.addEventListener('DOMContentLoaded', function() {
    // Ensure form screen is visible on load
    showFormScreen();

    // Ensure button is enabled
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.style.pointerEvents = 'auto';
        generateBtn.style.opacity = '1';
    }

    // Display user info in navbar
    displayUserInfo();

    // Focus on topic input
    document.getElementById('topicInput').focus();
});

/**
 * Display user information in navbar
 */
function displayUserInfo() {
    const userInfo = getUserInfo();
    
    if (userInfo) {
        const userWelcome = document.getElementById('userWelcome');
        if (userWelcome) {
            userWelcome.textContent = `Welcome, ${userInfo.name || userInfo.email}!`;
        }
    }
}

/**
 * Handle page unload
 */
window.addEventListener('beforeunload', function() {
    // Cleanup if needed
});
