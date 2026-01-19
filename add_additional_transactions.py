#!/usr/bin/env python3
"""
Add additional transactions not in CSV:
- W-2 income from PDF
- Rental income for properties
- Storm expenses
"""

import sqlite3
import pdfplumber
import re
from datetime import datetime


def parse_w2_pdf(pdf_path):
    """Extract W-2 information from PDF."""
    w2_data = {
        'wages': 0.0,
        'fed_tax_withheld': 0.0,
        'state_tax_withheld': 0.0,
        'ssn_tax_withheld': 0.0,
        'medicare_tax_withheld': 0.0,
        'ssn_wages': 0.0
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            # Extract from the formatted text - look for specific patterns
            # Box 1: Wages (207644.09)
            match = re.search(r'1\s+Wages[,\s]+tips[,\s]+othercomp[.\s]+(\d+\s+\d+\s+\d+\.\d+)', text)
            if match:
                w2_data['wages'] = float(match.group(1).replace(' ', ''))
            
            # Box 2: Federal tax (37262.73)
            match = re.search(r'2\s+Federalincometaxwithheld[:\s]+(\d+\s+\d+\s+\d+\.\d+)', text)
            if match:
                w2_data['fed_tax_withheld'] = float(match.group(1).replace(' ', ''))
            
            # Box 3: Social Security wages (176100.00)
            match = re.search(r'3\s+Socialsecuritywages[:\s]+(\d+\s+\d+\s+\d+\.\d+)', text)
            if match:
                w2_data['ssn_wages'] = float(match.group(1).replace(' ', ''))
            
            # Box 4: Social Security tax (10918.20)
            match = re.search(r'4\s+Socialsecuritytaxwithheld[:\s]+(\d+\s+\d+\.\d+)', text)
            if match:
                w2_data['ssn_tax_withheld'] = float(match.group(1).replace(' ', ''))
            
            # Box 5: Medicare wages (238147.59)
            match = re.search(r'5\s+Medicarewagesandtips[:\s]+(\d+\s+\d+\s+\d+\.\d+)', text)
            if match:
                # Use Box 5 for wages if Box 1 not found
                if w2_data['wages'] == 0:
                    w2_data['wages'] = float(match.group(1).replace(' ', ''))
            
            # Box 6: Medicare tax (3796.47)
            match = re.search(r'6\s+Medicaretaxwithheld[:\s]+(\d+\s+\d+\.\d+)', text)
            if match:
                w2_data['medicare_tax_withheld'] = float(match.group(1).replace(' ', ''))
            
            # Box 17: State tax (8644.00)
            match = re.search(r'17Stateincometax[:\s]+(\d+\s+\d+\.\d+)', text)
            if match:
                w2_data['state_tax_withheld'] = float(match.group(1).replace(' ', ''))
            
            # Fallback: try simpler patterns
            
            # Look for W-2 box numbers - try multiple patterns
            # Box 1: Wages, tips, other compensation
            patterns = [
                r'Box\s*1[:\s]+([\d,]+\.?\d*)',
                r'1\s+Wages[,\s]+tips[,\s]+other[,\s]+comp[.\s]+([\d,]+\.?\d*)',
                r'Wages[,\s]+tips[,\s]+othercomp[.\s]+([\d,]+\.?\d*)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    w2_data['wages'] = float(match.group(1).replace(',', '').replace(' ', ''))
                    break
            
            # Box 2: Federal income tax withheld
            patterns = [
                r'Box\s*2[:\s]+([\d,]+\.?\d*)',
                r'2\s+Federal[,\s]+income[,\s]+tax[,\s]+withheld[:\s]+([\d,]+\.?\d*)',
                r'Federalincometaxwithheld[:\s]+([\d,]+\.?\d*)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    w2_data['fed_tax_withheld'] = float(match.group(1).replace(',', '').replace(' ', ''))
                    break
            
            # Box 4: Social Security tax withheld
            patterns = [
                r'Box\s*4[:\s]+([\d,]+\.?\d*)',
                r'4\s+Social[,\s]+security[,\s]+tax[,\s]+withheld[:\s]+([\d,]+\.?\d*)',
                r'Socialsecuritytaxwithheld[:\s]+([\d,]+\.?\d*)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    w2_data['ssn_tax_withheld'] = float(match.group(1).replace(',', '').replace(' ', ''))
                    break
            
            # Box 6: Medicare tax withheld
            patterns = [
                r'Box\s*6[:\s]+([\d,]+\.?\d*)',
                r'6\s+Medicare[,\s]+tax[,\s]+withheld[:\s]+([\d,]+\.?\d*)',
                r'Medicaretaxwithheld[:\s]+([\d,]+\.?\d*)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    w2_data['medicare_tax_withheld'] = float(match.group(1).replace(',', '').replace(' ', ''))
                    break
            
            # Box 3: Social Security wages
            patterns = [
                r'Box\s*3[:\s]+([\d,]+\.?\d*)',
                r'3\s+Social[,\s]+security[,\s]+wages[:\s]+([\d,]+\.?\d*)',
                r'Socialsecuritywages[:\s]+([\d,]+\.?\d*)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    w2_data['ssn_wages'] = float(match.group(1).replace(',', '').replace(' ', ''))
                    break
            
            # Box 17: State income tax
            patterns = [
                r'Box\s*17[:\s]+([\d,]+\.?\d*)',
                r'17Stateincometax[:\s]+([\d,]+\.?\d*)',
                r'Stateincometax[:\s]+([\d,]+\.?\d*)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    w2_data['state_tax_withheld'] = float(match.group(1).replace(',', '').replace(' ', ''))
                    break
            
            # If still missing, try to extract from the formatted text
            # Look for patterns like "207644.09" near "Wages" or "37262.73" near "Federal"
            if w2_data['wages'] == 0:
                # Try to find "Reported W-2 Wages" line
                match = re.search(r'Reported\s+W-2\s+Wages[:\s]+([\d,]+\.?\d*)', text, re.IGNORECASE)
                if match:
                    w2_data['wages'] = float(match.group(1).replace(',', '').replace(' ', ''))
    
    except Exception as e:
        print(f"Error parsing W-2 PDF: {e}")
        import traceback
        traceback.print_exc()
    
    return w2_data


def add_additional_transactions():
    """Add W-2 income, rental income, and storm expenses to database."""
    
    db_path = "tax_data_2025.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tax_year = 2025
    
    print("=" * 70)
    print("ADDING ADDITIONAL TRANSACTIONS")
    print("=" * 70)
    
    # 1. Parse W-2 PDF
    print("\n1. Parsing W-2 PDF...")
    w2_path = "/Users/fjabbari/@@@PUBLIC/@@@TAX2025/W2.pdf"
    w2_data = parse_w2_pdf(w2_path)
    
    # Manual override with correct values from PDF (Box 1: 207644.09, Box 2: 37262.73, etc.)
    # If parsing failed, use manual values
    if w2_data['wages'] < 100000:  # If parsing didn't work correctly
        w2_data['wages'] = 207644.09  # Box 1
        w2_data['fed_tax_withheld'] = 37262.73  # Box 2
        w2_data['ssn_wages'] = 176100.00  # Box 3
        w2_data['ssn_tax_withheld'] = 10918.20  # Box 4
        w2_data['medicare_tax_withheld'] = 3796.47  # Box 6
        w2_data['state_tax_withheld'] = 8644.00  # Box 17
        print("   Using manual W-2 values from PDF")
    
    print(f"   W-2 Wages (Box 1): ${w2_data['wages']:,.2f}")
    print(f"   Federal Tax Withheld (Box 2): ${w2_data['fed_tax_withheld']:,.2f}")
    print(f"   State Tax Withheld (Box 17): ${w2_data['state_tax_withheld']:,.2f}")
    print(f"   SSN Tax Withheld (Box 4): ${w2_data['ssn_tax_withheld']:,.2f}")
    print(f"   Medicare Tax Withheld (Box 6): ${w2_data['medicare_tax_withheld']:,.2f}")
    
    # Add W-2 income transaction
    if w2_data['wages'] > 0:
        w2_date = datetime(2025, 12, 31).date()  # Use year-end date
        w2_description = f"W-2 Wages - Box 1"
        w2_entity = "W-2 INCOME"
        
        # Add to EntityDetail
        cursor.execute("""
            INSERT INTO EntityDetail
            (tax_year, entity_name, transaction_date, description, amount, running_balance, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tax_year, w2_entity, w2_date, w2_description, w2_data['wages'], None, 'W-2 Income'))
        
        # Add to TaxYearDetail
        cursor.execute("""
            INSERT INTO TaxYearDetail
            (tax_year, transaction_date, description, amount, running_balance, entity_name, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tax_year, w2_date, w2_description, w2_data['wages'], None, w2_entity, 'W-2 Income'))
        
        # Update or create EntitySummary
        cursor.execute("""
            INSERT OR REPLACE INTO EntitySummary
            (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tax_year, w2_entity, w2_data['wages'], 1, w2_date, w2_date, 'W-2 Income'))
        
        print(f"   ✓ Added W-2 income transaction")
    
    # 2. Add rental income
    print("\n2. Adding rental income...")
    rental_income = {
        '1029': 9130,
        '1035': 8350,
        '1108': 9360,
        '5015': 9580,
        '5952': 10210,
        '5956': 11390
    }
    
    for property_num, amount in rental_income.items():
        rent_date = datetime(2025, 12, 31).date()  # Use year-end date
        rent_description = f"Rental Income - Property {property_num}"
        rent_entity = f"RENTAL-{property_num}"
        
        # Add to EntityDetail
        cursor.execute("""
            INSERT INTO EntityDetail
            (tax_year, entity_name, transaction_date, description, amount, running_balance, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tax_year, rent_entity, rent_date, rent_description, amount, None, 'Rental Income'))
        
        # Add to TaxYearDetail
        cursor.execute("""
            INSERT INTO TaxYearDetail
            (tax_year, transaction_date, description, amount, running_balance, entity_name, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tax_year, rent_date, rent_description, amount, None, rent_entity, 'Rental Income'))
        
        # Update or create EntitySummary
        cursor.execute("""
            INSERT OR REPLACE INTO EntitySummary
            (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tax_year, rent_entity, amount, 1, rent_date, rent_date, 'Rental Income'))
        
        print(f"   ✓ Property {property_num}: ${amount:,.2f}")
    
    total_rental = sum(rental_income.values())
    print(f"   Total Rental Income: ${total_rental:,.2f}")
    
    # 3. Add storm expenses
    print("\n3. Adding storm expenses...")
    storm_amount = 8496.36
    storm_date = datetime(2025, 12, 31).date()
    storm_description = "Storm Expenses"
    storm_entity = "STORM-EXPENSES"
    
    # Add to EntityDetail (negative amount for expense)
    cursor.execute("""
        INSERT INTO EntityDetail
        (tax_year, entity_name, transaction_date, description, amount, running_balance, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tax_year, storm_entity, storm_date, storm_description, -storm_amount, None, 'Storm Expenses'))
    
    # Add to TaxYearDetail
    cursor.execute("""
        INSERT INTO TaxYearDetail
        (tax_year, transaction_date, description, amount, running_balance, entity_name, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tax_year, storm_date, storm_description, -storm_amount, None, storm_entity, 'Storm Expenses'))
    
    # Update or create EntitySummary
    cursor.execute("""
        INSERT OR REPLACE INTO EntitySummary
        (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tax_year, storm_entity, -storm_amount, 1, storm_date, storm_date, 'Storm Expenses'))
    
    print(f"   ✓ Storm Expenses: ${storm_amount:,.2f}")
    
    # Update TaxYearSummary
    print("\n4. Updating TaxYearSummary...")
    cursor.execute("""
        SELECT beginning_balance, total_credits, total_debits, ending_balance, transaction_count
        FROM TaxYearSummary
        WHERE tax_year = ?
    """, (tax_year,))
    
    result = cursor.fetchone()
    if result:
        beg_bal, total_credits, total_debits, end_bal, trans_count = result
        
        # Add new credits (W-2 income + rental income)
        new_credits = w2_data['wages'] + total_rental
        updated_credits = (total_credits or 0) + new_credits
        
        # Add new debits (storm expenses)
        updated_debits = (total_debits or 0) - storm_amount
        
        # Update transaction count
        updated_count = trans_count + 1 + len(rental_income) + 1  # W-2 + rentals + storm
        
        cursor.execute("""
            UPDATE TaxYearSummary
            SET total_credits = ?,
                total_debits = ?,
                transaction_count = ?
            WHERE tax_year = ?
        """, (updated_credits, updated_debits, updated_count, tax_year))
        
        print(f"   Updated total credits: ${updated_credits:,.2f}")
        print(f"   Updated total debits: ${updated_debits:,.2f}")
        print(f"   Updated transaction count: {updated_count}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("ADDITIONAL TRANSACTIONS ADDED!")
    print("=" * 70)
    
    # Show summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nNew entities added:")
    cursor.execute("""
        SELECT entity_name, total_amount, transaction_count
        FROM EntitySummary
        WHERE entity_name IN ('W-2 INCOME', 'STORM-EXPENSES') 
           OR entity_name LIKE 'RENTAL-%'
        ORDER BY entity_name
    """)
    
    for entity, total, count in cursor.fetchall():
        print(f"  {entity:30s} | ${total:12,.2f} | {count:4d} transactions")
    
    conn.close()


if __name__ == "__main__":
    add_additional_transactions()
