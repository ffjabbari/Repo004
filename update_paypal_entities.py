#!/usr/bin/env python3
"""
Update PayPal transactions to have separate entities like PAYPAL-OVIEDO.
"""

import sqlite3
import re
from pathlib import Path


def extract_paypal_id(description):
    """Extract unique ID from PayPal transaction description."""
    # Pattern: PAYPAL DES:... ID:XXXXX INDN:...
    # Look for ID: followed by alphanumeric characters
    match = re.search(r'ID:([A-Z0-9]+)', description)
    if match:
        paypal_id = match.group(1)
        # Clean up common patterns
        if paypal_id.startswith('OVIEDO'):
            return 'OVIEDO'
        # You can add more specific mappings here
        return paypal_id
    return None


def update_paypal_entities():
    """Update database to split PayPal transactions by unique IDs."""
    
    db_path = "tax_data_2025.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("UPDATING PAYPAL ENTITIES")
    print("=" * 70)
    
    # Find all PayPal transactions
    cursor.execute("""
        SELECT id, description, entity_name
        FROM EntityDetail
        WHERE entity_name = 'PAYPAL'
    """)
    
    paypal_transactions = cursor.fetchall()
    print(f"\nFound {len(paypal_transactions)} PayPal transactions")
    
    # Group by PayPal ID
    paypal_groups = {}
    no_id_count = 0
    
    for trans_id, description, entity_name in paypal_transactions:
        paypal_id = extract_paypal_id(description)
        
        if paypal_id:
            new_entity = f"PAYPAL-{paypal_id}"
            if new_entity not in paypal_groups:
                paypal_groups[new_entity] = []
            paypal_groups[new_entity].append(trans_id)
        else:
            # Keep as PAYPAL if no ID found
            if 'PAYPAL' not in paypal_groups:
                paypal_groups['PAYPAL'] = []
            paypal_groups['PAYPAL'].append(trans_id)
            no_id_count += 1
    
    print(f"\nFound {len(paypal_groups)} unique PayPal entities:")
    for entity, trans_list in sorted(paypal_groups.items()):
        print(f"  {entity}: {len(trans_list)} transactions")
    if no_id_count > 0:
        print(f"  (PAYPAL: {no_id_count} transactions without ID)")
    
    # Update EntityDetail table
    print("\nUpdating EntityDetail table...")
    for new_entity, trans_ids in paypal_groups.items():
        placeholders = ','.join(['?'] * len(trans_ids))
        cursor.execute(f"""
            UPDATE EntityDetail
            SET entity_name = ?
            WHERE id IN ({placeholders})
        """, [new_entity] + trans_ids)
    
    # Delete old PAYPAL entries from EntitySummary
    print("Updating EntitySummary table...")
    cursor.execute("DELETE FROM EntitySummary WHERE entity_name = 'PAYPAL'")
    
    # Recreate EntitySummary entries for each PayPal entity
    for new_entity in paypal_groups.keys():
        cursor.execute("""
            SELECT 
                tax_year,
                SUM(amount) as total_amount,
                COUNT(*) as transaction_count,
                MIN(transaction_date) as first_date,
                MAX(transaction_date) as last_date
            FROM EntityDetail
            WHERE entity_name = ?
            GROUP BY tax_year
        """, (new_entity,))
        
        result = cursor.fetchone()
        if result:
            tax_year, total_amount, transaction_count, first_date, last_date = result
            cursor.execute("""
                INSERT INTO EntitySummary
                (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tax_year, new_entity, total_amount, transaction_count, first_date, last_date))
    
    # Also update TaxYearDetail
    print("Updating TaxYearDetail table...")
    for new_entity, trans_ids in paypal_groups.items():
        placeholders = ','.join(['?'] * len(trans_ids))
        # Get the EntityDetail IDs to match with TaxYearDetail
        cursor.execute(f"""
            SELECT transaction_date, description
            FROM EntityDetail
            WHERE id IN ({placeholders})
        """, trans_ids)
        
        matching_trans = cursor.fetchall()
        for trans_date, description in matching_trans:
            cursor.execute("""
                UPDATE TaxYearDetail
                SET entity_name = ?
                WHERE transaction_date = ? AND description = ?
            """, (new_entity, trans_date, description))
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("UPDATE COMPLETE!")
    print("=" * 70)
    
    # Show summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT entity_name, total_amount, transaction_count
        FROM EntitySummary
        WHERE entity_name LIKE 'PAYPAL-%'
        ORDER BY ABS(total_amount) DESC
    """)
    
    print("\nPayPal entities summary:")
    print("-" * 70)
    for entity, total, count in cursor.fetchall():
        print(f"  {entity:30s} | ${total:12,.2f} | {count:4d} transactions")
    
    conn.close()


if __name__ == "__main__":
    update_paypal_entities()
