from app import app, db
from models import Customer
from datetime import datetime

if __name__ == '__main__':
    with app.app_context():
        # First try to create tables
        print("Creating tables...")
        db.create_all()
        
        # Then add a test customer
        print("Adding test customer...")
        test_customer = Customer(
            first_name="Test",
            last_name="Customer",
            business_name="Test Business",
            email="test@example.com",
            created_at=datetime.now()
        )
        db.session.add(test_customer)
        
        # Commit and verify
        try:
            db.session.commit()
            print("Customer added successfully with ID:", test_customer.id)
            
            # Query to verify
            customers = Customer.query.all()
            print(f"Found {len(customers)} customers in database")
            for c in customers:
                print(f"- {c.first_name} {c.last_name} ({c.business_name})")
                
        except Exception as e:
            db.session.rollback()
            print("Error:", str(e)) 