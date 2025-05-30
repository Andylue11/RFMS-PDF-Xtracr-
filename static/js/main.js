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
    // loadSalespersonValues(); // Commented out - using hardcoded values in HTML
    
    // Set up other global event listeners
    setupFormValidation();
    setupPdfUpload();
    setupBuilderSearch();
    setupAddCustomerAndCreateJob();
    setupClearSoldToButton();
});

/**
 * Set up Clear SOLD To button functionality
 */
function setupClearSoldToButton() {
    const clearSoldToBtn = document.getElementById('clear-sold-to-btn');
    if (clearSoldToBtn) {
        clearSoldToBtn.addEventListener('click', function() {
            // Clear search field
            const searchField = document.getElementById('sold-to-search');
            if (searchField) searchField.value = '';
            
            // Clear search results
            const resultsDiv = document.getElementById('sold-to-results');
            if (resultsDiv) resultsDiv.innerHTML = '';
            
            // Clear visible fields
            const visibleFields = [
                'sold-to-rfms-id',
                'sold-to-name',
                'sold-to-address1',
                'sold-to-address2',
                'sold-to-city',
                'sold-to-zip'
            ];
            
            visibleFields.forEach(id => {
                const field = document.getElementById(id);
                if (field) field.value = '';
            });
            
            // Clear hidden fields too
            const hiddenFields = [
                'sold-to-business-name',
                'sold-to-state',
                'sold-to-phone1',
                'sold-to-phone2',
                'sold-to-email'
            ];
            
            hiddenFields.forEach(id => {
                const field = document.getElementById(id);
                if (field) field.value = '';
            });
            
            // Reset salesperson dropdown to default (ZORAN VEKIC)
            const salespersonDropdown = document.getElementById('sold-to-salesperson');
            if (salespersonDropdown) {
                // Find the ZORAN VEKIC option and select it
                for (let i = 0; i < salespersonDropdown.options.length; i++) {
                    if (salespersonDropdown.options[i].value === 'ZORAN VEKIC') {
                        salespersonDropdown.selectedIndex = i;
                        break;
                    }
                }
            }
            
            console.log('Sold To fields cleared');
        });
    }
}

/**
 * Load salesperson values for the dropdown
 */
async function loadSalespersonValues() {
    const salespersonSelect = document.getElementById('sold-to-salesperson');
    
    if (!salespersonSelect) {
        console.error('Salesperson dropdown not found.');
        return;
    }
    
    // Skip if we already have options (hardcoded in HTML)
    if (salespersonSelect.options.length > 1) {
        console.log('Salesperson values already loaded from HTML');
        return;
    }
    
    try {
        const response = await fetchWithRetry('/api/salesperson_values');
        const salespersonValues = await response.json();
        
        if (Array.isArray(salespersonValues)) {
            // Clear existing options except the first placeholder
            salespersonSelect.innerHTML = '<option value="">Select Salesperson</option>';
            
            // Add new options
            salespersonValues.forEach(value => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                salespersonSelect.appendChild(option);
            });
            
            console.log('Loaded salesperson values:', salespersonValues);
        }
    } catch (error) {
        console.error('Error loading salesperson values:', error);
        // Add default value as fallback
        const option = document.createElement('option');
        option.value = 'ZORAN VEKIC';
        option.textContent = 'ZORAN VEKIC';
        salespersonSelect.appendChild(option);
    }
}

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
 * Set up PDF upload functionality
 */
