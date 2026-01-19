#!/usr/bin/env python3
"""
Show PayPal summary totals.
"""

import sqlite3

db_path = "tax_data_2025.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("PAYPAL ENTITIES SUMMARY")
print("=" * 80)

cursor.execute("""
    SELECT 
        entity_name, 
        total_amount, 
        transaction_count, 
        first_transaction_date, 
        last_transaction_date
    FROM EntitySummary 
    WHERE entity_name LIKE 'PAYPAL-%' 
    ORDER BY ABS(total_amount) DESC
""")

results = cursor.fetchall()

print(f"\n{'Entity Name':<30} {'Total Amount':>15} {'Count':>8} {'First Date':>12} {'Last Date':>12}")
print("-" * 80)

total_amount = 0
total_count = 0

for entity_name, total_amount_val, count, first_date, last_date in results:
    total_amount += total_amount_val
    total_count += count
    print(f"{entity_name:<30} ${total_amount_val:>14,.2f} {count:>8} {first_date:>12} {last_date:>12}")

print("-" * 80)
print(f"{'TOTAL':<30} ${total_amount:>14,.2f} {total_count:>8}")

print("\n" + "=" * 80)
print(f"Total PayPal Entities: {len(results)}")
print(f"Total Transactions: {total_count}")
print(f"Grand Total Amount: ${total_amount:,.2f}")
print("=" * 80)

conn.close()
