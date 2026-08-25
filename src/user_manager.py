"""User Management System - Handles multiple users with individual portfolios and accounts."""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class UserManager:
    """Manages multiple users, their accounts, and withdrawal taxes."""
    
    def __init__(self, data_dir: str = 'data'):
        """
        Initialize UserManager.
        
        Args:
            data_dir: Directory to store user data
        """
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, 'users.json')
        self.admin_earnings_file = os.path.join(data_dir, 'admin_earnings.json')
        self.withdrawal_history_file = os.path.join(data_dir, 'withdrawal_history.json')
        self.withdrawal_tax_rate = 0.02  # 2% withdrawal tax
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load or initialize data
        self.users = self._load_users()
        self.admin_earnings = self._load_admin_earnings()
        self.withdrawal_history = self._load_withdrawal_history()
    
    def _load_users(self) -> Dict:
        """Load users from file."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading users: {e}")
        return {}
    
    def _load_admin_earnings(self) -> Dict:
        """Load admin earnings from file."""
        if os.path.exists(self.admin_earnings_file):
            try:
                with open(self.admin_earnings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading admin earnings: {e}")
        return {'total_earnings': 0.0, 'transactions': []}
    
    def _load_withdrawal_history(self) -> List:
        """Load withdrawal history from file."""
        if os.path.exists(self.withdrawal_history_file):
            try:
                with open(self.withdrawal_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading withdrawal history: {e}")
        return []
    
    def _save_users(self):
        """Save users to file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def _save_admin_earnings(self):
        """Save admin earnings to file."""
        try:
            with open(self.admin_earnings_file, 'w') as f:
                json.dump(self.admin_earnings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving admin earnings: {e}")
    
    def _save_withdrawal_history(self):
        """Save withdrawal history to file."""
        try:
            with open(self.withdrawal_history_file, 'w') as f:
                json.dump(self.withdrawal_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving withdrawal history: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password for secure storage."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, initial_capital: float = 10000.0) -> Tuple[bool, str]:
        """
        Create a new user account.
        
        Args:
            username: Username
            password: User password
            initial_capital: Initial capital for the user's portfolio
            
        Returns:
            Tuple of (success, message)
        """
        if username in self.users:
            return False, f"User '{username}' already exists"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        self.users[username] = {
            'password_hash': self._hash_password(password),
            'initial_capital': initial_capital,
            'cash': initial_capital,
            'created_at': datetime.now().isoformat(),
            'total_withdrawn': 0.0,
            'total_taxes_paid': 0.0
        }
        
        self._save_users()
        logger.info(f"User '{username}' created with initial capital ${initial_capital}")
        return True, f"User '{username}' created successfully"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate a user.
        
        Args:
            username: Username
            password: User password
            
        Returns:
            Tuple of (authenticated, message)
        """
        if username not in self.users:
            return False, f"User '{username}' not found"
        
        stored_hash = self.users[username]['password_hash']
        if stored_hash != self._hash_password(password):
            return False, "Invalid password"
        
        return True, "Authentication successful"
    
    def get_user(self, username: str) -> Optional[Dict]:
        """
        Get user data.
        
        Args:
            username: Username
            
        Returns:
            User dictionary or None if not found
        """
        return self.users.get(username)
    
    def get_all_users(self) -> List[str]:
        """Get list of all usernames."""
        return list(self.users.keys())
    
    def deposit_cash(self, username: str, amount: float) -> Tuple[bool, str]:
        """
        Deposit cash to user's account.
        
        Args:
            username: Username
            amount: Amount to deposit
            
        Returns:
            Tuple of (success, message)
        """
        if username not in self.users:
            return False, f"User '{username}' not found"
        
        if amount <= 0:
            return False, "Deposit amount must be positive"
        
        self.users[username]['cash'] += amount
        self._save_users()
        logger.info(f"Deposit of ${amount:.2f} to {username}. New cash: ${self.users[username]['cash']:.2f}")
        return True, f"Deposited ${amount:.2f}"
    
    def withdraw_cash(self, username: str, amount: float) -> Tuple[bool, str, float]:
        """
        Withdraw cash from user's account with 2% tax.
        
        Args:
            username: Username
            amount: Amount to withdraw (before tax)
            
        Returns:
            Tuple of (success, message, tax_amount)
        """
        if username not in self.users:
            return False, f"User '{username}' not found", 0.0
        
        if amount <= 0:
            return False, "Withdrawal amount must be positive", 0.0
        
        user = self.users[username]
        
        if user['cash'] < amount:
            return False, f"Insufficient funds. Available: ${user['cash']:.2f}", 0.0
        
        # Calculate tax (2% of withdrawal amount)
        tax_amount = amount * self.withdrawal_tax_rate
        net_withdrawal = amount - tax_amount
        
        # Update user cash
        user['cash'] -= amount
        user['total_withdrawn'] += net_withdrawal
        user['total_taxes_paid'] += tax_amount
        
        # Add tax to admin earnings
        self.admin_earnings['total_earnings'] += tax_amount
        self.admin_earnings['transactions'].append({
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'withdrawal_amount': amount,
            'tax_amount': tax_amount,
            'type': 'withdrawal_tax'
        })
        
        # Record in withdrawal history
        self.withdrawal_history.append({
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'withdrawal_amount': amount,
            'tax_amount': tax_amount,
            'net_withdrawal': net_withdrawal,
            'user_cash_remaining': user['cash']
        })
        
        self._save_users()
        self._save_admin_earnings()
        self._save_withdrawal_history()
        
        logger.info(
            f"Withdrawal from {username}: ${amount:.2f} | "
            f"Tax: ${tax_amount:.2f} (2%) | Net: ${net_withdrawal:.2f}"
        )
        
        return True, f"Withdrew ${net_withdrawal:.2f} (${tax_amount:.2f} tax applied)", tax_amount
    
    def update_user_cash(self, username: str, new_cash: float) -> Tuple[bool, str]:
        """
        Update user's cash balance (used by portfolio).
        
        Args:
            username: Username
            new_cash: New cash amount
            
        Returns:
            Tuple of (success, message)
        """
        if username not in self.users:
            return False, f"User '{username}' not found"
        
        self.users[username]['cash'] = new_cash
        self._save_users()
        return True, "Cash updated"
    
    def get_admin_earnings(self) -> Dict:
        """
        Get total admin earnings from withdrawal taxes.
        
        Returns:
            Admin earnings dictionary
        """
        return self.admin_earnings
    
    def get_withdrawal_history(self, username: Optional[str] = None) -> List:
        """
        Get withdrawal history.
        
        Args:
            username: Optional username to filter by
            
        Returns:
            List of withdrawal records
        """
        if username:
            return [w for w in self.withdrawal_history if w['user'] == username]
        return self.withdrawal_history
    
    def get_user_stats(self, username: str) -> Optional[Dict]:
        """
        Get user statistics.
        
        Args:
            username: Username
            
        Returns:
            User statistics dictionary
        """
        if username not in self.users:
            return None
        
        user = self.users[username]
        return {
            'username': username,
            'initial_capital': user['initial_capital'],
            'current_cash': user['cash'],
            'total_withdrawn': user['total_withdrawn'],
            'total_taxes_paid': user['total_taxes_paid'],
            'created_at': user['created_at']
        }
    
    def delete_user(self, username: str) -> Tuple[bool, str]:
        """
        Delete a user account.
        
        Args:
            username: Username
            
        Returns:
            Tuple of (success, message)
        """
        if username not in self.users:
            return False, f"User '{username}' not found"
        
        del self.users[username]
        self._save_users()
        logger.info(f"User '{username}' deleted")
        return True, f"User '{username}' deleted"