function setupPdfUpload() {
    const uploadBtn = document.getElementById('upload-pdf-btn');
    const fileInput = document.getElementById('pdf-file-input');
    const clearDataBtn = document.getElementById('clear-data-btn');

    if (!uploadBtn || !fileInput) {
        console.error('PDF upload elements not found');
        return;
    }

    // Upload button click handler
    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change handler
    fileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('pdf_file', file);
        
        try {
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
            
            const response = await fetch('/upload-pdf', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const extractedData = await response.json();
            console.log('Extracted data:', extractedData);
            
            // Populate the ship-to fields with extracted data
                populateShipTo(extractedData);
            
            showNotification('PDF uploaded and data extracted successfully!', 'success');
            
        } catch (error) {
            console.error('Upload error:', error);
            showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload PDF';
            fileInput.value = ''; // Clear file input
        }
    });
    
    // Clear data button handler
    if (clearDataBtn) {
        clearDataBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all data? This will not affect the Sold To (Builder) information.')) {
                // Clear work order fields
                const workOrderFields = [
                    'po-number',
                    'dollar-value',
                    'description-of-works',
                    'commencement-date',
                    'completion-date',
                    'supervisor-name',
                    'supervisor-phone'
                ];
                
                workOrderFields.forEach(id => {
                    const field = document.getElementById(id);
                    if (field) field.value = '';
                });
                
                // Clear ship-to fields
                const shipToFields = [
                    'ship-to-first-name',
                    'ship-to-last-name',
                    'ship-to-name',
                    'ship-to-address1',
                    'ship-to-address2',
                    'ship-to-city',
                    'ship-to-state',
                    'ship-to-zip',
                    'ship-to-county',
                    'ship-to-phone1',
                    'ship-to-phone2',
                    'ship-to-email',
                    'pdf-phone1',
                    'pdf-phone2'
                ];
                
                shipToFields.forEach(id => {
                    const field = document.getElementById(id);
                    if (field) field.value = '';
                });
                
                // Clear best contacts
                clearBestContacts();
                
                // Clear alternate contacts
                const altContactsDiv = document.getElementById('alternate-contacts');
                if (altContactsDiv) altContactsDiv.innerHTML = '';
                
                console.log('Data cleared (Sold To information preserved)');
                showNotification('Data cleared successfully. Sold To information preserved.', 'success');
            }
        });
    }
}

/**
 * Populate the Ship To and Work Details fields with extracted data.
 * This function is moved from the HTML sketch.
 * @param {object} data - The extracted data object from the backend.
 */
function populateShipTo(data) {
    // Ship To fields
    document.getElementById('ship-to-name').value = data.customer_name || '';
    document.getElementById('ship-to-address1').value = data.address1 || '';
    document.getElementById('ship-to-address2').value = data.address2 || '';
    document.getElementById('ship-to-city').value = data.city || '';
    document.getElementById('ship-to-zip').value = data.zip_code || '';
    if (document.getElementById('ship-to-country')) document.getElementById('ship-to-country').value = data.country || '';

    // Work Order Details
    document.getElementById('po-number').value = data.po_number || '';
    document.getElementById('dollar-value').value = data.dollar_value || '';
    document.getElementById('supervisor-name').value = data.supervisor_name || '';
    document.getElementById('supervisor-phone').value = data.supervisor_phone || data.supervisor_mobile || '';
    document.getElementById('description-of-works').value = data.description_of_works || '';

    // Email
    document.getElementById('ship-to-email').value = data.email || '';

    // Phone numbers: prioritize phone, mobile, then extras
    let phoneNumbers = [];
    if (data.phone) phoneNumbers.push(data.phone);
    if (data.mobile && data.mobile !== data.phone) phoneNumbers.push(data.mobile);
    if (data.home_phone) phoneNumbers.push(data.home_phone);
    if (data.work_phone) phoneNumbers.push(data.work_phone);
    if (Array.isArray(data.extra_phones)) {
        data.extra_phones.forEach(p => {
            if (p && !phoneNumbers.includes(p)) phoneNumbers.push(p);
        });
    }
    phoneNumbers = [...new Set(phoneNumbers.filter(Boolean))];
    
    // Store original PDF phones in hidden fields for customer creation
    document.getElementById('pdf-phone1').value = phoneNumbers[0] || '';
    document.getElementById('pdf-phone2').value = phoneNumbers[1] || '';
    
    // Phone 3 and Phone 4 fields (initially empty, user can fill if needed)
    document.getElementById('ship-to-phone1').value = '';  // Phone 3
    document.getElementById('ship-to-phone2').value = '';  // Phone 4

    // Best Contact/Alternate Contact section - improved prioritization
    let bestContact = null;
    const priorities = [
        'Decision Maker', 'Best Contact', 'Site Contact', 'Authorised Contact', 'Occupant Contact'
    ];
    if (Array.isArray(data.alternate_contacts)) {
        for (const type of priorities) {
            bestContact = data.alternate_contacts.find(c => c.type && c.type.toLowerCase().includes(type.toLowerCase()));
            if (bestContact) break;
        }
        if (!bestContact && data.alternate_contacts.length > 0) {
            bestContact = data.alternate_contacts[0];
        }
    }
    document.getElementById('alternate-contact-name').value = bestContact ? bestContact.name || '' : '';
    document.getElementById('alternate-contact-phone').value = bestContact ? bestContact.phone || '' : '';
    document.getElementById('alternate-contact-phone2').value = bestContact ? bestContact.phone2 || '' : '';
    if (document.getElementById('alternate-contact-email')) document.getElementById('alternate-contact-email').value = bestContact ? bestContact.email || '' : '';

    // Store all alternates for export
    window._lastExtractedAlternateContacts = data.alternate_contacts || [];

    // Update prefix for secondary PO based on actual job number
    if (document.getElementById('secondary-po-prefix')) document.getElementById('secondary-po-prefix').textContent = (data.actual_job_number || '') + '-';
}

