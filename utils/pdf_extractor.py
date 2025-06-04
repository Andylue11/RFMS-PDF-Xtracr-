import pdfplumber
import re
from typing import Dict, Optional, Any
from .template_detector import TemplateDetector, BuilderType

class PDFExtractor:
    def __init__(self):
        self.template_detector = TemplateDetector()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.
        """
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            # Debug: Print first 2500 characters of extracted text
            print("\n=== FIRST 2500 CHARACTERS OF EXTRACTED TEXT ===")
            print(text[:2500])
            print("=== END OF EXTRACTED TEXT SAMPLE ===\n")
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""
        return text

    def parse_address(self, address_text: str) -> Dict[str, str]:
        """
        Parse address text into components.
        """
        address_parts = {
            'address1': '',
            'address2': '',
            'city': '',
            'state': '',
            'postal_code': ''
        }

        if not address_text:
            return address_parts

        # Split address into lines
        lines = [line.strip() for line in address_text.split('\n') if line.strip()]
        
        if not lines:
            return address_parts

        # First line is usually street address
        address_parts['address1'] = lines[0]

        # Second line might be additional address info
        if len(lines) > 1:
            address_parts['address2'] = lines[1]

        # Last line usually contains city, state, and postal code
        if len(lines) > 2:
            last_line = lines[-1]
            # Try to match state and postal code pattern
            state_postal_match = re.search(r'([A-Z]{2,3})\s+(\d{4})', last_line)
            if state_postal_match:
                address_parts['state'] = state_postal_match.group(1)
                address_parts['postal_code'] = state_postal_match.group(2)
                # City is everything before the state
                city = last_line[:state_postal_match.start()].strip()
                address_parts['city'] = city

        return address_parts

    def parse_name(self, name_text: str) -> Dict[str, str]:
        """
        Parse full name into first and last name.
        """
        name_parts = {
            'first_name': '',
            'last_name': ''
        }

        if not name_text:
            return name_parts

        # Split name into parts
        parts = name_text.strip().split()
        if len(parts) >= 2:
            name_parts['first_name'] = parts[0]
            name_parts['last_name'] = ' '.join(parts[1:])
        elif len(parts) == 1:
            name_parts['last_name'] = parts[0]

        return name_parts

    def extract_data_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract data from PDF using template detection.
        """
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {}

        # Detect template type
        builder_type, patterns = self.template_detector.detect_template(text)
        if not patterns:
            return {'error': 'Unknown template type'}

        # Debug: Print detected template type
        print(f"\nDetected template type: {builder_type.value}")

        # Extract data using template patterns
        extracted_data = {
            'builder_type': builder_type.value,
            'po_number': self.template_detector.extract_field(text, patterns.po_pattern),
            'dollar_value': self.template_detector.extract_dollar_value(text, patterns.dollar_value_pattern),
            'description_of_works': self.template_detector.extract_field(text, patterns.description_pattern),
            'supervisor_name': self.template_detector.extract_field(text, patterns.supervisor_pattern)
        }

        # Debug: Print extracted fields
        print("\nExtracted fields:")
        for key, value in extracted_data.items():
            print(f"{key}: {value}")

        # Extract and parse customer name
        customer_name = self.template_detector.extract_field(text, patterns.customer_name_pattern)
        if customer_name:
            name_parts = self.parse_name(customer_name)
            extracted_data.update(name_parts)

        # Extract and parse address
        address_text = self.template_detector.extract_field(text, patterns.address_pattern)
        if address_text:
            address_parts = self.parse_address(address_text)
            extracted_data.update(address_parts)

        # Extract dates if patterns exist
        if patterns.commencement_date_pattern:
            commencement_date = self.template_detector.extract_field(text, patterns.commencement_date_pattern)
            if commencement_date:
                extracted_data['commencement_date'] = commencement_date

        if patterns.completion_date_pattern:
            completion_date = self.template_detector.extract_field(text, patterns.completion_date_pattern)
            if completion_date:
                extracted_data['completion_date'] = completion_date

        # Extract phone numbers (common pattern across templates)
        phone_patterns = [
            r'Phone:\s*(\d[\d\s-]+)',
            r'Mobile:\s*(\d[\d\s-]+)',
            r'Contact No\.:\s*(\d[\d\s-]+)',
            r'Phone1:\s*(\d[\d\s-]+)',
            r'Phone2:\s*(\d[\d\s-]+)',
            r'Home:\s*(\d[\d\s-]+)',
            r'Work:\s*(\d[\d\s-]+)'
        ]

        phones = []
        for pattern in phone_patterns:
            phone = self.template_detector.extract_field(text, pattern)
            if phone:
                phones.append(phone)

        if phones:
            extracted_data['phone'] = phones[0]
            if len(phones) > 1:
                extracted_data['mobile'] = phones[1]
            if len(phones) > 2:
                extracted_data['extra_phones'] = phones[2:]

        # Extract email (common pattern across templates)
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, text)
        if email_match:
            extracted_data['email'] = email_match.group(0)

        return extracted_data 