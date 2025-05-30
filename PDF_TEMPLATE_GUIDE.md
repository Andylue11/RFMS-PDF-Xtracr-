# PDF Template Extraction Guide

## Overview

The enhanced PDF extractor can now handle multiple Purchase Order/Work Order templates from different construction companies. It automatically detects the template format and applies the appropriate extraction patterns.

## Supported Templates

### 1. Ambrose Construct Group (Default)
- **PO Format**: `20XXXXXX-XX` (e.g., `20172082-04`)
- **Key Terms**:
  - Purchase Order Number
  - Description of Works
  - Supervisor Details
  - Insured Owner/Customer

### 2. Profile Build Group
- **PO Format**: `PBG-XXXXX-XXXXX` (e.g., `PBG-18191-18039`)
- **Key Terms**:
  - Work Order
  - Scope of Works / Notes
  - Supervisor
  - Client

### 3. Campbell Construction
- **PO Format**: `CCCXXXXX-XXXXX` (e.g., `CCC55132-88512`)
- **Key Terms**:
  - Contract No.
  - Scope of Work
  - Contractor's Representative
  - Customer

### 4. Rizon Group
- **PO Format**: `PXXXXXX` (e.g., `P367117`)
- **Key Terms**:
  - Purchase Order No.
  - Scope of Works
  - Client / Site Details
  - Supervisor

### 5. Australian Restoration Company
- **PO Format**: `POXXXXX-XXXX-XXX` (e.g., `PO96799-BU01-003`)
- **Key Terms**:
  - Order Number
  - Flooring Contractor Material
  - Project Manager / Case Manager
  - Customer Details

### 6. Townsend Building Services
- **PO Format**: `TBS-XXXXX` or Work Order numbers
- **Key Terms**:
  - Purchase Order / Work Order
  - Scope of Works
  - Project Manager / Supervisor
  - Attention (Contact)

## Template Detection

The PDF extractor automatically detects which template to use based on:
1. **PO Number Format** - Specific patterns like PBG-, CCC, P367117, etc.
2. **Company Names** - Text mentions of the builder names
3. **Email Domains** - Company-specific email addresses
4. **Document Structure** - Specific section headers and terminology

## Usage

Simply upload any PDF from these 6 builders (or others), and the system will:
1. Automatically detect the builder template
2. Extract relevant data using builder-specific patterns
3. Fall back to generic patterns if needed
4. Map the data to the standard RFMS format

## Data Mapping

Regardless of the template, all extracted data is mapped to standard fields:
- Customer Name/Client → Customer Name
- Description/Scope of Works → Description of Works
- Supervisor/Project Manager/Contractor's Representative → Supervisor Details
- Contract No./Work Order/PO Number → Purchase Order Number
- Total/Sub Total → Dollar Value

## Adding New Templates

To add support for a new builder:
1. Add a new configuration in `TEMPLATE_CONFIGS` in `utils/pdf_extractor.py`
2. Define specific patterns for:
   - PO number format
   - Customer name patterns
   - Description/scope patterns
   - Dollar value patterns
3. Update the `detect_template()` function to identify the new builder

## Testing

Test PDFs are available in the `testing pdfs` folder with 2 examples per builder. 