/**
 * Setup logic for Builder Search functionality
 */
function setupBuilderSearch() {
    const searchInput = document.getElementById('sold-to-search');
    const searchButton = document.getElementById('sold-to-search-btn');
    const resultsDiv = document.getElementById('sold-to-results');

    if (!searchInput || !searchButton) {
        console.error('Builder search elements not found');
        return;
    }

    // Search button click handler
    searchButton.addEventListener('click', async () => {
        const searchTerm = searchInput.value.trim();
        if (!searchTerm) {
            alert('Please enter a search term');
            return;
        }

        try {
            const response = await fetchWithRetry('/api/customers/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ term: searchTerm })
            });
            
            const customers = await response.json();
            
            if (customers.error) {
                resultsDiv.innerHTML = `<p class="text-red-500">Error: ${customers.error}</p>`;
                return;
            }
            
            if (!customers.length) {
                resultsDiv.innerHTML = '<p class="text-gray-500">No customers found</p>';
                return;
            }
            
            // Display results
            let html = '<div class="space-y-2">';
            customers.forEach(customer => {
                html += `
                    <div class="border border-gray-600 rounded p-2 hover:bg-gray-700 cursor-pointer customer-result" 
                         data-id="${customer.id || customer.customer_source_id}"
                         data-customer='${JSON.stringify(customer).replace(/'/g, "&apos;")}'>
                        <p class="font-medium">${customer.name || customer.business_name || customer.first_name + ' ' + customer.last_name}</p>
                        <p class="text-sm text-gray-400">${customer.address1 || ''}, ${customer.city || ''}</p>
                        <p class="text-sm text-gray-400">ID: ${customer.id || customer.customer_source_id}</p>
                    </div>
                `;
            });
            html += '</div>';
            
            resultsDiv.innerHTML = html;
            
            // Add click handlers to results
            document.querySelectorAll('.customer-result').forEach(item => {
                item.addEventListener('click', function() {
                    const customerId = this.dataset.id;
                    const customerData = JSON.parse(this.dataset.customer);
                    
                    // Populate sold-to fields
                    document.getElementById('sold-to-rfms-id').value = customerId;
                    document.getElementById('sold-to-name').value = customerData.name || 
                        `${customerData.first_name || ''} ${customerData.last_name || ''}`.trim();
                    document.getElementById('sold-to-business-name').value = customerData.business_name || '';
                    document.getElementById('sold-to-address1').value = customerData.address1 || '';
                    document.getElementById('sold-to-address2').value = customerData.address2 || '';
                    document.getElementById('sold-to-city').value = customerData.city || '';
                    document.getElementById('sold-to-state').value = customerData.state || '';
                    document.getElementById('sold-to-zip').value = customerData.zip_code || '';
                    document.getElementById('sold-to-phone1').value = customerData.phone || '';
                    document.getElementById('sold-to-phone2').value = customerData.phone2 || '';
                    
                    const emailField = document.getElementById('sold-to-email');
                    if (emailField) emailField.value = customerData.email || '';
                    
                    // Clear results
                    resultsDiv.innerHTML = '<p class="text-green-500">Customer selected</p>';
        });
    });
    
        } catch (error) {
            console.error('Search error:', error);
            resultsDiv.innerHTML = `<p class="text-red-500">Search failed: ${error.message}</p>`;
        }
    });
}

