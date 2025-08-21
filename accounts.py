
# accounts.py

import datetime
from typing import Dict, List, Any

# --- Helper Function for Share Price Simulation ---

def get_share_price(symbol: str) -> float:
    """
    Simulates fetching the current share price for a given stock symbol.
    For demonstration purposes, this function returns fixed prices for a few
    predefined symbols. In a real-world application, this would query a
    live financial API.

    Args:
        symbol (str): The stock symbol (e.g., "AAPL", "TSLA", "GOOGL").
                      Case-insensitive lookup.

    Returns:
        float: The current price of the share. Returns 0.0 if the symbol
               is unknown or its price cannot be retrieved.
    """
    prices = {
        "AAPL": 170.00,
        "TSLA": 250.00,
        "GOOGL": 140.00,
        "MSFT": 300.00,
        "AMZN": 100.00,
        "NVDA": 500.00,
    }
    return prices.get(symbol.upper(), 0.0)


# --- Account Management System Class ---

class Account:
    """
    Manages a user's trading simulation account, including cash balance,
    stock holdings, and a detailed transaction history. It enforces rules
    to prevent invalid financial operations like negative balances or
    trading non-existent shares.
    """

    def __init__(self, initial_deposit: float = 0.0):
        """
        Initializes a new trading account with an optional initial cash deposit.

        Args:
            initial_deposit (float): The initial cash amount to deposit into the account.
                                     Must be a non-negative value.

        Raises:
            ValueError: If the initial_deposit provided is a negative value.
        """
        if initial_deposit < 0:
            raise ValueError("Initial deposit cannot be negative.")

        self._balance: float = initial_deposit
        self._initial_deposit: float = initial_deposit
        self._holdings: Dict[str, int] = {}  # Stores {symbol: quantity}
        self._transactions: List[Dict[str, Any]] = []  # Chronological list of transaction records

        # Record the initial account setup as a transaction
        if initial_deposit > 0:
            self._record_transaction(
                type="initial_deposit",
                amount=initial_deposit,
                success=True,
                message=f"Account initialized with an initial deposit of {initial_deposit:.2f}.",
            )
        else:
            self._record_transaction(
                type="initial_deposit",
                amount=initial_deposit,
                success=True,
                message="Account initialized with zero initial deposit.",
            )

    def _record_transaction(self, type: str, amount: float, success: bool,
                            symbol: str = None, quantity: int = None,
                            price_per_share: float = None, message: str = "") -> None:
        """
        Internal helper method to record a detailed transaction in the account's history.

        Args:
            type (str): The type of transaction (e.g., "initial_deposit", "deposit",
                        "withdrawal", "buy", "sell").
            amount (float): The cash amount involved in the transaction (e.g., deposit amount,
                            withdrawal amount, total cost/revenue of a trade).
            success (bool): True if the transaction was successful, False otherwise.
            symbol (str, optional): The stock symbol involved in the transaction, if applicable.
                                    Defaults to None.
            quantity (int, optional): The number of shares involved in the transaction, if applicable.
                                      Defaults to None.
            price_per_share (float, optional): The price per share at the time of a trade, if applicable.
                                               Defaults to None.
            message (str, optional): A descriptive message for the transaction, useful for
                                     success confirmations or error details. Defaults to "".
        """
        transaction_record = {
            "type": type,
            "timestamp": datetime.datetime.now().isoformat(),  # Store as ISO 8601 string
            "amount": round(amount, 2),  # Round to two decimal places for currency
            "symbol": symbol,
            "quantity": quantity,
            "price_per_share": round(price_per_share, 2) if price_per_share is not None else None,
            "success": success,
            "message": message,
            "balance_after_transaction": round(self._balance, 2),
            "holdings_after_transaction": dict(self._holdings)  # A snapshot of holdings at this time
        }
        self._transactions.append(transaction_record)

    def deposit(self, amount: float) -> bool:
        """
        Deposits funds into the account.

        Args:
            amount (float): The amount of money to deposit. Must be positive.

        Returns:
            bool: True if the deposit was successful, False otherwise (e.g., invalid amount).
        """
        if amount <= 0:
            self._record_transaction(type="deposit", amount=amount, success=False,
                                     message="Deposit amount must be positive.")
            return False

        self._balance += amount
        self._record_transaction(type="deposit", amount=amount, success=True,
                                 message=f"Deposited {amount:.2f}.")
        return True

    def withdraw(self, amount: float) -> bool:
        """
        Withdraws funds from the account.

        Args:
            amount (float): The amount of money to withdraw. Must be positive.

        Returns:
            bool: True if the withdrawal was successful, False otherwise (e.g., insufficient funds
                  or invalid amount).
        """
        if amount <= 0:
            self._record_transaction(type="withdrawal", amount=amount, success=False,
                                     message="Withdrawal amount must be positive.")
            return False

        if self._balance < amount:
            self._record_transaction(type="withdrawal", amount=amount, success=False,
                                     message=f"Insufficient funds. Current balance: {self._balance:.2f}.")
            return False

        self._balance -= amount
        self._record_transaction(type="withdrawal", amount=amount, success=True,
                                 message=f"Withdrew {amount:.2f}.")
        return True

    def buy_shares(self, symbol: str, quantity: int) -> bool:
        """
        Buys a specified quantity of shares for a given stock symbol.
        Checks for sufficient funds and valid stock price before executing.

        Args:
            symbol (str): The stock symbol (e.g., "AAPL"). Case-insensitive.
            quantity (int): The number of shares to buy. Must be a positive integer.

        Returns:
            bool: True if the purchase was successful, False otherwise.
        """
        symbol = symbol.upper()  # Standardize symbol to uppercase

        if quantity <= 0:
            self._record_transaction(type="buy", symbol=symbol, quantity=quantity, success=False,
                                     message="Buy quantity must be positive.")
            return False

        current_price = get_share_price(symbol)
        if current_price <= 0:
            self._record_transaction(type="buy", symbol=symbol, quantity=quantity, success=False,
                                     message=f"Invalid or unknown symbol '{symbol}'. Price lookup failed or price is zero/negative.")
            return False

        cost = current_price * quantity
        if self._balance < cost:
            self._record_transaction(type="buy", symbol=symbol, quantity=quantity, price_per_share=current_price,
                                     amount=cost, success=False,
                                     message=f"Insufficient funds to buy {quantity} shares of {symbol}. Cost: {cost:.2f}, Balance: {self._balance:.2f}.")
            return False

        self._balance -= cost
        self._holdings[symbol] = self._holdings.get(symbol, 0) + quantity
        self._record_transaction(type="buy", symbol=symbol, quantity=quantity, price_per_share=current_price,
                                 amount=cost, success=True,
                                 message=f"Bought {quantity} shares of {symbol} at {current_price:.2f} each. Total cost: {cost:.2f}.")
        return True

    def sell_shares(self, symbol: str, quantity: int) -> bool:
        """
        Sells a specified quantity of shares for a given stock symbol.
        Checks for sufficient shares in holdings and valid stock price before executing.

        Args:
            symbol (str): The stock symbol (e.g., "AAPL"). Case-insensitive.
            quantity (int): The number of shares to sell. Must be a positive integer.

        Returns:
            bool: True if the sale was successful, False otherwise.
        """
        symbol = symbol.upper()  # Standardize symbol to uppercase

        if quantity <= 0:
            self._record_transaction(type="sell", symbol=symbol, quantity=quantity, success=False,
                                     message="Sell quantity must be positive.")
            return False

        current_shares = self._holdings.get(symbol, 0)
        if current_shares < quantity:
            self._record_transaction(type="sell", symbol=symbol, quantity=quantity, success=False,
                                     message=f"Not enough shares of {symbol} to sell. Have: {current_shares}, Trying to sell: {quantity}.")
            return False

        current_price = get_share_price(symbol)
        if current_price <= 0:
            self._record_transaction(type="sell", symbol=symbol, quantity=quantity, success=False,
                                     message=f"Invalid or unknown symbol '{symbol}'. Price lookup failed or price is zero/negative.")
            return False

        revenue = current_price * quantity
        self._balance += revenue
        self._holdings[symbol] -= quantity
        if self._holdings[symbol] == 0:
            del self._holdings[symbol]  # Remove symbol from holdings if quantity becomes zero

        self._record_transaction(type="sell", symbol=symbol, quantity=quantity, price_per_share=current_price,
                                 amount=revenue, success=True,
                                 message=f"Sold {quantity} shares of {symbol} at {current_price:.2f} each. Total revenue: {revenue:.2f}.")
        return True

    def get_balance(self) -> float:
        """
        Returns the current cash balance of the account.

        Returns:
            float: The current cash balance, rounded to two decimal places.
        """
        return round(self._balance, 2)

    def get_holdings(self) -> Dict[str, int]:
        """
        Returns a dictionary of current stock holdings.

        Returns:
            Dict[str, int]: A copy of the dictionary where keys are stock symbols
                            (e.g., "AAPL") and values are the integer quantity of shares held.
        """
        return dict(self._holdings)  # Return a copy to prevent external modification

    def get_portfolio_value(self) -> float:
        """
        Calculates the total current market value of the entire portfolio,
        which includes the cash balance plus the current market value of all stock holdings.

        Returns:
            float: The total portfolio value, rounded to two decimal places.
        """
        holdings_market_value = 0.0
        for symbol, quantity in self._holdings.items():
            price = get_share_price(symbol)
            if price > 0:  # Only count holdings if price is valid
                holdings_market_value += price * quantity
        return round(self._balance + holdings_market_value, 2)

    def get_profit_loss(self) -> float:
        """
        Calculates the profit or loss of the portfolio relative to the initial deposit.
        Profit/Loss is calculated as: Current Portfolio Value - Initial Deposit.

        Returns:
            float: The calculated profit or loss, rounded to two decimal places.
        """
        return round(self.get_portfolio_value() - self._initial_deposit, 2)

    def get_transactions(self) -> List[Dict[str, Any]]:
        """
        Returns a chronological list of all transactions made in the account's history.

        Returns:
            List[Dict[str, Any]]: A copy of the list containing transaction records. Each record
                                  is a dictionary with details like type, timestamp, amount, etc.
        """
        return list(self._transactions)  # Return a copy to prevent external modification

    def get_initial_deposit_amount(self) -> float:
        """
        Returns the initial deposit amount used to set up the account.

        Returns:
            float: The initial deposit amount, rounded to two decimal places.
        """
        return round(self._initial_deposit, 2)


