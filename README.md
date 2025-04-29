
Built by https://www.blackbox.ai

---

```markdown
# Future MT5 Pro Trading

## Project Overview
The Future MT5 Pro Trading application is a multi-asset trading system built using MetaTrader 5 for algorithmic trading. It utilizes various trading strategies, including trend analysis and risk management, to automate trading decisions. The application provides a graphical user interface (GUI) using Tkinter, allowing users to configure assets, manage trades, and monitor system logs seamlessly.

## Installation
To set up the Future MT5 Pro Trading application, follow these steps:

1. **Prerequisites**:
   - Ensure you have Python 3.6 or above installed on your machine.
   - Install the MetaTrader 5 terminal and create a trading account.
   - Install required libraries via pip.

2. **Clone the Repository**:
   ```bash
   git clone https://your-repo-url.git
   cd your-repo-directory
   ```

3. **Install Dependencies**:
   Install the necessary Python packages using the following command:
   ```bash
   pip install MetaTrader5 pandas numpy
   ```

4. **Run the Application**:
   Before running the application, make sure to configure your MetaTrader 5 login credentials in `utils.py` (optional step for saved login). Then, start the application by executing:
   ```bash
   python painel.py
   ```

## Usage
Once the application is running, you can interact with the GUI to select trading assets, set parameters such as the timeframe and lot size, and start or stop the trading robot for each asset. The logs will display real-time updates and status messages.

### Starting a Trade
1. Select the desired asset from the dropdown menu.
2. Choose the timeframe (e.g., M1, M5, H1).
3. Input desired lot size.
4. Click the "▶ Iniciar Robô" button to start trading.

### Monitoring
Keep an eye on the log section to view status updates, error messages, and trade results.

## Features
- **Multi-Asset Trading**: Supports multiple assets simultaneously with individual configuration.
- **Real-Time Logs**: Displays system activity and trade results in real-time.
- **User-Friendly Interface**: Intuitive GUI with controls for each asset and global controls.
- **Risk Management**: Implements strategies to manage daily losses and maximum position limits.

## Dependencies
The application utilizes the following main dependencies, as noted in the `requirements.txt` (or relevant package.json):
- `MetaTrader5`
- `pandas`
- `numpy`
- `tkinter` (comes built-in with Python)

```json
{
  "dependencies": {
    "MetaTrader5": "^5.0",
    "pandas": "^1.3",
    "numpy": "^1.21"
  }
}
```

## Project Structure
The project is organized into several files:

- `estrategia.py`: Contains the trading strategy logic, including indicators and order execution.
- `painel.py`: Implements the graphical user interface to interact with users.
- `painel_multi.py`: Supports managing multiple trading assets simultaneously.
- `log_system.py`: Manages logging for trade actions and system messages.
- `utils.py`: Contains utility functions for account management and performance analysis.
- `plan.md`: A document outlining enhancement plans for the trading system.

## Contribution
Contributions to the project are welcome! To contribute, please fork the repository, create a new branch, and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for more information.

---

**Note**: Always ensure that you have a clear understanding of the risks associated with trading and that you comply with local regulations regarding algorithmic trading.
```