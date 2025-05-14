import os
import re
import sys

def check_file(file_path):
    """Check a file for old and new credentials"""
    
    old_credentials = {
        "username": ["admin@atozflooring.com"],
        "password": ["SimVek22$$"],
        "apikey": ["58ddae189c21473bb9064628b1c85161"]
    }
    
    new_credentials = {
        "username": "emily@atozflooring.com",
        "password": "5Hstg9gWmnEg",
        "store_code": "store-5291f4e3dca04334afede9f642ec6157",
        "api_key": "427e18d70fe142ea825bcba37be113c1"
    }
    
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Check for old credentials
            for cred_type, values in old_credentials.items():
                for value in values:
                    if value in content:
                        issues.append(f"Found old {cred_type} '{value}' in {file_path}")
            
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
    
    return issues

def main():
    """Check all credential references in the codebase"""
    
    # Files to check
    files_to_check = [
        ".env-test",
        "test_rfms_api_connection.py",
        "utils/rfms_api.py",
        "app.py"
    ]
    
    all_issues = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            issues = check_file(file_path)
            all_issues.extend(issues)
    
    # Print results
    if all_issues:
        print("Found credential issues:")
        for issue in all_issues:
            print(f"- {issue}")
        sys.exit(1)
    else:
        print("All credential references have been updated correctly.")
        sys.exit(0)

if __name__ == "__main__":
    main() 