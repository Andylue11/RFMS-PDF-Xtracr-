{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww29400\viewh18400\viewkind1
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 RFMS PDF XTRACR\
\
A web application that extracts all the required data from an upload pdf for creating quotes or job in RFMS (Retail Floor Management System) using the RFMS API v2.\
\
## Features\
\
- PDF upload and processing to extract purchase order details, builder supplying the po (purchase order) insurer customer information and scope of works requested and the dollar value that\'92s with the order information\
- Create quote from uploaded PDF data\
- Create job from uploaded PDF data\
- Search and view customers\
- Enter extracted customer data into RFMS\
- Dashboard with extracted builder and customer data field editable preview which include the scope of works and the $ value of the po and quick actions \
- Customer (aka BUILDER supplying the po look up index from RFMS using either name search or CustomId\
- quick action for confirm data js correct \
- tick box for \'93Is this PO part of a billing group\'94 and the ability to refill a dialog box next to it is selected showing the PO# prefix before - only for user to enter a 2 digit suffix number. (This would then create a duplicate job only which would be added to a billing group with the first PO uploaded job\
- a $ value entry field for the second po being part of a billing group request filling out to be entered with the second po job created in RFMS\
- Upload to RFMS action button\
- API status monitoring\
\
## Key Functionality\
\
- **PDF Processing**: Upload purchase orders or customer documents and automatically extract key information like customer details, PO numbers, and scope of work and dollar value of the purchase order.\
- Show User a preview of all the extracted data as per the example in UI layouts folder called Customer Layout UI\
- **Quote Creation**: Create quotes with multiple line items and automatically calculate totals.\
- **Job Creation**: Create jobs from orders with ability to check for duplicates.\
- **Customer Management**: Look up and create customer information.\
- The extracted purchase order data for the \'93NSURED CUSTOMER\'94 once confirmed and \'93quote or job create\'94 has been selected the application would need to create the new customer in rams first before starting the create action.  \
- Have a NEXT UPLOAD action button that clears the current uploaded pdf and extracted data ready to start the application process again. \
\
## Setup\
\
### Prerequisites\
\
- Python 3.8+\
- Virtual environment (recommended)\
- RFMS API credentials (username and API key)\
\
### Installation\
\
1. Clone the repository:\
   ```\
   git clone <repository-url>\
   cd rfms-quote-creator\
   ```\
\
2. Create and activate a virtual environment:\
   ```\
   python -m venv .venv\
   source .venv/bin/activate  # On Windows, use: .venv\\Scripts\\activate\
   ```\
\
3. Install dependencies:\
   ```\
   pip install -r requirements.txt\
   ```\
\
4. Create a `.env` file in the project root with the following content:\
   ```\
   RFMS_BASE_URL=https://api.rfms.online\
   RFMS_STORE_CODE=your_store_code\
   RFMS_USERNAME=your_username\
   RFMS_API_KEY=your_api_key\
   SECRET_KEY=your_secret_key_for_flask\
   DEBUG=True  # Set to False in production\
   ```\
\
### Running the Application\
\
Run the application with:\
```\
python app.py\
```\
\
The application will be available at http://localhost:5000.\
\
## Usage\
\
1. **Upload a PDF**:\
   - Navigate to the Customers section\
   - Click the "Upload PDF" button\
   - Select a customer (this will be the "Bill To" customer)\
   - Upload your PDF file\
   - Process the PDF to extract information\
\
2. **Create a Quote**:\
   - After processing a PDF, click "Create Quote"\
   - Review and edit the quote information\
   - Add additional items if needed\
   - Click "Create Quote" to save\
\
3. **Create a Job**:\
   - After processing a PDF, click "Create Job"\
   - Review and edit the job information\
   - Click "Create Job" to save\
\
4. **Search for Jobs**:\
   - Navigate to the Jobs section\
   - Use the filters to search for specific jobs\
   - Click the filter button to execute the search\
\
## Troubleshooting\
\
- **API Connection Issues**: Check that your API credentials are correct in the .env file\
- **PDF Extraction Problems**: Make sure your PDF is not scanned or contains extractable text\
- **File Upload Errors**: Verify that your PDF is not too large (max 16MB)\
\
## License\
\
[Your License Information]\
\
## Credits\
\
Developed for A to Z Flooring Solutions }