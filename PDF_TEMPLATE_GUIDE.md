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
- **PO Format**: `PBG-XXXXX` (e.g., `PBG-12345`)
- **Key Terms**:
  - Contract No. / Work Order
  - Scope of Works
  - Contractors Representative
  - Client

### 3. Campbell Construction
- **PO Format**: `CCCXXXXX` (e.g., `CCC55132`)
- **Key Terms**:
  - Contract No. / Work Order
  - Scope of Works
  - Contractors Representative
  - Client

## How It Works

### 1. Template Detection
The system automatically detects which template to use by looking for:
- Company-specific PO number formats (PBG-, CCC, 20XXXXXX-XX)
- Company names in the document
- Specific terminology patterns (e.g., "Scope of Works" vs "Description of Works")

### 2. Flexible Field Mapping
The extractor maps different terminology to standard fields:

| Standard Field | Ambrose | Profile Build / Campbell |
|----------------|---------|-------------------------|
| Customer | Insured Owner | Client |
| Work Description | Description of Works | Scope of Works |
| Contact Person | Supervisor | Contractors Representative |
| PO Number | Purchase Order | Contract No. |

### 3. Fallback Patterns
If template-specific patterns don't find data, the system falls back to generic patterns that work across all templates.

## Adding New Templates

To add support for a new company's PDF format:

1. Add a new template configuration in `TEMPLATE_CONFIGS` dictionary
2. Define company-specific patterns for:
   - PO number formats
   - Customer field names
   - Description/scope patterns
   - Dollar value patterns
   - Contact person sections

3. Update the `detect_template()` function to recognize the new format

## Example Template Configuration

```python
"new_company": {
    "name": "New Company Name",
    "po_patterns": [
        r"Your\s+PO\s+Pattern[:\s]+([A-Za-z0-9-]+)",
    ],
    "customer_patterns": [
        r"Client[:\s]+([A-Za-z\s]+?)(?=\n)",
    ],
    "description_patterns": [
        r"Work\s+Details[:\s]+([\s\S]+?)(?=TOTAL|Total)",
    ],
    "dollar_patterns": [
        r"Total[:\s]+\$?\s*([\d,]+\.\d{2})",
    ],
    "supervisor_section": r"CONTACT\s+PERSON",
    "contact_label": "Contact Person",
}
```

## Testing Different Templates

You can test the PDF extractor with different formats by uploading PDFs through the web interface. The system will:
1. Automatically detect the template type
2. Extract data using appropriate patterns
3. Log which template was detected
4. Fall back to generic patterns if needed 