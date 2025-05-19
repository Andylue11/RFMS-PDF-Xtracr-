/**
 * RFMS PDF XTRACR - Main JavaScript
 * Common functionality used across the application
 */

// Configuration
const API_CONFIG = {
    TIMEOUT: 30000, // 30 seconds
    RETRY_ATTEMPTS: 2,
    RETRY_DELAY: 1000 // 1 second
};

// Check API status on page load
document.addEventListener('DOMContentLoaded', function() {
    checkApiStatus();
    
    // Set up other global event listeners
    setupFormValidation();
    setupPdfUpload();
    setupBuilderSearch();
    setupExportToRFMS();
});

/**
 * Fetch with timeout and retry capability
 * @param {string} url - The URL to fetch from
 * @param {Object} options - Fetch options
 * @param {number} retryCount - Current retry count
 * @returns {Promise} - Fetch promise with timeout and retry handling
 */
async function fetchWithRetry(url, options = {}, retryCount = 0) {
    // Add timeout to fetch using AbortController
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        // Clear timeout since request completed
        clearTimeout(timeoutId);
        
        // Handle HTTP errors
        if (!response.ok) {
            // Get error details from response if possible
            let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData && errorData.error) {
                    errorMessage = errorData.error;
                }
            } catch (e) {
                // Unable to parse error response, use default error message
            }
            
            const error = new Error(errorMessage);
            error.status = response.status;
            throw error;
        }
        
        return response;
        
    } catch (error) {
        // Clear timeout if request failed
        clearTimeout(timeoutId);
        
        // Handle request timeout
        if (error.name === 'AbortError') {
            console.error('Request timeout');
            error.message = 'Request timed out. Please try again.';
        }
        
        // Retry logic for specific errors
        if (retryCount < API_CONFIG.RETRY_ATTEMPTS && 
            (error.status >= 500 || error.name === 'AbortError' || error.message.includes('network'))) {
            console.log(`Retrying request (${retryCount + 1}/${API_CONFIG.RETRY_ATTEMPTS})...`);
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_DELAY));
            
            return fetchWithRetry(url, options, retryCount + 1);
        }
        
        throw error;
    }
}

/**
 * Centralized error handler for API requests
 * @param {Error} error - The error object
 * @param {string} operation - The operation being performed
 * @returns {string} - User-friendly error message
 */
function handleApiError(error, operation) {
    console.error(`Error during ${operation}:`, error);
    
    // Default error message
    let userMessage = `An error occurred while ${operation}. Please try again.`;
    
    // Customize message based on error type
    if (error.name === 'AbortError') {
        userMessage = `Request timed out while ${operation}. Please check your connection and try again.`;
    } else if (error.status === 401 || error.status === 403) {
        userMessage = `Authentication failed while ${operation}. Please log in again.`;
    } else if (error.status === 404) {
        userMessage = `Resource not found while ${operation}.`;
    } else if (error.status >= 500) {
        userMessage = `Server error while ${operation}. Please try again later.`;
    } else if (error.message) {
        userMessage = error.message;
    }
    
    // Display error to user
    showNotification(userMessage, 'error');
    
    return userMessage;
}

/**
 * Check RFMS API status and update UI indicator
 */
