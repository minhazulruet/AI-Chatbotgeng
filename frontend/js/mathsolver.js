// Math Solver Frontend Logic

/**
 * Preprocess text to normalize LaTeX math delimiters
 * Converts: (( ... )) -> $$ ... $$
 * This ensures all math notation is recognized by MathJax
 */
function preprocessMathDelimiters(text) {
    // Convert double parentheses (( ... )) to display math $$ ... $$
    text = text.replace(/\(\(\s*/g, '$$');
    text = text.replace(/\s*\)\)/g, '$$');
    return text;
}

// Image upload handler
document.getElementById('imageUploadBox').addEventListener('click', () => {
    document.getElementById('imageInput').click();
});

document.getElementById('imageInput').addEventListener('change', handleImageUpload);

// Drag and drop support
const uploadBox = document.getElementById('imageUploadBox');

uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('active');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('active');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('active');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        document.getElementById('imageInput').files = files;
        handleImageUpload();
    }
});

function handleImageUpload() {
    const input = document.getElementById('imageInput');
    const preview = document.getElementById('imagePreview');
    const file = input.files[0];

    if (file) {
        // Validate file size (5MB)
        if (file.size > 5 * 1024 * 1024) {
            showError('File size must be less than 5MB');
            return;
        }

        // Validate file type
        if (!file.type.startsWith('image/')) {
            showError('Please upload a valid image file');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            preview.style.display = 'block';
            clearError();
        };
        reader.readAsDataURL(file);
    }
}

// Solve button handler
document.getElementById('solveBtn').addEventListener('click', async () => {
    const imageInput = document.getElementById('imageInput');
    const textInput = document.getElementById('textInput').value.trim();
    const solveBtn = document.getElementById('solveBtn');

    // Validation
    if (!imageInput.files.length) {
        showError('Please upload an image');
        return;
    }

    // Show loading state
    showLoading();
    solveBtn.disabled = true;

    try {
        // Read image as base64
        const file = imageInput.files[0];
        const base64Image = await fileToBase64(file);

        // Call backend API
        const response = await makeRequest('/api/mathsolver/solve', 'POST', {
            image: base64Image,
            image_type: file.type,
            text: textInput
        }, localStorage.getItem('token'));

        if (response.error) {
            showError(response.error);
        } else if (response.solution) {
            displaySolution(response.solution);
        } else {
            showError('No solution received from server');
        }
    } catch (error) {
        console.error('Error solving problem:', error);
        showError('Failed to solve the problem. Please try again.');
    } finally {
        solveBtn.disabled = false;
        hideLoading();
    }
});

// Clear button handler
document.getElementById('clearBtn').addEventListener('click', () => {
    document.getElementById('imageInput').value = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('textInput').value = '';
    document.getElementById('solutionContent').style.display = 'none';
    document.getElementById('emptyState').style.display = 'block';
    clearError();
});

// Helper functions
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = (error) => reject(error);
    });
}

function displaySolution(solution) {
    const solutionContent = document.getElementById('solutionContent');
    const solutionText = document.getElementById('solutionText');
    const emptyState = document.getElementById('emptyState');

    // Preprocess LaTeX delimiters
    const processedSolution = preprocessMathDelimiters(solution);

    // Use marked for markdown rendering if available
    if (window.marked) {
        solutionText.innerHTML = marked.parse(processedSolution);
    } else {
        solutionText.innerHTML = `<div>${processedSolution.replace(/\n/g, '<br>')}</div>`;
    }

    // Trigger MathJax rendering
    if (window.MathJax) {
        MathJax.typesetPromise([solutionText]).catch(err => console.log('MathJax error:', err));
    }

    solutionContent.style.display = 'block';
    emptyState.style.display = 'none';
    document.querySelector('.solution-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showLoading() {
    document.getElementById('loadingMessage').style.display = 'block';
    document.getElementById('solutionContent').style.display = 'none';
    document.getElementById('emptyState').style.display = 'none';
    document.querySelector('.solution-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideLoading() {
    document.getElementById('loadingMessage').style.display = 'none';
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = '❌ ' + message;
    errorMessage.style.display = 'block';
}

function clearError() {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.style.display = 'none';
}
