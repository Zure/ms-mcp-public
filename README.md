# MCP Servers Collection

This repository contains multiple Model Context Protocol (MCP) servers built with [FastMCP](https://github.com/jlowin/fastmcp), providing various functionalities including authentication, financial data, portfolio management, and data visualization.

## 📦 Available MCP Servers

### 1. Authentication MCP (`auth_mcp`)
**Purpose:** Provides Azure Entra ID authentication for secure user identification and access control.

**Features:**
- Azure Entra ID integration
- OAuth 2.0 authentication flow
- User information retrieval (name, email, job title, office location)

**Tools:**
- `get_user_info` - Fetch authenticated user information from access token

### 2. Finance MCP (`localFinance`)
**Purpose:** Fetch real-time stock quotes and historical price data from Yahoo Finance.

**Features:**
- Real-time stock quotes
- Historical OHLCV (Open, High, Low, Close, Volume) data
- Flexible date range and interval configurations

**Tools:**
- `ping` - Test connectivity
- `get_quote` - Fetch latest quote for a ticker symbol
- `get_history` - Download historical price data with customizable periods/dates

### 3. Portfolio MCP (`PortfolioMcp`)
**Purpose:** Comprehensive investment portfolio management with persistent storage using Azure Cosmos DB.

**Features:**
- Portfolio holdings management (CRUD operations)
- Transaction history tracking
- Watchlist management
- Cash balance tracking
- API key-based authentication
- Azure Cosmos DB integration

**Tools:**
- `add_to_portfolio` - Purchase stocks and add to holdings
- `remove_from_portfolio` - Sell stocks and remove holdings
- `update_position` - Update existing holdings
- `get_holdings` - View all portfolio holdings
- `get_transaction_history` - View transaction history
- `add_to_watchlist` / `remove_from_watchlist` - Manage watchlist
- `get_watchlist` - View watchlist

### 4. Visualization MCP (`vis_mcp`)
**Purpose:** Create various data visualizations including charts, graphs, and plots.

**Features:**
- Multiple chart types (scatter, line, histogram, heatmap, pie)
- Relationship graphs with networkx
- Automatic plot saving and display
- Customizable styling and configurations

**Tools:**
- `create_relationship_graph` - Directed relationship graphs
- `create_scatter_plot` - Scatter plots with labels
- `create_classification_plot` - Category-colored scatter plots
- `create_histogram` - Distribution histograms
- `create_line_plot` - Time series and line charts
- `create_heatmap` - 2D matrix heatmaps
- `create_pie_chart` - Pie charts for proportions

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- pip or uv package manager
- Docker Desktop (for Portfolio MCP only)
- Azure Entra ID credentials (for Auth MCP only)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ms-mcp
```

2. Install dependencies:
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install per server using uv
cd auth_mcp && uv pip install -e .
cd localFinance && uv pip install -e .
cd PortfolioMcp && uv pip install -e .
cd vis_mcp && uv pip install -e .
```

## 🔧 Starting the MCP Servers

### Auth MCP

1. Configure Azure Entra ID credentials in [auth_mcp/main.py](auth_mcp/main.py):
   - `tenant_id`
   - `client_id`
   - `client_secret`

2. Start the server:
```bash
cd auth_mcp
python main.py
```

The server runs on HTTP at `http://localhost:8010`

### Finance MCP

```bash
cd localFinance
python main.py
```

The server runs using stdio transport (standard input/output for MCP communication).

### Portfolio MCP

1. Start Azure Cosmos DB Emulator:
```bash
cd PortfolioMcp
docker-compose up -d
```

Wait for the Cosmos DB emulator to be healthy (takes ~60 seconds).

2. Configure environment variables (create `.env` file in `PortfolioMcp/`):
```env
# Database Configuration
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOS_DATABASE_NAME=portfolio_db

# Authentication
API_KEY=your-secure-api-key-here

# Logging
LOG_LEVEL=INFO
```

3. Start the server:
```bash
cd PortfolioMcp
python server.py
```

The server initializes database containers and repositories on first run.

### Visualization MCP

```bash
cd vis_mcp
python server.py
```

The server runs using stdio transport. Generated plots are saved to the system temp directory and automatically opened.

## 📝 MCP Client Configuration

### VS Code MCP Configuration

Add to your `.vscode/mcp.json` or MCP client settings:

**Windows:**
```json
{
  "mcpServers": {
    "mslab/auth": {
      "command": "${workspaceFolder}/auth_mcp/.venv/Scripts/python.exe",
      "args": ["main.py"],
      "cwd": "${workspaceFolder}/auth_mcp",
      "transport": "http",
    },
    "mslab/finance": {
      "command": "${workspaceFolder}/localFinance/.venv/Scripts/python.exe",
      "args": ["main.py"],
      "cwd": "${workspaceFolder}/localFinance"
    },
    "mslab/portfolio": {
      "command": "${workspaceFolder}/PortfolioMcp/.venv/Scripts/python.exe",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/PortfolioMcp",
      "env": {
        "API_KEY": "your-secure-api-key-here"
      }
    },
    "mslab/visualization": {
      "command": "${workspaceFolder}/vis_mcp/.venv/Scripts/python.exe",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/vis_mcp"
    }
  }
}
```

**Linux/macOS:**
```json
{
  "mcpServers": {
    "mslab/auth": {
      "command": "${workspaceFolder}/auth_mcp/.venv/bin/python",
      "args": ["main.py"],
      "cwd": "${workspaceFolder}/auth_mcp",
      "transport": "http",
    },
    "mslab/finance": {
      "command": "${workspaceFolder}/localFinance/.venv/bin/python",
      "args": ["main.py"],
      "cwd": "${workspaceFolder}/localFinance"
    },
    "mslab/portfolio": {
      "command": "${workspaceFolder}/PortfolioMcp/.venv/bin/python",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/PortfolioMcp",
      "env": {
        "API_KEY": "your-secure-api-key-here"
      }
    },
    "mslab/visualization": {
      "command": "${workspaceFolder}/vis_mcp/.venv/bin/python",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/vis_mcp"
    }
  }
}
```

> **Note:** The `${workspaceFolder}` variable automatically resolves to your workspace root directory. Make sure each server has its own `.venv` directory with dependencies installed.

### Setting Up Virtual Environments

Create and configure virtual environments for each server:

**Windows:**
```powershell
# Navigate to each server directory and set up venv
cd auth_mcp
python -m venv .venv
.venv\Scripts\activate
pip install -e .
deactivate

cd ../localFinance
python -m venv .venv
.venv\Scripts\activate
pip install -e .
deactivate

cd ../PortfolioMcp
python -m venv .venv
.venv\Scripts\activate
pip install -e .
deactivate

cd ../vis_mcp
python -m venv .venv
.venv\Scripts\activate
pip install -e .
deactivate
```

**Linux/macOS:**
```bash
# Navigate to each server directory and set up venv
cd auth_mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
deactivate

cd ../localFinance
python -m venv .venv
source .venv/bin/activate
pip install -e .
deactivate

cd ../PortfolioMcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
deactivate

cd ../vis_mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
deactivate
```

## 🗂️ Project Structure

```
ms-mcp/
├── README.md                      # This file
├── requirements.txt               # All dependencies
├── auth_mcp/                      # Authentication MCP
│   ├── main.py                    # Server entry point
│   └── pyproject.toml             # Project metadata
├── localFinance/                  # Finance data MCP
│   ├── main.py                    # Server entry point
│   ├── finance_tools.py           # Yahoo Finance integration
│   ├── pyproject.toml             # Project metadata
│   └── requirements.txt           # Dependencies
├── PortfolioMcp/                  # Portfolio management MCP
│   ├── server.py                  # Server entry point
│   ├── docker-compose.yml         # Cosmos DB emulator
│   ├── pyproject.toml             # Project metadata
│   ├── config/                    # Configuration modules
│   ├── database/                  # Database layer
│   ├── models/                    # Domain models
│   ├── services/                  # Business logic
│   └── tools/                     # MCP tools
└── vis_mcp/                       # Visualization MCP
    ├── server.py                  # Server entry point
    ├── config.py                  # Plot styling
    ├── plot_utils.py              # Utilities
    ├── pyproject.toml             # Project metadata
    ├── README.md                  # Detailed docs
    └── tools/                     # Visualization tools
```

## 🔒 Security Notes

- **Auth MCP:** Never commit Azure credentials to version control. Use environment variables or secure secret management.
- **Portfolio MCP:** Change the default API key before production use. The Cosmos DB emulator key is for development only.
- **All MCPs:** Run in trusted environments when exposing sensitive financial or user data.

## 🧪 Testing

Test each server's connectivity:

```bash
# Finance MCP
curl -X POST http://localhost:<port> -d '{"tool": "ping"}'

# Portfolio MCP (with API key)
curl -H "Authorization: Bearer your-api-key" http://localhost:<port>
```

## 📚 Dependencies

- **fastmcp** - MCP server framework
- **yfinance** - Yahoo Finance data
- **azure-cosmos** - Azure Cosmos DB client
- **matplotlib, networkx, plotly** - Visualization libraries
- **uvicorn** - ASGI server
- **pydantic** - Data validation

## 🤝 Contributing

Each MCP server is designed to be modular and independent. Feel free to:
- Add new tools to existing servers
- Create additional MCP servers
- Enhance authentication and security
- Improve data persistence and caching

## 📄 License

[Specify your license here]

## 🔗 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Azure Cosmos DB](https://docs.microsoft.com/azure/cosmos-db/)
- [Yahoo Finance API (yfinance)](https://github.com/ranaroussi/yfinance)
