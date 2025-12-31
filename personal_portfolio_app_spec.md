# Personal Investment Analytics App

## Goal

Build a fully local, privacy-first portfolio tracking and analytics
application similar to Finary but fully offline and customizable.

## Key Features

-   Manual input of accounts, cash flows, trades, and dividends
-   Automatic market price download and caching
-   Portfolio reconstruction over time
-   Performance metrics (CAGR, IRR, TWRR)
-   Realized / Unrealized PnL
-   Dividend analytics
-   Interactive dashboards

## Tech Stack

  Layer         Tech
  ------------- ------------
  Language      Python
  Database      SQLite
  Market Data   yfinance
  Analytics     Pandas
  Charts        Plotly
  UI            Streamlit
  Storage       Local disk

## Database Schema

### accounts

| id \| name \| currency \|

### transactions

| id \| date \| account_id \| type \| symbol \| qty \| price \| fee \|

Types: BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAW

### prices

| symbol \| date \| close \|

## Architecture

    portfolio_app/
     ├ app.py
     ├ db.sqlite
     ├ core/
     │   ├ engine.py
     │   ├ prices.py
     │   ├ metrics.py
     └ ui/
         ├ dashboard.py
         ├ trades.py

## Core Calculations

-   PRU (average cost)
-   Realized gains
-   Unrealized gains
-   Portfolio value over time
-   Dividend yield
-   CAGR
-   IRR / TWRR

## Security

-   Fully local execution
-   No cloud
-   Optional database encryption

## Next Steps

-   Initialize database
-   Implement price downloader & cache
-   Build core portfolio reconstruction engine
-   Create Streamlit dashboard
