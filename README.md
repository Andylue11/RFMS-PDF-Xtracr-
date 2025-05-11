# RFMS PDF XTRACR

A web application that extracts data from uploaded PDF purchase orders and integrates with the Retail Floor Management System (RFMS) using the RFMS API v2. Designed specifically for A to Z Flooring Solutions.

## Features

- PDF upload and data extraction (customer info, PO numbers, scope of work, dollar values)
- Interactive dashboard with extracted data preview
- Customer lookups and management within RFMS
- Quote and job creation from extracted data
- Billing group functionality with PO prefixes and suffixes
- API status monitoring
- Single-screen workflow based on customer file entry fields

## Setup

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- RFMS API credentials (username and API key)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd rfms-pdf-xtracr
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:
   ```
   cp .env-example .env
   ```
   Then edit `.env` to add your RFMS API credentials and other settings.

5. Create the necessary directories and initialize the database:
   ```
   mkdir -p uploads
   python -c "from app import db; db.create_all()"
   ```

### Running the Application

Run the application with:
```
python app.py
```

The application will be available at http://localhost:5000.

## Usage

1. **Upload a PDF**:
   - On the dashboard, click the "Upload and Process" button
   - Select a PDF purchase order to upload
   - The system will extract data and show it in a preview

2. **Review Extracted Data**:
   - Verify all fields are correctly extracted
   - Edit any incorrect information if needed
   - Click "Confirm Data" when ready

3. **Create a Quote or Job**:
   - Click "Create Quote" or "Create Job"
   - Select or create a customer in RFMS
   - Submit to create the quote/job in RFMS

4. **Billing Group Functionality**:
   - If needed, check "Is this PO part of a billing group"
   - Enter the 2-digit suffix and second PO dollar value
   - Two jobs will be created and added to a billing group

5. **Next Upload**:
   - Click "Next Upload" to clear the form and start again

## Project Structure

- `app.py` - Main Flask application
- `models/` - Database models
- `utils/` - Utility functions including PDF extraction and RFMS API client
- `templates/` - HTML templates for the user interface
- `templates/static/` - Static assets (CSS, JavaScript, images)
- `uploads/` - Directory for uploaded PDF files

## Troubleshooting

- **API Connection Issues**: Check that your API credentials are correct in the .env file
- **PDF Extraction Problems**: Make sure your PDF is not scanned or contains extractable text
- **File Upload Errors**: Verify that your PDF is not too large (max 16MB)

## License

[Your License Information]

## Credits

Developed for A to Z Flooring Solutions 