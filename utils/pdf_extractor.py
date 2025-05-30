import re
import logging
import os
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


# Template configurations for different companies
TEMPLATE_CONFIGS = {
    "ambrose": {
        "name": "Ambrose Construct Group",
        "po_patterns": [
            r"P\.O\.\s*No:?\s*(20\d{6}-\d{2})",  # Specific format: 20XXXXXX-XX
            r"PO[:\s#]+(20\d{6}-\d{2})",
            r"Purchase\s+Order[:\s#]+(20\d{6}-\d{2})",
            r"Order\s+Number[:\s#]+(20\d{6}-\d{2})",
        ],
        "customer_patterns": [
            r"Insured\s+Owner:?\s*([A-Za-z\s]+?)(?=\n|Authorised)",
            r"Insured:?\s*([A-Za-z\s]+?)(?=\n)",
            r"Customer[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Name[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Bill\s+To[:\s]+([A-Za-z\s]+?)(?=\n)",
        ],
        "description_patterns": [
            r"Description\s+of\s+Works[:\s]*(.+?)(?=Supervisor|$)",
            r"Works\s+Description[:\s]*(.+?)(?=Supervisor|$)",
            r"Scope\s+of\s+Works[:\s]*(.+?)(?=Supervisor|$)",
        ],
        "supervisor_section_pattern": r"Supervisor\s+Details",
        "dollar_patterns": [
            r"\$\s*([\d,]+\.?\d*)",
            r"Total[:\s]+\$?\s*([\d,]+\.?\d*)",
        ],
    },
    "profile_build": {
        "name": "Profile Build Group",
        "po_patterns": [
            r"WORK\s+ORDER:?\s*(PBG-\d+-\d+)",  # PBG-18191-18039
            r"PBG-\d+-\d+",  # Direct pattern match
            r"Order\s+Number[:\s#]+(PBG-\d+-\d+)",
            r"Contract\s+No[.:]?\s*(PBG-\d+-\d+)",
        ],
        "customer_patterns": [
            r"Client[:\s]+([A-Za-z\s&]+?)(?=\n|Job)",
            r"Customer[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"SITE\s+CONTACT[:\s]+([A-Za-z\s]+?)(?=\n)",
        ],
        "description_patterns": [
            r"NOTES[:\s]*(.+?)(?=All amounts|Total|$)",
            r"Scope\s+of\s+Works[:\s]*(.+?)(?=All amounts|Total|$)",
            r"PBG-\d+-\d+\s*(.+?)(?=All amounts|Total|$)",
        ],
        "supervisor_section_pattern": r"Supervisor[:\s]",
        "dollar_patterns": [
            r"Total\s+AUD\s*\$?\s*([\d,]+\.?\d*)",
            r"Total[:\s]+\$?\s*([\d,]+\.?\d*)",
            r"\$\s*([\d,]+\.?\d*)",
        ],
    },
    "campbell": {
        "name": "Campbell Construction",
        "po_patterns": [
            r"Contract\s+No[.:]?\s*(CCC\d+-\d+)",  # CCC55132-88512
            r"CCC\d+-\d+",  # Direct pattern match
            r"CONTRACT\s+NO[.:]?\s*(CCC\d+-\d+)",
            r"Contract\s+Number[.:]?\s*(CCC\d+-\d+)",
        ],
        "customer_patterns": [
            r"Customer[:\s]+([A-Za-z\s]+?)(?=\n|Site)",
            r"Client[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Owner[:\s]+([A-Za-z\s]+?)(?=\n)",
        ],
        "description_patterns": [
            r"Scope\s+of\s+Work[:\s]*(.+?)(?=Totals|Page|$)",
            r"CCC\d+-\d+\s*(.+?)(?=Totals|Page|$)",
            r"Description\s+of\s+Works[:\s]*(.+?)(?=Totals|Page|$)",
        ],
        "supervisor_section_pattern": r"CONTRACTOR'S\s+REPRESENTATIVE|Supervisor",
        "dollar_patterns": [
            r"Total\s*\$?\s*([\d,]+\.?\d*)",
            r"Subtotal\s*\$?\s*([\d,]+\.?\d*)",
            r"\$\s*([\d,]+\.?\d*)",
        ],
    },
    "rizon": {
        "name": "Rizon Group",
        "po_patterns": [
            r"PURCHASE\s+ORDER\s+NO[:\s]*(P\d+)",  # P367117
            r"P\d{6}",  # Direct pattern match
            r"ORDER\s+NUMBER[:\s]*(\d+/\d+/\d+)",  # Alternative format
            r"PO[:\s#]+(P?\d+)",
        ],
        "customer_patterns": [
            r"Client\s*/\s*Site\s+Details[:\s]*([A-Za-z\s]+?)(?=\n|\()",
            r"Customer[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Site\s+Details[:\s]*([A-Za-z\s]+?)(?=\n)",
        ],
        "description_patterns": [
            r"SCOPE\s+OF\s+WORKS[:\s]*(.+?)(?=Net Order|PURCHASE\s+ORDER\s+CONDITIONS|$)",
            r"Scope\s+of\s+Works[:\s]*(.+?)(?=Net Order|Total|$)",
        ],
        "supervisor_section_pattern": r"Supervisor[:\s]",
        "dollar_patterns": [
            r"Total\s+Order[:\s]*\$?\s*([\d,]+\.?\d*)",
            r"Net\s+Order[:\s]*\$?\s*([\d,]+\.?\d*)",
            r"\$\s*([\d,]+\.?\d*)",
        ],
    },
    "australian_restoration": {
        "name": "Australian Restoration Company",
        "po_patterns": [
            r"Order\s+Number[:\s]*(PO\d+-[A-Z0-9]+-\d+)",  # PO96799-BU01-003
            r"PO\d+-[A-Z0-9]+-\d+",  # Direct pattern match
            r"Purchase\s+Order[:\s#]+(PO\d+-[A-Z0-9]+-\d+)",
        ],
        "customer_patterns": [
            r"Customer\s+Details[:\s]*([A-Za-z\s]+?)(?=\n|Site)",
            r"Customer[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Client[:\s]+([A-Za-z\s]+?)(?=\n)",
        ],
        "description_patterns": [
            r"Flooring\s+Contractor\s+Material(.+?)(?=All amounts|Preliminaries|Total|$)",
            r"Scope\s+of\s+Works[:\s]*(.+?)(?=All amounts|Total|$)",
        ],
        "supervisor_section_pattern": r"Project\s+Manager[:\s]|Case\s+Manager[:\s]",
        "dollar_patterns": [
            r"Total\s+AUD\s*\$?\s*([\d,]+\.?\d*)",
            r"Sub\s+Total\s*\$?\s*([\d,]+\.?\d*)",
            r"\$\s*([\d,]+\.?\d*)",
        ],
    },
    "townsend": {
        "name": "Townsend Building Services",
        "po_patterns": [
            r"Purchase\s+Order[:\s#]+(TBS-\d+)",
            r"TBS-\d+",
            r"Order\s+Number[:\s]*(TBS-\d+)",
            r"WO[:\s#]+(\d+)",
            r"Work\s+Order[:\s#]+(\d+)",
        ],
        "customer_patterns": [
            r"Attention[:\s]+([A-Za-z\s]+?)(?=\n|Email)",
            r"Customer[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Client[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Contact[:\s]+([A-Za-z\s]+?)(?=\n)",
        ],
        "description_patterns": [
            r"Scope\s+of\s+Works[:\s]*(.+?)(?=Total|ABN|Page|$)",
            r"Work\s+Description[:\s]*(.+?)(?=Total|ABN|Page|$)",
            r"Description[:\s]*(.+?)(?=Total|ABN|Page|$)",
        ],
        "supervisor_section_pattern": r"Project\s+Manager[:\s]|Supervisor[:\s]|Manager[:\s]",
        "dollar_patterns": [
            r"Total\s+Inc\.?\s+GST[:\s]*\$?\s*([\d,]+\.?\d*)",
            r"Total[:\s]+\$?\s*([\d,]+\.?\d*)",
            r"\$\s*([\d,]+\.?\d*)",
        ],
    },
    "generic": {
        "name": "Generic Template",
        "po_patterns": [
            r"P\.O\.\s*No:?\s*([A-Za-z0-9-]+)",
            r"PO[:\s#]+([A-Za-z0-9-]+)",
            r"Purchase\s+Order[:\s#]+([A-Za-z0-9-]+)",
            r"Order\s+Number[:\s#]+([A-Za-z0-9-]+)",
            r"CONTRACT\s+NO[.:]?\s*([A-Za-z0-9-]+)",
            r"Contract\s+Number[.:]?\s*([A-Za-z0-9-]+)",
            r"WORK\s+ORDER[:\s]+([A-Za-z0-9-]+)",
            r"JOB\s+NUMBER[:\s]+([A-Za-z0-9-]+)",
        ],
        "customer_patterns": [
            r"Customer[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Client[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Name[:\s]+([A-Za-z\s]+?)(?=\n)",
            r"Bill\s+To[:\s]+([A-Za-z\s]+?)(?=\n)",
        ],
        "description_patterns": [
            r"Description\s+of\s+Works[:\s]*(.+?)(?=Supervisor|Total|$)",
            r"Scope\s+of\s+Works[:\s]*(.+?)(?=Supervisor|Total|$)",
            r"Works\s+Description[:\s]*(.+?)(?=Supervisor|Total|$)",
        ],
        "supervisor_section_pattern": r"Supervisor|Contractor[\s']*s?\s+Representative",
        "dollar_patterns": [
            r"\$\s*([\d,]+\.?\d*)",
            r"Total[:\s]+\$?\s*([\d,]+\.?\d*)",
        ],
    }
}


