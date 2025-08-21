import gradio as gr
import accounts # Import the backend class

# --- Helper functions for Gradio UI logic ---

def get_account_summary(account: accounts.Account):
    """Retrieves and formats account summary data for UI display."""
    if account is None:
        return "N/A", "N/A", "N/A", "N/A"
    
    balance = account.get_balance()
    holdings = account.get_holdings()
    portfolio_value = account.get_portfolio_value()
    profit_loss = account.get_profit_loss()

    holdings_str = ""
    if holdings:
        # Sort holdings for consistent display
        sorted_holdings = sorted(holdings.items())
        holdings_str = "\n".join([f"{symbol}: {qty} shares" for symbol, qty in sorted_holdings])
    else:
        holdings_str = "No shares held."
    
    return f"${balance:.2f}", holdings_str, f"${portfolio_value:.2f}", f"${profit_loss:.2f}"

def get_transactions_ui(account: accounts.Account):
    """Retrieves and formats transaction history for UI display (Gradio Dataframe)."""
    if account is None:
        return [] # Return empty list for an empty dataframe
    
    transactions = account.get_transactions()
    if not transactions:
        return []

    data = []
    # Note: `headers` are defined directly in gr.Dataframe component
    for tx in transactions:
        holdings_after_str = ""
        if tx.get('holdings_after_transaction'):
            # Sort holdings for consistent display in the transaction log
            sorted_tx_holdings = sorted(tx['holdings_after_transaction'].items())
            holdings_after_str = ", ".join([f"{s}:{q}" for s, q in sorted_tx_holdings])
        else:
            holdings_after_str = "N/A"

        row = [
            tx.get("timestamp", "N/A"),
            tx.get("type", "N/A"),
            tx.get("symbol", "N/A"),
            tx.get("quantity", "N/A"),
            f"${tx['price_per_share']:.2f}" if tx.get("price_per_share") is not None else "N/A",
            f"${tx['amount']:.2f}" if tx.get("amount") is not None else "N/A",
            "Yes" if tx.get("success") else "No",
            tx.get("message", ""),
            f"${tx['balance_after_transaction']:.2f}" if tx.get("balance_after_transaction") is not None else "N/A",
            holdings_after_str
        ]
        data.append(row)
    
    return data

def refresh_ui_state(account: accounts.Account):
    """Refreshes all display outputs and section visibilities based on current account state."""
    balance, holdings_str, portfolio_value, profit_loss = get_account_summary(account)
    transactions_data = get_transactions_ui(account)
    
    if account is None:
        # Hide main sections if no account is created
        return (
            balance, holdings_str, portfolio_value, profit_loss, transactions_data,
            gr.update(visible=False), # summary_section
            gr.update(visible=False), # cash_management_section
            gr.update(visible=False), # stock_trading_section
            gr.update(visible=False)  # transaction_history_section
        )
    else:
        # Show main sections if an account exists
        return (
            balance, holdings_str, portfolio_value, profit_loss, transactions_data,
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True)
        )

# --- Backend action wrappers for Gradio ---

def create_account_action(account: accounts.Account, initial_deposit: float):
    """
    Attempts to create a new account.
    Returns: (updated_account_object, status_message)
    """
    if account is not None:
        return account, "Account already created! Please reset the demo if you wish to start fresh."
    try:
        new_account = accounts.Account(initial_deposit=initial_deposit)
        return new_account, f"Account created successfully with initial deposit: ${initial_deposit:.2f}"
    except ValueError as e:
        # If account creation fails, explicitly return None for the account state
        return None, f"Error creating account: {e}"

def deposit_funds_action(account: accounts.Account, amount: float):
    """Deposits funds and returns updated account state and status message."""
    if account is None:
        return account, "Please create an account first."
    success = account.deposit(amount)
    return account, f"Deposit successful: ${amount:.2f}" if success else f"Deposit failed. Amount must be positive. (Attempted: ${amount:.2f})"

def withdraw_funds_action(account: accounts.Account, amount: float):
    """Withdraws funds and returns updated account state and status message."""
    if account is None:
        return account, "Please create an account first."
    success = account.withdraw(amount)
    if success:
        return account, f"Withdrawal successful: ${amount:.2f}"
    else:
        current_balance = account.get_balance()
        return account, f"Withdrawal failed. Insufficient funds or invalid amount. Current Balance: ${current_balance:.2f}. (Attempted: ${amount:.2f})"

def buy_shares_action(account: accounts.Account, symbol: str, quantity: int):
    """Buys shares and returns updated account state and status message."""
    if account is None:
        return account, "Please create an account first."
    success = account.buy_shares(symbol, quantity)
    if success:
        current_price = accounts.get_share_price(symbol)
        total_cost = current_price * quantity
        return account, f"Bought {quantity} shares of {symbol.upper()} at ${current_price:.2f} each. Total cost: ${total_cost:.2f}."
    else:
        # The backend provides detailed error messages which are captured in the transaction log.
        # Here, we give a general message for the UI.
        return account, f"Failed to buy {quantity} shares of {symbol.upper()}. Check funds, symbol, and quantity."

def sell_shares_action(account: accounts.Account, symbol: str, quantity: int):
    """Sells shares and returns updated account state and status message."""
    if account is None:
        return account, "Please create an account first."
    success = account.sell_shares(symbol, quantity)
    if success:
        current_price = accounts.get_share_price(symbol)
        total_revenue = current_price * quantity
        return account, f"Sold {quantity} shares of {symbol.upper()} at ${current_price:.2f} each. Total revenue: ${total_revenue:.2f}."
    else:
        # The backend provides detailed error messages which are captured in the transaction log.
        # Here, we give a general message for the UI.
        return account, f"Failed to sell {quantity} shares of {symbol.upper()}. Check holdings, symbol, and quantity."

