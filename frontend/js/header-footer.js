// Common Header and Footer for all pages

function initializeHeaderFooter() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const isAuthPage = currentPage === 'login.html' || currentPage === 'signup.html';

    const navLinks = isAuthPage
        ? `
            <li><a href="index.html">Home</a></li>
            <li><a href="login.html">Login</a></li>
            <li><a href="signup.html">Sign Up</a></li>
          `
        : `
            <li><a href="index.html">Home</a></li>
            <li><a href="chat.html">Chat</a></li>
            <li><a href="quiz.html">Quiz</a></li>
            <li><a href="flashcards.html">Flashcards</a></li>
            <li><a href="mathsolver.html">Math Solver</a></li>
            <li><a href="diagnostics.html">Diagnostics</a></li>
          `;

    const userActions = isAuthPage
        ? ``
        : `<button class="logout-btn" onclick="handleLogout()">Logout</button>`;

    // Inject header
    const headerHTML = `
    <nav class="navbar">
        <div class="navbar-brand">
            <a href="index.html">Khandakar's Digital Assistance</a>
        </div>
        <ul class="nav-links">
            ${navLinks}
        </ul>
        <div class="user-info" id="user-info-container">
            ${userActions}
        </div>
    </nav>
    `;

    // Inject footer
    const footerHTML = `
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h3>About</h3>
                <p><strong>GENG 300 Assistant</strong></p>
                <p>An intelligent chatbot for Applied Numerical Methods with MATLAB® powered by cutting-edge AI technology.</p>
                <p style="font-size: 0.9em; margin-top: 10px;">Based on: <strong>Applied Numerical Methods with MATLAB®</strong> by Steven C. Chapra (3rd Edition)</p>
            </div>
            <div class="footer-section">
                <h3>Developer</h3>
                <p>Developed and maintained by<br>
                <strong><a href="https://scholar.google.com/citations?user=VC8FmyEAAAAJ&hl=en" target="_blank">Dr. Amith Khandakar Md Abdullah</a></strong></p>
            </div>
            <div class="footer-section">
                <h3>Support</h3>
                <p>If you encounter any issues, please contact us at:<br>
                <strong><a href="mailto:aidevteam99@gmail.com">aidevteam99@gmail.com</a></strong></p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2024-2026 GENG 300 Assistant. All rights reserved.</p>
        </div>
    </footer>
    `;

    // Insert header at the beginning of body
    const headerElement = document.createElement('div');
    headerElement.innerHTML = headerHTML;
    document.body.insertBefore(headerElement, document.body.firstChild);

    // Insert footer at the end of body
    const footerElement = document.createElement('div');
    footerElement.innerHTML = footerHTML;
    document.body.appendChild(footerElement);

    // Mark active navigation link
    markActiveNav();
}

function markActiveNav() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage || (currentPage === '' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
}

// Call this when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeHeaderFooter);
} else {
    initializeHeaderFooter();
}
