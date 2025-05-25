import os
import sys
import logging
from collections import defaultdict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
from utils.rfms_api import RfmsApi
from app import app

# Setup logging
logging.basicConfig(
    filename='debug_customer_search.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Load test environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env-test'))

rfms_api = RfmsApi(
    base_url=os.getenv("RFMS_BASE_URL", "https://api.rfms.online"),
    store_code=os.getenv("RFMS_STORE_CODE"),
    username=os.getenv("RFMS_USERNAME"),
    api_key=os.getenv("RFMS_API_KEY"),
)

def try_payload(payload):
    try:
        url = f"{rfms_api.base_url}/v2/customers/find"
        result = rfms_api.execute_request("POST", url, payload)
        logging.info(f"Payload: {payload}\nResult count: {len(result) if isinstance(result, list) else 'N/A'}\nResult: {result}")
        print(f"Payload: {payload}\n  Result count: {len(result) if isinstance(result, list) else 'N/A'}\n")
        return result if isinstance(result, list) else []
    except Exception as e:
        logging.error(f"Error for payload {payload}: {e}")
        print(f"  Error: {e}\n")
        return []

def debug_customer_search(term):
    print(f"=== Debugging search for: {term} ===\n")
    summary = defaultdict(dict)
    # Try different searchText formats
    search_variants = [
        ("plain", term),
        ("lower", term.lower()),
        ("upper", term.upper()),
        ("title", term.title()),
        ("first3", term[:3]),
        ("first5", term[:5]),
        ("wildcard_star_end", f"{term}*"),
        ("wildcard_star_both", f"*{term}*"),
        ("wildcard_percent_both", f"%{term}%"),
    ]
    # Try different payload parameter combinations
    payload_options = [
        {"includeCustomers": True, "includeInactive": True, "storeNumber": 49, "customerType": "BUILDERS", "customerSource": "Customer"},
        {"includeCustomers": True, "includeInactive": True, "storeNumber": 49, "customerType": "BUILDERS"},  # no customerSource
        {"includeCustomers": True, "includeInactive": True, "customerType": "BUILDERS"},
        {"includeCustomers": True, "includeInactive": True, "storeNumber": 49},
        {"includeCustomers": True, "includeInactive": True},
        # New: storeNumber 1
        {"includeCustomers": True, "includeInactive": True, "storeNumber": 1, "customerType": "BUILDERS", "customerSource": "Customer"},
        {"includeCustomers": True, "includeInactive": True, "storeNumber": 1, "customerType": "BUILDERS"},
        {"includeCustomers": True, "includeInactive": True, "storeNumber": 1},
        # New: storeNumber as comma-separated string '49,1'
        {"includeCustomers": True, "includeInactive": True, "storeNumber": "49,1", "customerType": "BUILDERS", "customerSource": "Customer"},
        {"includeCustomers": True, "includeInactive": True, "storeNumber": "49,1", "customerType": "BUILDERS"},
        {"includeCustomers": True, "includeInactive": True, "storeNumber": "49,1"},
    ]
    for variant_name, variant in search_variants:
        for idx, opts in enumerate(payload_options):
            payload = {"searchText": variant}
            payload.update(opts)
            print(f"Trying payload: {payload}")
            results = try_payload(payload)
            summary[variant_name][idx] = len(results)
    return summary

def main():
    # List of terms to try
    search_terms = [
        "profile"
    ]
    all_summaries = {}
    with app.app_context():
        for term in search_terms:
            summary = debug_customer_search(term)
            all_summaries[term] = summary
    # Print summary of wildcard vs non-wildcard results
    print("\n=== SUMMARY OF RESULTS ===")
    for term, summary in all_summaries.items():
        print(f"\nTerm: {term}")
        for variant_name, results in summary.items():
            total = sum(results.values())
            print(f"  {variant_name}: max results for any payload = {max(results.values())}")
        # Compare wildcards
        wildcard_max = max(summary.get("wildcard_star_end", {}).values()) if "wildcard_star_end" in summary else 0
        wildcard_both_max = max(summary.get("wildcard_star_both", {}).values()) if "wildcard_star_both" in summary else 0
        percent_both_max = max(summary.get("wildcard_percent_both", {}).values()) if "wildcard_percent_both" in summary else 0
        plain_max = max(summary.get("plain", {}).values()) if "plain" in summary else 0
        print(f"    Wildcard *end: {wildcard_max}, *both: {wildcard_both_max}, %both: {percent_both_max}, plain: {plain_max}")
        if wildcard_max > plain_max or wildcard_both_max > plain_max or percent_both_max > plain_max:
            print("    Wildcard search returned more results than plain search!")
        else:
            print("    Wildcard search did NOT return more results than plain search.")

if __name__ == "__main__":
    main() 