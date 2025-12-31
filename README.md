# Personal Investment Analytics App

A fully local, privacy-first portfolio tracking and analytics application similar to Finary but fully offline and customizable.

## Features

- Manual input of accounts, cash flows, trades, and dividends
- Automatic market price download and caching
- Portfolio reconstruction over time
- Performance metrics (CAGR, IRR, TWRR)
- Realized / Unrealized PnL
- Dividend analytics
- Interactive dashboards

## Tech Stack

- **Language**: Python
- **Database**: SQLite
- **Market Data**: yfinance
- **Analytics**: Pandas
- **Charts**: Plotly
- **UI**: Streamlit
- **Storage**: Local disk

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd finarius
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install pre-commit hooks (optional but recommended):
```bash
pre-commit install
```

## Usage

Run the Streamlit application:
```bash
streamlit run portfolio_app/app.py
```

## Project Structure

```
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
```

## Database Schema

### accounts
| id | name | currency |

### transactions
| id | date | account_id | type | symbol | qty | price | fee |

Transaction types: BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAW

### prices
| symbol | date | close |

## Core Calculations

- PRU (average cost)
- Realized gains
- Unrealized gains
- Portfolio value over time
- Dividend yield
- CAGR
- IRR / TWRR

## Security

- Fully local execution
- No cloud dependencies
- Optional database encryption

## Development

### Code Quality

This project uses:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking
- `pre-commit` hooks for automated checks

Run checks manually:
```bash
black .
flake8 .
mypy .
```

### Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification. Commit messages should follow the format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## License

MIT License - see LICENSE file for details

