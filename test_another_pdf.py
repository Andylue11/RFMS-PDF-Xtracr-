import json
from utils.pdf_extractor import extract_data_from_pdf

def test_another_pdf():
    # Test on another PDF file
    pdf_path = "testing pdfs/master test Purchase Order.pdf"
    
    # Extract data using our updated extractor
    extracted_data = extract_data_from_pdf(pdf_path)
    
    # Print the extracted data in a readable format
    print("\n=== EXTRACTED DATA (MASTER TEST PO) ===")
    print(json.dumps(extracted_data, indent=2, default=str))
    
    # Check for specific key fields
    print("\n=== KEY FIELDS ===")
    print(f"PO Number: {extracted_data.get('po_number', 'Not found')}")
    print(f"Customer Name: {extracted_data.get('customer_name', 'Not found')}")
    print(f"Email: {extracted_data.get('email', 'Not found')}")
    print(f"Phone: {extracted_data.get('phone', 'Not found')}")
    print(f"Address: {extracted_data.get('address', 'Not found')}")
    print(f"City: {extracted_data.get('city', 'Not found')}")
    print(f"Job Number: {extracted_data.get('job_number', 'Not found')}")
    print(f"Supervisor Name: {extracted_data.get('supervisor_name', 'Not found')}")
    print(f"Description of Works: {extracted_data.get('description_of_works', 'Not found')[:100]}...")
    print(f"Dollar Value: ${extracted_data.get('dollar_value', 'Not found')}")

if __name__ == "__main__":
    test_another_pdf() 