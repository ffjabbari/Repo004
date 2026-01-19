# Tax Document Processing System - 2025

A comprehensive Python system to process bank statements, categorize transactions, and automatically fill your accountant's Excel tax template.

## Overview

This system processes your financial data from bank statements (CSV/PDF), categorizes transactions, stores everything in a SQLite database, and generates Excel files ready for your tax accountant.

## System Architecture

### Database Structure (SQLite)

The system uses `tax_data_2025.db` with 4 main tables:

1. **TaxYearSummary** - Year-level totals (beginning balance, total credits, total debits, ending balance)
2. **TaxYearDetail** - All individual transactions with dates, descriptions, amounts
3. **EntitySummary** - Aggregated totals by entity (e.g., PAYPAL-OVIEDO, UTIL-AMEREN, RENTAL-1029)
4. **EntityDetail** - All transactions grouped by entity

### Key Features

- ✅ Parses bank statements (CSV, PDF, Excel)
- ✅ Categorizes transactions automatically
- ✅ Consolidates similar payments (e.g., all PayPal payments to same entity)
- ✅ Groups utilities by type (UTIL-AMEREN, UTIL-SPIRE, etc.)
- ✅ Tracks rental income and expenses by property
- ✅ Generates Excel files for tax preparation
- ✅ Creates 1099 preparation worksheets

## Project Structure

```
Repo004/
├── tax_data_2025.db          # SQLite database (ALL YOUR DATA)
├── tax_filler/               # Core processing modules
│   ├── database_processor.py # Database operations
│   ├── bank_parser.py        # Parse bank statements
│   ├── categorizer.py        # Categorize transactions
│   └── ...
├── process_statements.py     # Main processing script
├── add_additional_transactions.py  # Add W-2, rental income, etc.
├── add_property_expenses.py  # Add property taxes/insurance
├── create_final002.py        # Generate final002.xlsx
├── create_final1099.py       # Generate final1099.xlsx
├── export_to_excel.py        # Export database to Excel
├── update_paypal_entities.py # Consolidate PayPal payments
├── update_utility_entities.py # Consolidate utility bills
└── README.md                 # This file
```

## How It Works

### 1. Data Processing Flow

```
Bank Statements (CSV/PDF)
    ↓
Parse Transactions
    ↓
Categorize by Entity
    ↓
Store in SQLite Database
    ↓
Generate Excel Files
```

### 2. Entity Consolidation

The system automatically consolidates similar transactions:

- **PayPal Payments:** `PAYPAL-OVIEDO`, `PAYPAL-RPARLMAN`, etc.
- **Utilities:** `UTIL-AMEREN`, `UTIL-SPIRE`, `UTIL-SPECTRUM`, etc.
- **Rental Income:** `RENTAL-1029`, `RENTAL-1035`, etc.
- **Property Expenses:** `PROPERTY-1029-TAX`, `PROPERTY-1029-INSURANCE`, etc.

### 3. Excel File Generation

- **final002.xlsx** - Main tax document (based on template)
- **final1099.xlsx** - PayPal payment summary for 1099 preparation
- **Database Exports** - TaxYearSummary, EntitySummary, etc.

## Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
```

Required packages:
- openpyxl (Excel file handling)
- pandas (Data processing)
- pdfplumber (PDF parsing)
- sqlite3 (Built-in Python)

### Initial Setup

1. Place your bank statement CSV in: `/Users/fjabbari/@@@PUBLIC/@@@TAX2025/stmt.csv`
2. Place your tax template in: `/Users/fjabbari/@@@PUBLIC/@@@TAX2025/final001.xlsx`
3. Run the processing script:

```bash
cd /Users/fjabbari/REPO_CURSOR/Repo004
python3 process_statements.py
```

## Usage

### Processing Bank Statements

```bash
python3 process_statements.py
```

This will:
- Parse the CSV file
- Create/update the database
- Categorize all transactions

### Adding Additional Data

**Add W-2 Income, Rental Income, Storm Expenses:**
```bash
python3 add_additional_transactions.py
```

**Add Property Expenses (Taxes, Insurance):**
```bash
python3 add_property_expenses.py
```

### Generating Excel Files

**Create final002.xlsx (Main Tax Document):**
```bash
python3 create_final002.py
```

**Create final1099.xlsx (PayPal Summary):**
```bash
python3 create_final1099.py
```

**Export Database to Excel:**
```bash
python3 export_to_excel.py
```

## Database Queries

You can query the database directly:

```bash
sqlite3 tax_data_2025.db
```

**Example queries:**

```sql
-- See all entities
SELECT entity_name, total_amount, transaction_count 
FROM EntitySummary 
ORDER BY ABS(total_amount) DESC;

