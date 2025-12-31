# Finarius - Detailed Implementation Plan

## Overview
This document tracks the complete implementation of Finarius, a fully local, privacy-first portfolio tracking and analytics application.

**Status Legend:**
- [ ] Not Started
- [🔄] In Progress
- [✅] Completed
- [⏸️] Blocked/Paused

---

## Phase 1: Project Foundation & Database Setup

### 1.1 Database Schema & Initialization
- [✅] Create `finarius_app/core/database/` (modularized structure)
  - [✅] Implement `Database` class with connection management
  - [✅] Add `init_db()` function to create database file
  - [✅] Add `close_db()` function for cleanup
  - [✅] Add database path configuration (default: `db.sqlite`)
  - [✅] Add connection pooling/singleton pattern
  - [✅] Add database versioning/migration support
  - [✅] Add error handling for database operations

- [✅] Create `accounts` table
  - [✅] `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - [✅] `name` TEXT NOT NULL
  - [✅] `currency` TEXT NOT NULL (default: 'USD')
  - [✅] `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  - [✅] `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  - [✅] Add UNIQUE constraint on `name`
  - [✅] Add indexes on `id`, `name`

- [✅] Create `transactions` table
  - [✅] `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - [✅] `date` DATE NOT NULL
  - [✅] `account_id` INTEGER NOT NULL
  - [✅] `type` TEXT NOT NULL (BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAW)
  - [✅] `symbol` TEXT (nullable for DEPOSIT/WITHDRAW)
  - [✅] `qty` REAL (nullable for DEPOSIT/WITHDRAW)
  - [✅] `price` REAL (nullable for DEPOSIT/WITHDRAW)
  - [✅] `fee` REAL DEFAULT 0.0
  - [✅] `notes` TEXT (optional)
  - [✅] `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  - [✅] Add FOREIGN KEY constraint on `account_id` REFERENCES `accounts(id)`
  - [✅] Add CHECK constraint on `type`
  - [✅] Add indexes on `date`, `account_id`, `symbol`, `type`
  - [✅] Add composite index on `(account_id, date)`

- [✅] Create `prices` table
  - [✅] `symbol` TEXT NOT NULL
  - [✅] `date` DATE NOT NULL
  - [✅] `close` REAL NOT NULL
  - [✅] `open` REAL (optional)
  - [✅] `high` REAL (optional)
  - [✅] `low` REAL (optional)
  - [✅] `volume` INTEGER (optional)
  - [✅] `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  - [✅] Add PRIMARY KEY on `(symbol, date)`
  - [✅] Add indexes on `symbol`, `date`
  - [✅] Add composite index on `(symbol, date DESC)`

- [✅] Create database migration system
  - [✅] Add `schema_version` table
  - [✅] Add migration scripts directory
  - [✅] Add migration runner
  - [✅] Create initial migration (v1)

- [✅] Add database utilities
  - [✅] `get_db_path()` - Get database file path
  - [✅] `backup_db()` - Create database backup
  - [✅] `restore_db()` - Restore from backup
  - [✅] `vacuum_db()` - Optimize database
  - [✅] `get_db_stats()` - Get database statistics

- [✅] Write tests for database module
  - [✅] Test database initialization
  - [✅] Test table creation
  - [✅] Test foreign key constraints
  - [✅] Test indexes
  - [✅] Test migration system
  - [✅] Test backup/restore

### 1.2 Database Models & ORM Layer
- [✅] Create `finarius_app/core/models/` (modularized structure)
  - [✅] Create `Account` model class
    - [✅] `__init__()` constructor
    - [✅] `save()` method
    - [✅] `delete()` method
    - [✅] `update()` method
    - [✅] `to_dict()` method
    - [✅] `from_dict()` class method
    - [✅] Validation methods
  - [✅] Create `Transaction` model class
    - [✅] `__init__()` constructor
    - [✅] `save()` method
    - [✅] `delete()` method
    - [✅] `update()` method
    - [✅] `to_dict()` method
    - [✅] `from_dict()` class method
    - [✅] Validation methods (type, qty, price validation)
    - [✅] `get_account()` method (relationship)
  - [✅] Create `Price` model class
    - [✅] `__init__()` constructor
    - [✅] `save()` method
    - [✅] `delete()` method
    - [✅] `update()` method
    - [✅] `to_dict()` method
    - [✅] `from_dict()` class method
    - [✅] Validation methods

