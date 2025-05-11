import re
import logging
import os
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def extract_data_from_pdf(file_path):
    """
    Extract relevant data from PDF purchase orders.
    
    This function tries multiple PDF parsing libraries to maximize extraction success.
    It looks for patterns like customer information, PO numbers, scope of work and dollar values.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        dict: Extracted data including customer_name, business_name, po_number, 
              scope_of_work, and dollar_value
    """
    logger.info(f"Extracting data from PDF: {file_path}")
    
    # Initialize extracted data dictionary
    extracted_data = {
        'customer_name': '',
        'business_name': '',
        'first_name': '',
        'last_name': '',
        'address': '',
        'city': '',
        'state': '',
        'zip_code': '',
        'country': 'USA',  # Default
        'phone': '',
        'email': '',
        'po_number': '',
        'scope_of_work': '',
        'dollar_value': 0,
        'raw_text': ''
    }
    
    # Try different extraction methods in order of reliability
    try:
        # Try PyMuPDF (fitz) first - generally fastest and most reliable
        text = extract_with_pymupdf(file_path)
        if text:
            extracted_data['raw_text'] = text
            parse_extracted_text(text, extracted_data)
        
        # If we didn't get all needed data, try pdfplumber
        if not all([extracted_data['customer_name'], extracted_data['po_number']]):
            text = extract_with_pdfplumber(file_path)
            if text and text != extracted_data['raw_text']:
                extracted_data['raw_text'] = text
                parse_extracted_text(text, extracted_data)
        
        # Last resort, try PyPDF2
        if not all([extracted_data['customer_name'], extracted_data['po_number']]):
            text = extract_with_pypdf2(file_path)
            if text and text != extracted_data['raw_text']:
                extracted_data['raw_text'] = text
                parse_extracted_text(text, extracted_data)
        
        # Split name into first and last name if not already done
        if extracted_data['customer_name'] and not (extracted_data['first_name'] and extracted_data['last_name']):
            names = extracted_data['customer_name'].split(maxsplit=1)
            if len(names) > 0:
                extracted_data['first_name'] = names[0]
            if len(names) > 1:
                extracted_data['last_name'] = names[1]
        
        logger.info(f"Successfully extracted data from PDF: {file_path}")
        return extracted_data
    
    except Exception as e:
        logger.error(f"Error extracting data from PDF: {str(e)}")
        extracted_data['error'] = str(e)
        return extracted_data


def extract_with_pymupdf(file_path):
    """Extract text from PDF using PyMuPDF."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        logger.error(f"PyMuPDF extraction error: {str(e)}")
        return ""


def extract_with_pdfplumber(file_path):
    """Extract text from PDF using pdfplumber."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"pdfplumber extraction error: {str(e)}")
        return ""


def extract_with_pypdf2(file_path):
    """Extract text from PDF using PyPDF2."""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"PyPDF2 extraction error: {str(e)}")
        return ""


def parse_extracted_text(text, extracted_data):
    """
    Parse the extracted text to find relevant information.
    
    Args:
        text (str): The extracted text from the PDF
        extracted_data (dict): Dictionary to update with parsed information
    """
    # Look for customer name patterns
    customer_patterns = [
        r"Customer[:\s]+([A-Za-z\s]+)",
        r"Name[:\s]+([A-Za-z\s]+)",
        r"Bill To[:\s]+([A-Za-z\s]+)",
        r"Insured[:\s]+([A-Za-z\s]+)"
    ]
    
    for pattern in customer_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['customer_name'] = match.group(1).strip()
            break
    
    # Look for business name
    business_patterns = [
        r"Business[:\s]+([A-Za-z0-9\s\.,&]+)",
        r"Company[:\s]+([A-Za-z0-9\s\.,&]+)",
        r"Builder[:\s]+([A-Za-z0-9\s\.,&]+)"
    ]
    
    for pattern in business_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['business_name'] = match.group(1).strip()
            break
    
    # Extract address
    address_patterns = [
        r"Address[:\s]+([A-Za-z0-9\s\.,#-]+)",
        r"Location[:\s]+([A-Za-z0-9\s\.,#-]+)",
        r"Property[:\s]+([A-Za-z0-9\s\.,#-]+)"
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['address'] = match.group(1).strip()
            break
    
    # Extract city, state, zip
    location_pattern = r"([A-Za-z\s]+)[,\s]+([A-Z]{2})[,\s]+(\d{5}(-\d{4})?)"
    match = re.search(location_pattern, text)
    if match:
        extracted_data['city'] = match.group(1).strip()
        extracted_data['state'] = match.group(2).strip()
        extracted_data['zip_code'] = match.group(3).strip()
    
    # Extract phone number
    phone_patterns = [
        r"Phone[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"Tel[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"Contact[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['phone'] = match.group(1).strip()
            break
    
    # Extract email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(email_pattern, text)
    if match:
        extracted_data['email'] = match.group(0)
    
    # Extract PO number
    po_patterns = [
        r"PO[:\s#]+([A-Za-z0-9-]+)",
        r"P\.O\.[:\s#]+([A-Za-z0-9-]+)",
        r"Purchase Order[:\s#]+([A-Za-z0-9-]+)",
        r"Order Number[:\s#]+([A-Za-z0-9-]+)"
    ]
    
    for pattern in po_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['po_number'] = match.group(1).strip()
            break
    
    # Extract scope of work
    scope_patterns = [
        r"Scope of Work[:\s]+([\s\S]+?)(?=Total|Amount|Price|\$|\n\n)",
        r"Description[:\s]+([\s\S]+?)(?=Total|Amount|Price|\$|\n\n)",
        r"Services[:\s]+([\s\S]+?)(?=Total|Amount|Price|\$|\n\n)"
    ]
    
    for pattern in scope_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['scope_of_work'] = match.group(1).strip()
            break
    
    # Extract dollar value
    dollar_patterns = [
        r"Total[:\s]+\$?([\d,]+\.\d{2})",
        r"Amount[:\s]+\$?([\d,]+\.\d{2})",
        r"Price[:\s]+\$?([\d,]+\.\d{2})",
        r"Value[:\s]+\$?([\d,]+\.\d{2})",
        r"\$\s?([\d,]+\.\d{2})"
    ]
    
    for pattern in dollar_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                extracted_data['dollar_value'] = float(value_str)
                break
            except ValueError:
                continue 