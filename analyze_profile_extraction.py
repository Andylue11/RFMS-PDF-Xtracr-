import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.pdf_extractor import extract_data_from_pdf, extract_with_pymupdf
import re
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Test Profile Build Group PDF
print("\n=== Analyzing Profile Build Group PDF Extraction ===")
pdf_path = os.path.join("testing pdfs", "Profile Build Group TESTING PDF Example1.pdf")

if os.path.exists(pdf_path):
    # Extract raw text first
    text = extract_with_pymupdf(pdf_path)
    
    print("\n--- First 10 lines of PDF ---")
    lines = text.split('\n')[:10]
    for i, line in enumerate(lines):
        print(f"Line {i}: {line}")
    
    print("\n--- Looking for SITE CONTACT ---")
    site_contact_match = re.search(
        r"SITE\s+CONTACT:\s*([A-Za-z\s]+?)(?=\n)",
        text,
        re.IGNORECASE
    )
    if site_contact_match:
        print(f"SITE CONTACT found: '{site_contact_match.group(1)}'")
    else:
        print("SITE CONTACT not found")
        # Try alternative patterns
        alt_match = re.search(r"SITE\s+CONTACT:\s*(.+)", text, re.IGNORECASE)
        if alt_match:
            print(f"Alternative match found: '{alt_match.group(1)}'")
    
    print("\n--- Looking for Phone ---")
    phone_match = re.search(
        r"SITE\s+CONTACT\s+PHONE:\s*([0-9\s\-\(\)]+)",
        text,
        re.IGNORECASE
    )
    if phone_match:
        print(f"Phone found: '{phone_match.group(1)}'")
    else:
        print("Phone not found")
    
    print("\n--- Looking for Supervisor ---")
    supervisor_match = re.search(
        r"Supervisor:\s*\n([A-Za-z\s]+?)(?:\n|ABN:|$)",
        text,
        re.IGNORECASE | re.MULTILINE
    )
    if supervisor_match:
        print(f"Supervisor found: '{supervisor_match.group(1)}'")
    else:
        print("Supervisor not found")
    
    print("\n--- Looking for Address ---")
    # Show what comes after different address indicators
    patterns = [
        r"SITE\s+LOCATION:\s*(.+)",
        r"Job\s+Address:\s*(.+)",
        r"Address:\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"Pattern '{pattern}' found: '{match.group(1)}'")
    
    print("\n--- Full Extraction Results ---")
    data = extract_data_from_pdf(pdf_path, builder_name="PROFILE BUILD GROUP")
    
    print(f"\nExtracted fields:")
    print(f"Customer Name: {data.get('customer_name', 'NOT FOUND')}")
    print(f"Phone: {data.get('phone', 'NOT FOUND')}")
    print(f"Address: {data.get('address', 'NOT FOUND')}")
    print(f"Address1: {data.get('address1', 'NOT FOUND')}")
    print(f"City: {data.get('city', 'NOT FOUND')}")
    print(f"State: {data.get('state', 'NOT FOUND')}")
    print(f"Zip: {data.get('zip_code', 'NOT FOUND')}")
    print(f"Supervisor Name: {data.get('supervisor_name', 'NOT FOUND')}")
    print(f"Supervisor Phone: {data.get('supervisor_mobile', 'NOT FOUND')}")
    print(f"PO Number: {data.get('po_number', 'NOT FOUND')}")
    print(f"Dollar Value: {data.get('dollar_value', 'NOT FOUND')}")
    
    print("\n--- Searching for HELEN KANE specifically ---")
    if "HELEN KANE" in text:
        # Find context around HELEN KANE
        idx = text.find("HELEN KANE")
        context_start = max(0, idx - 50)
        context_end = min(len(text), idx + 100)
        context = text[context_start:context_end]
        print(f"Context around HELEN KANE:\n{context}")
else:
    print(f"PDF file not found: {pdf_path}") 