- [✅] Create model query helpers
  - [✅] `get_account_by_id(id)` - Get account by ID
  - [✅] `get_account_by_name(name)` - Get account by name
  - [✅] `get_all_accounts()` - Get all accounts
  - [✅] `get_transaction_by_id(id)` - Get transaction by ID
  - [✅] `get_transactions_by_account(account_id, start_date, end_date)` - Filter transactions
  - [✅] `get_transactions_by_symbol(symbol, start_date, end_date)` - Filter by symbol
  - [✅] `get_price(symbol, date)` - Get price for symbol/date
  - [✅] `get_prices(symbol, start_date, end_date)` - Get price range
  - [✅] `get_latest_price(symbol)` - Get most recent price

- [✅] Write tests for models
  - [✅] Test Account CRUD operations
  - [✅] Test Transaction CRUD operations
  - [✅] Test Price CRUD operations
  - [✅] Test model validation
  - [✅] Test query helpers
  - [✅] Test relationships

---

## Phase 2: Market Data & Price Management

### 2.1 Price Downloader
- [✅] Create `finarius_app/core/prices/` (modularized structure)
  - [✅] Create `PriceDownloader` class (`downloader.py`)
    - [✅] Initialize with yfinance client
    - [✅] Add rate limiting/throttling
    - [✅] Add retry logic with exponential backoff
    - [✅] Add error handling for network issues
    - [✅] Add logging for download operations

- [✅] Implement price download functions
  - [✅] `download_price(symbol, date)` - Download single price
    - [✅] Handle missing data gracefully
    - [✅] Handle invalid symbols
    - [✅] Cache results
  - [✅] `download_prices(symbol, start_date, end_date)` - Download price range
    - [✅] Batch download optimization
    - [✅] Handle date ranges efficiently
    - [✅] Progress tracking
  - [✅] `download_latest_price(symbol)` - Get current price
    - [✅] Handle market hours
    - [✅] Handle delayed data
  - [✅] `download_multiple_symbols(symbols, start_date, end_date)` - Batch download
    - [✅] Sequential downloads with rate limiting
    - [✅] Rate limit handling

- [✅] Implement price caching (`cache.py`)
  - [✅] Check database before downloading
  - [✅] Cache downloaded prices to database
  - [✅] Cache invalidation strategy
  - [✅] Cache expiration (optional)
  - [✅] `is_price_cached(symbol, date)` - Check cache
  - [✅] `get_cached_price(symbol, date)` - Get from cache
  - [✅] `update_price_cache(symbol, date, price_data)` - Update cache

- [✅] Add symbol validation (`validation.py`)
  - [✅] `validate_symbol(symbol)` - Validate symbol format
  - [✅] `symbol_exists(symbol)` - Check if symbol is valid
  - [✅] Handle different exchanges (NYSE, NASDAQ, etc.)
  - [✅] Handle different asset types (stocks, ETFs, crypto, etc.)

- [✅] Add price data normalization (`normalization.py`)
  - [✅] Handle different currencies
  - [✅] Handle stock splits
  - [✅] Handle dividends (adjust prices)
  - [✅] Handle missing data points

- [✅] Write tests for price downloader
  - [✅] Test single price download
  - [✅] Test price range download
  - [✅] Test caching mechanism
  - [✅] Test error handling
  - [✅] Test rate limiting
  - [✅] Test symbol validation
  - [✅] Mock yfinance for unit tests

### 2.2 Price Management Utilities
- [✅] Create price update scheduler (`scheduler.py`)
  - [✅] `update_all_prices()` - Update prices for all symbols in portfolio
  - [✅] `update_prices_for_symbol(symbol)` - Update specific symbol
  - [✅] `schedule_daily_updates()` - Schedule automatic updates (placeholder)
  - [✅] Add last update tracking
  - [✅] `get_all_portfolio_symbols()` - Get unique symbols from transactions

