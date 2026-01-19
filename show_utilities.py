#!/usr/bin/env python3
"""
Show utility bills summary.
"""

import sqlite3
import re

db_path = "tax_data_2025.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("UTILITY BILLS SUMMARY")
print("=" * 80)

# Common utility keywords
utility_keywords = [
    'AMEREN', 'SPIRE', 'WATER', 'SEWER', 'WASTE', 'SPECTRUM', 
    'UTILITY', 'ELECTRIC', 'GAS', 'TRASH', 'INTERNET', 'PHONE'
]

# Find all entities that might be utilities
cursor.execute("""
    SELECT entity_name, total_amount, transaction_count
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
        entity_name LIKE '%TRASH%'
    ORDER BY ABS(total_amount) DESC
""")

results = cursor.fetchall()

print(f"\n{'Utility Company':<40} {'Total Amount':>15} {'Transactions':>12}")
print("-" * 80)

total_amount = 0
total_count = 0

# Group by utility type
utilities_by_type = {
    'Electric': [],
    'Gas': [],
    'Water': [],
    'Sewer': [],
    'Trash/Waste': [],
    'Internet/Phone': [],
    'Other': []
}

for entity_name, total_amount_val, count in results:
    total_amount += total_amount_val
    total_count += count
    
    # Categorize
    entity_upper = entity_name.upper()
    if 'AMEREN' in entity_upper or 'ELECTRIC' in entity_upper:
        utilities_by_type['Electric'].append((entity_name, total_amount_val, count))
    elif 'SPIRE' in entity_upper or 'GAS' in entity_upper:
        utilities_by_type['Gas'].append((entity_name, total_amount_val, count))
    elif 'WATER' in entity_upper:
        utilities_by_type['Water'].append((entity_name, total_amount_val, count))
    elif 'SEWER' in entity_upper:
        utilities_by_type['Sewer'].append((entity_name, total_amount_val, count))
    elif 'WASTE' in entity_upper or 'TRASH' in entity_upper:
        utilities_by_type['Trash/Waste'].append((entity_name, total_amount_val, count))
    elif 'SPECTRUM' in entity_upper or 'INTERNET' in entity_upper or 'PHONE' in entity_upper:
        utilities_by_type['Internet/Phone'].append((entity_name, total_amount_val, count))
    else:
        utilities_by_type['Other'].append((entity_name, total_amount_val, count))
    
    print(f"{entity_name:<40} ${total_amount_val:>14,.2f} {count:>12}")

print("-" * 80)
print(f"{'TOTAL':<40} ${total_amount:>14,.2f} {total_count:>12}")

print("\n" + "=" * 80)
print("UTILITIES BY CATEGORY")
print("=" * 80)

for category, items in utilities_by_type.items():
    if items:
        print(f"\n{category}:")
        print("-" * 80)
        cat_total = 0
        cat_count = 0
        for entity_name, amount, count in items:
            cat_total += amount
            cat_count += count
            print(f"  {entity_name:<38} ${amount:>14,.2f} {count:>12}")
        print(f"  {'Subtotal':<38} ${cat_total:>14,.2f} {cat_count:>12}")

print("\n" + "=" * 80)
print(f"Total Utility Entities: {len(results)}")
print(f"Total Utility Transactions: {total_count}")
print(f"Total Utility Amount: ${total_amount:,.2f}")
print("=" * 80)

conn.close()
