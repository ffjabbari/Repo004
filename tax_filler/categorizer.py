"""
Categorize transactions into tax categories.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from tax_filler.bank_parser import Transaction


@dataclass
class CategorizedTransaction:
    """Transaction with category information."""
    transaction: Transaction
    category: str
    subcategory: Optional[str] = None
    property_address: Optional[str] = None  # For rental expenses
    is_business_expense: bool = False
    is_rental_expense: bool = False
    is_rental_income: bool = False
    notes: Optional[str] = None


class TransactionCategorizer:
    """Categorize bank transactions into tax categories."""
    
    def __init__(self):
        """Initialize categorizer with keyword mappings."""
        self._setup_keyword_mappings()
    
    def _setup_keyword_mappings(self):
        """Setup keyword mappings for categorization."""
        
        # Business expense categories (FFJ Consulting LLC)
        self.business_expense_keywords = {
            'Software and MIS': [
                'intellij', 'zoom', 'jetbrains', 'software', 'subscription', 'saas',
                'adobe', 'microsoft', 'office 365', 'slack', 'github', 'gitlab'
            ],
            'Hardware Computer purchased': [
                'apple', 'macbook', 'computer', 'laptop', 'desktop', 'monitor',
                'keyboard', 'mouse', 'hardware', 'dell', 'hp', 'lenovo'
            ],
            'office exp': [
                'office', 'supplies', 'staples', 'office depot', 'paper', 'printer',
                'ink', 'toner', 'furniture', 'desk', 'chair'
            ],
            'Auto EXP': [
                'gas', 'fuel', 'exxon', 'shell', 'chevron', 'bp', 'mobil',
                'auto', 'car', 'vehicle', 'repair', 'maintenance', 'tire',
                'oil change', 'parking', 'toll', 'uber', 'lyft'
            ],
            'Bank Fee': [
                'fee', 'service charge', 'overdraft', 'atm fee', 'wire transfer',
                'monthly maintenance', 'bank fee'
            ],
            'Insurance liability/Medical': [
                'insurance', 'liability', 'medical', 'health', 'dental', 'vision',
                'premium', 'coverage', 'blue cross', 'aetna', 'cigna'
            ],
            'Meal/Entertainment': [
                'restaurant', 'dining', 'food', 'meal', 'starbucks', 'mcdonald',
                'subway', 'pizza', 'cafe', 'bar', 'entertainment', 'movie',
                'theater', 'concert'
            ],
            'Professional Fee (Udemy Courses)': [
                'udemy', 'course', 'training', 'education', 'professional',
                'certification', 'coursera', 'linkedin learning', 'pluralsight'
            ],
            'Phone and Comm + internet Exp': [
                'phone', 'verizon', 'at&t', 't-mobile', 'sprint', 'cellular',
                'internet', 'wifi', 'comcast', 'xfinity', 'spectrum', 'att',
                'communication', 'data plan'
            ],
            'Travel Exp(Lodging)': [
                'hotel', 'lodging', 'airbnb', 'booking', 'marriott', 'hilton',
                'hyatt', 'holiday inn', 'travelodge', 'motel'
            ],
            'Travel Transportation': [
                'airline', 'flight', 'delta', 'united', 'american', 'southwest',
                'jetblue', 'train', 'amtrak', 'taxi', 'rental car', 'hertz',
                'avis', 'enterprise'
            ],
            'Utilities': [
                'electric', 'gas utility', 'water', 'sewer', 'trash', 'waste',
                'utility', 'power', 'energy', 'con ed', 'pg&e', 'socal gas'
            ],
        }
        
        # Rental property addresses (from template analysis)
        self.rental_properties = [
            '1108', '1035', '1039', '5956', '5952', '5015', '1029',
            'HI-VIEW', 'ALMONT', 'Pershing'
        ]
        
        # Rental expense categories
        self.rental_expense_keywords = {
            'mamaint/lab': [  # Maintenance labor
                'labor', 'contractor', 'plumber', 'electrician', 'handyman',
                'repair', 'maintenance', 'service', 'work'
            ],
            'main/mat': [  # Maintenance materials
                'paint', 'supplies', 'material', 'hardware', 'lumber',
                'tools', 'parts', 'fixture', 'faucet', 'toilet', 'sink'
            ],
            'imp/lab': [  # Improvement labor
                'renovation', 'remodel', 'construction', 'installation',
                'improvement', 'upgrade', 'build', 'hvac', 'roof'
            ],
            'imp/mat': [  # Improvement materials
                'appliance', 'furnace', 'ac', 'heating', 'cooling',
                'windows', 'doors', 'flooring', 'cabinets', 'countertop'
            ],
        }
        
        # Income keywords
        self.income_keywords = {
            'rental_income': [
                'rent', 'rental', 'lease', 'tenant', 'property'
            ],
            'wages': [
                'payroll', 'salary', 'wage', 'paycheck', 'direct deposit'
            ],
            'interest': [
                'interest', 'dividend', 'savings', 'cd', 'certificate'
            ],
        }
    
    def categorize(self, transaction: Transaction) -> CategorizedTransaction:
        """
        Categorize a single transaction.
        
        Args:
            transaction: Transaction to categorize
        
        Returns:
            CategorizedTransaction
        """
        desc_lower = transaction.description.lower()
        
        # Check for rental income
        if self._is_rental_income(transaction):
            property_addr = self._extract_property_address(transaction.description)
            return CategorizedTransaction(
                transaction=transaction,
                category='Rental Income',
                property_address=property_addr,
                is_rental_income=True
            )
        
        # Check for rental expenses
        rental_expense_cat = self._categorize_rental_expense(transaction)
        if rental_expense_cat:
            property_addr = self._extract_property_address(transaction.description)
            return CategorizedTransaction(
                transaction=transaction,
                category=rental_expense_cat[0],
                subcategory=rental_expense_cat[1],
                property_address=property_addr,
                is_rental_expense=True
            )
        
        # Check for business expenses
        business_expense_cat = self._categorize_business_expense(transaction)
        if business_expense_cat:
            return CategorizedTransaction(
                transaction=transaction,
                category=business_expense_cat,
                is_business_expense=True
            )
        
        # Default: uncategorized
        return CategorizedTransaction(
            transaction=transaction,
            category='Uncategorized',
            notes='Needs manual review'
        )
    
    def _is_rental_income(self, transaction: Transaction) -> bool:
        """Check if transaction is rental income."""
        if transaction.transaction_type != 'credit':
            return False
        
        desc_lower = transaction.description.lower()
        return any(keyword in desc_lower for keyword in self.income_keywords['rental_income'])
    
    def _extract_property_address(self, description: str) -> Optional[str]:
        """Extract property address from transaction description."""
        desc_upper = description.upper()
        
        # Check for property numbers/addresses
        for prop in self.rental_properties:
            if prop in desc_upper:
                return prop
        
        # Try to find 4-digit numbers (property addresses)
        numbers = re.findall(r'\b\d{4}\b', description)
        if numbers:
            return numbers[0]
        
        return None
    
    def _categorize_rental_expense(self, transaction: Transaction) -> Optional[Tuple[str, str]]:
        """Categorize rental expense transaction."""
        if transaction.transaction_type != 'debit':
            return None
        
        desc_lower = transaction.description.lower()
        
        # Check if it's related to a rental property
        property_addr = self._extract_property_address(transaction.description)
        if not property_addr:
            return None
        
        # Categorize by expense type
        for category, keywords in self.rental_expense_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                return (category, None)
        
        # Default to maintenance materials if property found but no specific category
        return ('main/mat', None)
    
    def _categorize_business_expense(self, transaction: Transaction) -> Optional[str]:
        """Categorize business expense transaction."""
        if transaction.transaction_type != 'debit':
            return None
        
        desc_lower = transaction.description.lower()
        
        # Check each business expense category
        for category, keywords in self.business_expense_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                return category
        
        return None
    
    def categorize_batch(self, transactions: List[Transaction]) -> List[CategorizedTransaction]:
        """Categorize a batch of transactions."""
        return [self.categorize(t) for t in transactions]
