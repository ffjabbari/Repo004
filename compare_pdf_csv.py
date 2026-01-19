#!/usr/bin/env python3
"""
Compare PDF statements with CSV totals.
"""

import pdfplumber
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def parse_amount(amount_str):
    """Parse amount string to float."""
    if not amount_str:
        return 0.0
    amount_str = str(amount_str).replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
    try:
        return float(amount_str)
    except ValueError:
        return 0.0


def extract_totals_from_pdf(pdf_path):
    """Extract summary totals from PDF statement."""
    totals = {
        'beginning_balance': None,
        'total_credits': None,
        'total_debits': None,
        'ending_balance': None,
        'transaction_count': 0
    }
    
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Look for summary information
                    lines = text.split('\n')
                    
                    for line in lines:
                        line_lower = line.lower()
                        
                        # Beginning balance
                        if 'beginning balance' in line_lower or 'opening balance' in line_lower:
                            amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', line)
                            if amounts:
                                totals['beginning_balance'] = parse_amount(amounts[0])
                        
                        # Total credits
                        if 'total credits' in line_lower or 'total deposits' in line_lower:
                            amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', line)
                            if amounts:
                                totals['total_credits'] = parse_amount(amounts[0])
                        
                        # Total debits
                        if 'total debits' in line_lower or 'total withdrawals' in line_lower or 'total checks' in line_lower:
                            amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', line)
                            if amounts:
                                totals['total_debits'] = parse_amount(amounts[0])
                        
                        # Ending balance
                        if 'ending balance' in line_lower or 'closing balance' in line_lower:
                            amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', line)
                            if amounts:
                                totals['ending_balance'] = parse_amount(amounts[0])
                    
                    # Try to extract table data
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row in table:
                                if row and len(row) >= 3:
                                    # Look for transaction rows (date, description, amount)
                                    try:
                                        # Check if first column looks like a date
                                        if row[0] and re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', str(row[0])):
                                            if len(row) >= 3:
                                                amount_str = str(row[-1] if row[-1] else row[-2])
                                                amount = parse_amount(amount_str)
                                                if amount != 0:
                                                    transactions.append({
                                                        'date': row[0],
                                                        'description': str(row[1] if len(row) > 1 else ''),
                                                        'amount': amount
                                                    })
                                    except:
                                        pass
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
    
    totals['transaction_count'] = len(transactions)
    return totals, transactions


def get_csv_totals(csv_path):
    """Get totals from CSV file."""
    import csv
    totals = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
        # Parse summary rows (first few rows)
        for row in rows[:10]:
            if len(row) >= 3:
                desc = row[0].strip()
                amount_str = row[2].strip().replace('"', '').replace(',', '')
                
                if 'Beginning balance' in desc:
                    totals['beginning_balance'] = parse_amount(amount_str)
                elif 'Total credits' in desc:
                    totals['total_credits'] = parse_amount(amount_str)
                elif 'Total debits' in desc:
                    totals['total_debits'] = parse_amount(amount_str)
                elif 'Ending balance' in desc:
                    totals['ending_balance'] = parse_amount(amount_str)
    
    # Count transactions in CSV
    transaction_count = 0
    in_transactions = False
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3 and 'Date' in row[0] and 'Description' in row[1]:
                in_transactions = True
                continue
            if in_transactions and len(row) >= 3:
                date_str = row[0].strip()
                if date_str and re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                    # Skip summary rows
                    if 'Beginning balance' not in row[1] and 'Total' not in row[1]:
                        transaction_count += 1
    
    totals['transaction_count'] = transaction_count
    return totals


