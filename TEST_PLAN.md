# Finarius - Test Plan

## Overview

This document outlines the comprehensive test plan for the Finarius portfolio tracking application. It covers unit tests, integration tests, and manual testing procedures.

## Test Environment Setup

### Prerequisites
```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install -r requirements-dev.txt

# Verify pytest is installed
pytest --version
```

### Test Database
- Tests use temporary in-memory SQLite databases
- Each test creates its own isolated database
- No production data is affected

## Test Structure

### Test Organization
```
tests/
├── test_config.py          # Configuration management tests
├── test_database.py        # Database operations tests
├── test_models.py          # Model CRUD tests
├── test_prices.py          # Price downloader tests
├── test_price_utilities.py # Price utilities tests
├── test_engine.py          # Portfolio engine tests
├── test_metrics.py         # Metrics calculation tests
├── test_exceptions.py      # Exception handling tests
├── test_logger.py          # Logging configuration tests
├── test_utils.py           # Utility functions tests
├── test_ui_*.py           # UI component tests
└── test_ui_error_handler.py # Error handling tests
```

## Unit Tests

### 1. Configuration Tests (`test_config.py`)

**Test Cases:**
- ✅ Default configuration values
- ✅ Loading from JSON config file
- ✅ Loading from YAML config file (if PyYAML installed)
- ✅ Loading from TOML config file
- ✅ Environment variable overrides
- ✅ Config priority (env > file > defaults)
- ✅ Config singleton pattern
- ✅ Config reload functionality
- ✅ Type conversion (bool, int, float, string)

**Run:**
```bash
pytest tests/test_config.py -v
```

**Expected Coverage:** 92%+

### 2. Database Tests (`test_database.py`)

**Test Cases:**
- ✅ Database initialization
- ✅ Table creation (accounts, transactions, prices)
- ✅ Foreign key constraints
- ✅ Index creation
- ✅ Migration system
- ✅ Database backup/restore
- ✅ Database utilities (vacuum, stats)
- ✅ Connection pooling
- ✅ Error handling

**Run:**
```bash
pytest tests/test_database.py -v
```

**Expected Coverage:** 80%+

### 3. Model Tests (`test_models.py`)

**Test Cases:**
- ✅ Account model CRUD operations
- ✅ Transaction model CRUD operations
- ✅ Price model CRUD operations
- ✅ Model validation
- ✅ Model relationships
- ✅ Query helpers
- ✅ Data integrity

**Run:**
```bash
pytest tests/test_models.py -v
```

**Expected Coverage:** 85%+

### 4. Price Downloader Tests (`test_prices.py`)

**Test Cases:**
- ✅ Single price download (mocked)
- ✅ Price range download
- ✅ Latest price download
- ✅ Multiple symbols batch download
- ✅ Caching mechanism
- ✅ Error handling (network, invalid symbols)
- ✅ Rate limiting
- ✅ Symbol validation

**Run:**
```bash
pytest tests/test_prices.py -v
```

**Note:** Uses mocked yfinance to avoid network calls

**Expected Coverage:** 80%+

### 5. Portfolio Engine Tests (`test_engine.py`)

**Test Cases:**
- ✅ Position tracking
- ✅ PRU (average cost) calculation
- ✅ Portfolio value calculation
- ✅ Cash flow tracking
- ✅ Position history
- ✅ Multiple accounts
- ✅ Edge cases (empty portfolio, single transaction)

**Run:**
```bash
pytest tests/test_engine.py -v
```

**Expected Coverage:** 75%+

### 6. Metrics Tests (`test_metrics.py`)

**Test Cases:**
- ✅ Realized gains calculation
- ✅ Unrealized gains calculation
- ✅ CAGR calculation (known test cases)
- ✅ IRR calculation (known test cases)
- ✅ TWRR calculation (known test cases)
- ✅ Dividend analytics
- ✅ Risk metrics (Sharpe ratio, max drawdown, volatility)
- ✅ Edge cases (zero returns, negative returns)

**Run:**
```bash
pytest tests/test_metrics.py -v
```

**Expected Coverage:** 70%+

### 7. Exception Tests (`test_exceptions.py`)