/**
 * Setup logic for Add Customer and Create Job buttons
 */
function setupAddCustomerAndCreateJob() {
    const addCustomerButton = document.getElementById('add-customer-button');
    const createJobButton = document.getElementById('create-job-button');
    if (!addCustomerButton || !createJobButton) return;
    let createdCustomerId = null;
    createJobButton.disabled = true;

    // Helper to reset job creation state
    function resetJobCreationState() {
        createdCustomerId = null;
        createJobButton.disabled = true;
    }

    // Reset state when form is cleared or PDF is uploaded
    const clearTriggers = [
        document.getElementById('upload-button'),
        document.getElementById('pdf-upload'),
        document.getElementById('clear-form-button')
    ];
    clearTriggers.forEach(el => {
        if (el) {
            el.addEventListener('click', resetJobCreationState);
        }
    });

    addCustomerButton.addEventListener('click', async () => {
        // Gather Ship To data
        const shipTo = {
            first_name: document.getElementById('ship-to-first-name')?.value || '',
            last_name: document.getElementById('ship-to-last-name')?.value || '',
            address1: document.getElementById('ship-to-address1').value || '',
            address2: document.getElementById('ship-to-address2').value || '',
            city: document.getElementById('ship-to-city').value || '',
            state: document.getElementById('ship-to-state')?.value || '',
            zip_code: document.getElementById('ship-to-zip').value || '',
            county: document.getElementById('ship-to-county')?.value || '',
            phone: document.getElementById('pdf-phone1').value || '',  // Use PDF Phone 1
            phone2: document.getElementById('pdf-phone2').value || '', // Use PDF Phone 2
            email: document.getElementById('ship-to-email').value || '',
            customer_type: 'INSURANCE',
            business_name: document.getElementById('ship-to-business-name')?.value || ''
        };
        // Ensure required fields are present (even if empty)
        shipTo.business_name = shipTo.business_name || '';
        shipTo.first_name = shipTo.first_name || '';
        shipTo.last_name = shipTo.last_name || '';
        shipTo.state = shipTo.state || '';
        addCustomerButton.disabled = true;
        addCustomerButton.textContent = 'Processing...';
        try {
            const response = await fetchWithRetry('/api/create_customer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(shipTo)
            });
            const result = await response.json();
            if (result && result.id) {
                createdCustomerId = result.id;
                showNotification('Customer created in RFMS!', 'success');
                createJobButton.disabled = false;
            } else {
                showNotification('Failed to create customer in RFMS.', 'error');
                createJobButton.disabled = true;
            }
        } catch (error) {
            handleApiError(error, 'creating customer in RFMS');
            createJobButton.disabled = true;
        } finally {
            addCustomerButton.disabled = false;
            addCustomerButton.textContent = 'Add Customer';
        }
    });

    createJobButton.addEventListener('click', async () => {
        if (!createdCustomerId) {
            showNotification('Please add the customer to RFMS first.', 'warning');
            createJobButton.disabled = true;
            return;
        }
        // Gather Sold To data
        const soldToName = document.getElementById('sold-to-name').value.trim();
        const soldToCustomerId = document.getElementById('sold-to-rfms-id') ? 
            document.getElementById('sold-to-rfms-id').value.trim() : '';
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
        const soldTo = {
            id: soldToCustomerId,
            name: soldToName,
            address1: document.getElementById('sold-to-address1').value,
            address2: document.getElementById('sold-to-address2').value,
            city: document.getElementById('sold-to-city').value,
            zip_code: document.getElementById('sold-to-zip').value,
            country: document.getElementById('sold-to-country')?.value || 'Australia',
            phone: document.getElementById('sold-to-phone').value,
            email: document.getElementById('sold-to-email').value
        };
        const shipTo = {
            name: shipToName,
            address1: document.getElementById('ship-to-address1').value,
            address2: document.getElementById('ship-to-address2').value,
            city: document.getElementById('ship-to-city').value,
            zip_code: document.getElementById('ship-to-zip').value,
            country: document.getElementById('ship-to-country')?.value || 'Australia',
            phone3: document.getElementById('ship-to-phone1').value,  // Phone 3 from UI
            phone4: document.getElementById('ship-to-phone2').value,  // Phone 4 from UI
            pdf_phone1: document.getElementById('pdf-phone1').value,  // PDF Phone 1
            pdf_phone2: document.getElementById('pdf-phone2').value,  // PDF Phone 2
            email: document.getElementById('ship-to-email').value,
            id: createdCustomerId
        };
        const altContact = {
            name: document.getElementById('alternate-contact-name').value,
            phone: document.getElementById('alternate-contact-phone').value,
            phone2: document.getElementById('alternate-contact-phone2').value,
            email: document.getElementById('alternate-contact-email').value
        };
        let descriptionOfWorks = document.getElementById('description-of-works').value;
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
        const billingGroup = {};
        const billingGroupCheckbox = document.getElementById('billing-group-checkbox');
        if (billingGroupCheckbox && billingGroupCheckbox.checked) {
            billingGroup.is_billing_group = true;
            billingGroup.po_suffix = document.getElementById('secondary-po-suffix').value;
            billingGroup.second_value = parseFloat(document.getElementById('second-po-dollar-value').value) || 0;
        }
        const payload = {
            sold_to: soldTo,
            ship_to: shipTo,
            job_details: jobDetails,
            billing_group: billingGroup,
            alternate_contact: altContact,
            alternate_contacts: window._lastExtractedAlternateContacts || []
        };
        createJobButton.disabled = true;
        createJobButton.textContent = 'Processing...';
        const loadingNotification = showNotification('Creating job in RFMS...', 'info', 0);
        try {
            const response = await fetchWithRetry('/api/export-to-rfms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            showNotification('Job created in RFMS!', 'success');
            if (result.job_id) {
                showNotification(`Job created with ID: ${result.job_id}`, 'success', 5000);
            }
        } catch (error) {
            handleApiError(error, 'creating job in RFMS');
        } finally {
            createJobButton.disabled = false;
            createJobButton.textContent = 'Create Job';
            const persistentNotification = document.getElementById('notification-loading');
            if (persistentNotification) {
                document.body.removeChild(persistentNotification);
            }
        }
    });
}

/**
 * Clear best contact fields
 */
function clearBestContacts() {
    const bestContactFields = [
        'alternate-contact-name',
        'alternate-contact-phone',
        'alternate-contact-phone2',
        'alternate-contact-email'
    ];
    
    bestContactFields.forEach(id => {
        const field = document.getElementById(id);
        if (field) field.value = '';
    });
} 