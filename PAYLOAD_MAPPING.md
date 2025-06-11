# RFMS Order Payload Format Mapping

This document shows the mapping between the old nested format and the new comprehensive format that successfully creates orders with populated data.

## Overview

We've transitioned from a **nested format** (which caused weborders and empty fields) to a **comprehensive flat format** (which prevents weborders and populates all fields correctly).

## Key Structural Changes

### Old Format (Nested)
```json
{
  "username": "zoran.vekic",
  "order": {
    // All fields nested under 'order' key
  },
  "products": null
}
```

### New Format (Comprehensive)
```json
{
  "category": "Order",  // Prevents weborders
  "poNumber": "...",
  "soldTo": { ... },
  "shipTo": { ... },
  "lines": [ ... ]      // Comprehensive lines structure
}
```

## Field Mappings

### Customer Information

| Old Format (Nested) | New Format (Comprehensive) | Notes |
|----------------------|----------------------------|-------|
| `order.CustomerSeqNum` | `soldTo.customerId` | Customer ID |
| `order.CustomerFirstName` | `soldTo.firstName` | First name |
| `order.CustomerLastName` | `soldTo.lastName` | Last name |
| `order.CustomerAddress1` | `soldTo.address1` | Address line 1 |
| `order.CustomerAddress2` | `soldTo.address2` | Address line 2 |
| `order.CustomerCity` | `soldTo.city` | City |
| `order.CustomerState` | `soldTo.state` | State |
| `order.CustomerPostalCode` | `soldTo.postalCode` | Postal code |
| `order.Phone1` | `soldTo.phone1` | Primary phone |
| `order.Phone2` | `soldTo.phone2` | Secondary phone |
| `order.Email` | `soldTo.email` | Email address |

### Shipping Information

| Old Format (Nested) | New Format (Comprehensive) | Notes |
|----------------------|----------------------------|-------|
| `order.ShipToFirstName` | `shipTo.firstName` | Ship to first name |
| `order.ShipToLastName` | `shipTo.lastName` | Ship to last name |
| `order.ShipToAddress1` | `shipTo.address1` | Ship to address 1 |
| `order.ShipToAddress2` | `shipTo.address2` | Ship to address 2 |
| `order.ShipToCity` | `shipTo.city` | Ship to city |
| `order.ShipToState` | `shipTo.state` | Ship to state |
| `order.ShipToPostalCode` | `shipTo.postalCode` | Ship to postal code |

### Order Information

| Old Format (Nested) | New Format (Comprehensive) | Notes |
|----------------------|----------------------------|-------|
| `order.PONum` | `poNumber` | Purchase order number |
| `order.JobNumber` | `jobNumber` | Job number |
| `order.Store` | `storeNumber` | Store number |
| `order.SalesPerson1` | `salesperson1` | Primary salesperson |
| `order.SalesPerson2` | `salesperson2` | Secondary salesperson |

### Notes and Descriptions

| Old Format (Nested) | New Format (Comprehensive) | Notes |
|----------------------|----------------------------|-------|
| `order.CustomNote` | `privateNotes` | Private/internal notes |
| `order.Note` | `publicNotes` | Public/customer notes |
| `order.WorkOrderNote` | `workOrderNotes` | Work order notes |

### Dates

| Old Format (Nested) | New Format (Comprehensive) | Notes |
|----------------------|----------------------------|-------|
| `order.RequiredDate` | `estimatedDeliveryDate` | Delivery date |
| `order.MeasureDate` | `measureDate` | Measure date |
| `order.PromiseDate` | `promiseDate` | Promise date |

### Type IDs (Key Success Factors)

| Old Format (Nested) | New Format (Comprehensive) | Working Values |
|----------------------|----------------------------|----------------|
| `order.UserOrderType` | `userOrderTypeId` | 18 (RESIDENTIAL INSURANCE) |
| `order.ServiceType` | `serviceTypeId` | 8 (SUPPLY & INSTALL) |
| `order.ContractType` | `contractTypeId` | 1 (30 DAY ACCOUNT) |
| `order.AdSource` | `adSource` | 1 |

### Lines Structure (Major Change)

#### Old Format (Simple)
```json
"order": {
  "Lines": [
    {
      "productId": "213322",
      "colorId": "2133", 
      "quantity": 1000.0,
      "priceLevel": 10
    }
  ]
}
```

#### New Format (Comprehensive)
```json
"lines": [
  {
    "id": "",
    "isUseTaxLine": false,
    "notes": "PDF Supervisor: John Smith",
    "internalNotes": "Contact: 0447012125",
    "productId": 213322,
    "colorId": 2133,
    "quantity": 1000.0,
    "serialNumber": "",
    "ecProductId": null,
    "ecColorId": null,
    "delete": false,
    "priceLevel": 10,
    "lineStatus": "none",
    "lineGroupId": 4
  }
]
```

## Phone Field Strategy

**Critical Success Factor**: Phone fields only in `soldTo`, NOT in `shipTo`

### Working Pattern (AZ002876)
```json
"soldTo": {
  "phone1": "0447012125",  // Mobile
  "phone2": "0732341234"   // Office
},
"shipTo": {
  // NO phone fields here!
}
```

## Data Flow Mapping

### From PDF Extraction to RFMS

| PDF Field | Intermediate Field | RFMS Field | Notes |
|-----------|-------------------|------------|-------|
| `supervisor_name` | `job_details.supervisor_name` | `soldTo.firstName` + `soldTo.lastName` | Split name |
| `supervisor_phone` | `job_details.supervisor_phone` | `soldTo.phone1` | Primary contact |
| `supervisor_mobile` | `job_details.supervisor_mobile` | `soldTo.phone1` | Alternative primary |
| `po_number` | `job_details.po_number` | `poNumber` | Direct mapping |
| `dollar_value` | `job_details.dollar_value` | `lines[0].quantity` | Used as quantity |
| `description_of_works` | `job_details.description_of_works` | `publicNotes` | Customer visible |

## Backward Compatibility

The updated system maintains backward compatibility by:

1. **RfmsApi.create_job()** detects format automatically:
   - If `order` key exists → Legacy nested format
   - If `soldTo` key exists → New comprehensive format

2. **PayloadService** maps old request format to new RFMS format internally

3. **Existing API endpoints** continue to work without changes

## Testing Results

### Successful Orders
- **AZ002876**: Comprehensive format, customer data + phone fields ✅
- **AZ002871**: All successful fields combined ✅  
- **AZ002854**: Customer details populated ✅

### Failed Patterns
- Any nested `order` structure → Weborders ❌
- Phone fields in `shipTo` → Empty phone data ❌
- Missing `category: "Order"` → Weborders ❌
- Simple lines structure → "Key not present" error ❌

## Migration Checklist

- [x] Update `payload_service.py` with comprehensive format
- [x] Update `rfms_api.py` to handle both formats  
- [x] Maintain field mapping relationships
- [x] Add comprehensive lines structure
- [x] Test backward compatibility
- [ ] Update frontend to use new field names (optional)
- [ ] Update documentation and examples

## Usage Examples

### Creating Order with PDF Data
```python
export_data = {
    "sold_to": {"id": 5, "first_name": "John", ...},
    "ship_to": {"first_name": "Site", ...}, 
    "job_details": {"supervisor_name": "John Smith", ...}
}

result = payload_service.export_data_to_rfms(api_client, export_data, logger)
# Returns comprehensive format order
```

### Result Structure
```json
{
    "success": true,
    "message": "Successfully exported main job to RFMS using comprehensive format",
    "order_id": "AZ002876",
    "format_used": "comprehensive_lines_az002876_structure"
}
``` 