**Test Cases:**
- ✅ Base exception class
- ✅ All exception types (DatabaseError, PriceDownloadError, etc.)
- ✅ Exception hierarchy
- ✅ Exception serialization
- ✅ Exception details dictionary
- ✅ Exception catching (specific and general)

**Run:**
```bash
pytest tests/test_exceptions.py -v
```

**Expected Coverage:** 100%

### 8. Logger Tests (`test_logger.py`)

**Test Cases:**
- ✅ Logging setup with defaults
- ✅ Logging setup with config
- ✅ Console handler
- ✅ File handler (when enabled)
- ✅ Log level configuration
- ✅ Log format configuration
- ✅ Auto-setup on get_logger()
- ✅ Reset logging functionality

**Run:**
```bash
pytest tests/test_logger.py -v
```

**Expected Coverage:** 96%+

### 9. Utility Tests (`test_utils.py`)

**Test Cases:**
- ✅ Date parsing (multiple formats)
- ✅ Date formatting
- ✅ Date range generation
- ✅ Currency formatting (multiple currencies)
- ✅ Percentage formatting
- ✅ Decimal rounding
- ✅ Symbol validation
- ✅ Date validation
- ✅ Amount validation
- ✅ Safe division
- ✅ Percentage change calculation

**Run:**
```bash
pytest tests/test_utils.py -v
```

**Expected Coverage:** 98%+

### 10. UI Component Tests (`test_ui_*.py`)

**Test Cases:**
- ✅ Session state management
- ✅ Navigation rendering
- ✅ Error handler functionality
- ✅ UI component imports
- ✅ Page routing

**Run:**
```bash
pytest tests/test_ui_*.py -v
```

**Note:** UI tests are limited due to Streamlit's architecture

## Integration Tests

### 1. End-to-End Workflow Tests

**Test Scenario 1: Complete Portfolio Setup**
```python
1. Create account
2. Add BUY transaction
3. Add SELL transaction
4. Add DIVIDEND transaction
5. Download prices
6. Calculate portfolio value
7. View dashboard
8. Check metrics
```

**Test Scenario 2: Multi-Account Portfolio**
```python
1. Create multiple accounts
2. Add transactions to each account
3. View aggregate portfolio
4. Compare account performance
```

**Test Scenario 3: Price Update Flow**
```python
1. Add transaction with symbol
2. Trigger price download
3. Verify price cached
4. Update portfolio value
5. Verify calculations use cached price
```

### 2. Database Integration Tests

**Test Cases:**
- ✅ Real SQLite database operations
- ✅ Migration from old schema to new
- ✅ Backup and restore functionality
- ✅ Concurrent access handling
- ✅ Large dataset performance

### 3. Configuration Integration Tests

**Test Cases:**
- ✅ Config file + environment variables
- ✅ Config changes during runtime
- ✅ Config reload without restart
- ✅ Multiple config file formats

## Manual Testing Checklist

### Application Startup
- [ ] Application starts without errors
- [ ] Database initializes correctly
- [ ] Logging works (check console output)
- [ ] All pages load without errors
- [ ] Navigation works between pages

### Account Management
- [ ] Create new account
- [ ] Edit account details
- [ ] Delete account (with transactions)
- [ ] View account list
- [ ] Account validation (duplicate names, etc.)

### Transaction Management
- [ ] Add BUY transaction
- [ ] Add SELL transaction
- [ ] Add DIVIDEND transaction
- [ ] Add DEPOSIT transaction
- [ ] Add WITHDRAW transaction
- [ ] Edit transaction
- [ ] Delete transaction
- [ ] Filter transactions (by account, date, symbol)
- [ ] Export transactions to CSV
- [ ] Import transactions from CSV

### Price Management
- [ ] Download price for single symbol
- [ ] Download prices for multiple symbols
- [ ] Price caching works
- [ ] Manual price update
- [ ] Price update for all symbols
- [ ] Handle invalid symbols gracefully
- [ ] Handle network errors gracefully

### Dashboard
- [ ] Portfolio value displays correctly
- [ ] Cost basis calculated correctly
- [ ] Unrealized gains/losses correct
- [ ] Realized gains/losses correct
- [ ] Charts render correctly
- [ ] Date range filtering works
- [ ] Account selection works
- [ ] Metrics display correctly (CAGR, IRR, TWRR)

