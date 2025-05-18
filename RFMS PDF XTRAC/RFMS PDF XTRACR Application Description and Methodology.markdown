# RFMS PDF XTRACR Application Description and Methodology

## Application Description

The **RFMS PDF XTRACR** is a web-based application designed to streamline the extraction of data from uploaded PDF purchase orders (POs) and integrate it with the Retail Floor Management System (RFMS) using the RFMS API v2. Tailored for A to Z Flooring Solutions, the application features a single-screen dashboard inspired by the provided customer file entry fields image. This dashboard allows users to upload PDFs, extract key details (e.g., customer information, PO numbers, scope of work, dollar values), and perform actions such as creating quotes, jobs, or managing customers in RFMS. The frontend is built with HTML, JavaScript, and Tailwind CSS for a responsive interface, while the backend leverages Python with Flask to handle API interactions. The design aligns with the "Customer Layout UI" and follows workflows from the workflow folder, with API integration guided by the RFMS API v2 documentation in the RFMSAPI docs folder.

### Key Features
- **PDF Upload and Data Extraction**: Users can upload PDFs, with data (e.g., customer name, PO number, scope of work, dollar value) extracted using a JavaScript-based PDF parsing library like pdf.js.
- **Single-Screen Dashboard**: Displays extracted data in a layout matching the customer file entry fields image, with editable fields and action buttons (e.g., Confirm Data, Create Quote, Create Job, Upload to RFMS, Next Upload).
- **RFMS Integration**: Interacts with the RFMS API to create quotes, jobs, and customer records, including billing group support with PO# prefix and 2-digit suffix for duplicate jobs.
- **Customer Management**: Enables searching for customers by name or CustomId and creating new "INSURED CUSTOMER" records in RFMS.
- **Workflow Support**: Implements data clearing for next uploads and data confirmation based on workflow folder guidelines.
- **API Status Monitoring**: Provides feedback on RFMS API connectivity issues.

### User Interface
The UI is a single dashboard based on the customer file entry fields image, featuring:
- Editable fields for "Sold To" and "Ship To" (e.g., Salutation, First Name, Last Name, Business, Address, City, State, Country, Phone, Email).
- Additional fields for Client Ph#, Default Store, Buyer Type, Active Since, Renewal Date, Renew Amount, Renew Group, and Sales Rep percentages.
- Buttons for Confirm Data, Create Quote, Create Job, Upload to RFMS, and Next Upload, styled with Tailwind CSS for usability.
- A checkbox for billing group functionality, revealing fields for PO# prefix and 2-digit suffix, plus a dollar value field for the second PO.

## Methodology

The development follows an agile methodology with iterative sprints, ensuring alignment with the README.md, customer layout, workflow folder, and RFMSAPI docs. The process includes:

1. **Requirements Analysis**:
   - Analyze README.md, customer file entry fields image, workflow folder, and RFMSAPI docs to define PDF extraction, dashboard design, and RFMS integration needs.
   - Develop user stories for PDF upload, data preview, customer management, and action execution.

2. **Design**:
   - Create a single-screen dashboard wireframe based on the customer file entry fields image, using Tailwind CSS for responsiveness.
   - Design API interaction workflows with error handling, referencing RFMSAPI docs.
   - Plan data models for extracted PDF data and RFMS API payloads.

3. **Development**:
   - **Frontend**: Build the dashboard with HTML, JavaScript, and Tailwind CSS. Use pdf.js for client-side PDF parsing and DOM manipulation for dynamic field updates.
   - **Backend**: Develop a Flask API to proxy RFMS API requests, handling authentication and data transformation based on RFMSAPI docs.
   - **Integration**: Implement RFMS API calls for customer lookup, quote/job creation, and billing group management.
   - Follow workflow folder for data clearing and next-upload logic.