-- See all PayPal entities
SELECT * FROM EntitySummary 
WHERE entity_name LIKE 'PAYPAL-%';

-- See all transactions for an entity
SELECT * FROM EntityDetail 
WHERE entity_name = 'PAYPAL-OVIEDO';

-- See year summary
SELECT * FROM TaxYearSummary;
```

## Current Data Status (2025)

### Income
- ✅ W-2 Income: $207,644.09
- ✅ Rental Income: $58,020.00 (6 properties)
- ✅ Social Security: $43,641.00

### Expenses
- ✅ Property Taxes: $23,578.03 (7 properties)
- ✅ Property Insurance: $5,850.90 (6 properties)
- ✅ Utilities: $21,887.08 (6 types)
- ✅ Storm Expenses: $8,496.36

### Transactions
- ✅ Total Transactions: 1,231
- ✅ PayPal Entities: 20
- ✅ Utility Entities: 6

## Important Notes

### Properties
- **Rental Properties:** 1029, 1035, 1108, 5015, 5952, 5956
- **Owner-Occupied:** 1039 (NOT a rental - no rental income/expenses)

### Entity Naming Convention
- `PAYPAL-XXX` - PayPal payments to entity XXX
- `UTIL-XXX` - Utility bills (e.g., UTIL-AMEREN, UTIL-SPIRE)
- `RENTAL-XXX` - Rental income for property XXX
- `PROPERTY-XXX-TAX` - Property tax for property XXX
- `PROPERTY-XXX-INSURANCE` - Insurance for property XXX

## Continuing Your Work

### Next Session

1. **Open the workspace:** `/Users/fjabbari/REPO_CURSOR/Repo004`
2. **Say:** "I'm back, let's continue working on my 2025 taxes"
3. **The system will:**
   - Access the database (`tax_data_2025.db`)
   - Use all existing scripts
   - Continue from where you left off

### Typical Workflow

1. **Review generated files:**
   - Check `final002.xlsx` for accuracy
   - Review `final1099.xlsx` and mark which need 1099 forms

2. **Add new data:**
   - When you receive 1099 forms, we'll add them
   - Any additional income/expenses

3. **Update and regenerate:**
   - Update database with new information
   - Regenerate Excel files (final003.xlsx, etc.)

### Updating the Database

All scripts update the database automatically. The database is the **single source of truth** for all your tax data.

## File Locations

### Database
- **Location:** `/Users/fjabbari/REPO_CURSOR/Repo004/tax_data_2025.db`
- **Size:** ~492 KB
- **Format:** SQLite3

### Template
- **Location:** `/Users/fjabbari/@@@PUBLIC/@@@TAX2025/final001.xlsx`
- **Purpose:** Reference template from previous year

### Output Files
- **Location:** `/Users/fjabbari/@@@PUBLIC/@@@TAX2025/`
- **Files:**
  - `final002.xlsx` - Main tax document
  - `final1099.xlsx` - PayPal summary
  - `TaxYearSummary.xlsx` - Database export
  - `EntitySummary.xlsx` - Database export
  - etc.

## Troubleshooting

### Database Issues

If you need to reset or recreate the database:
```bash
# Backup first!
cp tax_data_2025.db tax_data_2025.db.backup

# Then reprocess
python3 process_statements.py
```

### Excel File Issues

If Excel files are corrupted or need regeneration:
```bash
python3 create_final002.py
python3 create_final1099.py
```

## Version History

- **v1.0** (January 2025) - Initial system creation
  - Bank statement processing
  - Entity consolidation
  - Excel file generation
  - Database structure

## Support

For questions or issues:
1. Check the `SESSION_SUMMARY.md` file for session notes
2. Review database queries using SQLite
3. Check generated Excel files for data verification

## License

This project is for personal tax preparation use.

---

**Last Updated:** January 2025  
**Database:** tax_data_2025.db  
**Status:** Ready for tax year 2025