- [✅] Create price analytics helpers (`analytics.py`)
  - [✅] `get_price_history(symbol, days)` - Get price history
  - [✅] `calculate_returns(symbol, start_date, end_date)` - Calculate returns
  - [✅] `get_price_statistics(symbol, start_date, end_date)` - Get stats (min, max, avg, std)
  - [✅] `calculate_daily_returns()` - Calculate daily returns
  - [✅] `get_price_range()` - Get price range information

- [✅] Write tests for price utilities
  - [✅] Test price update scheduler
  - [✅] Test price analytics

---

## Phase 3: Core Portfolio Engine

### 3.1 Portfolio Reconstruction Engine
- [ ] Create `finarius_app/core/engine.py`
  - [ ] Create `PortfolioEngine` class
    - [ ] Initialize with database connection
    - [ ] Initialize with price downloader
    - [ ] Add caching for portfolio state

- [ ] Implement position tracking
  - [ ] `get_positions(account_id, date)` - Get positions at specific date
    - [ ] Calculate from transactions
    - [ ] Handle BUY/SELL transactions
    - [ ] Handle stock splits
    - [ ] Return dict: `{symbol: {qty, cost_basis, avg_price}}`
  - [ ] `get_all_positions(date)` - Get positions across all accounts
  - [ ] `get_current_positions(account_id)` - Get current positions
  - [ ] `get_position_history(symbol, account_id, start_date, end_date)` - Position over time

- [ ] Implement PRU (Prix de Revient Unitaire / Average Cost) calculation
  - [ ] `calculate_pru(symbol, account_id, date)` - Calculate average cost
    - [ ] Handle FIFO method
    - [ ] Handle multiple purchases
    - [ ] Handle partial sales
    - [ ] Include fees in cost basis
  - [ ] `get_pru_history(symbol, account_id, start_date, end_date)` - PRU over time

- [ ] Implement portfolio value calculation
  - [ ] `calculate_portfolio_value(account_id, date)` - Portfolio value at date
    - [ ] Get positions
    - [ ] Get prices for all symbols
    - [ ] Calculate total value
  - [ ] `calculate_portfolio_value_over_time(account_id, start_date, end_date)` - Value history
    - [ ] Daily/weekly/monthly snapshots
    - [ ] Efficient calculation
  - [ ] `get_portfolio_breakdown(account_id, date)` - Breakdown by symbol

- [ ] Implement cash flow tracking
  - [ ] `get_cash_flows(account_id, start_date, end_date)` - Get all cash flows
    - [ ] DEPOSIT transactions
    - [ ] WITHDRAW transactions
    - [ ] DIVIDEND transactions
  - [ ] `calculate_net_cash_flow(account_id, start_date, end_date)` - Net cash flow
  - [ ] `get_cash_balance(account_id, date)` - Cash balance at date

- [ ] Write tests for portfolio engine
  - [ ] Test position tracking
  - [ ] Test PRU calculation
  - [ ] Test portfolio value calculation
  - [ ] Test cash flow tracking
  - [ ] Test edge cases (empty portfolio, single transaction, etc.)

### 3.2 Performance Metrics
- [ ] Create `finarius_app/core/metrics.py`
  - [ ] Create `MetricsCalculator` class
    - [ ] Initialize with portfolio engine
    - [ ] Initialize with database connection

- [ ] Implement realized gains/losses
  - [ ] `calculate_realized_gains(account_id, start_date, end_date)` - Realized PnL
    - [ ] Track cost basis for sold positions
    - [ ] Calculate gain/loss per sale
    - [ ] Include fees
  - [ ] `get_realized_gains_by_symbol(account_id, start_date, end_date)` - Breakdown by symbol
  - [ ] `get_realized_gains_history(account_id, start_date, end_date)` - Over time

- [ ] Implement unrealized gains/losses
  - [ ] `calculate_unrealized_gains(account_id, date)` - Unrealized PnL
    - [ ] Current positions
    - [ ] Current market prices
    - [ ] Cost basis (PRU)
  - [ ] `get_unrealized_gains_by_symbol(account_id, date)` - Breakdown by symbol
  - [ ] `get_unrealized_gains_history(account_id, start_date, end_date)` - Over time

- [ ] Implement total return calculation
  - [ ] `calculate_total_return(account_id, start_date, end_date)` - Total return
    - [ ] Realized + Unrealized gains
    - [ ] Include dividends
  - [ ] `calculate_total_return_percentage(account_id, start_date, end_date)` - Return %

