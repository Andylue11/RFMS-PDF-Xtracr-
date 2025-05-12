/**
 * RFMS PDF XTRACR - Main JavaScript
 * Common functionality used across the application
 */

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

        // Clear all fields before uploading new PDF
        clearFields();

        const formData = new FormData();
        formData.append('pdf_file', file);

        // Show loading indicator/message
        showNotification('Uploading and extracting data...', 'info', 0);

        try {
            const response = await fetch('/upload-pdf', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const extractedData = await response.json();
                console.log('Extracted Data:', extractedData);
                populateShipTo(extractedData);
                showNotification('PDF extracted successfully!', 'success');
            } else {
                const errorData = await response.json();
                console.error('Upload failed:', errorData.error);
                showNotification(`Error: ${errorData.error}`, 'error');
            }
        } catch (error) {
            console.error('Error during PDF upload and extraction:', error);
            showNotification(`An error occurred: ${error.message}`, 'error');
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
    document.getElementById('ship-to-name').value = data.customer_name || '';
    document.getElementById('ship-to-address1').value = data.address1 || '';
    document.getElementById('ship-to-address2').value = data.address2 || '';
    document.getElementById('ship-to-city').value = data.city || '';
    document.getElementById('ship-to-state').value = data.state || '';
    document.getElementById('ship-to-zip').value = data.zip_code || '';
    document.getElementById('ship-to-country').value = data.country || '';

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

    // Format and populate phone fields
    const formattedPhones = phoneNumbers.map(formatPhoneNumber);
    document.getElementById('ship-to-phone1').value = formattedPhones[0] || '';
    document.getElementById('ship-to-phone2').value = formattedPhones[1] || '';

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
        showNotification('Searching for builders...', 'info');

        try {
            const response = await fetch(`/api/customers/search?term=${encodeURIComponent(searchTerm)}`);
            
            // Reset button state
            searchButton.disabled = false;
            searchButton.textContent = 'Search Builders';

            if (response.ok) {
                const searchResults = await response.json();
                
                if (Array.isArray(searchResults) && searchResults.length > 0) {
                    // Display search results for selection if there are multiple matches
                    if (searchResults.length > 1) {
                        displaySearchResults(searchResults);
                    } else {
                        // If only one result, auto-select it
                        populateSoldTo(searchResults[0]);
                        showNotification('Builder found and details populated.', 'success');
                    }
                } else {
                    showNotification('No builders found matching your search term.', 'warning');
                }
            } else {
                const errorData = await response.json();
                console.error('Search failed:', errorData.error);
                showNotification(`Error: ${errorData.error}`, 'error');
            }
        } catch (error) {
            console.error('Error during builder search:', error);
            showNotification(`An error occurred: ${error.message}`, 'error');
            
            // Reset button state
            searchButton.disabled = false;
            searchButton.textContent = 'Search Builders';
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
    title.className = 'text-lg font-bold';
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
    
    results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'p-3 border rounded hover:bg-gray-100 cursor-pointer';
        
        // Format the display based on available properties in the result
        let displayText = `${result.name || 'Unknown Name'}`;
        if (result.id) {
            displayText = `${result.id}: ${displayText}`;
        }
        if (result.address) {
            displayText += ` - ${result.address}`;
        }
        
        resultItem.textContent = displayText;
        resultItem.onclick = () => {
            populateSoldTo(result);
            resultsContainer.remove();
            showNotification('Builder selected and details populated.', 'success');
        };
        
        resultsList.appendChild(resultItem);
    });
    
    // Assemble the modal
    modalContent.appendChild(header);
    modalContent.appendChild(resultsList);
    resultsContainer.appendChild(modalContent);
}

/**
 * Populate the Sold To fields with the selected builder data
 * @param {Object} builderData - The builder data object from the API
 */
