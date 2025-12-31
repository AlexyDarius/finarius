# Finarius - Run Guide

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Virtual environment (will be created automatically if missing)

### Running the Application

**Option 1: Using the run script (Recommended)**
```bash
./run.sh
```

**Option 2: Manual start**
```bash
source venv/bin/activate
# Ensure PYTHONPATH includes project root
export PYTHONPATH="$(pwd):$PYTHONPATH"
streamlit run finarius_app/app.py
```

**Note:** The app automatically adds the project root to Python path, so it should work even without setting PYTHONPATH manually.

**Option 3: Windows**
```bash
run.bat
```

The application will start and be available at:
- **URL**: http://localhost:8501
- **Port**: 8501 (default Streamlit port)

## First Run Setup

### 1. Initial Setup
On first run, the application will:
- Create the database file (`db.sqlite`) automatically
- Initialize all database tables
- Run any necessary migrations
- Set up logging

### 2. Configuration
The application uses `config.yaml` for configuration. Default settings:
- **Database**: `db.sqlite` (SQLite database file)
- **Currency**: USD
- **Date Format**: `%Y-%m-%d` (ISO format)
- **Logging**: INFO level, console output

To customize, edit `config.yaml` or use environment variables:
```bash
export FINARIUS_DATABASE__PATH="custom.db"
export FINARIUS_DISPLAY__DEFAULT_CURRENCY="EUR"
export FINARIUS_LOGGING__LEVEL="DEBUG"
```

### 3. Optional: Install PyYAML
To use YAML config files (instead of JSON), install PyYAML:
```bash
pip install pyyaml
```
Note: This is optional - the app works without it using defaults.

## Application Structure

### Main Pages
1. **Dashboard** - Portfolio overview, metrics, and charts
2. **Accounts** - Manage investment accounts
3. **Transactions** - Add/edit transactions (BUY, SELL, DIVIDEND, etc.)
4. **Portfolio** - Portfolio details (coming soon)
5. **Analytics** - Performance analytics and reports
6. **Settings** - Application settings and configuration

### Getting Started Workflow

1. **Create an Account**
   - Go to "Accounts" page
   - Click "Add Account"
   - Enter account name and currency
   - Save

2. **Add Transactions**
   - Go to "Transactions" page
   - Click "Add Transaction"
   - Select account, date, type (BUY/SELL/DIVIDEND)
   - Enter symbol, quantity, price
   - Save

3. **View Dashboard**
   - Go to "Dashboard" page
   - Select account and date range
   - View portfolio value, gains, and performance metrics

4. **Download Prices**
   - Prices are downloaded automatically when needed
   - Or use "Settings" → "Price Updates" → "Update All Prices"

## Configuration Options

### Database Settings
- **Path**: Location of SQLite database file
- **Backup**: Create database backups
- **Restore**: Restore from backup
- **Vacuum**: Optimize database

### Display Settings
- **Default Currency**: USD, EUR, GBP, etc.
- **Date Format**: Customize date display format
- **Number Format**: Customize number formatting

### Price Update Settings
- **Update Frequency**: daily, weekly, or manual
- **Cache Enabled**: Enable/disable price caching
- **Cache Expiry**: Days before cache expires

### Logging Settings
- **Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **File Logging**: Enable/disable log file
- **Log File Path**: Location of log file

## Environment Variables

All configuration can be overridden with environment variables:

```bash
# Database
export FINARIUS_DATABASE__PATH="custom.db"

# Display
export FINARIUS_DISPLAY__DEFAULT_CURRENCY="EUR"
export FINARIUS_DISPLAY__DATE_FORMAT="%d/%m/%Y"
export FINARIUS_DISPLAY__NUMBER_FORMAT="{:,.2f}"

# Prices
export FINARIUS_PRICES__UPDATE_FREQUENCY="daily"
export FINARIUS_PRICES__CACHE_ENABLED="true"
export FINARIUS_PRICES__CACHE_EXPIRY_DAYS="1"

# Logging
export FINARIUS_LOGGING__LEVEL="DEBUG"
export FINARIUS_LOGGING__FILE_ENABLED="true"
export FINARIUS_LOGGING__FILE_PATH="finarius.log"
```

## Troubleshooting

### Database Issues
- **Database locked**: Close other instances of the app
- **Permission denied**: Check file permissions on database directory
- **Corrupted database**: Restore from backup or delete and recreate

### Price Download Issues
- **Network errors**: Check internet connection
- **Rate limiting**: Wait a few minutes and try again
- **Invalid symbols**: Verify symbol format (e.g., "AAPL" not "apple")

### Import Errors
- **Module not found**: Ensure virtual environment is activated
- **Missing dependencies**: Run `pip install -r requirements.txt`

### Configuration Issues
- **Config not loading**: Check `config.yaml` syntax (if using YAML)
- **Defaults used**: This is normal if config file is missing
- **Environment variables not working**: Ensure format is `FINARIUS_SECTION__KEY`

## Development Mode

### Running Tests
```bash
source venv/bin/activate
pytest tests/ -v
```

### Running with Coverage
```bash
pytest tests/ --cov=finarius_app --cov-report=html
```

### Code Quality Checks
```bash
# Linting
flake8 finarius_app/

# Formatting
black finarius_app/

# Type checking
mypy finarius_app/
```

## Production Deployment

### Considerations
1. **Database**: Use a dedicated location with backups
2. **Logging**: Enable file logging for production
3. **Security**: Ensure database file has proper permissions
4. **Performance**: Consider database optimization (VACUUM)

### Recommended Settings for Production
```yaml
logging:
  level: "WARNING"
  file_enabled: true
  file_path: "/var/log/finarius.log"

database:
  path: "/var/lib/finarius/db.sqlite"
```

## Stopping the Application

- Press `Ctrl+C` in the terminal
- Or close the browser tab (Streamlit will detect and stop)

## Data Backup

### Manual Backup
```bash
cp db.sqlite db.sqlite.backup
```

### Using Settings Page
1. Go to "Settings" → "Database"
2. Click "Backup Database"
3. Choose backup location

### Restore from Backup
1. Go to "Settings" → "Database"
2. Click "Restore Database"
3. Select backup file

## Support

For issues or questions:
1. Check the logs: `finarius.log` (if file logging enabled)
2. Review `IMPLEMENTATION_PLAN.md` for development status
3. Check console output for error messages

## Next Steps

After running the application:
1. Create your first account
2. Add some transactions
3. Explore the dashboard and analytics
4. Customize settings as needed

Enjoy tracking your portfolio! 📊

