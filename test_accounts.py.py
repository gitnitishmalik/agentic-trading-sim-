```python
import unittest
import datetime
from unittest.mock import patch
import sys
import os

# To allow importing accounts.py from the same directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import the functions and classes from accounts.py
from accounts import get_share_price, Account

class TestAccounts(unittest.TestCase):

    # Mock the get_share_price to ensure consistent test results
    @patch('accounts.get_share_price')
    def test_get_share_price(self, mock_get_share_price):
        # Configure the mock to return specific values for known symbols
        mock_get_share_price.side_effect = lambda symbol: {
            "AAPL": 170.00,
            "TSLA": 250.00,
            "GOOGL": 140.00,
            "MSFT": 300.00,
            "AMZN": 100.00,
            "NVDA": 500.00,
        }.get(symbol.upper(), 0.0)

        self.assertEqual(get_share_price("AAPL"), 170.00)
        self.assertEqual(get_share_price("aapl"), 170.00) # Case insensitivity
        self.assertEqual(get_share_price("TSLA"), 250.00)
        self.assertEqual(get_share_price("UNKNOWN"), 0.0) # Unknown symbol

    @patch('datetime.datetime')
    def test_account_initialization(self, mock_dt):
        # Mock datetime.datetime.now() to return a fixed time
        fixed_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw) # Ensure other datetime calls work

        # Test with positive initial deposit
        account1 = Account(initial_deposit=1000.00)
        self.assertEqual(account1.get_balance(), 1000.00)
        self.assertEqual(account1.get_holdings(), {})
        self.assertEqual(account1.get_initial_deposit_amount(), 1000.00)
        self.assertEqual(len(account1.get_transactions()), 1)
        self.assertEqual(account1.get_transactions()[0]["type"], "initial_deposit")
        self.assertTrue(account1.get_transactions()[0]["success"])
        self.assertEqual(account1.get_transactions()[0]["amount"], 1000.00)
        self.assertEqual(account1.get_transactions()[0]["timestamp"], fixed_time.isoformat())

        # Test with zero initial deposit
        account2 = Account() # Defaults to 0.0
        self.assertEqual(account2.get_balance(), 0.0)
        self.assertEqual(account2.get_holdings(), {})
        self.assertEqual(account2.get_initial_deposit_amount(), 0.0)
        self.assertEqual(len(account2.get_transactions()), 1)
        self.assertEqual(account2.get_transactions()[0]["message"], "Account initialized with zero initial deposit.")

        # Test with negative initial deposit (should raise ValueError)
        with self.assertRaises(ValueError):
            Account(initial_deposit=-100.00)

    @patch('datetime.datetime')
    def test_deposit(self, mock_dt):
        fixed_time = datetime.datetime(2023, 1, 2, 10, 0, 0)
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        account = Account(initial_deposit=100.00)
        initial_transactions_count = len(account.get_transactions())

        # Valid deposit
        self.assertTrue(account.deposit(50.00))
        self.assertEqual(account.get_balance(), 150.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 1)
        self.assertEqual(account.get_transactions()[-1]["type"], "deposit")
        self.assertTrue(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["amount"], 50.00)
        self.assertEqual(account.get_transactions()[-1]["balance_after_transaction"], 150.00)

        # Deposit zero amount
        self.assertFalse(account.deposit(0.0))
        self.assertEqual(account.get_balance(), 150.00) # Balance should not change
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 2)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Deposit amount must be positive.")

        # Deposit negative amount
        self.assertFalse(account.deposit(-10.00))
        self.assertEqual(account.get_balance(), 150.00) # Balance should not change
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 3)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Deposit amount must be positive.")

    @patch('datetime.datetime')
    def test_withdraw(self, mock_dt):
        fixed_time = datetime.datetime(2023, 1, 3, 10, 0, 0)
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        account = Account(initial_deposit=200.00)
        initial_transactions_count = len(account.get_transactions())

        # Valid withdrawal
        self.assertTrue(account.withdraw(50.00))
        self.assertEqual(account.get_balance(), 150.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 1)
        self.assertEqual(account.get_transactions()[-1]["type"], "withdrawal")
        self.assertTrue(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["amount"], 50.00)
        self.assertEqual(account.get_transactions()[-1]["balance_after_transaction"], 150.00)


        # Withdraw more than balance (insufficient funds)
        self.assertFalse(account.withdraw(200.00))
        self.assertEqual(account.get_balance(), 150.00) # Balance should not change
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 2)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertIn("Insufficient funds", account.get_transactions()[-1]["message"])

        # Withdraw zero amount
        self.assertFalse(account.withdraw(0.0))
        self.assertEqual(account.get_balance(), 150.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 3)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Withdrawal amount must be positive.")

        # Withdraw negative amount
        self.assertFalse(account.withdraw(-10.0))
        self.assertEqual(account.get_balance(), 150.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 4)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Withdrawal amount must be positive.")

    @patch('accounts.get_share_price')
    @patch('datetime.datetime')
    def test_buy_shares(self, mock_dt, mock_get_share_price):
        mock_get_share_price.side_effect = lambda symbol: {
            "AAPL": 170.00, "TSLA": 250.00, "GOOGL": 140.00
        }.get(symbol.upper(), 0.0)

        fixed_time = datetime.datetime(2023, 1, 4, 10, 0, 0)
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        account = Account(initial_deposit=2000.00)
        initial_transactions_count = len(account.get_transactions())

        # Successful buy
        self.assertTrue(account.buy_shares("AAPL", 5)) # 5 * 170 = 850
        self.assertEqual(account.get_balance(), 2000.00 - 850.00)
        self.assertEqual(account.get_holdings(), {"AAPL": 5})
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 1)
        self.assertEqual(account.get_transactions()[-1]["type"], "buy")
        self.assertTrue(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["symbol"], "AAPL")
        self.assertEqual(account.get_transactions()[-1]["quantity"], 5)
        self.assertEqual(account.get_transactions()[-1]["price_per_share"], 170.00)
        self.assertEqual(account.get_transactions()[-1]["amount"], 850.00)
        self.assertEqual(account.get_transactions()[-1]["balance_after_transaction"], 1150.00)
        self.assertEqual(account.get_transactions()[-1]["holdings_after_transaction"], {"AAPL": 5})

        # Buy more of the same symbol
        self.assertTrue(account.buy_shares("AAPL", 3)) # 3 * 170 = 510
        self.assertEqual(account.get_balance(), 1150.00 - 510.00) # 640.00
        self.assertEqual(account.get_holdings(), {"AAPL": 8})
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 2)

        # Insufficient funds
        self.assertFalse(account.buy_shares("TSLA", 10)) # 10 * 250 = 2500, balance is 640
        self.assertEqual(account.get_balance(), 640.00) # Balance should not change
        self.assertEqual(account.get_holdings(), {"AAPL": 8}) # Holdings should not change
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 3)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertIn("Insufficient funds", account.get_transactions()[-1]["message"])

        # Unknown symbol
        self.assertFalse(account.buy_shares("UNKNOWN", 1))
        self.assertEqual(account.get_balance(), 640.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 4)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertIn("Invalid or unknown symbol", account.get_transactions()[-1]["message"])

        # Zero quantity
        self.assertFalse(account.buy_shares("AAPL", 0))
        self.assertEqual(account.get_balance(), 640.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 5)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Buy quantity must be positive.")

        # Negative quantity
        self.assertFalse(account.buy_shares("AAPL", -1))
        self.assertEqual(account.get_balance(), 640.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 6)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Buy quantity must be positive.")

    @patch('accounts.get_share_price')
    @patch('datetime.datetime')
    def test_sell_shares(self, mock_dt, mock_get_share_price):
        mock_get_share_price.side_effect = lambda symbol: {
            "AAPL": 170.00, "TSLA": 250.00, "GOOGL": 140.00
        }.get(symbol.upper(), 0.0)

        fixed_time = datetime.datetime(2023, 1, 5, 10, 0, 0)
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        account = Account(initial_deposit=2000.00)
        account.buy_shares("AAPL", 10) # 10 * 170 = 1700.00, Balance: 300, Holdings: {"AAPL": 10}
        account.buy_shares("TSLA", 2) # 2 * 250 = 500.00, Balance: -200 (this is okay for testing sell logic as initial deposit can be modified)
        # Manually adjust state to represent a known initial state for selling tests
        account._balance = 1000.00
        account._holdings = {"AAPL": 10, "TSLA": 2}
        initial_transactions_count = len(account.get_transactions())

        # Successful sell
        self.assertTrue(account.sell_shares("AAPL", 5)) # 5 * 170 = 850
        self.assertEqual(account.get_balance(), 1000.00 + 850.00) # 1850.00
        self.assertEqual(account.get_holdings(), {"AAPL": 5, "TSLA": 2})
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 1)
        self.assertEqual(account.get_transactions()[-1]["type"], "sell")
        self.assertTrue(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["symbol"], "AAPL")
        self.assertEqual(account.get_transactions()[-1]["quantity"], 5)
        self.assertEqual(account.get_transactions()[-1]["price_per_share"], 170.00)
        self.assertEqual(account.get_transactions()[-1]["amount"], 850.00)
        self.assertEqual(account.get_transactions()[-1]["balance_after_transaction"], 1850.00)
        self.assertEqual(account.get_transactions()[-1]["holdings_after_transaction"], {"AAPL": 5, "TSLA": 2})


        # Sell remaining shares (should remove symbol from holdings)
        self.assertTrue(account.sell_shares("AAPL", 5)) # 5 * 170 = 850
        self.assertEqual(account.get_balance(), 1850.00 + 850.00) # 2700.00
        self.assertEqual(account.get_holdings(), {"TSLA": 2}) # AAPL should be gone
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 2)
        self.assertEqual(account.get_transactions()[-1]["holdings_after_transaction"], {"TSLA": 2})

        # Sell more shares than held
        self.assertFalse(account.sell_shares("TSLA", 3)) # Have 2, trying to sell 3
        self.assertEqual(account.get_balance(), 2700.00) # Balance should not change
        self.assertEqual(account.get_holdings(), {"TSLA": 2}) # Holdings should not change
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 3)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertIn("Not enough shares of TSLA", account.get_transactions()[-1]["message"])

        # Sell shares of a symbol not held
        self.assertFalse(account.sell_shares("GOOGL", 1))
        self.assertEqual(account.get_balance(), 2700.00)
        self.assertEqual(account.get_holdings(), {"TSLA": 2})
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 4)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertIn("Not enough shares of GOOGL", account.get_transactions()[-1]["message"])

        # Unknown symbol (price lookup fails)
        self.assertFalse(account.sell_shares("UNKNOWN", 1))
        self.assertEqual(account.get_balance(), 2700.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 5)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertIn("Invalid or unknown symbol", account.get_transactions()[-1]["message"])

        # Zero quantity
        self.assertFalse(account.sell_shares("TSLA", 0))
        self.assertEqual(account.get_balance(), 2700.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 6)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Sell quantity must be positive.")

        # Negative quantity
        self.assertFalse(account.sell_shares("TSLA", -1))
        self.assertEqual(account.get_balance(), 2700.00)
        self.assertEqual(len(account.get_transactions()), initial_transactions_count + 7)
        self.assertFalse(account.get_transactions()[-1]["success"])
        self.assertEqual(account.get_transactions()[-1]["message"], "Sell quantity must be positive.")

    @patch('accounts.get_share_price')
    def test_get_balance(self, mock_get_share_price):
        mock_get_share_price.return_value = 100.00 # Not directly relevant but good to mock

        account = Account(initial_deposit=123.456)
        self.assertEqual(account.get_balance(), 123.46) # Test rounding

        account.deposit(10.00)
        self.assertEqual(account.get_balance(), 133.46)

        account.withdraw(3.46)
        self.assertEqual(account.get_balance(), 130.00)

    @patch('accounts.get_share_price')
    def test_get_holdings(self, mock_get_share_price):
        mock_get_share_price.side_effect = lambda symbol: {
            "AAPL": 170.00, "TSLA": 250.00
        }.get(symbol.upper(), 0.0)

        account = Account(initial_deposit=10000.00)
        self.assertEqual(account.get_holdings(), {})

        account.buy_shares("AAPL", 5)
        self.assertEqual(account.get_holdings(), {"AAPL": 5})

        account.buy_shares("TSLA", 2)
        self.assertEqual(account.get_holdings(), {"AAPL": 5, "TSLA": 2})

        account.sell_shares("AAPL", 3)
        self.assertEqual(account.get_holdings(), {"AAPL": 2, "TSLA": 2})

        account.sell_shares("TSLA", 2) # Sell all TSLA
        self.assertEqual(account.get_holdings(), {"AAPL": 2}) # TSLA should be removed

        # Test that returning a copy prevents external modification
        holdings_copy = account.get_holdings()
        holdings_copy["FAKE"] = 100
        self.assertEqual(account.get_holdings(), {"AAPL": 2})


    @patch('accounts.get_share_price')
    def test_get_portfolio_value(self, mock_get_share_price):
        account = Account(initial_deposit=1000.00)
        self.assertEqual(account.get_portfolio_value(), 1000.00)

        # Buy some shares
        mock_get_share_price.side_effect = lambda symbol: {
            "AAPL": 170.00,
            "TSLA": 250.00,
            "GOOGL": 140.00,
            "UNKNOWN": 0.0 # Simulate unknown price
        }.get(symbol.upper(), 0.0)

        account.buy_shares("AAPL", 5) # Cost: 850. Balance: 150. Holdings: {"AAPL": 5}
        # Portfolio: 150 (cash) + (5 * 170 = 850) = 1000.00
        self.assertEqual(account.get_portfolio_value(), 1000.00)

        account.buy_shares("TSLA", 2) # Cost: 500. Balance: -350. Holdings: {"AAPL": 5, "TSLA": 2}
        # Portfolio: -350 (cash) + (5 * 170 = 850) + (2 * 250 = 500) = 1000.00
        self.assertEqual(account.get_portfolio_value(), 1000.00)

        # Add a holding with an unknown price (should not contribute to value)
        account._holdings["UNKNOWN"] = 10
        # Portfolio: -350 (cash) + (5 * 170 = 850) + (2 * 250 = 500) + (10 * 0 = 0) = 1000.00
        self.assertEqual(account.get_portfolio_value(), 1000.00)

        # Sell some shares
        account.sell_shares("AAPL", 1) # Revenue: 170. Balance: -350 + 170 = -180. Holdings: {"AAPL": 4, "TSLA": 2, "UNKNOWN": 10}
        # Portfolio: -180 (cash) + (4 * 170 = 680) + (2 * 250 = 500) = 1000.00
        self.assertEqual(account.get_portfolio_value(), 1000.00)

    @patch('accounts.get_share_price')
    def test_get_profit_loss(self, mock_get_share_price):
        mock_get_share_price.side_effect = lambda symbol: {
            "AAPL": 170.00, "TSLA": 250.00
        }.get(symbol.upper(), 0.0)

        account = Account(initial_deposit=1000.00)
        self.assertEqual(account.get_profit_loss(), 0.0) # Portfolio 1000 - Initial 1000 = 0

        account.deposit(500.00) # Balance 1500. Portfolio 1500. P&L = 500
        self.assertEqual(account.get_profit_loss(), 500.00)

        account.buy_shares("AAPL", 2) # Cost 340. Balance 1160. Holdings {"AAPL": 2}
        # Portfolio Value: 1160 (cash) + (2 * 170 = 340) = 1500
        # P&L: 1500 - 1000 = 500
        self.assertEqual(account.get_profit_loss(), 500.00)

        # Simulate price change for profit/loss calculation (need to mock get_share_price dynamically)
        def changing_price_mock(symbol):
            if symbol == "AAPL":
                return 200.00 # Price goes up
            elif symbol == "TSLA":
                return 200.00 # Price goes down
            return 0.0

        mock_get_share_price.side_effect = changing_price_mock

        # Portfolio Value now: 1160 (cash) + (2 * 200 = 400) = 1560
        # P&L: 1560 - 1000 = 560
        self.assertEqual(account.get_portfolio_value(), 1560.00)
        self.assertEqual(account.get_profit_loss(), 560.00)

    @patch('datetime.datetime')
    def test_get_transactions(self, mock_dt):
        fixed_time_initial = datetime.datetime(2023, 1, 6, 9, 0, 0)
        fixed_time_deposit = datetime.datetime(2023, 1, 6, 10, 0, 0)
        fixed_time_buy = datetime.datetime(2023, 1, 6, 11, 0, 0)

        # Initial deposit transaction
        mock_dt.now.return_value = fixed_time_initial
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)
        account = Account(initial_deposit=500.00)
        self.assertEqual(len(account.get_transactions()), 1)
        self.assertEqual(account.get_transactions()[0]["type"], "initial_deposit")
        self.assertEqual(account.get_transactions()[0]["timestamp"], fixed_time_initial.isoformat())

        # Deposit transaction
        mock_dt.now.return_value = fixed_time_deposit
        account.deposit(100.00)
        self.assertEqual(len(account.get_transactions()), 2)
        self.assertEqual(account.get_transactions()[1]["type"], "deposit")
        self.assertEqual(account.get_transactions()[1]["timestamp"], fixed_time_deposit.isoformat())

        # Buy transaction (requires mocking get_share_price)
        with patch('accounts.get_share_price', return_value=10.00):
            mock_dt.now.return_value = fixed_time_buy
            account.buy_shares("XYZ", 10) # 10*10 = 100
        self.assertEqual(len(account.get_transactions()), 3)
        self.assertEqual(account.get_transactions()[2]["type"], "buy")
        self.assertEqual(account.get_transactions()[2]["timestamp"], fixed_time_buy.isoformat())
        self.assertEqual(account.get_transactions()[2]["holdings_after_transaction"], {"XYZ": 10})


        # Test that returning a copy prevents external modification
        transactions_copy = account.get_transactions()
        transactions_copy.append({"fake_transaction": True})
        self.assertEqual(len(account.get_transactions()), 3) # Should still be 3

    def test_get_initial_deposit_amount(self):
        account1 = Account(initial_deposit=500.00)
        self.assertEqual(account1.get_initial_deposit_amount(), 500.00)

        account2 = Account() # Default 0.0
        self.assertEqual(account2.get_initial_deposit_amount(), 0.0)

        account3 = Account(initial_deposit=123.456)
        self.assertEqual(account3.get_initial_deposit_amount(), 123.46) # Test rounding

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

```