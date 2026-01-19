"""
Parse bank statements from various formats (PDF, CSV, Excel).
"""

import csv
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@dataclass
class Transaction:
    """Represents a bank transaction."""
    date: datetime
    description: str
    amount: float
    transaction_type: str  # 'debit' or 'credit'
    account: Optional[str] = None
    raw_text: Optional[str] = None
    
    def __post_init__(self):
        """Ensure amount is positive for debits, negative for credits."""
        if self.transaction_type == 'debit' and self.amount > 0:
            self.amount = -abs(self.amount)
        elif self.transaction_type == 'credit' and self.amount < 0:
            self.amount = abs(self.amount)


class BankStatementParser:
    """Parse bank statements from various formats."""
    
    def __init__(self):
        """Initialize parser."""
        self.transactions: List[Transaction] = []
    
    def parse_file(self, file_path: str) -> List[Transaction]:
        """
        Parse a bank statement file.
        
        Args:
            file_path: Path to the bank statement file
        
        Returns:
            List of Transaction objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._parse_pdf(file_path)
        elif suffix in ['.csv', '.txt']:
            return self._parse_csv(file_path)
        elif suffix in ['.xlsx', '.xls']:
            return self._parse_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def _parse_pdf(self, file_path: Path) -> List[Transaction]:
        """Parse PDF bank statement."""
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber is required for PDF parsing. Install with: pip install pdfplumber")
        
        transactions = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Try to extract table data
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            page_transactions = self._parse_table(table)
                            transactions.extend(page_transactions)
                    else:
                        # Fallback to text parsing
                        page_transactions = self._parse_text(text)
                        transactions.extend(page_transactions)
        
        self.transactions.extend(transactions)
        return transactions
    
    def _parse_csv(self, file_path: Path) -> List[Transaction]:
        """Parse CSV bank statement."""
        transactions = []
        
        # Try different CSV formats
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Try to detect delimiter
                    sample = f.read(1024)
                    f.seek(0)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                    
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    for row in reader:
                        transaction = self._parse_csv_row(row)
                        if transaction:
                            transactions.append(transaction)
                
                break  # Successfully parsed
            except Exception as e:
                if encoding == encodings[-1]:
                    raise ValueError(f"Could not parse CSV file: {e}")
                continue
        
        self.transactions.extend(transactions)
        return transactions
    
    def _parse_excel(self, file_path: Path) -> List[Transaction]:
        """Parse Excel bank statement."""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel parsing. Install with: pip install pandas")
        
        transactions = []
        
        # Try reading as Excel
        try:
            df = pd.read_excel(file_path)
            
            # Common column name patterns
            date_cols = [c for c in df.columns if 'date' in c.lower()]
            desc_cols = [c for c in df.columns if any(x in c.lower() for x in ['desc', 'memo', 'detail', 'transaction'])]
            amount_cols = [c for c in df.columns if any(x in c.lower() for x in ['amount', 'debit', 'credit', 'balance'])]
            
            for _, row in df.iterrows():
                transaction = self._parse_excel_row(row, date_cols, desc_cols, amount_cols)
                if transaction:
                    transactions.append(transaction)
        except Exception as e:
            raise ValueError(f"Could not parse Excel file: {e}")
        
        self.transactions.extend(transactions)
        return transactions
    
    def _parse_table(self, table: List[List]) -> List[Transaction]:
        """Parse a table structure from PDF."""
        transactions = []
        # This is a simplified parser - would need to be customized per bank format
        # Look for date, description, amount columns
        return transactions
    
    def _parse_text(self, text: str) -> List[Transaction]:
        """Parse plain text bank statement."""
        transactions = []
        # Pattern matching for common bank statement formats
        # Date patterns: MM/DD/YYYY, DD/MM/YYYY, etc.
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        # Amount patterns: $1,234.56, -$123.45, etc.
        amount_pattern = r'[\$]?([\d,]+\.\d{2})'
        
        lines = text.split('\n')
        for line in lines:
            # Try to extract transaction data
            dates = re.findall(date_pattern, line)
            amounts = re.findall(amount_pattern, line)
            
            if dates and amounts:
                try:
                    date_str = dates[0]
                    amount_str = amounts[-1].replace(',', '')
                    amount = float(amount_str)
                    
                    # Determine if debit or credit
                    trans_type = 'debit' if '-' in line or amount < 0 else 'credit'
                    
                    # Extract description (everything except date and amount)
                    desc = re.sub(date_pattern, '', line)
                    desc = re.sub(amount_pattern, '', desc)
                    desc = desc.strip()
                    
                    transaction = Transaction(
                        date=self._parse_date(date_str),
                        description=desc,
                        amount=abs(amount),
                        transaction_type=trans_type,
                        raw_text=line
                    )
                    transactions.append(transaction)
                except Exception:
                    continue
        
        return transactions
    
    def _parse_csv_row(self, row: Dict) -> Optional[Transaction]:
        """Parse a single CSV row into a Transaction."""
        # Common column names
        date_col = None
        desc_col = None
        amount_col = None
        
        for col in row.keys():
            col_lower = col.lower()
            if 'date' in col_lower and not date_col:
                date_col = col
            elif any(x in col_lower for x in ['desc', 'memo', 'detail', 'transaction', 'payee']):
                desc_col = col
            elif any(x in col_lower for x in ['amount', 'debit', 'credit']):
                amount_col = col
        
        if not (date_col and desc_col and amount_col):
            return None
        
        try:
            date = self._parse_date(row[date_col])
            description = str(row[desc_col]).strip()
            amount_str = str(row[amount_col]).replace('$', '').replace(',', '').strip()
            amount = float(amount_str)
            
            # Determine transaction type
            if 'debit' in amount_col.lower() or amount < 0:
                trans_type = 'debit'
            else:
                trans_type = 'credit'
            
            return Transaction(
                date=date,
                description=description,
                amount=abs(amount),
                transaction_type=trans_type,
                raw_text=str(row)
            )
        except Exception as e:
            return None
    
    def _parse_excel_row(self, row, date_cols, desc_cols, amount_cols) -> Optional[Transaction]:
        """Parse a single Excel row into a Transaction."""
        if not (date_cols and desc_cols and amount_cols):
            return None
        
        try:
            date_col = date_cols[0]
            desc_col = desc_cols[0]
            amount_col = amount_cols[0]
            
            date_val = row[date_col]
            if pd.isna(date_val):
                return None
            
            date = self._parse_date(str(date_val))
            description = str(row[desc_col]).strip()
            
            amount_val = row[amount_col]
            if pd.isna(amount_val):
                return None
            
            amount = float(amount_val)
            
            trans_type = 'debit' if amount < 0 or 'debit' in amount_col.lower() else 'credit'
            
            return Transaction(
                date=date,
                description=description,
                amount=abs(amount),
                transaction_type=trans_type
            )
        except Exception:
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        date_str = str(date_str).strip()
        
        # Try common date formats
        formats = [
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%m/%d/%y',
            '%d/%m/%y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all fail, try pandas parsing
        if PANDAS_AVAILABLE:
            try:
                return pd.to_datetime(date_str).to_pydatetime()
            except:
                pass
        
        raise ValueError(f"Could not parse date: {date_str}")