- [ ] Implement CAGR (Compound Annual Growth Rate)
  - [ ] `calculate_cagr(account_id, start_date, end_date)` - CAGR calculation
    - [ ] Formula: (End Value / Start Value)^(1/years) - 1
    - [ ] Handle different time periods
    - [ ] Handle negative returns
  - [ ] `get_cagr_history(account_id, start_date, end_date)` - CAGR over time

- [ ] Implement IRR (Internal Rate of Return)
  - [ ] `calculate_irr(account_id, start_date, end_date)` - IRR calculation
    - [ ] Use numpy financial functions or custom implementation
    - [ ] Handle cash flows (deposits, withdrawals)
    - [ ] Handle multiple cash flows
  - [ ] `get_irr_history(account_id, start_date, end_date)` - IRR over time

- [ ] Implement TWRR (Time-Weighted Rate of Return)
  - [ ] `calculate_twrr(account_id, start_date, end_date)` - TWRR calculation
    - [ ] Handle cash flows properly
    - [ ] Calculate period returns
    - [ ] Chain period returns
  - [ ] `get_twrr_history(account_id, start_date, end_date)` - TWRR over time

- [ ] Implement dividend analytics
  - [ ] `get_dividend_history(account_id, start_date, end_date)` - All dividends
  - [ ] `calculate_dividend_yield(account_id, date)` - Dividend yield
  - [ ] `calculate_dividend_income(account_id, start_date, end_date)` - Total dividend income
  - [ ] `get_dividend_by_symbol(account_id, start_date, end_date)` - Breakdown by symbol
  - [ ] `calculate_dividend_yield_by_symbol(symbol, account_id, date)` - Yield per symbol

- [ ] Implement additional metrics
  - [ ] `calculate_sharpe_ratio(account_id, start_date, end_date, risk_free_rate)` - Sharpe ratio
  - [ ] `calculate_max_drawdown(account_id, start_date, end_date)` - Maximum drawdown
  - [ ] `calculate_volatility(account_id, start_date, end_date)` - Portfolio volatility
  - [ ] `calculate_beta(account_id, benchmark_symbol, start_date, end_date)` - Beta vs benchmark

- [ ] Write tests for metrics
  - [ ] Test realized gains calculation
  - [ ] Test unrealized gains calculation
  - [ ] Test CAGR calculation (known test cases)
  - [ ] Test IRR calculation (known test cases)
  - [ ] Test TWRR calculation (known test cases)
  - [ ] Test dividend analytics
  - [ ] Test edge cases

---

## Phase 4: User Interface - Streamlit App

### 4.1 Main Application Structure
- [ ] Update `finarius_app/app.py`
  - [ ] Configure Streamlit page settings
    - [ ] Page title: "Finarius"
    - [ ] Page icon: 📊
    - [ ] Layout: wide
    - [ ] Sidebar state: expanded
  - [ ] Initialize database connection (singleton)
  - [ ] Add navigation/sidebar menu
    - [ ] Dashboard
    - [ ] Accounts
    - [ ] Transactions
    - [ ] Portfolio
    - [ ] Analytics
    - [ ] Settings
  - [ ] Add session state management
  - [ ] Add error handling wrapper

### 4.2 Accounts Management UI
- [ ] Create `finarius_app/ui/accounts.py`
  - [ ] `render_accounts_page()` function
    - [ ] Display list of accounts (table)
      - [ ] Account name
      - [ ] Currency
      - [ ] Created date
      - [ ] Actions (Edit, Delete)
    - [ ] Add account form
      - [ ] Name input
      - [ ] Currency selector
      - [ ] Validation
      - [ ] Submit button
    - [ ] Edit account modal/form
    - [ ] Delete confirmation dialog
    - [ ] Success/error messages
  - [ ] Add account statistics
    - [ ] Total accounts
    - [ ] Total value per account
    - [ ] Account breakdown chart

- [ ] Write tests for accounts UI
  - [ ] Test account creation
  - [ ] Test account editing
  - [ ] Test account deletion
  - [ ] Test validation