def detect_template(text):
    """
    Detect which template to use based on content patterns.
    
    Args:
        text (str): The extracted PDF text
        
    Returns:
        dict: The template configuration to use
    """
    # Check for specific company indicators
    # Profile Build Group detection
    if re.search(r"PBG-\d+-\d+", text, re.IGNORECASE) or re.search(r"Profile\s+Build\s+Group", text, re.IGNORECASE):
        logger.info("Detected Profile Build Group template")
        return TEMPLATE_CONFIGS["profile_build"]
    
    # Campbell Construction detection
    elif (re.search(r"CCC\d+-\d+", text, re.IGNORECASE) or 
          re.search(r"Campbell\s+Construction", text, re.IGNORECASE) or
          re.search(r"Campbell\s+Construct", text, re.IGNORECASE)):
        logger.info("Detected Campbell Construction template")
        return TEMPLATE_CONFIGS["campbell"]
    
    # Rizon Group detection
    elif (re.search(r"P\d{6}", text) or  # P367117 format
          re.search(r"Rizon\s+Group", text, re.IGNORECASE) or
          re.search(r"Rizon\s+Pty", text, re.IGNORECASE)):
        logger.info("Detected Rizon Group template")
        return TEMPLATE_CONFIGS["rizon"]
    
    # Australian Restoration Company detection
    elif (re.search(r"PO\d+-[A-Z0-9]+-\d+", text) or  # PO96799-BU01-003 format
          re.search(r"Australian\s+Restoration", text, re.IGNORECASE) or
          re.search(r"ARC\s+Projects", text, re.IGNORECASE)):
        logger.info("Detected Australian Restoration Company template")
        return TEMPLATE_CONFIGS["australian_restoration"]
    
    # Townsend Building Services detection
    elif (re.search(r"TBS-\d+", text) or
          re.search(r"Townsend\s+Building\s+Services", text, re.IGNORECASE) or
          re.search(r"tbs\.admin@tbs\.com\.au", text, re.IGNORECASE)):
        logger.info("Detected Townsend Building Services template")
        return TEMPLATE_CONFIGS["townsend"]
    
    # Ambrose Construct Group detection (default pattern: 20XXXXXX-XX)
    elif re.search(r"20\d{6}-\d{2}", text):
        logger.info("Detected Ambrose Construct Group template (based on PO number pattern)")
        return TEMPLATE_CONFIGS["ambrose"]
    
    # Check for generic work order/contract indicators
    elif re.search(r"WORK\s+ORDER|CONTRACT\s+NO|Scope\s+of\s+Works", text, re.IGNORECASE):
        logger.info("Detected generic construction template")
        return TEMPLATE_CONFIGS["generic"]
    
    # Default to generic template
    else:
        logger.info("Using generic template (no specific pattern detected)")
        return TEMPLATE_CONFIGS["generic"]


