/**
 * RFMS PDF XTRACR - Main JavaScript
 * Common functionality used across the application
 */

// Check API status on page load
document.addEventListener('DOMContentLoaded', function() {
    checkApiStatus();
    
    // Set up other global event listeners
    setupFormValidation();
});

/**
 * Check RFMS API status and update UI indicator
 */
function checkApiStatus() {
    const indicator = document.getElementById('api-status-indicator');
    const text = document.getElementById('api-status-text');
    
    if (!indicator || !text) return;
    
    fetch('/api/check_status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'online') {
                indicator.classList.remove('bg-gray-400', 'bg-red-500');
                indicator.classList.add('bg-green-500');
                text.textContent = 'RFMS API: Online';
                text.classList.remove('text-gray-600', 'text-red-600');
                text.classList.add('text-green-600');
            } else {
                indicator.classList.remove('bg-gray-400', 'bg-green-500');
                indicator.classList.add('bg-red-500');
                text.textContent = 'RFMS API: Offline';
                text.classList.remove('text-gray-600', 'text-green-600');
                text.classList.add('text-red-600');
            }
        })
        .catch(error => {
            console.error('Error checking API status:', error);
            indicator.classList.remove('bg-gray-400', 'bg-green-500');
            indicator.classList.add('bg-red-500');
            text.textContent = 'RFMS API: Error';
            text.classList.remove('text-gray-600', 'text-green-600');
            text.classList.add('text-red-600');
        });
}

/**
 * Set up form validation for common forms
 */
function setupFormValidation() {
    // Get all forms with the 'needs-validation' class
    const forms = document.querySelectorAll('form.needs-validation');
    
    // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Format currency value as USD
 * @param {number} value - The value to format
 * @returns {string} - Formatted currency string
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

/**
 * Format phone number in standard US format
 * @param {string} phoneNumberString - The phone number to format
 * @returns {string} - Formatted phone number
 */
function formatPhoneNumber(phoneNumberString) {
    const cleaned = ('' + phoneNumberString).replace(/\D/g, '');
    const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    
    if (match) {
        return '(' + match[1] + ') ' + match[2] + '-' + match[3];
    }
    
    return phoneNumberString;
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-md shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    } transition-opacity duration-300 ease-in-out`;
    notification.textContent = message;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Fade in
    setTimeout(() => {
        notification.classList.add('opacity-100');
    }, 10);
    
    // Remove after duration
    setTimeout(() => {
        notification.classList.remove('opacity-100');
        notification.classList.add('opacity-0');
        
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, duration);
} 