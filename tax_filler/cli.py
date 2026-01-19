"""
Command-line interface for tax document filler.
"""

import sys
import argparse
from pathlib import Path
from typing import List
from tax_filler.bank_parser import BankStatementParser
from tax_filler.categorizer import TransactionCategorizer
from tax_filler.template_analyzer import TemplateAnalyzer
from tax_filler.excel_filler import ExcelFiller


def process_statements(
    template_path: str,
    statement_paths: List[str],
    output_path: str = None,
    year: int = None
):
    """
    Process bank statements and fill tax template.
    
    Args:
        template_path: Path to Excel tax template
        statement_paths: List of paths to bank statement files
        output_path: Optional output path for filled template
        year: Tax year (for filtering transactions)
    """
    print("=" * 60)
    print("TAX DOCUMENT FILLER")
    print("=" * 60)
    
    # Step 1: Analyze template
    print("\n1. Analyzing template structure...")
    analyzer = TemplateAnalyzer(template_path)
    structure = analyzer.analyze()
    analyzer.close()
    print("✓ Template analyzed")
    
    # Step 2: Parse bank statements
    print("\n2. Parsing bank statements...")
    parser = BankStatementParser()
    all_transactions = []
    
    for stmt_path in statement_paths:
        print(f"   Processing: {stmt_path}")
        try:
            transactions = parser.parse_file(stmt_path)
            all_transactions.extend(transactions)
            print(f"   ✓ Found {len(transactions)} transactions")
        except Exception as e:
            print(f"   ✗ Error processing {stmt_path}: {e}")
            continue
    
    print(f"\n✓ Total transactions found: {len(all_transactions)}")
    
    # Filter by year if specified
    if year:
        all_transactions = [
            t for t in all_transactions
            if t.date.year == year
        ]
        print(f"✓ Filtered to {year}: {len(all_transactions)} transactions")
    
    # Step 3: Categorize transactions
    print("\n3. Categorizing transactions...")
    categorizer = TransactionCategorizer()
    categorized = categorizer.categorize_batch(all_transactions)
    
    # Show categorization summary
    business_count = sum(1 for t in categorized if t.is_business_expense)
    rental_income_count = sum(1 for t in categorized if t.is_rental_income)
    rental_expense_count = sum(1 for t in categorized if t.is_rental_expense)
    uncategorized_count = sum(1 for t in categorized if t.category == 'Uncategorized')
    
    print(f"   Business expenses: {business_count}")
    print(f"   Rental income: {rental_income_count}")
    print(f"   Rental expenses: {rental_expense_count}")
    print(f"   Uncategorized: {uncategorized_count}")
    
    # Step 4: Fill template
    print("\n4. Filling Excel template...")
    filler = ExcelFiller(template_path, structure)
    filler.fill(categorized, output_path)
    filler.close()
    
    print("\n" + "=" * 60)
    print("✓ PROCESSING COMPLETE!")
    print("=" * 60)
    
    # Show uncategorized transactions for review
    if uncategorized_count > 0:
        print(f"\n⚠ {uncategorized_count} transactions need manual review:")
        for trans in categorized:
            if trans.category == 'Uncategorized':
                print(f"   {trans.transaction.date.strftime('%Y-%m-%d')} | "
                      f"${abs(trans.transaction.amount):.2f} | "
                      f"{trans.transaction.description[:50]}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Fill tax Excel template from bank statements'
    )
    parser.add_argument(
        'template',
        help='Path to Excel tax template'
    )
    parser.add_argument(
        'statements',
        nargs='+',
        help='Paths to bank statement files (PDF, CSV, or Excel)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output path for filled template (default: template_filled.xlsx)'
    )
    parser.add_argument(
        '-y', '--year',
        type=int,
        help='Tax year to filter transactions (e.g., 2025)'
    )
    
    args = parser.parse_args()
    
    # Validate template exists
    if not Path(args.template).exists():
        print(f"Error: Template file not found: {args.template}")
        sys.exit(1)
    
    # Validate statements exist
    missing = [s for s in args.statements if not Path(s).exists()]
    if missing:
        print(f"Error: Statement files not found: {missing}")
        sys.exit(1)
    
    try:
        process_statements(
            template_path=args.template,
            statement_paths=args.statements,
            output_path=args.output,
            year=args.year
        )
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