# --- Gradio UI Definition ---

with gr.Blocks(title="Trading Account Simulator") as demo:
    gr.Markdown("# Simple Trading Account Simulator")
    gr.Markdown("A prototype UI to demonstrate the `Account` backend. Available Symbols (Fixed Prices): AAPL ($170), TSLA ($250), GOOGL ($140), MSFT ($300), AMZN ($100), NVDA ($500).")

    # State variable to hold the Account object, initialized to None
    account_state = gr.State(None)

    # Output for status messages
    status_output = gr.Textbox(label="Status / Messages", interactive=False, value="Welcome! Please create an account.", lines=2)

    with gr.Accordion("1. Account Setup", open=True) as account_setup_section:
        with gr.Row():
            initial_deposit_input = gr.Number(label="Initial Deposit Amount", value=1000.00, minimum=0)
            create_account_btn = gr.Button("Create Account", variant="primary")

    # Outputs for Account Summary section
    with gr.Accordion("2. Account Summary", open=True, visible=False) as summary_section:
        with gr.Row():
            current_balance_output = gr.Textbox(label="Current Balance", interactive=False)
            portfolio_value_output = gr.Textbox(label="Total Portfolio Value", interactive=False)
            profit_loss_output = gr.Textbox(label="Profit/Loss", interactive=False)
        holdings_output = gr.Textbox(label="Current Holdings", interactive=False, lines=3)

    # Inputs/Outputs for Cash Management section
    with gr.Accordion("3. Cash Management", open=False, visible=False) as cash_management_section:
        with gr.Row():
            deposit_amount = gr.Number(label="Deposit Amount", minimum=0.01, value=100.00)
            deposit_btn = gr.Button("Deposit", variant="secondary")
        with gr.Row():
            withdraw_amount = gr.Number(label="Withdraw Amount", minimum=0.01, value=50.00)
            withdraw_btn = gr.Button("Withdraw", variant="secondary")

    # Inputs/Outputs for Stock Trading section
    with gr.Accordion("4. Stock Trading", open=False, visible=False) as stock_trading_section:
        with gr.Row():
            buy_symbol = gr.Textbox(label="Buy Symbol (e.g., AAPL)", placeholder="AAPL")
            buy_quantity = gr.Number(label="Quantity", minimum=1, step=1, value=1)
            buy_btn = gr.Button("Buy Shares", variant="secondary")
        with gr.Row():
            sell_symbol = gr.Textbox(label="Sell Symbol (e.g., AAPL)", placeholder="AAPL")
            sell_quantity = gr.Number(label="Quantity", minimum=1, step=1, value=1)
            sell_btn = gr.Button("Sell Shares", variant="secondary")

    # Output for Transaction History section
    with gr.Accordion("5. Transaction History", open=False, visible=False) as transaction_history_section:
        transactions_output = gr.Dataframe(
            label="Transaction Log",
            headers=[
                "Timestamp", "Type", "Symbol", "Quantity",
                "Price/Share", "Amount ($)", "Success", "Message",
                "Balance After", "Holdings After"
            ],
            wrap=True,
            row_count=(5, "dynamic"), # Show at least 5 rows, dynamic if more
            col_count=(10, "fixed"), # Fixed number of columns
            interactive=False # Users cannot edit this table
        )

    # --- Gradio Event Handlers ---

    # Define common outputs for UI refresh after most actions
    refresh_outputs = [
        current_balance_output, holdings_output, portfolio_value_output, profit_loss_output, transactions_output,
        summary_section, cash_management_section, stock_trading_section, transaction_history_section
    ]

    # Create Account button click event
    create_account_btn.click(
        fn=create_account_action,
        inputs=[account_state, initial_deposit_input],
        outputs=[account_state, status_output]
    ).then(
        fn=refresh_ui_state,
        inputs=[account_state],
        outputs=refresh_outputs
    )

    # Deposit Funds button click event
    deposit_btn.click(
        fn=deposit_funds_action,
        inputs=[account_state, deposit_amount],
        outputs=[account_state, status_output]
    ).then(
        fn=refresh_ui_state,
        inputs=[account_state],
        outputs=refresh_outputs
    )

    # Withdraw Funds button click event
    withdraw_btn.click(
        fn=withdraw_funds_action,
        inputs=[account_state, withdraw_amount],
        outputs=[account_state, status_output]
    ).then(
        fn=refresh_ui_state,
        inputs=[account_state],
        outputs=refresh_outputs
    )

    # Buy Shares button click event
    buy_btn.click(
        fn=buy_shares_action,
        inputs=[account_state, buy_symbol, buy_quantity],
        outputs=[account_state, status_output]
    ).then(
        fn=refresh_ui_state,
        inputs=[account_state],
        outputs=refresh_outputs
    )

    # Sell Shares button click event
    sell_btn.click(
        fn=sell_shares_action,
        inputs=[account_state, sell_symbol, sell_quantity],
        outputs=[account_state, status_output]
    ).then(
        fn=refresh_ui_state,
        inputs=[account_state],
        outputs=refresh_outputs
    )

# Launch the Gradio application
if __name__ == "__main__":
    demo.launch(share=True)