function populateSoldTo(builderData) {
    // Map the API fields to our form fields
    // These mappings will depend on the actual structure of the builder data from RFMS API
    document.getElementById('sold-to-name').value = builderData.name || '';
    
    // These field mappings are guesses and should be adjusted based on actual API response
    if (builderData.address) {
        // If address is a single string, attempt to parse
        if (typeof builderData.address === 'string') {
            const addressParts = builderData.address.split(',').map(part => part.trim());
            
            if (addressParts.length >= 1) {
                document.getElementById('sold-to-address1').value = addressParts[0] || '';
            }
            if (addressParts.length >= 2) {
                document.getElementById('sold-to-address2').value = addressParts[1] || '';
            }
            // Try to parse city, state, zip from the last part
            if (addressParts.length >= 3) {
                const lastPart = addressParts[addressParts.length - 1];
                const cityStateZip = lastPart.split(' ');
                
                if (cityStateZip.length >= 2) {
                    // Assume format: City STATE ZIP
                    const city = cityStateZip.slice(0, -2).join(' ');
                    const state = cityStateZip[cityStateZip.length - 2];
                    const zip = cityStateZip[cityStateZip.length - 1];
                    
                    document.getElementById('sold-to-city').value = city || '';
                    document.getElementById('sold-to-state').value = state || '';
                    document.getElementById('sold-to-zip').value = zip || '';
                }
            }
        } else if (typeof builderData.address === 'object') {
            // If address is an object with separate fields
            document.getElementById('sold-to-address1').value = builderData.address.line1 || '';
            document.getElementById('sold-to-address2').value = builderData.address.line2 || '';
            document.getElementById('sold-to-city').value = builderData.address.city || '';
            document.getElementById('sold-to-state').value = builderData.address.state || '';
            document.getElementById('sold-to-zip').value = builderData.address.zip || '';
        }
    }
    
    // Populate additional fields if available
    document.getElementById('sold-to-country').value = builderData.country || 'Australia';
    document.getElementById('sold-to-phone').value = builderData.phone || '';
    document.getElementById('sold-to-email').value = builderData.email || '';
    
    // Store the builder's RFMS customer ID for later use when creating the job
    // This might be a hidden field or data attribute
    if (builderData.id) {
        // Add a hidden field if it doesn't exist
        let builderIdField = document.getElementById('sold-to-customer-id');
        if (!builderIdField) {
            builderIdField = document.createElement('input');
            builderIdField.type = 'hidden';
            builderIdField.id = 'sold-to-customer-id';
            document.getElementById('sold-to-fields').appendChild(builderIdField);
        }
        builderIdField.value = builderData.id;
    }
}

/**
 * Gather all form data and send to /api/export-to-rfms
 */
function setupExportToRFMS() {
    const exportButton = document.getElementById('export-to-rfms-button');
    if (!exportButton) return;

    exportButton.addEventListener('click', async () => {
        // Gather Sold To data
        const soldTo = {
            id: document.getElementById('sold-to-customer-id') ? document.getElementById('sold-to-customer-id').value : '',
            name: document.getElementById('sold-to-name').value,
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
            name: document.getElementById('ship-to-name').value,
            address1: document.getElementById('ship-to-address1').value,
            address2: document.getElementById('ship-to-address2').value,
            city: document.getElementById('ship-to-city').value,
            state: document.getElementById('ship-to-state').value,
            zip_code: document.getElementById('ship-to-zip').value,
            country: document.getElementById('ship-to-country').value,
            phone: document.getElementById('ship-to-phone1').value + ' ' + document.getElementById('ship-to-phone2').value,
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
            po_number: document.getElementById('po-number').value,
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
        showNotification('Exporting to RFMS...', 'info', 0);
        exportButton.disabled = true;

        try {
            const response = await fetch('/api/export-to-rfms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            exportButton.disabled = false;

            if (response.ok) {
                const result = await response.json();
                showNotification('Exported to RFMS successfully!', 'success');
                // Optionally, display a summary or redirect
                console.log('RFMS Export Result:', result);
            } else {
                const errorData = await response.json();
                showNotification(`Export failed: ${errorData.error}`, 'error');
                console.error('Export error:', errorData);
            }
        } catch (error) {
            exportButton.disabled = false;
            showNotification(`An error occurred: ${error.message}`, 'error');
            console.error('Export error:', error);
        }
    });
} 