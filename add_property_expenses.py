#!/usr/bin/env python3
"""
Add property expenses: Real Estate Taxes and Home Insurance for each property.
Also verify/update rental income.
"""

import sqlite3
from datetime import datetime


def add_property_expenses():
    """Add real estate taxes and home insurance to database."""
    
    db_path = "tax_data_2025.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tax_year = 2025
    expense_date = datetime(2025, 12, 31).date()  # Use year-end date
    
    print("=" * 70)
    print("ADDING PROPERTY EXPENSES")
    print("=" * 70)
    
    # Property data: (property_num, rent_income, real_estate_tax, home_insurance, is_rental)
    properties = [
        ('1029', 9130.00, 3089.46, 0.00, True),
        ('1035', 8350.00, 3169.86, 975.15, True),
        ('1108', 9360.00, 3505.53, 975.15, True),
        ('5015', 9580.00, 2938.37, 975.15, True),
        ('5952', 10210.00, 2827.86, 975.15, True),
        ('5956', 11390.00, 2802.48, 975.15, True),
        ('1039', 0.00, 5244.47, 975.15, False),  # Not rental - owner occupied
    ]
    
    total_real_estate_tax = 0.0
    total_home_insurance = 0.0
    
    print("\nProcessing properties...")
    for prop_num, rent, real_estate_tax, home_insurance, is_rental in properties:
        print(f"\nProperty {prop_num} ({'Rental' if is_rental else 'Owner Occupied'}):")
        
        # 1. Update/Add rental income (if rental and rent > 0)
        if is_rental and rent > 0:
            rent_entity = f"RENTAL-{prop_num}"
            rent_description = f"Rental Income - Property {prop_num}"
            
            # Check if already exists
            cursor.execute("""
                SELECT total_amount FROM EntitySummary
                WHERE entity_name = ? AND tax_year = ?
            """, (rent_entity, tax_year))
            
            existing = cursor.fetchone()
            if existing:
                # Update if different
                if abs(existing[0] - rent) > 0.01:
                    cursor.execute("""
                        UPDATE EntitySummary
                        SET total_amount = ?
                        WHERE entity_name = ? AND tax_year = ?
                    """, (rent, rent_entity, tax_year))
                    
                    cursor.execute("""
                        UPDATE EntityDetail
                        SET amount = ?
                        WHERE entity_name = ? AND tax_year = ?
                    """, (rent, rent_entity, tax_year))
                    
                    cursor.execute("""
                        UPDATE TaxYearDetail
                        SET amount = ?
                        WHERE entity_name = ? AND tax_year = ?
                    """, (rent, rent_entity, tax_year))
                    
                    print(f"  ✓ Updated rental income: ${rent:,.2f}")
                else:
                    print(f"  ✓ Rental income already correct: ${rent:,.2f}")
            else:
                # Add new rental income
                cursor.execute("""
                    INSERT INTO EntityDetail
                    (tax_year, entity_name, transaction_date, description, amount, running_balance, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tax_year, rent_entity, expense_date, rent_description, rent, None, 'Rental Income'))
                
                cursor.execute("""
                    INSERT INTO TaxYearDetail
                    (tax_year, transaction_date, description, amount, running_balance, entity_name, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tax_year, expense_date, rent_description, rent, None, rent_entity, 'Rental Income'))
                
                cursor.execute("""
                    INSERT INTO EntitySummary
                    (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tax_year, rent_entity, rent, 1, expense_date, expense_date, 'Rental Income'))
                
                print(f"  ✓ Added rental income: ${rent:,.2f}")
        
        # 2. Add Real Estate Tax
        if real_estate_tax > 0:
            tax_entity = f"PROPERTY-{prop_num}-TAX"
            tax_description = f"Real Estate Tax - Property {prop_num}"
            
            # Check if already exists
            cursor.execute("""
                SELECT id FROM EntityDetail
                WHERE entity_name = ? AND tax_year = ? AND description LIKE '%Real Estate Tax%'
            """, (tax_entity, tax_year))
            
            if cursor.fetchone():
                print(f"  ✓ Real Estate Tax already exists: ${real_estate_tax:,.2f}")
            else:
                # Add to EntityDetail
                cursor.execute("""
                    INSERT INTO EntityDetail
                    (tax_year, entity_name, transaction_date, description, amount, running_balance, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tax_year, tax_entity, expense_date, tax_description, -real_estate_tax, None, 'Real Estate Tax'))
                
                # Add to TaxYearDetail
                cursor.execute("""
                    INSERT INTO TaxYearDetail
                    (tax_year, transaction_date, description, amount, running_balance, entity_name, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tax_year, expense_date, tax_description, -real_estate_tax, None, tax_entity, 'Real Estate Tax'))
                
                # Update or create EntitySummary
                cursor.execute("""
                    SELECT total_amount, transaction_count FROM EntitySummary
                    WHERE entity_name = ? AND tax_year = ?
                """, (tax_entity, tax_year))
                
                existing = cursor.fetchone()
                if existing:
                    new_total = existing[0] - real_estate_tax
                    new_count = existing[1] + 1
                    cursor.execute("""
                        UPDATE EntitySummary
                        SET total_amount = ?, transaction_count = ?
                        WHERE entity_name = ? AND tax_year = ?
                    """, (new_total, new_count, tax_entity, tax_year))
                else:
                    cursor.execute("""
                        INSERT INTO EntitySummary
                        (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (tax_year, tax_entity, -real_estate_tax, 1, expense_date, expense_date, 'Real Estate Tax'))
                
                print(f"  ✓ Added Real Estate Tax: ${real_estate_tax:,.2f}")
                total_real_estate_tax += real_estate_tax
        
        # 3. Add Home Insurance
        if home_insurance > 0:
            ins_entity = f"PROPERTY-{prop_num}-INSURANCE"
            ins_description = f"Home Insurance - Property {prop_num}"
            
            # Check if already exists
            cursor.execute("""
                SELECT id FROM EntityDetail
                WHERE entity_name = ? AND tax_year = ? AND description LIKE '%Home Insurance%'
            """, (ins_entity, tax_year))
            
            if cursor.fetchone():
                print(f"  ✓ Home Insurance already exists: ${home_insurance:,.2f}")
            else:
                # Add to EntityDetail
                cursor.execute("""
                    INSERT INTO EntityDetail
                    (tax_year, entity_name, transaction_date, description, amount, running_balance, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tax_year, ins_entity, expense_date, ins_description, -home_insurance, None, 'Home Insurance'))
                
                # Add to TaxYearDetail
                cursor.execute("""
                    INSERT INTO TaxYearDetail
                    (tax_year, transaction_date, description, amount, running_balance, entity_name, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tax_year, expense_date, ins_description, -home_insurance, None, ins_entity, 'Home Insurance'))
                
                # Update or create EntitySummary
                cursor.execute("""
                    SELECT total_amount, transaction_count FROM EntitySummary
                    WHERE entity_name = ? AND tax_year = ?
                """, (ins_entity, tax_year))
                
                existing = cursor.fetchone()
                if existing:
                    new_total = existing[0] - home_insurance
                    new_count = existing[1] + 1
                    cursor.execute("""
                        UPDATE EntitySummary
                        SET total_amount = ?, transaction_count = ?
                        WHERE entity_name = ? AND tax_year = ?
                    """, (new_total, new_count, ins_entity, tax_year))
                else:
                    cursor.execute("""
                        INSERT INTO EntitySummary
                        (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (tax_year, ins_entity, -home_insurance, 1, expense_date, expense_date, 'Home Insurance'))
                
                print(f"  ✓ Added Home Insurance: ${home_insurance:,.2f}")
                total_home_insurance += home_insurance
    
    # Update TaxYearSummary
    print("\n4. Updating TaxYearSummary...")
    cursor.execute("""
        SELECT total_debits FROM TaxYearSummary WHERE tax_year = ?
    """, (tax_year,))
    
    result = cursor.fetchone()
    if result:
        current_debits = result[0] or 0
        new_debits = current_debits - total_real_estate_tax - total_home_insurance
        
        cursor.execute("""
            UPDATE TaxYearSummary
            SET total_debits = ?
            WHERE tax_year = ?
        """, (new_debits, tax_year))
        
        print(f"   Updated total debits by: ${total_real_estate_tax + total_home_insurance:,.2f}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("PROPERTY EXPENSES ADDED!")
    print("=" * 70)
    print(f"\nTotal Real Estate Taxes: ${total_real_estate_tax:,.2f}")
    print(f"Total Home Insurance: ${total_home_insurance:,.2f}")
    print(f"Total Property Expenses: ${total_real_estate_tax + total_home_insurance:,.2f}")
    
    # Show summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nProperty expenses by property:")
    cursor.execute("""
        SELECT entity_name, total_amount, transaction_count
        FROM EntitySummary
        WHERE entity_name LIKE 'PROPERTY-%'
        ORDER BY entity_name
    """)
    
    for entity, total, count in cursor.fetchall():
        print(f"  {entity:40s} | ${total:12,.2f} | {count:4d} transactions")
    
    conn.close()


if __name__ == "__main__":
    add_property_expenses()
