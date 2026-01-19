#!/usr/bin/env python3
"""
Update utility transactions to have consolidated entities like UTIL-AMEREN, UTIL-SPIRE, etc.
"""

import sqlite3
import re


def normalize_utility_name(entity_name):
    """Normalize utility entity name to standard form."""
    entity_upper = entity_name.upper()
    
    # Electric - Ameren
    if 'AMEREN' in entity_upper:
        return 'UTIL-AMEREN'
    
    # Gas - Spire
    if 'SPIRE' in entity_upper or 'LACLEDE' in entity_upper or 'MGE' in entity_upper:
        return 'UTIL-SPIRE'
    
    # Water
    if 'WATER' in entity_upper and 'AMERICAN' in entity_upper:
        return 'UTIL-WATER'
    
    # Sewer
    if 'SEWER' in entity_upper or 'METROPOLITAN' in entity_upper:
        return 'UTIL-SEWER'
    
    # Trash/Waste
    if 'WASTE' in entity_upper or 'TRASH' in entity_upper:
        return 'UTIL-WASTE'
    
    # Internet/Phone - Spectrum
    if 'SPECTRUM' in entity_upper:
        return 'UTIL-SPECTRUM'
    
    # Other utilities
    if 'UTILITY' in entity_upper or 'UTIL' in entity_upper:
        return 'UTIL-OTHER'
    
    return None


def update_utility_entities():
    """Update database to consolidate utility transactions."""
    
    db_path = "tax_data_2025.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("UPDATING UTILITY ENTITIES")
    print("=" * 70)
    
    # Find all utility-related entities
    cursor.execute("""
        SELECT DISTINCT entity_name
        FROM EntitySummary
        WHERE 
            entity_name LIKE '%AMEREN%' OR
            entity_name LIKE '%SPIRE%' OR
            entity_name LIKE '%WATER%' OR
            entity_name LIKE '%SEWER%' OR
            entity_name LIKE '%WASTE%' OR
            entity_name LIKE '%SPECTRUM%' OR
            entity_name LIKE '%UTIL%' OR
            entity_name LIKE '%ELECTRIC%' OR
            entity_name LIKE '%GAS%' OR
            entity_name LIKE '%TRASH%' OR
            entity_name LIKE '%METROPOLITAN%' OR
            entity_name LIKE '%LACLEDE%' OR
            entity_name LIKE '%MGE%'
    """)
    
    utility_entities = [row[0] for row in cursor.fetchall()]
    print(f"\nFound {len(utility_entities)} utility-related entities")
    
    # Group by normalized utility name
    utility_groups = {}
    unmapped = []
    
    for entity_name in utility_entities:
        normalized = normalize_utility_name(entity_name)
        if normalized:
            if normalized not in utility_groups:
                utility_groups[normalized] = []
            utility_groups[normalized].append(entity_name)
        else:
            unmapped.append(entity_name)
    
    print(f"\nGrouped into {len(utility_groups)} utility categories:")
    for util_name, original_names in sorted(utility_groups.items()):
        print(f"  {util_name}: {len(original_names)} variations")
        for orig in original_names:
            print(f"    - {orig}")
    
    if unmapped:
        print(f"\nUnmapped entities: {unmapped}")
    
    # Update EntityDetail table
    print("\nUpdating EntityDetail table...")
    for util_name, original_names in utility_groups.items():
        for orig_name in original_names:
            cursor.execute("""
                UPDATE EntityDetail
                SET entity_name = ?
                WHERE entity_name = ?
            """, (util_name, orig_name))
    
    # Delete old utility entries from EntitySummary
    print("Updating EntitySummary table...")
    for orig_name in utility_entities:
        cursor.execute("DELETE FROM EntitySummary WHERE entity_name = ?", (orig_name,))
    
    # Recreate EntitySummary entries for each utility
    for util_name in utility_groups.keys():
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
        """, (util_name,))
        
        result = cursor.fetchone()
        if result:
            tax_year, total_amount, transaction_count, first_date, last_date = result
            cursor.execute("""
                INSERT INTO EntitySummary
                (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tax_year, util_name, total_amount, transaction_count, first_date, last_date))
    
    # Update TaxYearDetail
    print("Updating TaxYearDetail table...")
    for util_name, original_names in utility_groups.items():
        for orig_name in original_names:
            cursor.execute("""
                UPDATE TaxYearDetail
                SET entity_name = ?
                WHERE entity_name = ?
            """, (util_name, orig_name))
    
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
        WHERE entity_name LIKE 'UTIL-%'
        ORDER BY ABS(total_amount) DESC
    """)
    
    print("\nUtility entities summary:")
    print("-" * 70)
    total_amount = 0
    total_count = 0
    for entity, total, count in cursor.fetchall():
        total_amount += total
        total_count += count
        print(f"  {entity:30s} | ${total:12,.2f} | {count:4d} transactions")
    print("-" * 70)
    print(f"  {'TOTAL':30s} | ${total_amount:12,.2f} | {total_count:4d} transactions")
    
    conn.close()


if __name__ == "__main__":
    update_utility_entities()