def main():
    """Compare PDF totals with CSV totals."""
    pdf_dir = Path("/Users/fjabbari/@@@PUBLIC/@@@TAX2025/")
    csv_path = "/Users/fjabbari/@@@PUBLIC/@@@TAX2025/stmt.csv"
    
    print("=" * 70)
    print("COMPARING PDF STATEMENTS WITH CSV TOTALS")
    print("=" * 70)
    
    # Get CSV totals
    print("\n1. Reading CSV totals...")
    csv_totals = get_csv_totals(csv_path)
    print(f"   CSV Beginning Balance: ${csv_totals.get('beginning_balance', 0):,.2f}")
    print(f"   CSV Total Credits:     ${csv_totals.get('total_credits', 0):,.2f}")
    print(f"   CSV Total Debits:        ${csv_totals.get('total_debits', 0):,.2f}")
    print(f"   CSV Ending Balance:      ${csv_totals.get('ending_balance', 0):,.2f}")
    print(f"   CSV Transaction Count:   {csv_totals.get('transaction_count', 0)}")
    
    # Get PDF files
    pdf_files = sorted(pdf_dir.glob("eStmt_*.pdf"))
    print(f"\n2. Found {len(pdf_files)} PDF files")
    
    # Parse each PDF
    pdf_totals = {
        'beginning_balance': None,
        'total_credits': 0.0,
        'total_debits': 0.0,
        'ending_balance': None,
        'transaction_count': 0
    }
    
    monthly_totals = {}
    
    print("\n3. Parsing PDF files...")
    for pdf_file in pdf_files:
        month = pdf_file.stem.split('_')[1] if '_' in pdf_file.stem else 'unknown'
        print(f"   Processing {pdf_file.name}...", end=' ')
        
        totals, transactions = extract_totals_from_pdf(pdf_file)
        
        # Track first beginning balance and last ending balance
        if totals.get('beginning_balance') is not None:
            if pdf_totals['beginning_balance'] is None:
                pdf_totals['beginning_balance'] = totals['beginning_balance']
        
        if totals.get('ending_balance') is not None:
            pdf_totals['ending_balance'] = totals['ending_balance']
        
        # Sum credits and debits
        if totals.get('total_credits'):
            pdf_totals['total_credits'] += totals['total_credits']
        if totals.get('total_debits'):
            pdf_totals['total_debits'] += totals['total_debits']
        
        pdf_totals['transaction_count'] += totals['transaction_count']
        
        monthly_totals[month] = {
            'credits': totals.get('total_credits', 0),
            'debits': totals.get('total_debits', 0),
            'transactions': totals['transaction_count']
        }
        
        print(f"✓ ({totals['transaction_count']} transactions)")
    
    # Compare totals
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    print("\nPDF Totals:")
    print(f"   Beginning Balance: ${pdf_totals.get('beginning_balance', 0):,.2f}")
    print(f"   Total Credits:     ${pdf_totals.get('total_credits', 0):,.2f}")
    print(f"   Total Debits:      ${pdf_totals.get('total_debits', 0):,.2f}")
    print(f"   Ending Balance:    ${pdf_totals.get('ending_balance', 0):,.2f}")
    print(f"   Transaction Count: {pdf_totals.get('transaction_count', 0)}")
    
    print("\nDifferences:")
    beg_diff = abs((pdf_totals.get('beginning_balance') or 0) - (csv_totals.get('beginning_balance') or 0))
    cred_diff = abs((pdf_totals.get('total_credits') or 0) - (csv_totals.get('total_credits') or 0))
    deb_diff = abs((pdf_totals.get('total_debits') or 0) - (csv_totals.get('total_debits') or 0))
    end_diff = abs((pdf_totals.get('ending_balance') or 0) - (csv_totals.get('ending_balance') or 0))
    trans_diff = abs(pdf_totals.get('transaction_count', 0) - csv_totals.get('transaction_count', 0))
    
    print(f"   Beginning Balance: ${beg_diff:,.2f}")
    print(f"   Total Credits:     ${cred_diff:,.2f}")
    print(f"   Total Debits:      ${deb_diff:,.2f}")
    print(f"   Ending Balance:    ${end_diff:,.2f}")
    print(f"   Transaction Count: {trans_diff}")
    
    # Judgment
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    tolerance = 0.01  # Allow $0.01 difference for rounding
    
    if (beg_diff <= tolerance and cred_diff <= tolerance and 
        deb_diff <= tolerance and end_diff <= tolerance):
        print("✓ MATCH: PDF totals match CSV totals within tolerance")
        match = True
    else:
        print("⚠ MISMATCH: There are differences between PDF and CSV totals")
        match = False
        
        if beg_diff > tolerance:
            print(f"   - Beginning balance differs by ${beg_diff:,.2f}")
        if cred_diff > tolerance:
            print(f"   - Total credits differ by ${cred_diff:,.2f}")
        if deb_diff > tolerance:
            print(f"   - Total debits differ by ${deb_diff:,.2f}")
        if end_diff > tolerance:
            print(f"   - Ending balance differs by ${end_diff:,.2f}")
    
    # Monthly breakdown
    print("\nMonthly Breakdown:")
    print("-" * 70)
    for month in sorted(monthly_totals.keys()):
        data = monthly_totals[month]
        print(f"  {month}: Credits=${data['credits']:,.2f}, Debits=${data['debits']:,.2f}, Transactions={data['transactions']}")
    
    return match


if __name__ == "__main__":
    main()
