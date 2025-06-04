import json
from utils.pdf_extractor import PDFExtractor
from utils.template_detector import BuilderType

def test_extractor():
    # Initialize the PDF extractor
    extractor = PDFExtractor()
    
    # Test on the alternate One Solutions PDF file with dates
    pdf_path = "testing pdfs/One Soutions 4242424 TESTING PDF Example.pdf"
    
    # Extract data using our updated extractor
    extracted_data = extractor.extract_data_from_pdf(pdf_path)
    
    # Print the extracted data in a readable format
    print("\n=== EXTRACTED DATA ===")
    print(json.dumps(extracted_data, indent=2, default=str))
    
    # Print all import data fields in a clean, organized format
    print("\n=== IMPORT DATA FOR API ===")
    print(f"Builder Type: {extracted_data.get('builder_type', 'Unknown')}")
    
    print("\nCustomer Information:")
    print(f"  Name: {extracted_data.get('first_name', '')} {extracted_data.get('last_name', '')}")
    print(f"  Email: {extracted_data.get('email', '')}")
    print(f"  Phone: {extracted_data.get('phone', '')}")
    print(f"  Mobile: {extracted_data.get('mobile', '')}")
    if extracted_data.get('extra_phones'):
        for i, phone in enumerate(extracted_data['extra_phones']):
            print(f"  Extra Phone {i+1}: {phone}")
    
    print("\nAddress Information:")
    print(f"  Address Line 1: {extracted_data.get('address1', '')}")
    print(f"  Address Line 2: {extracted_data.get('address2', '')}")
    print(f"  City: {extracted_data.get('city', '')}")
    print(f"  State: {extracted_data.get('state', '')}")
    print(f"  Postal Code: {extracted_data.get('postal_code', '')}")
    
    print("\nJob Information:")
    print(f"  PO Number: {extracted_data.get('po_number', '')}")
    print(f"  Supervisor Name: {extracted_data.get('supervisor_name', '')}")
    print(f"  Dollar Value: ${extracted_data.get('dollar_value', 0):.2f}")
    print(f"  Commencement Date: {extracted_data.get('commencement_date', '')}")
    print(f"  Completion Date: {extracted_data.get('completion_date', '')}")
    
    # Print description of works (formatted)
    print("\nDescription of Works:")
    description = extracted_data.get('description_of_works', '')
    if description:
        # Print full description
        print(description)
    else:
        print("  No description available")

if __name__ == "__main__":
    test_extractor() 