### 4.3 Transactions Management UI
- [ ] Create `finarius_app/ui/transactions.py`
  - [ ] `render_transactions_page()` function
    - [ ] Display transactions table
      - [ ] Date
      - [ ] Account
      - [ ] Type
      - [ ] Symbol
      - [ ] Quantity
      - [ ] Price
      - [ ] Fee
      - [ ] Total
      - [ ] Actions (Edit, Delete)
    - [ ] Filtering options
      - [ ] By account
      - [ ] By date range
      - [ ] By symbol
      - [ ] By type
    - [ ] Sorting options
    - [ ] Pagination (if needed)
    - [ ] Export to CSV option

- [ ] Create transaction form
  - [ ] `render_transaction_form()` function
    - [ ] Account selector
    - [ ] Date picker
    - [ ] Type selector (BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAW)
    - [ ] Symbol input (with autocomplete/validation)
      - [ ] Show current price when symbol entered
    - [ ] Quantity input
    - [ ] Price input (auto-fill from market if available)
    - [ ] Fee input
    - [ ] Notes textarea
    - [ ] Validation
      - [ ] Required fields
      - [ ] Positive quantities
      - [ ] Valid dates
      - [ ] Symbol validation
    - [ ] Submit button
    - [ ] Cancel button

- [ ] Add transaction editing
  - [ ] Edit form (pre-filled)
  - [ ] Update functionality
  - [ ] Validation

- [ ] Add transaction deletion
  - [ ] Delete confirmation
  - [ ] Cascade handling (if needed)

- [ ] Add bulk import
  - [ ] CSV import form
  - [ ] File upload
  - [ ] CSV parsing
  - [ ] Validation
  - [ ] Preview before import
  - [ ] Import execution
  - [ ] Error reporting

- [ ] Write tests for transactions UI
  - [ ] Test transaction creation
  - [ ] Test transaction editing
  - [ ] Test transaction deletion
  - [ ] Test filtering
  - [ ] Test CSV import

### 4.4 Dashboard UI
- [ ] Create `finarius_app/ui/dashboard.py`
  - [ ] `render_dashboard_page()` function
    - [ ] Account selector (if multiple accounts)
    - [ ] Date range selector
    - [ ] Refresh button

- [ ] Portfolio overview section
  - [ ] Total portfolio value (current)
  - [ ] Total cost basis
  - [ ] Total unrealized gains/losses
  - [ ] Total realized gains/losses
  - [ ] Total return (absolute and %)
  - [ ] Number of positions
  - [ ] Number of symbols

- [ ] Performance metrics section
  - [ ] CAGR display
  - [ ] IRR display
  - [ ] TWRR display
  - [ ] Sharpe ratio (if implemented)
  - [ ] Max drawdown (if implemented)

- [ ] Charts section
  - [ ] Portfolio value over time (Plotly line chart)
    - [ ] Interactive
    - [ ] Hover tooltips
    - [ ] Date range selection
  - [ ] Portfolio allocation (Pie chart)
    - [ ] By symbol
    - [ ] By sector (if data available)
  - [ ] Returns distribution (Histogram)
  - [ ] Performance vs benchmark (if implemented)
  - [ ] Dividend income over time (Bar chart)

- [ ] Top positions table
  - [ ] Symbol
  - [ ] Quantity
  - [ ] Current price
  - [ ] Cost basis
  - [ ] Current value
  - [ ] Unrealized gain/loss
  - [ ] Return %

- [ ] Recent transactions table
  - [ ] Last 10 transactions
  - [ ] Quick view

- [ ] Dividend summary
  - [ ] Total dividends (period)
  - [ ] Dividend yield
  - [ ] Top dividend payers

- [ ] Write tests for dashboard UI
  - [ ] Test data display
  - [ ] Test chart rendering
  - [ ] Test filtering

### 4.5 Portfolio Analytics UI
- [ ] Create `finarius_app/ui/analytics.py`
  - [ ] `render_analytics_page()` function
    - [ ] Date range selector
    - [ ] Account selector

- [ ] Performance analytics section
  - [ ] Performance metrics table
    - [ ] CAGR
    - [ ] IRR
    - [ ] TWRR
    - [ ] Total return
    - [ ] Volatility
  - [ ] Performance comparison chart
  - [ ] Rolling returns chart

