"""
Analyze and understand the Excel template structure.
"""

import openpyxl
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TemplateStructure:
    """Structure of the tax template."""
    income_sheet_name: str = None
    consulting_expenses_sheet: str = "FFJ Consulting LLC EXP"
    rental_income_sheet: str = "worksheet-RENT INCOME"
    rental_expenses_sheet: str = "worksheet Rental DetailRecieptA"
    
    # Column mappings for consulting expenses
    consulting_expense_columns: Dict[str, str] = None
    
    # Rental property addresses
    rental_properties: List[str] = None


class TemplateAnalyzer:
    """Analyze the Excel template to understand its structure."""
    
    def __init__(self, template_path: str):
        """
        Initialize template analyzer.
        
        Args:
            template_path: Path to the Excel template file
        """
        self.template_path = template_path
        self.wb = None
        self.structure = TemplateStructure()
    
    def analyze(self) -> TemplateStructure:
        """Analyze the template and return its structure."""
        self.wb = openpyxl.load_workbook(self.template_path, data_only=True)
        
        # Identify sheets
        sheet_names = self.wb.sheetnames
        print(f"Found sheets: {sheet_names}")
        
        # Find income sheet (first sheet or one with W2 headers)
        for sheet_name in sheet_names:
            sheet = self.wb[sheet_name]
            first_row = [cell.value for cell in sheet[1]]
            if any(cell and 'W2' in str(cell).upper() for cell in first_row):
                self.structure.income_sheet_name = sheet_name
                break
        
        if not self.structure.income_sheet_name:
            self.structure.income_sheet_name = sheet_names[0]
        
        # Analyze consulting expenses sheet
        if self.structure.consulting_expenses_sheet in sheet_names:
            self._analyze_consulting_expenses()
        
        # Analyze rental income sheet
        if self.structure.rental_income_sheet in sheet_names:
            self._analyze_rental_income()
        
        # Analyze rental expenses sheet
        if self.structure.rental_expenses_sheet in sheet_names:
            self._analyze_rental_expenses()
        
        return self.structure
    
    def _analyze_consulting_expenses(self):
        """Analyze the consulting expenses sheet structure."""
        sheet = self.wb[self.structure.consulting_expenses_sheet]
        
        # Get header row (row 1)
        headers = {}
        for col_idx, cell in enumerate(sheet[1], 1):
            if cell.value:
                header_text = str(cell.value).strip()
                headers[header_text] = col_idx
        
        self.structure.consulting_expense_columns = headers
        print(f"Consulting expense columns: {headers}")
    
    def _analyze_rental_income(self):
        """Analyze rental income sheet to find property addresses."""
        sheet = self.wb[self.structure.rental_income_sheet]
        
        # Properties are typically in column A or B, starting from row 2-4
        properties = []
        for row_idx in range(2, 20):
            row = sheet[row_idx]
            # Check first few columns for property identifiers
            for col_idx in range(1, 5):
                cell_value = row[col_idx].value
                if cell_value and isinstance(cell_value, (int, str)):
                    prop_str = str(cell_value).strip()
                    # Look for property numbers (like "1108", "1035", etc.)
                    if prop_str.isdigit() and len(prop_str) == 4:
                        if prop_str not in properties:
                            properties.append(prop_str)
                    # Also check for property names
                    elif prop_str and prop_str not in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                                                       'TOTAL', 'RENTAL INCOME', 'Fred Jabbari']:
                        if len(prop_str) > 2 and prop_str not in properties:
                            properties.append(prop_str)
        
        self.structure.rental_properties = properties
        print(f"Found rental properties: {properties}")
    
    def _analyze_rental_expenses(self):
        """Analyze rental expenses sheet structure."""
        # This sheet has property addresses in column A
        sheet = self.wb[self.structure.rental_expenses_sheet]
        
        # Headers are in row 1
        headers = {}
        for col_idx, cell in enumerate(sheet[1], 1):
            if cell.value:
                header_text = str(cell.value).strip()
                headers[header_text] = col_idx
        
        print(f"Rental expense columns: {list(headers.keys())[:10]}...")
    
    def close(self):
        """Close the workbook."""
        if self.wb:
            self.wb.close()
