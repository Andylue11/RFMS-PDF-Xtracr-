import json
from utils.pdf_extractor import extract_data_from_pdf

def test_extractor():
    # Test on the reference PDF file
    pdf_path = "testing pdfs/EXTRACTR REFERENCE Purchase Order.pdf"
    
    # Extract data using our updated extractor
    extracted_data = extract_data_from_pdf(pdf_path)
    
    # Print the extracted data in a readable format
    print("\n=== EXTRACTED DATA ===")
    print(json.dumps(extracted_data, indent=2, default=str))
    
    # Print all import data fields in a clean, organized format
    print("\n=== IMPORT DATA FOR API ===")
    print("Customer Information:")
    print(f"  Name: {extracted_data.get('first_name', '')} {extracted_data.get('last_name', '')}")
    print(f"  Customer Type: {extracted_data.get('customer_type', '')}")
    print(f"  Email: {extracted_data.get('email', '')}")
    print(f"  Phone: {extracted_data.get('phone', '')}")
    print(f"  Mobile: {extracted_data.get('mobile', '')}")
    print(f"  Work Phone: {extracted_data.get('work_phone', '')}")
    print(f"  Home Phone: {extracted_data.get('home_phone', '')}")
    
    print("\nAddress Information:")
    print(f"  Address Line 1: {extracted_data.get('address1', '')}")
    print(f"  Address Line 2: {extracted_data.get('address2', '')}")
    print(f"  City: {extracted_data.get('city', '')}")
    print(f"  State: {extracted_data.get('state', '')}")
    print(f"  Zip Code: {extracted_data.get('zip_code', '')}")
    print(f"  Country: {extracted_data.get('country', '')}")
    
    print("\nJob Information:")
    print(f"  Job Number (API field): {extracted_data.get('job_number', '')}")
    print(f"  Actual Job Number: {extracted_data.get('actual_job_number', '')}")
    print(f"  PO Number: {extracted_data.get('po_number', '')}")
    print(f"  Supervisor Name: {extracted_data.get('supervisor_name', '')}")
    print(f"  Supervisor Mobile: {extracted_data.get('supervisor_mobile', '')}")
    print(f"  Supervisor Email: {extracted_data.get('supervisor_email', '')}")
    
    print("\nWork Details:")
    print(f"  Dollar Value: ${extracted_data.get('dollar_value', 0):.2f}")
    
    # Print description of works (formatted)
    print("\nDescription of Works:")
    description = extracted_data.get('description_of_works', '')
    if description:
        # Print full description
        print(description)
    else:
        print("  No description available")
    
    # Print any extra phone numbers
    print("\nExtra Phone Numbers:")
    if extracted_data.get('extra_phones'):
        for i, phone in enumerate(extracted_data['extra_phones']):
            print(f"  Extra Phone {i+1}: {phone}")
    else:
        print("  No extra phone numbers found")

if __name__ == "__main__":
    test_extractor() 