import unittest
import os
import logging
from app import app, db
from models import Customer, Quote, Job, PdfData

class TestDevEnvironment(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rfms_xtracr_test.db'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up after each test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_database_connection(self):
        """Test database connection and table creation."""
        try:
            # Try to create a test record
            test_customer = Customer(
                name="Test Customer",
                email="test@example.com"
            )
            db.session.add(test_customer)
            db.session.commit()
            
            # Verify the record was created
            customer = Customer.query.filter_by(email="test@example.com").first()
            self.assertIsNotNone(customer)
            self.assertEqual(customer.name, "Test Customer")
            
            logging.info("Database connection test passed")
        except Exception as e:
            logging.error(f"Database connection test failed: {str(e)}")
            raise

    def test_rfms_api_connection(self):
        """Test RFMS API connection."""
        try:
            response = self.app.get('/api/check_status')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('status', data)
            logging.info(f"RFMS API connection test passed. Status: {data['status']}")
        except Exception as e:
            logging.error(f"RFMS API connection test failed: {str(e)}")
            raise

    def test_file_upload_directory(self):
        """Test file upload directory exists and is writable."""
        try:
            upload_dir = app.config['UPLOAD_FOLDER']
            self.assertTrue(os.path.exists(upload_dir))
            self.assertTrue(os.access(upload_dir, os.W_OK))
            logging.info("File upload directory test passed")
        except Exception as e:
            logging.error(f"File upload directory test failed: {str(e)}")
            raise

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("test_dev.log")
        ]
    )
    
    # Run tests
    unittest.main() 