function checkApiStatus() {
    const indicator = document.getElementById('api-status-indicator');
    const text = document.getElementById('api-status-text');
    
    if (!indicator || !text) return;
    
    // Set initial state
    indicator.classList.remove('bg-green-500', 'bg-red-500');
    indicator.classList.add('bg-gray-400');
    text.textContent = 'RFMS API: Checking...';
    text.classList.remove('text-green-600', 'text-red-600');
    text.classList.add('text-gray-600');
    
    fetchWithRetry('/api/check_status')
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
            handleApiError(error, 'checking API status');
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
 * Format phone number in standard US format (or suitable for AU)
 * @param {string} phoneNumberString - The phone number to format
 * @returns {string} - Formatted phone number
 */
function formatPhoneNumber(phoneNumberString) {
    // Keep only digits
    const cleaned = ('' + phoneNumberString).replace(/\D/g, '');
    
    // Attempt Australian mobile format 04xx xxx xxx
    if (cleaned.length === 10 && cleaned.startsWith('04')) {
        return cleaned.replace(/^(\d{4})(\d{3})(\d{3})$/, '$1 $2 $3');
    }
     // Attempt Australian landline format 0x xxxx xxxx
    if (cleaned.length === 10 && cleaned.startsWith('0') && !cleaned.startsWith('04')) {
         return cleaned.replace(/^(\d{1})(\d{4})(\d{4})$/, '$1 $2 $3');
    }
     // Attempt International format +61 x xxx xxx xxx
    if (cleaned.length === 11 && cleaned.startsWith('61')) {
         return '+' + cleaned.replace(/^(\d{2})(\d{1})(\d{4})(\d{4})$/, '$1 $2 $3 $4');
    }
    
    // If no specific format matches, return cleaned or original
    return phoneNumberString; // Or return cleaned if preferred
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds
 * @returns {HTMLElement} - The notification element
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Remove any existing notification with id 'notification-loading'
    const existingNotification = document.getElementById('notification-loading');
    if (existingNotification) {
        document.body.removeChild(existingNotification);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-md shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    } transition-opacity duration-300 ease-in-out opacity-0 z-50`;
    
    // For loading notifications, add an ID to allow removal later
    if (duration === 0) {
        notification.id = 'notification-loading';
    }
    
    notification.textContent = message;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Fade in
    setTimeout(() => {
        notification.classList.add('opacity-100');
        notification.classList.remove('opacity-0');
    }, 10);
    
    // Remove after duration (if not a persistent notification)
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.remove('opacity-100');
            notification.classList.add('opacity-0');
            
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, duration);
    }
    
    return notification;
}

/**
 * Clear all form fields in the application
 */
function clearFields() {
    // Clear all input fields
    const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="number"], textarea');
    inputs.forEach(input => {
        input.value = '';
    });
    
    // Clear checkboxes
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Hide secondary PO details if visible
    const secondaryPoDetails = document.getElementById('secondary-po-details');
    if (secondaryPoDetails) {
        secondaryPoDetails.classList.add('hidden');
    }
}

/**
 * Setup logic for PDF upload button and file input.
 */
function setupPdfUpload() {
    const uploadButton = document.getElementById('upload-button');
    const pdfInput = document.getElementById('pdf-upload');

    if (!uploadButton || !pdfInput) {
        console.error('PDF upload button or input not found.');
        return;
    }

    uploadButton.addEventListener('click', async () => {
        const file = pdfInput.files[0];
        if (!file) {
            showNotification('Please select a PDF file to upload.', 'warning');
            return;
        }
        
        // Validate file type
        if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
            showNotification('Please select a valid PDF file.', 'error');
            return;
        }

        // Clear all fields before uploading new PDF
        clearFields();

        const formData = new FormData();
        formData.append('pdf_file', file);

        // Show loading indicator/message
        const loadingNotification = showNotification('Uploading and extracting data...', 'info', 0);
        
        // Disable button during upload
        uploadButton.disabled = true;
        uploadButton.textContent = 'Processing...';

        try {
            const response = await fetchWithRetry('/upload-pdf', {
                method: 'POST',
                body: formData
            });

            const extractedData = await response.json();
            console.log('Extracted Data:', extractedData);
            populateShipTo(extractedData);
            
            // Remove loading notification and show success
            if (document.body.contains(loadingNotification)) {
                document.body.removeChild(loadingNotification);
            }
            showNotification('PDF extracted successfully!', 'success');
        } catch (error) {
            handleApiError(error, 'uploading PDF');
        } finally {
            // Reset button state
            uploadButton.disabled = false;
            uploadButton.textContent = 'Clear Data, Upload and Extract';
            
            // Remove loading notification if it still exists
            const persistentNotification = document.getElementById('notification-loading');
            if (persistentNotification) {
                document.body.removeChild(persistentNotification);
            }
        }
    });
}

/**
 * Populate the Ship To and Work Details fields with extracted data.
 * This function is moved from the HTML sketch.
 * @param {object} data - The extracted data object from the backend.
 */
function populateShipTo(data) {
    // Populate Ship To fields
    document.getElementById('ship-to-name').value = data.business_name || data.name || '';
    document.getElementById('ship-to-address1').value = data.address1 || '';
    document.getElementById('ship-to-address2').value = data.address2 || '';
    document.getElementById('ship-to-city').value = data.city || '';
    document.getElementById('ship-to-state').value = data.state || '';
    document.getElementById('ship-to-zip').value = data.zip_code || '';
    document.getElementById('ship-to-country').value = 'USA'; // Default to USA

    // Handle phone numbers
    let phoneNumbers = [];
    if (data.phone) phoneNumbers.push(data.phone);
    if (data.mobile) phoneNumbers.push(data.mobile);
    if (data.home_phone) phoneNumbers.push(data.home_phone);
    if (data.work_phone) phoneNumbers.push(data.work_phone);
    if (data.extra_phones && data.extra_phones.length > 0) {
        const mainPhonesCleaned = [data.phone, data.mobile, data.home_phone, data.work_phone]
            .map(p => (p || '').replace(/\D/g, ''))
            .filter(p => p);
        const uniqueExtraPhones = data.extra_phones.filter(extraPhone => {
            const cleanedExtra = (extraPhone || '').replace(/\D/g, '');
            return cleanedExtra && !mainPhonesCleaned.includes(cleanedExtra);
        });
        phoneNumbers = phoneNumbers.concat(uniqueExtraPhones);
    }

    // Format and populate phone field
    const formattedPhones = phoneNumbers.map(formatPhoneNumber);
    document.getElementById('ship-to-phone').value = formattedPhones.join('\n') || '';

    document.getElementById('ship-to-email').value = data.email || '';

    // Populate Work Details fields from PDF
    document.getElementById('supervisor-name').value = data.supervisor_name || '';
    document.getElementById('supervisor-phone').value = data.supervisor_mobile || '';
    document.getElementById('actual-job-number').value = data.actual_job_number || '';
    document.getElementById('po-number').value = data.po_number || '';
    document.getElementById('description-of-works').value = data.description_of_works || '';
    document.getElementById('dollar-value').value = data.dollar_value || '';

    // Update prefix for secondary PO based on actual job number
    document.getElementById('secondary-po-prefix').textContent = (data.actual_job_number || '') + '-';
}

/**
 * Setup logic for Builder Search functionality
 */
function setupBuilderSearch() {
    const searchButton = document.getElementById('search-builder-button');
    const searchInput = document.getElementById('builder-search-input');

    if (!searchButton || !searchInput) {
        console.error('Builder search button or input not found.');
        return;
    }

    searchButton.addEventListener('click', async () => {
        const searchTerm = searchInput.value.trim();
        if (!searchTerm) {
            showNotification('Please enter a customer ID or builder name to search.', 'warning');
            return;
        }

        // Show loading indicator
        searchButton.disabled = true;
        searchButton.textContent = 'Searching...';
        const loadingNotification = showNotification('Searching for builders...', 'info', 0);

        try {
            console.log('Searching with term:', searchTerm);
            const response = await fetchWithRetry(`/api/customers/search?term=${encodeURIComponent(searchTerm)}`);
            const searchResults = await response.json();
            
            console.log('Search results:', searchResults);
            
            if (Array.isArray(searchResults) && searchResults.length > 0) {
                // Display search results for selection if there are multiple matches
                if (searchResults.length > 1) {
                    displaySearchResults(searchResults);
                    showNotification('Multiple builders found. Please select one.', 'success');
                } else {
                    // If only one result, auto-select it
                    const result = searchResults[0];
                    console.log('Auto-selecting single result:', result);
                    populateSoldTo(result);
                    showNotification('Builder found and details populated.', 'success');
                }
            } else {
                // No results found
                // Do NOT clear sold-to fields automatically; let user clear if needed
                showNotification('No builders found matching your search term. Please try a different search term or contact RFMS support.', 'warning');
            }
        } catch (error) {
            // Do NOT clear sold-to fields on error; let user clear if needed
            handleApiError(error, 'searching for builders');
        } finally {
            // Reset button state
            searchButton.disabled = false;
            searchButton.textContent = 'Retrieve Builders Details';
            
            // Remove loading notification
            const persistentNotification = document.getElementById('notification-loading');
            if (persistentNotification) {
                document.body.removeChild(persistentNotification);
            }
        }
    });

    // Add keyup event listener for Enter key
    searchInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            searchButton.click();
        }
    });
}

/**
 * Display search results in a modal or dropdown for user selection
 * @param {Array} results - The search results from the API
 */
function displaySearchResults(results) {
    // Create or clear the results container
    let resultsContainer = document.getElementById('search-results-container');
    
    if (!resultsContainer) {
        // Create the container if it doesn't exist
        resultsContainer = document.createElement('div');
        resultsContainer.id = 'search-results-container';
        resultsContainer.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';
        document.body.appendChild(resultsContainer);
    } else {
        resultsContainer.innerHTML = '';
    }

    // Create the modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white p-6 rounded-lg shadow-lg max-w-2xl w-full max-h-[80vh] overflow-auto';
    
    // Create the header
    const header = document.createElement('div');
    header.className = 'flex justify-between items-center mb-4';
    
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold text-black';
    title.textContent = 'Search Results';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'text-gray-500 hover:text-gray-700';
    closeButton.textContent = '✕';
    closeButton.onclick = () => {
        resultsContainer.remove();
    };
    
    header.appendChild(title);
    header.appendChild(closeButton);
    
    // Create the results list
    const resultsList = document.createElement('div');
    resultsList.className = 'space-y-2';
    
    // Create search info text
    const searchCount = document.createElement('p');
    searchCount.className = 'text-sm text-gray-600 mb-2';
    searchCount.textContent = `Found ${results.length} result${results.length !== 1 ? 's' : ''}`;
    
    // Add a search input to filter results locally
    const searchFilter = document.createElement('input');
    searchFilter.type = 'text';
    searchFilter.placeholder = 'Filter results...';
    searchFilter.className = 'w-full p-2 border rounded mb-3';
    searchFilter.addEventListener('input', (e) => {
        const filterValue = e.target.value.toLowerCase();
        
        // Show/hide results based on filter
        Array.from(resultsList.children).forEach(item => {
            const itemText = item.textContent.toLowerCase();
            item.style.display = itemText.includes(filterValue) ? 'block' : 'none';
        });
    });
    
    results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'p-3 border rounded hover:bg-gray-100 cursor-pointer text-black';
        
        // Format the display with CustomerID first
        let displayText = '';
        if (result.customer_source_id) {
            displayText = `CustomerID: ${result.customer_source_id} - `;
        }
        displayText += `${result.name || result.first_name + ' ' + result.last_name || 'Unknown Name'}`;
        
        if (result.address) {
            displayText += `\n${result.address}`;
        }
        
        resultItem.textContent = displayText;
        resultItem.onclick = () => {
            populateSoldTo(result);
            resultsContainer.remove();
            showNotification('Customer selected and details populated.', 'success');
        };
        
        resultsList.appendChild(resultItem);
    });
    
    // Assemble the modal
    modalContent.appendChild(header);
    modalContent.appendChild(searchCount);
    modalContent.appendChild(searchFilter);
    modalContent.appendChild(resultsList);
    resultsContainer.appendChild(modalContent);
    
    // Add keyboard support for closing modal with ESC
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            resultsContainer.remove();
            document.removeEventListener('keydown', escHandler);
        }
    });
}

/**
 * Populate the Sold To fields with the selected builder data
 * @param {Object} builderData - The builder data object from the API
 */
function populateSoldTo(builderData) {
    console.log('Populating Sold To with data:', builderData);
    
    // Clear existing data first
    document.getElementById('sold-to-name').value = '';
    document.getElementById('sold-to-address1').value = '';
    document.getElementById('sold-to-address2').value = '';
    document.getElementById('sold-to-city').value = '';
    document.getElementById('sold-to-state').value = '';
    document.getElementById('sold-to-zip').value = '';
    document.getElementById('sold-to-country').value = '';
    document.getElementById('sold-to-phone').value = '';
    document.getElementById('sold-to-email').value = '';
    
    // Set customer ID (hidden field)
    let builderIdField = document.getElementById('sold-to-customer-id');
    if (!builderIdField) {
        builderIdField = document.createElement('input');
        builderIdField.type = 'hidden';
        builderIdField.id = 'sold-to-customer-id';
        document.getElementById('sold-to-fields').appendChild(builderIdField);
    }
    builderIdField.value = builderData.customer_source_id || '';
    
    // Populate the fields with the builder data
    document.getElementById('sold-to-name').value = builderData.business_name || builderData.name || '';
    document.getElementById('sold-to-address1').value = builderData.address1 || '';
    document.getElementById('sold-to-address2').value = builderData.address2 || '';
    document.getElementById('sold-to-city').value = builderData.city || '';
    document.getElementById('sold-to-state').value = builderData.state || '';
    document.getElementById('sold-to-zip').value = builderData.zip_code || '';
    document.getElementById('sold-to-country').value = 'USA'; // Default to USA
    document.getElementById('sold-to-phone').value = builderData.phone || '';
    document.getElementById('sold-to-email').value = builderData.email || '';
    
    // If there's ship-to data, populate it as well
    if (builderData.ship_to) {
        populateShipTo(builderData.ship_to);
    }
    
    // Show success notification
    showNotification('Customer details populated successfully.', 'success');
}

/**
 * Clear all Sold To fields
 */
function clearSoldToFields() {
    document.getElementById('sold-to-name').value = '';
    document.getElementById('sold-to-address1').value = '';
    document.getElementById('sold-to-address2').value = '';
    document.getElementById('sold-to-city').value = '';
    document.getElementById('sold-to-state').value = '';
    document.getElementById('sold-to-zip').value = '';
    document.getElementById('sold-to-country').value = '';
    document.getElementById('sold-to-phone').value = '';
    document.getElementById('sold-to-email').value = '';
    
    // Clear hidden customer ID field if it exists
    const builderIdField = document.getElementById('sold-to-customer-id');
    if (builderIdField) {
        builderIdField.value = '';
    }
}

/**
 * Gather all form data and send to /api/export-to-rfms
 */
function setupExportToRFMS() {
    const exportButton = document.getElementById('export-to-rfms-button');
    if (!exportButton) return;

    exportButton.addEventListener('click', async () => {
        // Validate required fields before submitting
        const soldToName = document.getElementById('sold-to-name').value.trim();
        const soldToCustomerId = document.getElementById('sold-to-customer-id') ? 
            document.getElementById('sold-to-customer-id').value.trim() : '';
        const shipToName = document.getElementById('ship-to-name').value.trim();
        const poNumber = document.getElementById('po-number').value.trim();
        
        const missingFields = [];
        if (!soldToName) missingFields.push('Builder Name');
        if (!soldToCustomerId) missingFields.push('Builder ID');
        if (!shipToName) missingFields.push('Ship To Name');
        if (!poNumber) missingFields.push('PO Number');
        
        if (missingFields.length > 0) {
            showNotification(`Please complete the following required fields: ${missingFields.join(', ')}`, 'warning');
            return;
        }
        
        // Gather Sold To data
        const soldTo = {
            id: soldToCustomerId,
            name: soldToName,
            address1: document.getElementById('sold-to-address1').value,
            address2: document.getElementById('sold-to-address2').value,
            city: document.getElementById('sold-to-city').value,
            state: document.getElementById('sold-to-state').value,
            zip_code: document.getElementById('sold-to-zip').value,
            country: document.getElementById('sold-to-country').value,
            phone: document.getElementById('sold-to-phone').value,
            email: document.getElementById('sold-to-email').value
        };

        // Gather Ship To data
        const shipTo = {
            name: shipToName,
            address1: document.getElementById('ship-to-address1').value,
            address2: document.getElementById('ship-to-address2').value,
            city: document.getElementById('ship-to-city').value,
            state: document.getElementById('ship-to-state').value,
            zip_code: document.getElementById('ship-to-zip').value,
            country: document.getElementById('ship-to-country').value,
            phone: document.getElementById('ship-to-phone').value,
            email: document.getElementById('ship-to-email').value
        };

        // Gather alternate contact info
        const altContact = {
            name: document.getElementById('alternate-contact-name').value,
            phone: document.getElementById('alternate-contact-phone').value,
            phone2: document.getElementById('alternate-contact-phone2').value,
            email: document.getElementById('alternate-contact-email').value
        };

        // Gather Job Details
        let descriptionOfWorks = document.getElementById('description-of-works').value;
        // If alternate contact is present, append to work order notes
        if (altContact.name || altContact.phone || altContact.phone2 || altContact.email) {
            let bestContactStr = `Best Contact: ${altContact.name || ''} ${altContact.phone || ''}`;
            if (altContact.phone2) bestContactStr += `, ${altContact.phone2}`;
            if (altContact.email) bestContactStr += ` (${altContact.email})`;
            descriptionOfWorks += `\n${bestContactStr}`;
        }
        const jobDetails = {
            job_number: document.getElementById('supervisor-phone').value,
            actual_job_number: document.getElementById('actual-job-number').value,
            po_number: poNumber,
            description_of_works: descriptionOfWorks,
            dollar_value: parseFloat(document.getElementById('dollar-value').value) || 0
        };

        // Gather Billing Group info if checked
        const billingGroup = {};
        const billingGroupCheckbox = document.getElementById('billing-group-checkbox');
        if (billingGroupCheckbox && billingGroupCheckbox.checked) {
            billingGroup.is_billing_group = true;
            billingGroup.po_suffix = document.getElementById('secondary-po-suffix').value;
            billingGroup.second_value = parseFloat(document.getElementById('second-po-dollar-value').value) || 0;
        }

        // Build the payload
        const payload = {
            sold_to: soldTo,
            ship_to: shipTo,
            job_details: jobDetails,
            billing_group: billingGroup,
            alternate_contact: altContact,
            alternate_contacts: window._lastExtractedAlternateContacts || []
        };

        // Show loading notification
        const loadingNotification = showNotification('Exporting to RFMS...', 'info', 0);
        exportButton.disabled = true;
        exportButton.textContent = 'Processing...';

        try {
            const response = await fetchWithRetry('/api/export-to-rfms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            showNotification('Exported to RFMS successfully!', 'success');
            console.log('RFMS Export Result:', result);
            
            // Option: Display success details
            if (result.job_id) {
                showNotification(`Job created with ID: ${result.job_id}`, 'success', 5000);
            }
            
        } catch (error) {
            handleApiError(error, 'exporting to RFMS');
        } finally {
            exportButton.disabled = false;
            exportButton.textContent = 'Export to RFMS';
            
            // Remove loading notification
            const persistentNotification = document.getElementById('notification-loading');
            if (persistentNotification) {
                document.body.removeChild(persistentNotification);
            }
        }
    });
}

// Add a button for clearing the builder (if not present in your HTML)
<button id="clear-builder-btn" type="button">Clear Builder</button>

// Add event listener for the clear button
const clearBuilderBtn = document.getElementById('clear-builder-btn');
if (clearBuilderBtn) {
    clearBuilderBtn.addEventListener('click', clearSoldToFields);
} 