# --- Example Usage (for testing and demonstration) ---

if __name__ == "__main__":
    print("--- Account Management System Demo ---")

    # 1. Create an account
    print("\n1. Creating a new account with an initial deposit of $1000.")
    my_account = Account(initial_deposit=1000.00)
    print(f"Initial Balance: ${my_account.get_balance():.2f}")
    print(f"Initial Portfolio Value: ${my_account.get_portfolio_value():.2f}")
    print(f"Initial P&L: ${my_account.get_profit_loss():.2f}")

    # 2. Deposit more funds
    print("\n2. Depositing $500.")
    if my_account.deposit(500.00):
        print(f"Deposit successful. New Balance: ${my_account.get_balance():.2f}")
    else:
        print("Deposit failed.")

    # 3. Buy shares
    print("\n3. Buying 5 shares of AAPL.")
    if my_account.buy_shares("AAPL", 5):
        print(f"AAPL purchase successful. New Balance: ${my_account.get_balance():.2f}")
    else:
        print("AAPL purchase failed.")
    print(f"Current Holdings: {my_account.get_holdings()}")

    print("\n4. Buying 10 shares of TSLA.")
    if my_account.buy_shares("TSLA", 10):
        print(f"TSLA purchase successful. New Balance: ${my_account.get_balance():.2f}")
    else:
        print("TSLA purchase failed.")
    print(f"Current Holdings: {my_account.get_holdings()}")

    # 5. Attempt to buy more than affordable
    print("\n5. Attempting to buy 1000 shares of GOOGL (should fail due to insufficient funds).")
    if not my_account.buy_shares("GOOGL", 1000):
        print("GOOGL purchase failed as expected: Insufficient funds.")
    print(f"Current Balance: ${my_account.get_balance():.2f}")

    # 6. Check portfolio value and P&L
    print("\n6. Checking portfolio value and P&L.")
    print(f"Current Balance: ${my_account.get_balance():.2f}")
    print(f"Current Holdings: {my_account.get_holdings()}")
    print(f"Current Portfolio Value: ${my_account.get_portfolio_value():.2f}")
    print(f"Profit/Loss: ${my_account.get_profit_loss():.2f}")

    # 7. Sell shares
    print("\n7. Selling 2 shares of AAPL.")
    if my_account.sell_shares("AAPL", 2):
        print(f"AAPL sale successful. New Balance: ${my_account.get_balance():.2f}")
    else:
        print("AAPL sale failed.")
    print(f"Current Holdings: {my_account.get_holdings()}")

    # 8. Attempt to sell shares not owned
    print("\n8. Attempting to sell 5 shares of GOOGL (should fail as none are owned).")
    if not my_account.sell_shares("GOOGL", 5):
        print("GOOGL sale failed as expected: Not enough shares.")
    print(f"Current Holdings: {my_account.get_holdings()}")

    # 9. Withdraw funds
    print(f"\n9. Attempting to withdraw ${my_account.get_balance() / 2:.2f} (Current Balance: ${my_account.get_balance():.2f}).")
    if my_account.withdraw(my_account.get_balance() / 2):
        print(f"Withdrawal successful. New Balance: ${my_account.get_balance():.2f}")
    else:
        print("Withdrawal failed.")

    print(f"\n10. Attempting to withdraw $2000 (Current Balance: ${my_account.get_balance():.2f}, should fail).")
    if not my_account.withdraw(2000.00):
        print("Withdrawal failed as expected: Insufficient funds.")
    print(f"Current Balance: ${my_account.get_balance():.2f}")

    # 11. Final summary
    print("\n--- Final Account Summary ---")
    print(f"Final Balance: ${my_account.get_balance():.2f}")
    print(f"Final Holdings: {my_account.get_holdings()}")
    print(f"Final Portfolio Value: ${my_account.get_portfolio_value():.2f}")
    print(f"Final Profit/Loss: ${my_account.get_profit_loss():.2f}")
    print(f"Initial Deposit: ${my_account.get_initial_deposit_amount():.2f}")

    # 12. List all transactions
    print("\n--- Transaction History ---")
    for i, tx in enumerate(my_account.get_transactions()):
        print(f"Transaction {i+1}:")
        for k, v in tx.items():
            print(f"  {k}: {v}")
        print("-" * 20)


