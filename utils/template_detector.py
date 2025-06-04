import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class BuilderType(Enum):
    AMBROSE = "Ambrose Construct Group"
    PROFILE = "Profile Build Group"
    CAMPBELL = "Campbell Construction"
    RIZON = "Rizon Group"
    AUSTRALIAN_RESTORATION = "Australian Restoration Company"
    TOWNSEND = "Townsend Building Services"
    ONE_SOLUTIONS = "One Solutions"
    UNKNOWN = "Unknown"

@dataclass
class TemplatePatterns:
    po_pattern: str
    customer_name_pattern: str
    description_pattern: str
    dollar_value_pattern: str
    supervisor_pattern: str
    address_pattern: str
    commencement_date_pattern: str = None
    completion_date_pattern: str = None

class TemplateDetector:
    def __init__(self):
        self.template_configs = {
            BuilderType.AMBROSE: TemplatePatterns(
                po_pattern=r'20\d{6}-\d{2}',
                customer_name_pattern=r'Insured Owner/Customer:\s*(.*?)(?:\n|$)',
                description_pattern=r'Description of Works:\s*(.*?)(?=\n\n|\Z)',
                dollar_value_pattern=r'Total:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                supervisor_pattern=r'Supervisor:\s*(.*?)(?:\n|$)',
                address_pattern=r'Address:\s*(.*?)(?:\n|$)'
            ),
            BuilderType.PROFILE: TemplatePatterns(
                po_pattern=r'PBG-\d{5}-\d{5}',
                customer_name_pattern=r'Client:\s*(.*?)(?:\n|$)',
                description_pattern=r'Scope of Works / Notes:\s*(.*?)(?=\n\n|\Z)',
                dollar_value_pattern=r'Subtotal:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                supervisor_pattern=r'Supervisor:\s*(.*?)(?:\n|$)',
                address_pattern=r'Site Address:\s*(.*?)(?:\n|$)'
            ),
            BuilderType.CAMPBELL: TemplatePatterns(
                po_pattern=r'CCC\d{5}-\d{5}',
                customer_name_pattern=r'Customer:\s*(.*?)(?:\n|$)',
                description_pattern=r'Scope of Work:\s*(.*?)(?=\n\n|\Z)',
                dollar_value_pattern=r'Subtotal\s*\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
                supervisor_pattern=r"Contractor's Representative:\s*(.*?)(?:\n|$)",
                address_pattern=r'Site Address:\s*(.*?)(?:\n|$)'
            ),
            BuilderType.RIZON: TemplatePatterns(
                po_pattern=r'P\d{6}',
                customer_name_pattern=r'Client / Site Details:\s*(.*?)(?:\n|$)',
                description_pattern=r'Scope of Works:\s*(.*?)(?=\n\n|\Z)',
                dollar_value_pattern=r'Total:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                supervisor_pattern=r'Supervisor:\s*(.*?)(?:\n|$)',
                address_pattern=r'Address:\s*(.*?)(?:\n|$)'
            ),
            BuilderType.AUSTRALIAN_RESTORATION: TemplatePatterns(
                po_pattern=r'PO\d{5}-[A-Z]{2}\d{2}-\d{3}',
                customer_name_pattern=r'Customer Details:\s*(.*?)(?:\n|$)',
                description_pattern=r'Flooring Contractor Material:\s*(.*?)(?=\n\n|\Z)',
                dollar_value_pattern=r'Sub Total\s*\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
                supervisor_pattern=r'Project Manager:\s*(.*?)(?:\n|$)',
                address_pattern=r'Site Address:\s*(.*?)(?:\n|$)'
            ),
            BuilderType.TOWNSEND: TemplatePatterns(
                po_pattern=r'(?:TBS-\d{5}|Work Order \d+)',
                customer_name_pattern=r'Site Contact name:\s*(.*?)(?:\n|$)',
                description_pattern=r'(?:Flooring|Floor Preparation):\s*(.*?)(?=\n\n|\Z)',
                dollar_value_pattern=r'Subtotal:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                supervisor_pattern=r'Project Manager:\s*(.*?)(?:\n|$)',
                address_pattern=r'Site Address:\s*(.*?)(?:\n|$)'
            ),
            BuilderType.ONE_SOLUTIONS: TemplatePatterns(
                po_pattern=r'Purchase Order Number:\s*([A-Z0-9-]+)',
                customer_name_pattern=r'Site Contact Name:\s*([^\n]+)',
                description_pattern=r'Floor Covers[\s\n]+([\s\S]+?)(?=Totals)',
                dollar_value_pattern=r'Subtotal[\s:]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                supervisor_pattern=r'One Solution Representative:\s*([^\n]+)',
                address_pattern=r'Address:\s*([^\n]+)',
                commencement_date_pattern=r'Works to Commence[\s\n]+([^\n]+)',
                completion_date_pattern=r'Works to be Completed By[\s\n]+([^\n]+)'
            )  # One Solutions template finalized and ready for production
        }

    def detect_template(self, text: str) -> Tuple[BuilderType, Optional[TemplatePatterns]]:
        """
        Detect the template type based on the content of the PDF text.
        Returns a tuple of (BuilderType, TemplatePatterns)
        """
        # First try to detect by PO number pattern
        for builder_type, patterns in self.template_configs.items():
            if re.search(patterns.po_pattern, text):
                return builder_type, patterns

        # If no PO pattern match, try to detect by company name mentions
        company_indicators = {
            BuilderType.AMBROSE: ['Ambrose Construct', 'Ambrose Group'],
            BuilderType.PROFILE: ['Profile Build', 'PBG'],
            BuilderType.CAMPBELL: ['Campbell Construction', 'CCC'],
            BuilderType.RIZON: ['Rizon Group', 'Rizon'],
            BuilderType.AUSTRALIAN_RESTORATION: ['Australian Restoration', 'ARC'],
            BuilderType.TOWNSEND: ['Townsend Building', 'TBS'],
            BuilderType.ONE_SOLUTIONS: ['One Solutions', 'A To Z Flooring Solutions']
        }

        for builder_type, indicators in company_indicators.items():
            if any(indicator.lower() in text.lower() for indicator in indicators):
                return builder_type, self.template_configs[builder_type]

        return BuilderType.UNKNOWN, None

    def get_patterns(self, builder_type: BuilderType) -> Optional[TemplatePatterns]:
        """
        Get the template patterns for a specific builder type.
        """
        return self.template_configs.get(builder_type)

    def extract_field(self, text: str, pattern: str) -> Optional[str]:
        """
        Extract a field from text using the provided pattern.
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else None

    def extract_dollar_value(self, text: str, pattern: str) -> Optional[float]:
        """
        Extract and convert dollar value from text using the provided pattern.
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                return float(value_str)
            except ValueError:
                return None
        return None 