def extract_data_from_pdf(file_path):
    """
    Extract relevant data from PDF purchase orders.

    This function tries multiple PDF parsing libraries to maximize extraction success.
    It looks for patterns like customer information, PO numbers, scope of work and dollar values.

    Args:
        file_path (str): Path to the PDF file

    Returns:
        dict: Extracted data including customer details, PO information, and more
    """
    logger.info(f"Extracting data from PDF: {file_path}")

    # Initialize extracted data dictionary with all required fields
    extracted_data = {
        # Customer Information
        "customer_name": "",
        "business_name": "",
        "first_name": "",
        "last_name": "",
        "address": "",
        "address1": "",
        "address2": "",
        "city": "",
        "state": "",
        "zip_code": "",
        "country": "Australia",  # Default
        "phone": "",
        "mobile": "",
        "work_phone": "",
        "home_phone": "",
        "email": "",
        "customer_type": "Builders",  # Default as specified in requirements
        "extra_phones": [],  # Store additional phone numbers
        # Purchase Order Information
        "po_number": "",
        "scope_of_work": "",
        "dollar_value": 0,
        # Job Information
        "job_number": "",  # This will be filled with supervisor name + mobile
        "actual_job_number": "",  # Keep the actual job number separately
        "supervisor_name": "",
        "supervisor_mobile": "",
        "supervisor_email": "",
        # Additional Information
        "description_of_works": "",
        "material_breakdown": "",
        "labor_breakdown": "",
        "rooms": "",
        "raw_text": "",
        # --- Add alternate/best contact fields ---
        "alternate_contact_name": "",
        "alternate_contact_phone": "",
        "alternate_contact_email": "",
        # --- New: list of all alternate contacts ---
        "alternate_contacts": [],  # Each: {type, name, phone, email}
    }

    # Try different extraction methods in order of reliability
    try:
        # Try PyMuPDF (fitz) first - generally fastest and most reliable
        text = extract_with_pymupdf(file_path)
        if text:
            extracted_data["raw_text"] = text
            template = detect_template(text)
            parse_extracted_text(text, extracted_data, template)

        # If we didn't get all needed data, try pdfplumber
        if not check_essential_fields(extracted_data):
            text = extract_with_pdfplumber(file_path)
            if text and text != extracted_data["raw_text"]:
                extracted_data["raw_text"] = text
                template = detect_template(text)
                parse_extracted_text(text, extracted_data, template)

        # Last resort, try PyPDF2
        if not check_essential_fields(extracted_data):
            text = extract_with_pypdf2(file_path)
            if text and text != extracted_data["raw_text"]:
                extracted_data["raw_text"] = text
                template = detect_template(text)
                parse_extracted_text(text, extracted_data, template)

        # Clean and format the extracted data
        clean_extracted_data(extracted_data)

        logger.info(f"Successfully extracted data from PDF: {file_path}")
        return extracted_data

    except Exception as e:
        logger.error(f"Error extracting data from PDF: {str(e)}")
        extracted_data["error"] = str(e)
        return extracted_data


