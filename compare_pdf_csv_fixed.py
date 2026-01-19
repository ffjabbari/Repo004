#!/usr/bin/env python3
"""
Compare PDF statements with CSV totals - Fixed version.
"""

import pdfplumber
import re
import csv
from pathlib import Path
from datetime import datetime


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
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Focus on first page which has summary
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            if text:
                lines = text.split('\n')
                
                # Look for account summary section
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    
                    # Beginning balance
                    if 'Beginning balance' in line_stripped and 'on' in line_stripped:
                        amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', line_stripped)
                        if amounts:
                            totals['beginning_balance'] = parse_amount(amounts[0])
                    
                    # Deposits and other additions (credits)
                    if 'Deposits and other additions' in line_stripped:
                        amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', line_stripped)
                        if amounts:
                            totals['total_credits'] = parse_amount(amounts[0])
                        # Also check next line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', next_line)
                            if amounts and not totals['total_credits']:
                                totals['total_credits'] = parse_amount(amounts[0])
                    
                    # Ending balance
                    if 'Ending balance' in line_stripped and 'on' in line_stripped:
                        amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', line_stripped)
                        if amounts:
                            totals['ending_balance'] = parse_amount(amounts[0])
                
                # Calculate total debits from components
                # Look for: "ATM and debit card subtractions", "Other subtractions", "Checks"
                atm_debits = 0.0
                other_debits = 0.0
                checks = 0.0
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    
                    # ATM and debit card subtractions
                    if 'ATM and debit card subtractions' in line_stripped:
                        # Amount is usually on same line or next
                        amounts = re.findall(r'-?([\d,]+\.\d{2})', line_stripped)
                        if amounts:
                            atm_debits = abs(parse_amount(amounts[0]))
                        elif i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            amounts = re.findall(r'-?([\d,]+\.\d{2})', next_line)
                            if amounts:
                                atm_debits = abs(parse_amount(amounts[0]))
                    
                    # Other subtractions
                    if 'Other subtractions' in line_stripped and 'ATM' not in line_stripped:
                        amounts = re.findall(r'-?([\d,]+\.\d{2})', line_stripped)
                        if amounts:
                            other_debits = abs(parse_amount(amounts[0]))
                        elif i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            amounts = re.findall(r'-?([\d,]+\.\d{2})', next_line)
                            if amounts:
                                other_debits = abs(parse_amount(amounts[0]))
                    
                    # Checks (standalone line)
                    if line_stripped == 'Checks' or (line_stripped.startswith('Checks') and len(line_stripped) < 20):
                        amounts = re.findall(r'-?([\d,]+\.\d{2})', line_stripped)
                        if amounts:
                            checks = abs(parse_amount(amounts[0]))
                        elif i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            amounts = re.findall(r'-?([\d,]+\.\d{2})', next_line)
                            if amounts:
                                checks = abs(parse_amount(amounts[0]))
                
                # Total debits = sum of all components (as negative)
                total_debits = -(atm_debits + other_debits + checks)
                if total_debits != 0:
                    totals['total_debits'] = total_debits
                
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return totals


def get_csv_totals(csv_path):
    """Get totals from CSV file."""
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
        
        totals = extract_totals_from_pdf(pdf_file)
        
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
        
        monthly_totals[month] = {
            'beginning': totals.get('beginning_balance'),
            'credits': totals.get('total_credits', 0),
            'debits': totals.get('total_debits', 0),
            'ending': totals.get('ending_balance')
        }
        
        print(f"✓ Credits=${totals.get('total_credits', 0):,.2f}, Debits=${totals.get('total_debits', 0):,.2f}")
    
    # Compare totals
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    print("\nPDF Totals (sum of all monthly statements):")
    print(f"   Beginning Balance (first PDF): ${pdf_totals.get('beginning_balance', 0):,.2f}")
    print(f"   Total Credits (sum):           ${pdf_totals.get('total_credits', 0):,.2f}")
    print(f"   Total Debits (sum):            ${pdf_totals.get('total_debits', 0):,.2f}")
    print(f"   Ending Balance (last PDF):     ${pdf_totals.get('ending_balance', 0):,.2f}")
    
    print("\nDifferences:")
    beg_diff = abs((pdf_totals.get('beginning_balance') or 0) - (csv_totals.get('beginning_balance') or 0))
    cred_diff = abs((pdf_totals.get('total_credits') or 0) - (csv_totals.get('total_credits') or 0))
    deb_diff = abs((pdf_totals.get('total_debits') or 0) - (csv_totals.get('total_debits') or 0))
    end_diff = abs((pdf_totals.get('ending_balance') or 0) - (csv_totals.get('ending_balance') or 0))
    
    print(f"   Beginning Balance: ${beg_diff:,.2f}")
    print(f"   Total Credits:     ${cred_diff:,.2f}")
    print(f"   Total Debits:       ${deb_diff:,.2f}")
    print(f"   Ending Balance:    ${end_diff:,.2f}")
    
    # Judgment
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    tolerance = 1.00  # Allow $1 difference for rounding
    
    # Note: Beginning balance difference is expected - PDFs start Dec 24, CSV starts Jan 1
    # So we focus on credits, debits, and ending balance
    
    credits_match = cred_diff <= tolerance
    debits_match = deb_diff <= tolerance
    ending_match = end_diff <= tolerance
    
    if credits_match and debits_match and ending_match:
        print("✓ MATCH: PDF totals match CSV totals (within tolerance)")
        print("\nNote: Beginning balance difference is expected:")
        print("  - PDFs start from Dec 24, 2024")
        print("  - CSV starts from Jan 1, 2025")
        match = True
    else:
        print("⚠ MISMATCH: There are differences between PDF and CSV totals")
        match = False
        
        if not credits_match:
            print(f"   - Total credits differ by ${cred_diff:,.2f}")
        if not debits_match:
            print(f"   - Total debits differ by ${deb_diff:,.2f}")
        if not ending_match:
            print(f"   - Ending balance differs by ${end_diff:,.2f}")
    
    # Monthly breakdown
    print("\nMonthly Breakdown:")
    print("-" * 70)
    for month in sorted(monthly_totals.keys()):
        data = monthly_totals[month]
        print(f"  {month}: Beg=${data.get('beginning', 0):,.2f}, "
              f"Credits=${data.get('credits', 0):,.2f}, "
              f"Debits=${data.get('debits', 0):,.2f}, "
              f"End=${data.get('ending', 0):,.2f}")
    
    return match


if __name__ == "__main__":
    main()
