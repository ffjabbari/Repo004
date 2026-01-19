#!/usr/bin/env python3
"""
Process bank statements into SQLite database and fill Excel template.
"""

import sys
from pathlib import Path
from tax_filler.database_processor import DatabaseProcessor
from tax_filler.template_analyzer import TemplateAnalyzer
from tax_filler.excel_filler import ExcelFiller
from tax_filler.categorizer import TransactionCategorizer


def main():
    """Main processing function."""
    # Configuration
    csv_path = "/Users/fjabbari/@@@PUBLIC/@@@TAX2025/stmt.csv"
    template_path = "/Users/fjabbari/@@@PUBLIC/@@@TAX2025/final001.xlsx"
    db_path = "tax_data_2025.db"
    tax_year = 2025
    output_path = "/Users/fjabbari/@@@PUBLIC/@@@TAX2025/final001_2025.xlsx"
    
    print("=" * 60)
    print("TAX DOCUMENT PROCESSOR")
    print("=" * 60)
    
    # Step 1: Parse CSV and create database
    print("\n1. Parsing CSV and creating database...")
    processor = DatabaseProcessor(db_path)
    
    try:
        transactions = processor.parse_csv(csv_path, tax_year)
        print(f"✓ Parsed {len(transactions)} transactions from CSV")
        
        # Process into database
        processor.process_transactions(transactions, tax_year)
        print(f"✓ Created SQLite database: {db_path}")
        
        # Show entity summary
        print("\n2. Entity Summary (Top 20 by amount):")
        print("-" * 60)
        entity_summary = processor.get_entity_summary(tax_year)
        for i, (entity, total, count, first_date, last_date) in enumerate(entity_summary[:20], 1):
            print(f"{i:2d}. {entity:40s} | ${total:12,.2f} | {count:4d} transactions")
        
    except Exception as e:
        print(f"✗ Error processing CSV: {e}")
        import traceback
        traceback.print_exc()
        processor.close()
        sys.exit(1)
    
    # Step 2: Categorize transactions
    print("\n3. Categorizing transactions...")
    categorizer = TransactionCategorizer()
    
    # Convert database transactions to categorized format
    from tax_filler.bank_parser import Transaction as ParserTransaction
    parser_transactions = []
    for trans in transactions:
        parser_trans = ParserTransaction(
            date=trans.date,
            description=trans.description,
            amount=abs(trans.amount),
            transaction_type='debit' if trans.amount < 0 else 'credit',
            account=None,
            raw_text=trans.description
        )
        parser_transactions.append(parser_trans)
    
    categorized = categorizer.categorize_batch(parser_transactions)
    
    business_count = sum(1 for t in categorized if t.is_business_expense)
    rental_income_count = sum(1 for t in categorized if t.is_rental_income)
    rental_expense_count = sum(1 for t in categorized if t.is_rental_expense)
    
    print(f"   Business expenses: {business_count}")
    print(f"   Rental income: {rental_income_count}")
    print(f"   Rental expenses: {rental_expense_count}")
    
    # Step 3: Analyze template
    print("\n4. Analyzing Excel template...")
    analyzer = TemplateAnalyzer(template_path)
    structure = analyzer.analyze()
    analyzer.close()
    print("✓ Template analyzed")
    
    # Step 4: Fill template
    print("\n5. Filling Excel template...")
    filler = ExcelFiller(template_path, structure)
    filler.fill(categorized, output_path)
    filler.close()
    print(f"✓ Filled template saved to: {output_path}")
    
    processor.close()
    
    print("\n" + "=" * 60)
    print("✓ PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"\nDatabase: {db_path}")
    print(f"Filled Excel: {output_path}")


if __name__ == "__main__":
    main()