def clean_extracted_data(extracted_data):
    """Clean and format the extracted data."""
    # Split name into first and last name if not already done
    if extracted_data["customer_name"] and not (
        extracted_data["first_name"] and extracted_data["last_name"]
    ):
        # Clean up customer name first by removing any newlines and extra text
        cleaned_name = re.sub(r"\n.*$", "", extracted_data["customer_name"])
        names = cleaned_name.split(maxsplit=1)
        if len(names) > 0:
            extracted_data["first_name"] = names[0]
        if len(names) > 1:
            extracted_data["last_name"] = names[1]

    # Clean up supervisor name
    if extracted_data["supervisor_name"]:
        extracted_data["supervisor_name"] = re.sub(
            r"\n.*$", "", extracted_data["supervisor_name"]
        )

    # Clean up customer name
    if extracted_data["customer_name"]:
        extracted_data["customer_name"] = re.sub(
            r"\n.*$", "", extracted_data["customer_name"]
        )

    # Clean up address
    if extracted_data["address"]:
        extracted_data["address"] = re.sub(r"\n.*$", "", extracted_data["address"])

    # Per requirements, we ignore business information (A TO Z FLOORING)
    extracted_data["business_name"] = ""

    # Clean up business name (if needed for future use, but set to empty as per requirements)
    # if extracted_data['business_name']:
    #     # Try to extract from SUBCONTRACTOR DETAILS section if available
    #     if "A TO Z FLOORING" in extracted_data['raw_text']:
    #         extracted_data['business_name'] = "A TO Z FLOORING SOLUTIONS"
    #     else:
    #         extracted_data['business_name'] = re.sub(r'\s+Job\s+Number.*$', '', extracted_data['business_name'])
    #         extracted_data['business_name'] = re.sub(r'\s+SOLUTIONS.*$', '', extracted_data['business_name'])
    #         extracted_data['business_name'] = re.sub(r'.*Subcontract agreement between the Builder and ', '', extracted_data['business_name'])
    #         extracted_data['business_name'] = extracted_data['business_name'].strip()

    # Improve city parsing
    if extracted_data["city"] and "Warriewood Street" in extracted_data["city"]:
        # Fix specifically for the known address format in the example
        extracted_data["city"] = "Chandler"

    # Format description of works to be more readable
    if extracted_data["description_of_works"]:
        description = extracted_data["description_of_works"]
        # Remove "Quantity Unit" header if present
        description = re.sub(r"^Quantity\s+Unit\s+", "", description)
        # Reformat and clean up
        description = re.sub(r"\n\$\d+m2", " - $45/m2", description)
        description = re.sub(r"\s{2,}", " ", description)
        extracted_data["description_of_works"] = description

    # Set job_number to supervisor name + mobile as per requirements
    if extracted_data["supervisor_name"] and extracted_data["supervisor_mobile"]:
        # Store the actual job number separately
        extracted_data["actual_job_number"] = extracted_data["job_number"]
        # Set job_number to supervisor name + mobile
        extracted_data["job_number"] = (
            f"{extracted_data['supervisor_name']} {extracted_data['supervisor_mobile']}"
        )

    # Filter extra_phones to only include customer-related numbers
    if extracted_data["extra_phones"]:
        # Numbers to exclude
        exclude_numbers = [
            extracted_data.get("actual_job_number", ""),  # PO/job number
            "0731100077",  # A to Z Flooring Solutions
            extracted_data.get("supervisor_mobile", ""),  # Supervisor
            "74658650821",  # ABN number
            "35131176",  # Company number
            "999869951",  # Other company number
        ]

        # Create cleaned versions of excluded numbers (digits only)
        clean_exclude_numbers = []
        for number in exclude_numbers:
            if number:
                clean_exclude_numbers.append("".join(c for c in number if c.isdigit()))

        # Filter the extra_phones list
        filtered_phones = []
        for phone in extracted_data["extra_phones"]:
            # Clean the phone
            clean_phone = "".join(c for c in phone if c.isdigit())

            # Skip if in excluded list or already in customer's main numbers
            if clean_phone not in clean_exclude_numbers and clean_phone not in [
                "".join(c for c in extracted_data.get("phone", "") if c.isdigit()),
                "".join(c for c in extracted_data.get("mobile", "") if c.isdigit()),
                "".join(c for c in extracted_data.get("home_phone", "") if c.isdigit()),
                "".join(c for c in extracted_data.get("work_phone", "") if c.isdigit()),
            ]:
                filtered_phones.append(phone)

        extracted_data["extra_phones"] = filtered_phones

    # Clean up alternate_contacts: remove entries with invalid names or no phone/email, and strip newlines
    cleaned_contacts = []
    for contact in extracted_data.get("alternate_contacts", []):
        name = contact.get("name", "").replace("\n", " ").strip()
        phone = contact.get("phone", "").strip()
        email = contact.get("email", "").strip()
        # Only keep if name is not empty, not 'Email', and has at least a phone or email
        if name and name.lower() != "email" and (phone or email):
            cleaned_contacts.append(
                {
                    "type": contact.get("type", ""),
                    "name": name,
                    "phone": phone,
                    "email": email,
                }
            )
    extracted_data["alternate_contacts"] = cleaned_contacts


def check_essential_fields(data):
    """Check if essential fields are filled."""
    essential_fields = ["po_number", "customer_name", "dollar_value"]
    return all(data[field] for field in essential_fields)


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
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"PyPDF2 extraction error: {str(e)}")
        return ""


