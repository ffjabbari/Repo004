"""
Process bank statements into SQLite database with aggregated summaries.
"""

import sqlite3
import csv
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Transaction:
    """Represents a bank transaction."""
    date: datetime
    description: str
    amount: float
    running_balance: Optional[float] = None
    entity: Optional[str] = None  # Extracted entity name
    category: Optional[str] = None  # Tax category


class DatabaseProcessor:
    """Process transactions into SQLite database."""
    
    def __init__(self, db_path: str = "tax_data.db"):
        """
        Initialize database processor.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._create_database()
    
    def _create_database(self):
        """Create database schema."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # TaxYearSummary - Summary by year
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TaxYearSummary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_year INTEGER NOT NULL,
                beginning_balance REAL,
                total_credits REAL,
                total_debits REAL,
                ending_balance REAL,
                net_amount REAL,
                transaction_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tax_year)
            )
        """)
        
        # TaxYearDetail - High-level detail by year
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TaxYearDetail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_year INTEGER NOT NULL,
                transaction_date DATE NOT NULL,
                description TEXT,
                amount REAL,
                running_balance REAL,
                entity_name TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # EntitySummary - Aggregated summary by entity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS EntitySummary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_year INTEGER NOT NULL,
                entity_name TEXT NOT NULL,
                total_amount REAL,
                transaction_count INTEGER,
                first_transaction_date DATE,
                last_transaction_date DATE,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tax_year, entity_name)
            )
        """)
        
        # EntityDetail - All individual transactions by entity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS EntityDetail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_year INTEGER NOT NULL,
                entity_name TEXT NOT NULL,
                transaction_date DATE NOT NULL,
                description TEXT,
                amount REAL,
                running_balance REAL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tax_year ON TaxYearDetail(tax_year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_year ON EntitySummary(tax_year, entity_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_detail_year ON EntityDetail(tax_year, entity_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_detail_date ON EntityDetail(transaction_date)")
        
        self.conn.commit()
    
    def parse_csv(self, csv_path: str, tax_year: int = 2025) -> List[Transaction]:
        """
        Parse CSV bank statement.
        
        Args:
            csv_path: Path to CSV file
            tax_year: Tax year
        
        Returns:
            List of Transaction objects
        """
        transactions = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Find where transactions start (look for "Date,Description,Amount" header)
        start_row = None
        summary_data = {}
        
        for i, row in enumerate(rows):
            if len(row) > 0:
                # Check for summary rows
                if 'Beginning balance' in row[0]:
                    try:
                        summary_data['beginning_balance'] = self._parse_amount(row[2])
                    except:
                        pass
                elif 'Total credits' in row[0]:
                    try:
                        summary_data['total_credits'] = self._parse_amount(row[2])
                    except:
                        pass
                elif 'Total debits' in row[0]:
                    try:
                        summary_data['total_debits'] = self._parse_amount(row[2])
                    except:
                        pass
                elif 'Ending balance' in row[0]:
                    try:
                        summary_data['ending_balance'] = self._parse_amount(row[2])
                    except:
                        pass
                
                # Find transaction header
                if len(row) >= 4 and 'Date' in row[0] and 'Description' in row[1]:
                    start_row = i + 1
                    break
        
        if start_row is None:
            raise ValueError("Could not find transaction data in CSV")
        
        # Parse transactions
        for row in rows[start_row:]:
            if len(row) < 3 or not row[0] or not row[1]:
                continue
            
            try:
                date_str = row[0].strip()
                description = row[1].strip()
                amount_str = row[2].strip() if len(row) > 2 else "0"
                running_bal_str = row[3].strip() if len(row) > 3 else None
                
                # Skip summary rows
                if 'Beginning balance' in description or 'Total' in description:
                    continue
                
                # Parse date
                date = datetime.strptime(date_str, '%m/%d/%Y')
                
                # Parse amount
                amount = self._parse_amount(amount_str)
                
                # Parse running balance
                running_balance = None
                if running_bal_str:
                    running_balance = self._parse_amount(running_bal_str)
                
                # Extract entity name
                entity = self._extract_entity(description)
                
                transaction = Transaction(
                    date=date,
                    description=description,
                    amount=amount,
                    running_balance=running_balance,
                    entity=entity
                )
                
                transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing row: {row} - {e}")
                continue
        
        # Store summary data
        if summary_data:
            self._store_year_summary(tax_year, summary_data, len(transactions))
        
        return transactions
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float."""
        if not amount_str:
            return 0.0
        
        # Remove $, commas, and spaces
        amount_str = amount_str.replace('$', '').replace(',', '').strip()
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def _extract_entity(self, description: str) -> str:
        """
        Extract entity name from transaction description.
        
        Examples:
        - "St Louis County DES:WEB PYMNT..." -> "St Louis County"
        - "Bill Pay Check 9399: SPECTRUM" -> "SPECTRUM"
        - "Uber Technolog 12/31 PURCHASE..." -> "Uber Technolog"
        """
        desc = description.strip()
        
        # Pattern 1: "Bill Pay Check XXXX: ENTITY"
        match = re.search(r'Bill Pay Check \d+: (.+?)$', desc)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "ENTITY DES:..." or "ENTITY ID:..."
        match = re.search(r'^([A-Z][A-Z\s&]+?)\s+(?:DES:|ID:)', desc)
        if match:
            entity = match.group(1).strip()
            # Clean up common suffixes
            entity = re.sub(r'\s+(LLC|INC|CORP|CO)$', '', entity, flags=re.IGNORECASE)
            return entity
        
        # Pattern 3: "Check XXXX" -> "Check Payment"
        if desc.startswith('Check '):
            return "Check Payment"
        
        # Pattern 4: Extract first meaningful words (up to 3 words)
        words = desc.split()
        if len(words) >= 1:
            # Take first word or first few words if they look like a name
            entity = words[0]
            if len(words) > 1 and words[1][0].isupper():
                entity = f"{words[0]} {words[1]}"
            if len(words) > 2 and words[2][0].isupper() and len(entity.split()) < 3:
                entity = f"{entity} {words[2]}"
            return entity
        
        return "Unknown"
    
    def _store_year_summary(self, tax_year: int, summary_data: Dict, transaction_count: int):
        """Store year summary."""
        cursor = self.conn.cursor()
        
        net_amount = summary_data.get('ending_balance', 0) - summary_data.get('beginning_balance', 0)
        
        cursor.execute("""
            INSERT OR REPLACE INTO TaxYearSummary 
            (tax_year, beginning_balance, total_credits, total_debits, ending_balance, net_amount, transaction_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tax_year,
            summary_data.get('beginning_balance'),
            summary_data.get('total_credits'),
            summary_data.get('total_debits'),
            summary_data.get('ending_balance'),
            net_amount,
            transaction_count
        ))
        
        self.conn.commit()
    
    def process_transactions(self, transactions: List[Transaction], tax_year: int = 2025):
        """
        Process transactions into database tables.
        
        Args:
            transactions: List of Transaction objects
            tax_year: Tax year
        """
        cursor = self.conn.cursor()
        
        # Clear existing data for this year
        cursor.execute("DELETE FROM TaxYearDetail WHERE tax_year = ?", (tax_year,))
        cursor.execute("DELETE FROM EntitySummary WHERE tax_year = ?", (tax_year,))
        cursor.execute("DELETE FROM EntityDetail WHERE tax_year = ?", (tax_year,))
        
        # Group transactions by entity
        entity_transactions = {}
        
        for trans in transactions:
            entity = trans.entity or "Unknown"
            
            # Store in TaxYearDetail
            cursor.execute("""
                INSERT INTO TaxYearDetail 
                (tax_year, transaction_date, description, amount, running_balance, entity_name, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                tax_year,
                trans.date.date(),
                trans.description,
                trans.amount,
                trans.running_balance,
                entity,
                trans.category
            ))
            
            # Group by entity for EntityDetail and EntitySummary
            if entity not in entity_transactions:
                entity_transactions[entity] = []
            entity_transactions[entity].append(trans)
        
        # Create EntityDetail and EntitySummary
        for entity, trans_list in entity_transactions.items():
            # Insert all individual transactions into EntityDetail
            for trans in trans_list:
                cursor.execute("""
                    INSERT INTO EntityDetail 
                    (tax_year, entity_name, transaction_date, description, amount, running_balance, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tax_year,
                    entity,
                    trans.date.date(),
                    trans.description,
                    trans.amount,
                    trans.running_balance,
                    trans.category
                ))
            
            # Create aggregated summary for EntitySummary
            total_amount = sum(t.amount for t in trans_list)
            transaction_count = len(trans_list)
            dates = [t.date for t in trans_list]
            first_date = min(dates).date()
            last_date = max(dates).date()
            
            cursor.execute("""
                INSERT INTO EntitySummary 
                (tax_year, entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                tax_year,
                entity,
                total_amount,
                transaction_count,
                first_date,
                last_date,
                trans_list[0].category if trans_list else None
            ))
        
        self.conn.commit()
        print(f"Processed {len(transactions)} transactions into database")
        print(f"Created summaries for {len(entity_transactions)} entities")
    
    def get_entity_summary(self, tax_year: int = 2025) -> List[Tuple]:
        """Get entity summary for a tax year."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT entity_name, total_amount, transaction_count, first_transaction_date, last_transaction_date
            FROM EntitySummary
            WHERE tax_year = ?
            ORDER BY ABS(total_amount) DESC
        """, (tax_year,))
        return cursor.fetchall()
    
    def get_entity_details(self, entity_name: str, tax_year: int = 2025) -> List[Tuple]:
        """Get all transactions for an entity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT transaction_date, description, amount, running_balance
            FROM EntityDetail
            WHERE tax_year = ? AND entity_name = ?
            ORDER BY transaction_date
        """, (tax_year, entity_name))
        return cursor.fetchall()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