- [ ] Gains/losses analysis
  - [ ] Realized gains breakdown
    - [ ] By symbol
    - [ ] By date
    - [ ] Chart
  - [ ] Unrealized gains breakdown
    - [ ] By symbol
    - [ ] Chart
  - [ ] Combined PnL chart

- [ ] Dividend analytics section
  - [ ] Dividend income over time
  - [ ] Dividend by symbol
  - [ ] Dividend yield trends
  - [ ] Dividend calendar (if applicable)

- [ ] Position analytics
  - [ ] Position size analysis
  - [ ] Concentration risk
  - [ ] Diversification metrics

- [ ] Write tests for analytics UI
  - [ ] Test analytics calculations
  - [ ] Test chart rendering

### 4.6 Settings & Configuration UI
- [ ] Create `finarius_app/ui/settings.py`
  - [ ] `render_settings_page()` function
    - [ ] Database settings
      - [ ] Database path
      - [ ] Backup database button
      - [ ] Restore database button
      - [ ] Vacuum database button
    - [ ] Price update settings
      - [ ] Auto-update frequency
      - [ ] Manual update button
      - [ ] Update all prices button
    - [ ] Display settings
      - [ ] Default currency
      - [ ] Date format
      - [ ] Number format
    - [ ] Export/Import settings
      - [ ] Export data button
      - [ ] Import data button

- [ ] Write tests for settings UI

---

## Phase 5: Configuration & Utilities

### 5.1 Configuration Management
- [ ] Create `finarius_app/core/config.py`
  - [ ] Create `Config` class
    - [ ] Load from config file (YAML/JSON/TOML)
    - [ ] Environment variable support
    - [ ] Default values
  - [ ] Configuration options
    - [ ] Database path
    - [ ] Default currency
    - [ ] Price update frequency
    - [ ] Cache settings
    - [ ] Logging level
    - [ ] Date format
    - [ ] Number format

- [ ] Create `config.yaml` or `config.toml`
  - [ ] Default configuration
  - [ ] Documentation comments

- [ ] Write tests for configuration
  - [ ] Test config loading
  - [ ] Test environment variable override
  - [ ] Test default values

### 5.2 Logging Setup
- [ ] Create `finarius_app/core/logger.py`
  - [ ] Configure logging
    - [ ] Log level (INFO, DEBUG, etc.)
    - [ ] Log format
    - [ ] Log file output (optional)
    - [ ] Console output
  - [ ] Create logger instances for modules
  - [ ] Add structured logging (optional)

- [ ] Add logging throughout application
  - [ ] Database operations
  - [ ] Price downloads
  - [ ] Portfolio calculations
  - [ ] UI interactions
  - [ ] Errors and exceptions

### 5.3 Error Handling
- [ ] Create `finarius_app/core/exceptions.py`
  - [ ] `FinariusException` base class
  - [ ] `DatabaseError` exception
  - [ ] `PriceDownloadError` exception
  - [ ] `ValidationError` exception
  - [ ] `SymbolNotFoundError` exception
  - [ ] `InsufficientDataError` exception

- [ ] Add error handling throughout
  - [ ] Database operations
  - [ ] Price downloads
  - [ ] Calculations
  - [ ] UI components

- [ ] Add user-friendly error messages
  - [ ] Display in UI
  - [ ] Log detailed errors

### 5.4 Utility Functions
- [ ] Create `finarius_app/core/utils.py`
  - [ ] Date utilities
    - [ ] `parse_date(date_string)` - Parse date string
    - [ ] `format_date(date)` - Format date
    - [ ] `get_date_range(start, end)` - Generate date range
  - [ ] Number utilities
    - [ ] `format_currency(amount, currency)` - Format currency
    - [ ] `format_percentage(value)` - Format percentage
    - [ ] `round_decimal(value, decimals)` - Round to decimals
  - [ ] Validation utilities
    - [ ] `validate_symbol(symbol)` - Validate symbol
    - [ ] `validate_date(date)` - Validate date
    - [ ] `validate_amount(amount)` - Validate amount
  - [ ] Data utilities
    - [ ] `safe_divide(numerator, denominator)` - Safe division
    - [ ] `calculate_percentage_change(old, new)` - Percentage change

