// DOM Elements
const shortenForm = document.getElementById('shorten-form');
const originalUrlInput = document.getElementById('original-url');
const customCodeInput = document.getElementById('custom-code');
const resultSection = document.getElementById('result-section');
const shortUrlDisplay = document.getElementById('short-url-display');
const originalUrlDisplay = document.getElementById('original-url-display');
const urlsContainer = document.getElementById('urls-container');
const loading = document.getElementById('loading');
const noUrls = document.getElementById('no-urls');

// Load URLs on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUrls();
});

// Form submission
shortenForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await shortenUrl();
});

// Shorten URL
async function shortenUrl() {
    const originalUrl = originalUrlInput.value.trim();
    const customCode = customCodeInput.value.trim();
    
    if (!originalUrl) {
        showToast('Please enter a URL', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/urls', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: originalUrl,
                custom_code: customCode
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show result
            shortUrlDisplay.value = data.short_url;
            originalUrlDisplay.textContent = data.original_url;
            resultSection.style.display = 'block';
            
            // Clear form
            shortenForm.reset();
            
            // Reload URLs list
            await loadUrls();
            
            showToast('URL shortened successfully!');
        } else {
            showToast(data.error || 'Failed to shorten URL', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    }
}

// Load all URLs
async function loadUrls() {
    loading.style.display = 'block';
    urlsContainer.innerHTML = '';
    noUrls.style.display = 'none';
    
    try {
        const response = await fetch('/api/urls');
        const data = await response.json();
        
        if (data.success && data.urls.length > 0) {
            displayUrls(data.urls);
        } else {
            noUrls.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading URLs:', error);
        showToast('Error loading URLs', 'error');
    } finally {
        loading.style.display = 'none';
    }
}

// Display URLs
function displayUrls(urls) {
    urlsContainer.innerHTML = '';
    
    urls.forEach(url => {
        const card = createUrlCard(url);
        urlsContainer.appendChild(card);
    });
}

// Create URL Card
function createUrlCard(url) {
    const card = document.createElement('div');
    card.className = 'url-card';
    
    const createdDate = new Date(url.created_at).toLocaleDateString();
    
    card.innerHTML = `
        <div class="url-header">
            <div class="url-short">
                <a href="${escapeHtml(url.short_url)}" target="_blank" class="url-short-link">
                    ${escapeHtml(url.short_url)}
                </a>
            </div>
            <div class="url-actions">
                <button class="url-btn copy" onclick="copyUrl('${escapeHtml(url.short_url)}')" title="Copy">
                    📋
                </button>
                <button class="url-btn delete" onclick="deleteUrl(${url.id})" title="Delete">
                    🗑️
                </button>
            </div>
        </div>
        
        <div class="url-original">
            <strong>Original:</strong> ${escapeHtml(url.original_url)}
        </div>
        
        <div class="url-meta">
            <span class="url-clicks">👆 ${url.clicks} clicks</span>
            <span>📅 Created: ${createdDate}</span>
            <span>🔑 Code: ${escapeHtml(url.short_code)}</span>
        </div>
    `;
    
    return card;
}

// Copy to Clipboard (main result)
function copyToClipboard() {
    shortUrlDisplay.select();
    document.execCommand('copy');
    showToast('Copied to clipboard!');
}

// Copy URL (from list)
function copyUrl(url) {
    const textarea = document.createElement('textarea');
    textarea.value = url;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('Copied to clipboard!');
}

// Delete URL
async function deleteUrl(urlId) {
    if (!confirm('Are you sure you want to delete this shortened URL?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/urls/${urlId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('URL deleted successfully!');
            await loadUrls();
        } else {
            showToast('Failed to delete URL', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    }
}

// Show Toast Message
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = 'success-toast';
    toast.textContent = message;
    
    if (type === 'error') {
        toast.style.background = '#f56565';
    }
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}