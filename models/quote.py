from models import db
from datetime import datetime

class Quote(db.Model):
    """
    Quote model for storing quote information.
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic quote information
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    po_number = db.Column(db.String(50))
    scope_of_work = db.Column(db.Text)
    dollar_value = db.Column(db.Float, default=0.0)
    
    # RFMS specific fields
    rfms_quote_id = db.Column(db.String(50), nullable=True)
    store_code = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Status tracking
    status = db.Column(db.String(20), default="DRAFT")
    
    def __repr__(self):
        return f"<Quote #{self.id} PO:{self.po_number} ${self.dollar_value}>"
    
    def to_dict(self):
        """
        Convert the model instance to a dictionary.
        """
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'po_number': self.po_number,
            'scope_of_work': self.scope_of_work,
            'dollar_value': self.dollar_value,
            'rfms_quote_id': self.rfms_quote_id,
            'store_code': self.store_code,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @classmethod
    def from_rfms_data(cls, rfms_data, customer_id):
        """
        Create a Quote instance from RFMS API data.
        
        Args:
            rfms_data (dict): Quote data from RFMS API
            customer_id (int): Local customer ID
        
        Returns:
            Quote: New Quote instance
        """
        # Extract total dollar value from lines if available
        dollar_value = 0.0
        if 'lines' in rfms_data:
            for line in rfms_data.get('lines', []):
                price = float(line.get('price', 0))
                quantity = float(line.get('quantity', 1))
                dollar_value += price * quantity
        
        quote = cls(
            customer_id=customer_id,
            po_number=rfms_data.get('poNumber', ''),
            scope_of_work=rfms_data.get('workOrderNotes', ''),
            dollar_value=dollar_value,
            rfms_quote_id=rfms_data.get('id'),
            store_code=rfms_data.get('storeCode'),
            status=rfms_data.get('status', 'DRAFT')
        )
        
        return quote 

    def to_rfms_data(self):
        """Convert quote to RFMS API format."""
        return {
            'username': 'zoran.vekic',
            'order': {
                'CustomerSeqNum': self.customer_id,
                'CustomerUpSeqNum': self.customer_id,
                'PONumber': self.po_number,
                'WorkOrderNote': self.scope_of_work,
                'CustomerType': 'INSURANCE',
                'UserOrderType': 12,
                'ServiceType': 9,
                'ContractType': 2,
                'SalesPerson1': 'ZORAN VEKIC',
                'Store': 49,
                'InstallStore': 49,
                'OrderDate': datetime.now().strftime('%Y-%m-%d'),
                'DateEntered': datetime.now().strftime('%Y-%m-%d'),
                'GrandInvoiceTotal': self.dollar_value,
                'MaterialOnly': 0.0,
                'Labor': 0.0,
                'MiscCharges': self.dollar_value,
                'InvoiceTotal': self.dollar_value,
                'Balance': self.dollar_value,
                'Lines': []
            }
        } 