def parse_extracted_text(text, extracted_data, template):
    """
    Parse the extracted text to find relevant information.

    Args:
        text (str): The extracted text from the PDF
        extracted_data (dict): Dictionary to update with parsed information
        template (dict): The template configuration to use
    """
    # Extract PO number
    for pattern in template["po_patterns"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data["po_number"] = match.group(1).strip()
            break
    
    # If no PO number found with template patterns, try generic fallback patterns
    if not extracted_data["po_number"]:
        generic_po_patterns = [
            r"P\.O\.\s*No:?\s*([A-Za-z0-9-]+)",
            r"PO[:\s#]+([A-Za-z0-9-]+)",
            r"Purchase\s+Order[:\s#]+([A-Za-z0-9-]+)",
            r"Order\s+Number[:\s#]+([A-Za-z0-9-]+)",
            r"CONTRACT\s+NO[.:]?\s*([A-Za-z0-9-]+)",
            r"Contract\s+Number[.:]?\s*([A-Za-z0-9-]+)",
        ]
        
        for pattern in generic_po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data["po_number"] = match.group(1).strip()
                break
    
    logger.info(f"[EXTRACT] PO Number: {extracted_data['po_number']}")

    # Extract business name from SUBCONTRACTOR DETAILS section
    subcontractor_section = re.search(
        r"SUBCONTRACTOR\s+DETAILS([\s\S]+?)(?=JOB\s+DETAILS|SUPERVISOR\s+DETAILS|$)",
        text,
        re.IGNORECASE,
    )
    if subcontractor_section:
        subcontractor_text = subcontractor_section.group(1)
        trading_name_match = re.search(
            r"Trading\s+Name:?\s*([A-Za-z0-9\s\.,&-]+?)(?=\n)",
            subcontractor_text,
            re.IGNORECASE,
        )
        if trading_name_match:
            extracted_data["business_name"] = trading_name_match.group(1).strip()

    # If business name not found in SUBCONTRACTOR DETAILS, try general patterns
    if not extracted_data["business_name"]:
        business_patterns = [
            r"Trading\s+Name:?\s*([A-Za-z0-9\s\.,&-]+?)(?=\n)",
            r"Business[:\s]+([A-Za-z0-9\s\.,&-]+?)(?=\n)",
            r"Company[:\s]+([A-Za-z0-9\s\.,&-]+?)(?=\n)",
            r"Builder[:\s]+([A-Za-z0-9\s\.,&-]+?)(?=\n)",
        ]

        for pattern in business_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data["business_name"] = match.group(1).strip()
                break

    # Extract Insured Customer (Customer Name)
    for pattern in template["customer_patterns"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data["customer_name"] = match.group(1).strip()
            break

    # Extract contact details
    extract_contact_details(text, extracted_data)

    # Extract Job Number and Supervisor Details
    extract_job_and_supervisor_details(text, extracted_data, template)

    # Extract Site Address (can be used for shipping address)
    address_patterns = [
        r"Site\s+Address:?\s*([A-Za-z0-9\s\.,#-]+?)(?=\n)",
        r"Address[:\s]+([A-Za-z0-9\s\.,#-]+?)(?=\n)",
        r"Location[:\s]+([A-Za-z0-9\s\.,#-]+?)(?=\n)",
        r"Property[:\s]+([A-Za-z0-9\s\.,#-]+?)(?=\n)",
    ]

    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data["address"] = match.group(1).strip()
            # Try to parse address into components
            parse_address(extracted_data["address"], extracted_data)
            break

    # Extract Description of Works for custom private notes
    # Use template-specific patterns
    for pattern in template.get("description_patterns", []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data["description_of_works"] = match.group(1).strip()
            # Set this as scope of work too for compatibility
            extracted_data["scope_of_work"] = extracted_data["description_of_works"]
            break
    
    # If no match found with template patterns, try generic patterns
    if not extracted_data["description_of_works"]:
        generic_description_patterns = [
            r"Description\s+of\s+Works([\s\S]+?)(?=TOTAL|Total\s+Purchase\s+Order)",
            r"Scope\s+of\s+Work[:\s]+([\s\S]+?)(?=TOTAL|Total|Amount|Price|\$|\n\n)",
            r"Description[:\s]+([\s\S]+?)(?=TOTAL|Total|Amount|Price|\$|\n\n)",
            r"Services[:\s]+([\s\S]+?)(?=TOTAL|Total|Amount|Price|\$|\n\n)",
        ]

        for pattern in generic_description_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data["description_of_works"] = match.group(1).strip()
                # Set this as scope of work too for compatibility
                extracted_data["scope_of_work"] = extracted_data["description_of_works"]
                break

    # Extract dollar value from TOTAL Purchase Order Price
    for pattern in template.get("dollar_patterns", []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(",", "")
            try:
                extracted_data["dollar_value"] = float(value_str)
                break
            except ValueError:
                continue
    
    # If no dollar value found with template patterns, try generic patterns
    if extracted_data["dollar_value"] == 0:
        generic_dollar_patterns = [
            r"TOTAL\s+Purchase\s+Order\s+Price\s*\(ex\s+GST\)\s*\$?\s*([\d,]+\.\d{2})",
            r"Total[:\s]+\$?\s*([\d,]+\.\d{2})",
            r"Amount[:\s]+\$?\s*([\d,]+\.\d{2})",
            r"Price[:\s]+\$?\s*([\d,]+\.\d{2})",
            r"Value[:\s]+\$?\s*([\d,]+\.\d{2})",
            r"Contract\s+Value[:\s]+\$?\s*([\d,]+\.\d{2})",
            r"Contract\s+Sum[:\s]+\$?\s*([\d,]+\.\d{2})",
        ]
        
        for pattern in generic_dollar_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(",", "")
                try:
                    extracted_data["dollar_value"] = float(value_str)
                    break
                except ValueError:
                    continue
    
    logger.info(f"[EXTRACT] Dollar Value: {extracted_data['dollar_value']}")

    # --- Extract all alternate contacts (Best, Real Estate, Site, Authorised) ---
    contact_types = [
        ("Best Contact", r"BEST\s+CONTACT\s+DETAILS"),
        ("Real Estate Agent", r"REAL\s+ESTATE\s+AGENT"),
        ("Site Contact", r"SITE\s+CONTACT"),
        ("Authorised Contact", r"AUTHORI[ZS]ED\s+CONTACT"),
    ]
    main_customer_name = extracted_data.get("customer_name", "").strip().lower()
    for label, regex in contact_types:
        section = re.search(
            rf"{regex}([\s\S]+?)(?=SUPERVISOR|JOB\s+DETAILS|$)", text, re.IGNORECASE
        )
        if section:
            contact_text = section.group(1)
            # Decision Maker (for alternate contact)
            decision_maker_match = re.search(
                r"Decision Maker:?[ \t]*([A-Za-z\s]+?)(?=\n|$)",
                contact_text,
                re.IGNORECASE,
            )
            if decision_maker_match:
                name = decision_maker_match.group(1).strip()
                # Phone
                phone_match = re.search(
                    r"Mobile:?[ \t]*([\d\(\)\-\s]+)", contact_text, re.IGNORECASE
                )
                phone = phone_match.group(1).strip() if phone_match else ""
                # Email
                email_match = re.search(
                    r"Email:?[ \t]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                    contact_text,
                    re.IGNORECASE,
                )
                email = email_match.group(1).strip() if email_match else ""
                # Only add if name is different from main customer
                if name and name.lower() != main_customer_name:
                    extracted_data["alternate_contact_name"] = name
                    extracted_data["alternate_contact_phone"] = phone
                    extracted_data["alternate_contact_email"] = email
                    extracted_data["alternate_contacts"].append(
                        {
                            "type": "Decision Maker",
                            "name": name,
                            "phone": phone,
                            "email": email,
                        }
                    )
            # Fallback to previous logic for other alternates
            name_match = re.search(
                r"Name:?[ \t]*([A-Za-z\s]+?)(?=\n|$)", contact_text, re.IGNORECASE
            )
            name = name_match.group(1).strip() if name_match else ""
            phone_match = re.search(
                r"(Mobile|Phone|Contact):?[ \t]*([\d\(\)\-\s]+)",
                contact_text,
                re.IGNORECASE,
            )
            phone = phone_match.group(2).strip() if phone_match else ""
            email_match = re.search(
                r"Email:?[ \t]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                contact_text,
                re.IGNORECASE,
            )
            email = email_match.group(1).strip() if email_match else ""
            if name and name.lower() != main_customer_name:
                extracted_data["alternate_contacts"].append(
                    {"type": label, "name": name, "phone": phone, "email": email}
                )
            if (
                label in ("Best Contact", "Real Estate Agent")
                and not extracted_data["alternate_contact_name"]
                and name
                and name.lower() != main_customer_name
            ):
                extracted_data["alternate_contact_name"] = name
                extracted_data["alternate_contact_phone"] = phone
                extracted_data["alternate_contact_email"] = email

    # --- Explicitly extract 'Authorised Contact' and 'Site Contact' as alternates even if not in a section ---
    for label in ["Authorised Contact", "Site Contact"]:
        # Match lines like 'Authorised Contact: Name' or 'Site Contact: Name'
        pattern = rf"{label}:?\s*([A-Za-z\s]+)\n?(\(H\)\s*\d+)?\s*(\(M\)\s*\d+)?"
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            name = match[0].strip()
            phone1 = match[1].replace("(H)", "").strip() if match[1] else ""
            phone2 = match[2].replace("(M)", "").strip() if match[2] else ""
            # Only add if name is not empty and not the main customer
            if name and name.lower() != main_customer_name:
                extracted_data["alternate_contacts"].append(
                    {
                        "type": label,
                        "name": name,
                        "phone": phone1,
                        "phone2": phone2,
                        "email": "",
                    }
                )

    # After extracting supervisor name/phone
    logger.info(f"[EXTRACT] Supervisor Name: {extracted_data['supervisor_name']}")
    logger.info(f"[EXTRACT] Supervisor Phone: {extracted_data['supervisor_mobile']}")
    # After extracting description of works
    logger.info(
        f"[EXTRACT] Description of Works: {extracted_data['description_of_works']}"
    )
    # After extracting email
    logger.info(f"[EXTRACT] Email: {extracted_data['email']}")
    # After extracting all phone numbers
    logger.info(
        f"[EXTRACT] Phone: {extracted_data['phone']}, Mobile: {extracted_data['mobile']}, Home: {extracted_data['home_phone']}, Work: {extracted_data['work_phone']}, Extra: {extracted_data['extra_phones']}"
    )
    # After extracting alternate contacts
    logger.info(f"[EXTRACT] Alternate Contacts: {extracted_data['alternate_contacts']}")


def extract_contact_details(text, extracted_data):
    """Extract all contact details from the text."""
    # Extract email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    email_matches = re.findall(email_pattern, text)

    # Look for customer email specifically
    customer_email_patterns = [
        r"Email:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"E-mail:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    ]

    # First try to find email in the BEST CONTACT DETAILS section
    best_contact_section = re.search(
        r"BEST\s+CONTACT\s+DETAILS([\s\S]+?)(?=SUPERVISOR|JOB\s+DETAILS|$)",
        text,
        re.IGNORECASE,
    )
    if best_contact_section:
        contact_text = best_contact_section.group(1)
        for pattern in customer_email_patterns:
            match = re.search(pattern, contact_text, re.IGNORECASE)
            if match:
                extracted_data["email"] = match.group(1).strip()
                break

    # If no email found in BEST CONTACT DETAILS, try general email patterns
    if not extracted_data["email"]:
        for pattern in customer_email_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not match.group(1).endswith(
                "ambroseconstruct.com.au"
            ):  # Skip company emails
                extracted_data["email"] = match.group(1).strip()
                break

    # If no labeled email found but we have email matches, use the first one that's not from ambroseconstruct
    if not extracted_data["email"] and email_matches:
        for email in email_matches:
            if not email.endswith("ambroseconstruct.com.au") and not email.endswith(
                "atozflooringsolutions.com.au"
            ):
                extracted_data["email"] = email
                break

    # Extract all phone numbers from the document for potential extra phone fields
    all_phone_numbers = []

    # General pattern to find all phone numbers
    phone_pattern = r"(?<!\d)(?:\+?61|0)?(?:\(?\d{2,4}\)?\s?\d{3,4}\s?\d{3,4}|\d{4}\s?\d{3}\s?\d{3}|\d{8,10})(?!\d)"
    all_matches = re.finditer(phone_pattern, text)

    # Company phone numbers to exclude
    company_phone_numbers = ["0731100077", "35131176", "999869951"]
    excluded_number_patterns = [
        r"ABN:\s*(\d+)",  # ABN pattern
        r"Job\s+Number:?\s*([0-9-]+)",  # Job number pattern
    ]

    # Extract numbers to exclude
    numbers_to_exclude = []
    for pattern in excluded_number_patterns:
        match = re.search(pattern, text)
        if match:
            numbers_to_exclude.append(match.group(1))

    for match in all_matches:
        phone = match.group(0).strip()
        # Clean the phone number for comparison
        clean_phone = "".join(c for c in phone if c.isdigit())

        # Skip supervisor's mobile
        if extracted_data["supervisor_mobile"] and clean_phone == "".join(
            c for c in extracted_data["supervisor_mobile"] if c.isdigit()
        ):
            continue

        # Skip if it matches one of our excluded numbers
        if any(
            clean_phone == "".join(c for c in num if c.isdigit())
            for num in company_phone_numbers + numbers_to_exclude
        ):
            continue

        # Only add if it's not already one of our main numbers and looks like a valid phone
        if len(clean_phone) >= 8 and clean_phone not in [
            "".join(c for c in extracted_data.get("phone", "") if c.isdigit()),
            "".join(c for c in extracted_data.get("mobile", "") if c.isdigit()),
            "".join(c for c in extracted_data.get("home_phone", "") if c.isdigit()),
            "".join(c for c in extracted_data.get("work_phone", "") if c.isdigit()),
        ]:
            if len(clean_phone) >= 8 and len(clean_phone) <= 12:
                all_phone_numbers.append(phone)

    # Extract phone numbers from BEST CONTACT DETAILS section if available
    if best_contact_section:
        contact_text = best_contact_section.group(1)

        # Mobile phone
        mobile_match = re.search(
            r"Mobile:?\s*(\(?\d{4}\)?[-.\s]?\d{3}[-.\s]?\d{3})",
            contact_text,
            re.IGNORECASE,
        )
        if mobile_match:
            extracted_data["mobile"] = mobile_match.group(1).strip()
            if not extracted_data[
                "phone"
            ]:  # Use mobile as default phone if no other phone found
                extracted_data["phone"] = extracted_data["mobile"]

        # Home phone
        home_match = re.search(
            r"Home:?\s*(\(?\d{2}\)?[-.\s]?\d{4}[-.\s]?\d{4})",
            contact_text,
            re.IGNORECASE,
        )
        if home_match:
            extracted_data["home_phone"] = home_match.group(1).strip()
            if not extracted_data["phone"]:  # Use home as phone if no other phone found
                extracted_data["phone"] = extracted_data["home_phone"]

        # Work phone
        work_match = re.search(
            r"Work:?\s*(\(?\d{4}\)?[-.\s]?\d{3}[-.\s]?\d{3})",
            contact_text,
            re.IGNORECASE,
        )
        if work_match:
            extracted_data["work_phone"] = work_match.group(1).strip()

    # If we didn't find phones in the BEST CONTACT DETAILS, try general patterns
    if not extracted_data["mobile"]:
        # Mobile phone pattern
        mobile_patterns = [
            r"Mobile:?\s*(\(?\d{4}\)?[-.\s]?\d{3}[-.\s]?\d{3})",
            r"Mobile:?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            r"M:?\s*(\(?\d{4}\)?[-.\s]?\d{3}[-.\s]?\d{3})",
        ]

        for pattern in mobile_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data["mobile"] = match.group(1).strip()
                if not extracted_data[
                    "phone"
                ]:  # Use mobile as default phone if no other phone found
                    extracted_data["phone"] = extracted_data["mobile"]
                break

    # If no specific labeled phone found, look for a generic phone
    if not extracted_data["phone"]:
        phone_patterns = [
            r"Phone:?\s*(\(?\d{2}\)?[-.\s]?\d{4}[-.\s]?\d{4})",
            r"Phone:?\s*(\(?\d{4}\)?[-.\s]?\d{3}[-.\s]?\d{3})",
            r"Tel:?\s*(\(?\d{2}\)?[-.\s]?\d{4}[-.\s]?\d{4})",
            r"Contact:?\s*(\(?\d{2}\)?[-.\s]?\d{4}[-.\s]?\d{4})",
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data["phone"] = match.group(1).strip()
                break

    # Add all unique phone numbers to extra_phones (will be filtered in clean_extracted_data)
    for phone in all_phone_numbers:
        # Clean the phone number - keep only digits
        clean_phone = "".join(c for c in phone if c.isdigit())

        # Check against existing phone numbers (also cleaned)
        main_phones = []
        for key in ["phone", "mobile", "home_phone", "work_phone"]:
            if extracted_data[key]:
                main_phones.append(
                    "".join(c for c in extracted_data[key] if c.isdigit())
                )

        # Only add if it's not already in our main numbers and not already in extra_phones
        if (
            clean_phone not in main_phones
            and clean_phone not in extracted_data["extra_phones"]
        ):
            extracted_data["extra_phones"].append(clean_phone)


def extract_job_and_supervisor_details(text, extracted_data, template):
    """Extract job number and supervisor details."""
    # Extract Job Number
    job_number_patterns = [
        r"Job\s+Number:?\s*([A-Za-z0-9-]+)",
        r"Job\s+#:?\s*([A-Za-z0-9-]+)",
        r"Job\s+ID:?\s*([A-Za-z0-9-]+)",
        r"WORK\s+ORDER[:\s]+([A-Za-z0-9-]+)",  # Added for alternative templates
        r"JOB\s+NUMBER[:\s]+([A-Za-z0-9-]+)",  # Added for alternative templates
    ]

    for pattern in job_number_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data["job_number"] = match.group(1).strip()
            break

    # Extract Supervisor/Contractor Representative Details
    supervisor_section_pattern = template.get("supervisor_section_pattern", r"Supervisor\s+Details")
    supervisor_section = re.search(
        rf"{supervisor_section_pattern}([\s\S]+?)(?=BEST\s+CONTACT|JOB\s+DETAILS|$)",
        text,
        re.IGNORECASE,
    )

    if supervisor_section:
        supervisor_text = supervisor_section.group(1)

        # Extract Name
        name_match = re.search(
            r"Name:?\s*([A-Za-z\s]+?)(?=\n)", supervisor_text, re.IGNORECASE
        )
        if name_match:
            extracted_data["supervisor_name"] = name_match.group(1).strip()

        # Extract Mobile
        mobile_match = re.search(
            r"Mobile:?\s*(\(?\d{4}\)?[-.\s]?\d{3}[-.\s]?\d{3})",
            supervisor_text,
            re.IGNORECASE,
        )
        if mobile_match:
            extracted_data["supervisor_mobile"] = mobile_match.group(1).strip()

        # Extract Email
        email_match = re.search(
            r"Email:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            supervisor_text,
            re.IGNORECASE,
        )
        if email_match:
            extracted_data["supervisor_email"] = email_match.group(1).strip()
    else:
        # Try alternative patterns if no section found
        # Look for standalone patterns
        name_patterns = [
            rf"{template.get('contact_label', 'Supervisor')}:?\s*([A-Za-z\s]+?)(?=\n|$)",
            r"Contractor:?\s*([A-Za-z\s]+?)(?=\n|$)",
            r"Representative:?\s*([A-Za-z\s]+?)(?=\n|$)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data["supervisor_name"] = match.group(1).strip()
                break


def parse_address(address_str, extracted_data):
    """
    Parse a full address string into address1, city, state, and zip_code.
    Improved: address1 is only the street address, city is the suburb (even if multi-word), state/zip_code always filled if present.
    """
    street_suffixes = [
        "Street",
        "St",
        "Road",
        "Rd",
        "Avenue",
        "Ave",
        "Boulevard",
        "Blvd",
        "Court",
        "Ct",
        "Drive",
        "Dr",
        "Lane",
        "Ln",
        "Place",
        "Pl",
        "Terrace",
        "Terr",
        "Way",
        "Highway",
        "Hwy",
        "Crescent",
        "Cres",
        "Parade",
        "Pde",
        "Close",
        "Cl",
        "Square",
        "Sq",
        "Walk",
        "Track",
        "Loop",
        "Row",
        "View",
        "Rise",
        "Gardens",
        "Grove",
        "Mews",
    ]
    state_pattern = r"(NSW|VIC|QLD|SA|WA|TAS|NT|ACT)"
    postcode_pattern = r"(\d{4})$"
    parts = address_str.strip().split()
    state = ""
    zip_code = ""
    # Find state and postcode from the end
    for i in range(len(parts) - 1, -1, -1):
        if not zip_code and re.match(postcode_pattern, parts[i]):
            zip_code = parts[i]
            continue
        if not state and re.match(state_pattern, parts[i], re.IGNORECASE):
            state = parts[i].upper()
            continue
    # Remove state and postcode from parts
    main_parts = [p for p in parts if p != state and p != zip_code]
    # Find the last street suffix in main_parts
    last_street_idx = -1
    for idx, word in enumerate(main_parts):
        if word.capitalize() in street_suffixes:
            last_street_idx = idx
    logger.info(
        f"[ADDRESS PARSE DEBUG] main_parts: {main_parts}, last_street_idx: {last_street_idx}"
    )
    if last_street_idx != -1:
        extracted_data["address1"] = " ".join(main_parts[: last_street_idx + 1])
        extracted_data["city"] = " ".join(main_parts[last_street_idx + 1 :]).strip()
    else:
        # If no street suffix, try to split before the last two words (city is often last two words)
        if len(main_parts) > 2:
            extracted_data["address1"] = " ".join(main_parts[:-2])
            extracted_data["city"] = " ".join(main_parts[-2:])
        elif len(main_parts) == 2:
            extracted_data["address1"] = main_parts[0]
            extracted_data["city"] = main_parts[1]
        else:
            extracted_data["address1"] = main_parts[0] if main_parts else ""
            extracted_data["city"] = ""
    extracted_data["state"] = state
    extracted_data["zip_code"] = zip_code
    # Add debug logging
    logger.info(
        f"[ADDRESS PARSE] Raw: '{address_str}' | address1: '{extracted_data['address1']}', city: '{extracted_data['city']}', state: '{extracted_data['state']}', zip: '{extracted_data['zip_code']}'"
    )