- [ ] Write tests for utilities
  - [ ] Test date utilities
  - [ ] Test number utilities
  - [ ] Test validation utilities

---

## Phase 6: Testing & Quality Assurance

### 6.1 Unit Tests
- [ ] Set up test framework
  - [ ] Configure pytest
  - [ ] Create test fixtures
    - [ ] Database fixture (in-memory SQLite)
    - [ ] Sample data fixtures
    - [ ] Mock price downloader fixture

- [ ] Database tests
  - [ ] Test database initialization
  - [ ] Test table creation
  - [ ] Test CRUD operations
  - [ ] Test constraints
  - [ ] Test migrations

- [ ] Model tests
  - [ ] Test Account model
  - [ ] Test Transaction model
  - [ ] Test Price model
  - [ ] Test validation
  - [ ] Test relationships

- [ ] Price downloader tests
  - [ ] Test price download (mocked)
  - [ ] Test caching
  - [ ] Test error handling
  - [ ] Test symbol validation

- [ ] Portfolio engine tests
  - [ ] Test position tracking
  - [ ] Test PRU calculation
  - [ ] Test portfolio value
  - [ ] Test cash flows

- [ ] Metrics tests
  - [ ] Test realized gains
  - [ ] Test unrealized gains
  - [ ] Test CAGR
  - [ ] Test IRR
  - [ ] Test TWRR
  - [ ] Test dividend analytics

- [ ] Utility tests
  - [ ] Test all utility functions

### 6.2 Integration Tests
- [ ] End-to-end workflow tests
  - [ ] Create account → Add transaction → View portfolio
  - [ ] Add multiple transactions → Calculate metrics
  - [ ] Download prices → Update portfolio value
  - [ ] Export/import data

- [ ] Database integration tests
  - [ ] Test with real SQLite database
  - [ ] Test migrations
  - [ ] Test backup/restore

### 6.3 Test Coverage
- [ ] Set up coverage reporting
  - [ ] Configure pytest-cov
  - [ ] Set coverage thresholds
  - [ ] Generate coverage reports

- [ ] Achieve target coverage
  - [ ] Aim for 80%+ coverage
  - [ ] Focus on core logic
  - [ ] Document uncovered areas

### 6.4 Code Quality
- [ ] Set up linting
  - [ ] Configure flake8 (already done)
  - [ ] Configure black (already done)
  - [ ] Configure mypy (already done)
  - [ ] Run linting in CI

- [ ] Code review checklist
  - [ ] Follow PEP 8
  - [ ] Add docstrings
  - [ ] Add type hints
  - [ ] Handle errors properly
  - [ ] Write tests

---

## Phase 7: Documentation

### 7.1 Code Documentation
- [ ] Add docstrings to all modules
  - [ ] Module-level docstrings
  - [ ] Class docstrings
  - [ ] Function docstrings
  - [ ] Parameter documentation
  - [ ] Return value documentation
  - [ ] Example usage

- [ ] Add type hints throughout
  - [ ] Function parameters
  - [ ] Return types
  - [ ] Class attributes
  - [ ] Use `typing` module

- [ ] Generate API documentation
  - [ ] Use Sphinx or similar
  - [ ] Create HTML documentation
  - [ ] Include examples

### 7.2 User Documentation
- [ ] Update README.md
  - [ ] Installation instructions
  - [ ] Quick start guide
  - [ ] Feature overview
  - [ ] Screenshots
  - [ ] FAQ

- [ ] Create user guide
  - [ ] Getting started
  - [ ] Adding accounts
  - [ ] Adding transactions
  - [ ] Understanding metrics
  - [ ] Troubleshooting

- [ ] Create developer guide
  - [ ] Setup development environment
  - [ ] Architecture overview
  - [ ] Adding new features
  - [ ] Testing guidelines
  - [ ] Contributing guidelines

### 7.3 API Documentation
- [ ] Document core API
  - [ ] Database API
  - [ ] Portfolio engine API
  - [ ] Metrics API
  - [ ] Price downloader API

---

## Phase 8: Performance & Optimization

### 8.1 Database Optimization
- [ ] Analyze query performance
  - [ ] Add missing indexes
  - [ ] Optimize slow queries
  - [ ] Use EXPLAIN QUERY PLAN

