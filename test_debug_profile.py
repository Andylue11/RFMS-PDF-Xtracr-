import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.pdf_extractor import extract_data_from_pdf, extract_with_pymupdf, detect_template
import re
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Test Profile Build Group PDF
print("\n=== Testing Profile Build Group PDF ===")
pdf_path = os.path.join("testing pdfs", "Profile Build Group TESTING PDF Example1.pdf")

if os.path.exists(pdf_path):
    # Extract raw text first
    text = extract_with_pymupdf(pdf_path)
    
    # Show what we're looking for
    print("\n--- Looking for SITE CONTACT ---")
    site_contact_match = re.search(
        r"SITE\s+CONTACT:\s*([A-Za-z\s]+?)(?=\nSITE\s+CONTACT\s+PHONE|$)",
        text,
        re.IGNORECASE
    )
    if site_contact_match:
        print(f"FOUND SITE CONTACT: '{site_contact_match.group(1)}'")
    else:
        print("NO MATCH for SITE CONTACT")
        # Try simpler pattern
        simple_match = re.search(r"SITE\s+CONTACT:\s*(.+)", text, re.IGNORECASE)
        if simple_match:
            print(f"Simple pattern found: '{simple_match.group(1)}'")
    
    print("\n--- Looking for SITE CONTACT PHONE ---")
    phone_match = re.search(
        r"SITE\s+CONTACT\s+PHONE:\s*([0-9\s\-\(\)]+)",
        text,
        re.IGNORECASE
    )
    if phone_match:
        print(f"FOUND PHONE: '{phone_match.group(1)}'")
    else:
        print("NO MATCH for PHONE")
    
    print("\n--- Looking for Supervisor ---")
    # Show the exact text around Supervisor
    supervisor_section = re.search(r"(Supervisor:[\s\S]{0,200})", text, re.IGNORECASE)
    if supervisor_section:
        print("Supervisor section:")
        print(repr(supervisor_section.group(1)))
    
    # Try different supervisor patterns
    patterns = [
        r"Supervisor:\s*\n([A-Za-z\s]+?)(?=\nABN)",
        r"Supervisor:\s*\n([A-Za-z\s]+?)(?=\n)",
        r"Supervisor:\s*\r?\n([A-Za-z\s]+?)(?=\r?\n)",  # Handle Windows line endings
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"Pattern {i} matched: '{match.group(1)}'")
        else:
            print(f"Pattern {i} did not match")
    
    # Extract phone after supervisor
    phone_pattern = r"Supervisor:[\s\S]*?Phone:\s*\r?\n([0-9\s\-\(\)]+)"
    phone_match = re.search(phone_pattern, text, re.IGNORECASE)
    if phone_match:
        print(f"\nSupervisor phone found: '{phone_match.group(1)}'")
    
    # Now run the full extraction to see what happens
    print("\n--- Running Full Extraction ---")
    data = extract_data_from_pdf(pdf_path)
    
    print(f"\nCustomer Name: {data.get('customer_name', 'NOT FOUND')}")
    print(f"Supervisor Name: {data.get('supervisor_name', 'NOT FOUND')}")
    print(f"Supervisor Mobile: {data.get('supervisor_mobile', 'NOT FOUND')}")
    print(f"Phone: {data.get('phone', 'NOT FOUND')}")
    
else:
    print(f"PDF file not found: {pdf_path}") 