# RFMS-PDF-Xtracr Development Environment Setup Guide

## Prerequisites
- Python 3.8 or higher
- Git
- Visual Studio Code (recommended) or your preferred IDE
- Elasticsearch account (elastic.co)
- SQL database (PostgreSQL recommended)

## Initial Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/[your-username]/RFMS-PDF-Xtracr.git
   cd RFMS-PDF-Xtracr
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory with the following structure:
   ```
   # Database Configuration
   DEV_DATABASE_URL=postgresql://username:password@localhost:5432/rfms_dev
   TEST_DATABASE_URL=postgresql://username:password@localhost:5432/rfms_test
   PROD_DATABASE_URL=postgresql://username:password@localhost:5432/rfms_prod

   # Elasticsearch Configuration
   ELASTICSEARCH_DEV_URL=https://your-dev-cluster.elastic.co
   ELASTICSEARCH_PROD_URL=https://your-prod-cluster.elastic.co
   ELASTICSEARCH_API_KEY=your-api-key

   # Application Settings
   FLASK_ENV=development
   FLASK_APP=app.py
   SECRET_KEY=your-secret-key
   ```

5. **Database Setup**
   - Install PostgreSQL if not already installed
   - Create three databases: rfms_dev, rfms_test, rfms_prod
   - Run database migrations:
     ```bash
     flask db upgrade
     ```

6. **Elasticsearch Setup**
   - Log in to your elastic.co account
   - Create separate indices for dev and prod environments
   - Configure the API key in your .env file

## Development Workflow

1. **Branch Management**
   - Create feature branches from `main`
   - Use descriptive branch names (e.g., `feature/user-authentication`)
   - Submit pull requests for code review

2. **Testing**
   - Run tests before committing:
     ```bash
     python -m pytest
     ```
   - Ensure test coverage meets requirements

3. **Code Quality**
   - Follow PEP 8 guidelines
   - Keep files under 300 lines
   - Write clear documentation
   - Use type hints

## Environment-Specific Notes

### Development
- Use the dev database and Elasticsearch index
- Enable debug mode
- Use mock data only in tests

### Testing
- Use the test database
- Run all tests before deployment
- Ensure test data is isolated

### Production
- Use the prod database and Elasticsearch index
- Disable debug mode
- Never use mock data

## Troubleshooting

1. **Database Connection Issues**
   - Verify database credentials in .env
   - Check if PostgreSQL service is running
   - Ensure database exists

2. **Elasticsearch Issues**
   - Verify API key
   - Check cluster health
   - Ensure indices exist

3. **Python Environment Issues**
   - Verify Python version
   - Check virtual environment activation
   - Reinstall dependencies if needed

## Security Notes

- Never commit .env files
- Keep API keys secure
- Use environment variables for sensitive data
- Regular security updates

## Additional Resources

- [Python Documentation](https://docs.python.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/index.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