- [ ] Implement query caching
  - [ ] Cache frequently accessed data
  - [ ] Cache invalidation strategy

- [ ] Database maintenance
  - [ ] Regular VACUUM
  - [ ] ANALYZE tables
  - [ ] Optimize indexes

### 8.2 Calculation Optimization
- [ ] Optimize portfolio calculations
  - [ ] Cache intermediate results
  - [ ] Batch calculations
  - [ ] Parallel processing (if applicable)

- [ ] Optimize price downloads
  - [ ] Batch downloads
  - [ ] Parallel downloads (if possible)
  - [ ] Smart caching

### 8.3 UI Performance
- [ ] Optimize Streamlit rendering
  - [ ] Use caching (@st.cache_data)
  - [ ] Lazy loading
  - [ ] Pagination for large datasets

- [ ] Optimize chart rendering
  - [ ] Limit data points
  - [ ] Use sampling for long time series
  - [ ] Optimize Plotly charts

---

## Phase 9: Security & Privacy

### 9.1 Data Security
- [ ] Implement database encryption (optional)
  - [ ] SQLCipher or similar
  - [ ] Encryption key management

- [ ] Secure data storage
  - [ ] File permissions
  - [ ] Backup encryption

### 9.2 Input Validation
- [ ] Validate all user inputs
  - [ ] SQL injection prevention (use parameterized queries)
  - [ ] XSS prevention (Streamlit handles this)
  - [ ] Data type validation
  - [ ] Range validation

### 9.3 Privacy
- [ ] Ensure no external data transmission
  - [ ] Verify all operations are local
  - [ ] Document data flow
  - [ ] No telemetry or tracking

---

## Phase 10: Deployment & Distribution

### 10.1 Packaging
- [ ] Create setup.py or use pyproject.toml
  - [ ] Package metadata
  - [ ] Dependencies
  - [ ] Entry points

- [ ] Create distribution packages
  - [ ] Source distribution (sdist)
  - [ ] Wheel distribution
  - [ ] Test installation

### 10.2 Distribution
- [ ] Create installation script
  - [ ] Automated setup
  - [ ] Dependency installation
  - [ ] Database initialization

- [ ] Create release notes
  - [ ] Version history
  - [ ] Changelog
  - [ ] Known issues

### 10.3 Optional: Docker Support
- [ ] Create Dockerfile
  - [ ] Base image
  - [ ] Dependencies
  - [ ] Application setup
  - [ ] Expose port

- [ ] Create docker-compose.yml
  - [ ] Service definition
  - [ ] Volume mounts
  - [ ] Port mapping

---

## Phase 11: Future Enhancements (Optional)

### 11.1 Additional Features
- [ ] Multi-currency support
  - [ ] Currency conversion
  - [ ] Multi-currency portfolios
  - [ ] Exchange rate tracking

- [ ] Tax reporting
  - [ ] Tax lot tracking
  - [ ] Tax report generation
  - [ ] Wash sale detection

- [ ] Benchmark comparison
  - [ ] Compare to S&P 500
  - [ ] Compare to custom benchmarks
  - [ ] Relative performance charts

- [ ] Alerts and notifications
  - [ ] Price alerts
  - [ ] Performance alerts
  - [ ] Dividend alerts

- [ ] Advanced analytics
  - [ ] Risk metrics (VaR, CVaR)
  - [ ] Factor analysis
  - [ ] Correlation analysis

- [ ] Data export
  - [ ] Export to Excel
  - [ ] Export to PDF reports
  - [ ] API for external tools

---

## Progress Tracking

**Last Updated:** 2025-01-27
**Current Phase:** Phase 2 - Market Data & Price Management
**Current Step:** Phase 2.1 Complete - Price Downloader implemented
**Overall Progress:** ~10% (Steps 1.1, 1.2, and 2.1 completed)

### Quick Stats
- Total Tasks: ~300+
- Completed: ~50 (Steps 1.1, 1.2, and 2.1 fully completed)
- In Progress: 0
- Not Started: ~250+

---

## Notes

- Update this document as tasks are completed
- Check off items using `[x]` when done
- Add notes for any blockers or issues
- Update progress percentage regularly