4. **Testing**:
   - Unit test JavaScript components (e.g., PDF parsing, form validation) with Jest.
   - Integration test Flask endpoints with RFMS API mocks using Pytest.
   - Validate UI against the customer file entry fields image.
   - Test PDF extraction accuracy with sample POs.

5. **Deployment**:
   - Deploy Flask backend on a cloud platform (e.g., Heroku) with environment variables for RFMS credentials.
   - Host the frontend as a static site or bundle with Flask.
   - Monitor API performance with logging.

6. **Maintenance**:
   - Iterate based on user feedback and RFMS API updates.
   - Update documentation as needed.

## Best Practices and Principles

### General Principles
- **DRY**: Reuse JavaScript functions for PDF parsing and form handling, and Python modules for API calls.
- **KISS**: Keep PDF extraction and API logic simple, avoiding unnecessary complexity.
- **SOLID Principles**:
  - **Single Responsibility**: Separate PDF parsing, UI rendering, and API calls into distinct files.
  - **Open/Closed**: Allow adding new PDF fields without altering core logic.
  - **Interface Segregation**: Define clear interfaces for frontend-backend communication.
- **Modularity**: Organize code into `pdfProcessor.js`, `dashboard.js`, `app.py`, and `rfmsApi.py`.

### Frontend (HTML, JavaScript, Tailwind CSS)
- **Responsive Design**: Use Tailwind CSS for a mobile-friendly dashboard matching the customer file entry fields layout.
- **Component-Based**: Create reusable JavaScript components for form fields and buttons.
- **Event-Driven**: Handle PDF uploads and button clicks with event listeners for a reactive UI.
- **Client-Side Validation**: Validate inputs (e.g., 2-digit suffix, dollar values) before API calls.
- **Error Handling**: Show alerts for PDF upload errors or API issues.
- **Performance Optimization**: Lazy-load pdf.js and cache extracted data in localStorage.
- **Security**: Sanitize inputs and restrict uploads to PDFs (max 16MB).

### Backend (Python, Flask)
- **RESTful API**: Structure Flask endpoints (e.g., `/upload`, `/create-quote`) per RFMSAPI docs.
- **Environment Configuration**: Store RFMS credentials in a `.env` file using `python-dotenv`.
- **Error Handling**: Use try-except for API calls, returning HTTP status codes (e.g., 400, 500).
- **Logging**: Track requests and errors with Python’s `logging` module.
- **Security**: Validate file uploads server-side and enforce HTTPS.
- **Scalability**: Design stateless endpoints for horizontal scaling.

### RFMS API Integration
- **Authentication**: Pass RFMS credentials in headers as per RFMSAPI docs.
- **Idempotency**: Check for duplicate jobs before creation.
- **Rate Limiting**: Respect RFMS API limits with retry logic.

### Testing and Quality Assurance
- **Unit Testing**: Test JavaScript functions with Jest and Python code with Pytest.
- **Integration Testing**: Simulate RFMS API responses for end-to-end tests.
- **Code Reviews**: Ensure adherence to standards via peer reviews.
- **Linting**: Use ESLint for JavaScript and Black/Flake8 for Python.

### Documentation
- **Code Comments**: Add comments for PDF parsing and billing group logic.
- **User Guide**: Document dashboard usage in README.md.
- **API Documentation**: Reference RFMSAPI docs for Flask endpoints.

### Version Control
- **Git Workflow**: Use feature branches and pull requests with clear commit messages.
- **Changelog**: Track updates in `CHANGELOG.md`.

## References
- **Customer File Entry Fields Image**: Guides the dashboard layout.
- **Workflow Folder**: Defines action sequences and data clearing.
- **RFMSAPI Docs**: Provides API endpoints and schemas.

## Conclusion
The RFMS PDF XTRACR delivers an efficient, user-friendly solution with a single-screen dashboard, leveraging HTML, JavaScript, Tailwind CSS, and Flask. Adhering to best practices ensures reliability, maintainability, and scalability, aligning with the provided documentation and requirements.