### Analytics
- [ ] Performance metrics calculate correctly
- [ ] Gains/losses breakdown by symbol
- [ ] Dividend analytics display
- [ ] Position analytics
- [ ] Risk metrics display
- [ ] Date range filtering
- [ ] Export functionality

### Settings
- [ ] Database settings accessible
- [ ] Database backup works
- [ ] Database restore works
- [ ] Database vacuum works
- [ ] Display settings persist
- [ ] Price update settings work
- [ ] Logging settings apply

### Error Handling
- [ ] Invalid input shows user-friendly errors
- [ ] Network errors handled gracefully
- [ ] Database errors handled gracefully
- [ ] Missing data handled gracefully
- [ ] Error messages logged correctly

## Performance Tests

### Database Performance
- [ ] 1000+ transactions load quickly
- [ ] Portfolio calculations complete in < 1 second
- [ ] Price downloads don't block UI
- [ ] Large date ranges handled efficiently

### UI Performance
- [ ] Pages load in < 2 seconds
- [ ] Charts render smoothly
- [ ] No UI freezing during calculations
- [ ] Responsive to user interactions

## Security Tests

### Data Security
- [ ] Database file permissions correct
- [ ] No SQL injection vulnerabilities
- [ ] Input validation prevents malicious data
- [ ] Sensitive data not logged

### Privacy
- [ ] No external data transmission
- [ ] All operations local
- [ ] No telemetry or tracking
- [ ] Data stays on local machine

## Regression Tests

### Critical Paths
1. **Portfolio Calculation**
   - Create account → Add transactions → View portfolio
   - Verify all calculations correct

2. **Price Updates**
   - Add transaction → Download price → Update portfolio
   - Verify price used correctly

3. **Metrics Calculation**
   - Add multiple transactions → Calculate metrics
   - Verify metrics match expected values

## Running All Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=finarius_app --cov-report=html --cov-report=term
```

### Run Specific Test Category
```bash
# Core functionality
pytest tests/test_database.py tests/test_models.py tests/test_engine.py -v

# Configuration and utilities
pytest tests/test_config.py tests/test_logger.py tests/test_utils.py -v

# Metrics and calculations
pytest tests/test_metrics.py tests/test_prices.py -v
```

### Run Tests in Parallel
```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

## Test Coverage Goals

### Current Coverage
- Overall: ~15-20% (UI components not fully tested)
- Core modules: 70-100%
- Utilities: 95%+

### Target Coverage
- Core modules: 90%+
- Utilities: 95%+
- UI components: 50%+ (limited by Streamlit architecture)
- Overall: 80%+

## Continuous Integration

### Pre-commit Checks
```bash
# Run before committing
pre-commit run --all-files
```

### CI Pipeline (Recommended)
1. Run all tests
2. Check code coverage
3. Run linting (flake8)
4. Run type checking (mypy)
5. Run formatting check (black)

## Known Test Limitations

1. **Streamlit UI Tests**: Limited due to Streamlit's architecture
   - Solution: Focus on logic tests, manual UI testing

2. **Network-Dependent Tests**: Price downloads require mocking
   - Solution: All price tests use mocked yfinance

3. **Database Tests**: Some require file system access
   - Solution: Use temporary files, clean up after tests

## Test Data

### Sample Test Data
Located in test fixtures:
- Sample accounts
- Sample transactions
- Sample prices
- Edge cases (empty data, invalid data)

### Test Fixtures
```python
@pytest.fixture
def sample_account():
    # Returns test account data

@pytest.fixture
def sample_transactions():
    # Returns test transaction data
```

## Reporting Issues

### When Tests Fail
1. Check error message and stack trace
2. Verify test data is correct
3. Check for environment issues
4. Review recent code changes
5. Check test coverage for affected area

### Test Maintenance
- Update tests when adding new features
- Add tests for bug fixes
- Review and update test data regularly
- Keep test coverage reports up to date

## Next Steps

1. **Expand Integration Tests**: Add more end-to-end scenarios
2. **Performance Benchmarking**: Add performance regression tests
3. **Load Testing**: Test with large datasets
4. **Browser Testing**: Add Selenium tests for critical UI flows
5. **Accessibility Testing**: Ensure UI is accessible

---

**Last Updated:** 2025-12-31
**Test Framework:** pytest
**Coverage Tool:** pytest-cov

