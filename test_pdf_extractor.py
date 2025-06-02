import json
import os
from utils.pdf_extractor import extract_data_from_pdf

def test_extractor_all_builders():
    # List of all builder PDF test files
    pdf_files = [
        "Profile Build Group TESTING PDF Example1.pdf",
        "Profile Build Group TESTING PDF Example2.pdf",
        "Australian Restoration Company TESTING PDF Example1.pdf",
        "Australian Restoration Company TESTING PDF Example2.pdf",
        "Townsend Building Services TESTING PDF Example1.pdf",
        "Townsend Building Services TESTING PDF Example2.pdf",
        "Rizon Group TESTING PDF Example1.pdf",
        "Rizon Group TESTING PDF Example2.PDF",
        "Campbell Construct TESTING PDF Example1.pdf",
        "Campbell Construct TESTING PDF Example2.pdf",
    ]
    base_dir = "testing pdfs"
    for pdf_file in pdf_files:
        pdf_path = os.path.join(base_dir, pdf_file)
        print(f"\n================= {pdf_file} =================")
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            continue
        extracted_data = extract_data_from_pdf(pdf_path)
        print(json.dumps(extracted_data, indent=2, default=str))
        # Print summary of key fields
        print("\n--- SUMMARY ---")
        print(f"PO Number: {extracted_data.get('po_number', '')}")
        print(f"Customer Name: {extracted_data.get('customer_name', '')}")
        print(f"Email: {extracted_data.get('email', '')}")
        print(f"Phone: {extracted_data.get('phone', '')}")
        print(f"Mobile: {extracted_data.get('mobile', '')}")
        print(f"Work Phone: {extracted_data.get('work_phone', '')}")
        print(f"Home Phone: {extracted_data.get('home_phone', '')}")
        print(f"Address: {extracted_data.get('address', '')}")
        print(f"City: {extracted_data.get('city', '')}")
        print(f"Job Number: {extracted_data.get('job_number', '')}")
        print(f"Supervisor Name: {extracted_data.get('supervisor_name', '')}")
        print(f"Supervisor Mobile: {extracted_data.get('supervisor_mobile', '')}")
        print(f"Description of Works: {extracted_data.get('description_of_works', '')[:100]}")
        print(f"Dollar Value: ${extracted_data.get('dollar_value', 0):.2f}")
        print(f"Alternate Contacts: {extracted_data.get('alternate_contacts', [])}")
        print(f"Commencement Date: {extracted_data.get('commencement_date', '')}")
        print(f"Installation Date: {extracted_data.get('installation_date', '')}")
        print(f"Extra Phones: {extracted_data.get('extra_phones', [])}")
        print(f"Extra Emails: {extracted_data.get('extra_emails', []) if 'extra_emails' in extracted_data else []}")

if __name__ == "__main__":
    test_extractor_all_builders() 