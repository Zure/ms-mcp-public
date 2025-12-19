# Part 2: Portfolio MCP - Implementation Plan

## Overview
A persistence-focused MCP server for managing investment portfolios, watchlists, and holdings tracking. This server demonstrates stateful operations, data persistence, and cross-server resource exposure for composition with the Market Data MCP (Part 1).

## Educational Goals
- Introduce stateful MCP operations (CRUD patterns)
- Demonstrate data persistence strategies (file-based, SQLite, or JSON)
- Show how MCP servers expose persistent data as resources
- Teach transaction patterns and data consistency
- Prepare for multi-server composition (Part 3)
- Illustrate separation of concerns: data vs computation

---

## Core Concepts

### What This Server DOES
✅ Store and manage portfolio holdings
✅ Track positions (ticker, quantity, purchase price, purchase date)
✅ Manage multiple watchlists (custom categories)
✅ Calculate portfolio totals and position values
✅ Provide historical transaction log
✅ Expose portfolio data as resources for other MCPs

### What This Server DOES NOT Do
❌ Fetch real-time stock prices (that's Part 1's job)
❌ Perform stock analysis (that's Part 1's job)
❌ Execute actual trades (educational tool only)
❌ Handle real money or brokerage connections

---

## Architecture Decisions

### Data Persistence Layer
**Options:**
1. **JSON Files** (Recommended for Education)
   - Simple, human-readable
   - Easy to inspect and debug
   - Version control friendly
   - Good for demos and learning

2. **SQLite** (Alternative)
   - More robust
   - Query capabilities
   - Better for larger datasets
   - Good for teaching database concepts

3. **In-Memory with Serialization** (Simplest)
   - Dict-based storage
   - Pickle/JSON dump on shutdown
   - Fastest but less durable

**Decision:** Use **JSON files** for transparency and educational value

### File Structure
```
portfolio_data/
├── holdings.json          # Current positions
├── transactions.json      # Historical trades
├── watchlists.json       # Custom watchlists
└── metadata.json         # Portfolio settings
```

### Data Models

#### Holdings Schema
```json
{
  "holdings": [
    {
      "id": "uuid-string",
      "ticker": "AAPL",
      "quantity": 10,
      "purchase_price": 150.00,
      "purchase_date": "2024-01-15",
      "notes": "Tech diversification"
    }
  ],
  "cash_balance": 10000.00,
  "last_updated": "2024-12-11T10:30:00Z"
}
```

#### Transaction Schema
```json
{
  "transactions": [
    {
      "id": "uuid-string",
      "type": "BUY",
      "ticker": "AAPL",
      "quantity": 10,
      "price": 150.00,
      "total": 1500.00,
      "date": "2024-01-15",
      "notes": "Initial position"
    }
  ]
}
```

#### Watchlist Schema
```json
{
  "watchlists": {
    "tech": {
      "name": "Technology Stocks",
      "tickers": ["AAPL", "GOOGL", "MSFT", "NVDA"],
      "created": "2024-01-01",
      "notes": "Major tech companies to monitor"
    },
    "value": {
      "name": "Value Plays",
      "tickers": ["BRK-B", "JNJ", "PG"],
      "created": "2024-01-01",
      "notes": "Undervalued dividend stocks"
    }
  }
}
```

---

## Phase 1: Core Data Layer

### Setup & Infrastructure
1. **File I/O Module:**
   - `load_data(filename)` - Read JSON with error handling
   - `save_data(filename, data)` - Write JSON with atomic operations
   - `ensure_data_dir()` - Create directory if missing
   - `initialize_empty_files()` - Create default schemas

2. **Data Validation:**
   - Ticker format validation (uppercase, valid characters)
   - Quantity validation (positive numbers)
   - Price validation (positive floats)
   - Date validation (ISO format)
   - UUID generation for records

3. **Error Handling:**
   - File corruption recovery
   - Concurrent access protection (file locking)
   - Validation error messages
   - Rollback on failed operations

---

## Phase 2: Portfolio Management Tools

### Tool 1: Add to Portfolio
**Name:** `add_to_portfolio`

**Signature:**
```python
add_to_portfolio(
    ticker: str,
    quantity: int,
    purchase_price: float,
    purchase_date: str | None = None,  # Default to today
    notes: str = ""
) -> dict
```

**Behavior:**
1. Validate all inputs
2. Generate unique ID for position
3. Add to holdings.json
4. Record transaction in transactions.json
5. Deduct from cash_balance (quantity × price)
6. Return confirmation with position details

**Educational Points:**
- CRUD operation (Create)
- Transaction atomicity
- Data validation
- State mutation

### Tool 2: Remove from Portfolio
**Name:** `remove_from_portfolio`

**Signature:**
```python
remove_from_portfolio(
    position_id: str,
    quantity: int | None = None  # None = remove entire position
) -> dict
```

**Behavior:**
1. Find position by ID
2. If partial removal, update quantity
3. If full removal, delete position
4. Record SELL transaction
5. Add to cash_balance
6. Return confirmation with proceeds

**Educational Points:**
- CRUD operation (Delete/Update)
- Partial vs full operations
- Cash flow tracking

### Tool 3: Update Position
**Name:** `update_position`

**Signature:**
```python
update_position(
    position_id: str,
    notes: str | None = None,
    # Could add: adjust cost basis, etc.
) -> dict
```

**Behavior:**
1. Find position by ID
2. Update specified fields
3. Preserve other fields
4. Update last_updated timestamp
5. Return updated position

**Educational Points:**
- CRUD operation (Update)
- Partial updates
- Data integrity

### Tool 4: Get Holdings
**Name:** `get_holdings`

**Signature:**
```python
get_holdings(
    filter_ticker: str | None = None,
    include_totals: bool = True
) -> dict
```

**Behavior:**
1. Read holdings.json
2. Optionally filter by ticker
3. Optionally calculate totals:
   - Total invested (cost basis)
   - Total quantity per ticker
   - Cash balance
4. Return structured data

**Educational Points:**
- CRUD operation (Read)
- Filtering and aggregation
- Read-only operations (safe)

### Tool 5: Get Transaction History
**Name:** `get_transaction_history`

**Signature:**
```python
get_transaction_history(
    ticker: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    transaction_type: str | None = None  # "BUY", "SELL", or None
) -> list[dict]
```

**Behavior:**
1. Read transactions.json
2. Apply filters
3. Sort by date (newest first)
4. Return matched transactions

**Educational Points:**
- Query patterns
- Date range filtering
- Historical data access

---

## Phase 3: Watchlist Management Tools

### Tool 6: Create Watchlist
**Name:** `create_watchlist`

**Signature:**
```python
create_watchlist(
    name: str,
    tickers: list[str] = [],
    notes: str = ""
) -> dict
```

**Behavior:**
1. Generate watchlist ID (slug from name)
2. Validate tickers format
3. Add to watchlists.json
4. Return watchlist details

**Educational Points:**
- Collection management
- List operations
- Naming conventions

### Tool 7: Add to Watchlist
**Name:** `add_to_watchlist`

**Signature:**
```python
add_to_watchlist(
    watchlist_id: str,
    ticker: str
) -> dict
```

**Behavior:**
1. Find watchlist
2. Check if ticker already exists
3. Add ticker to list
4. Save and return updated watchlist

**Educational Points:**
- Append operations
- Duplicate prevention
- Incremental updates

### Tool 8: Remove from Watchlist
**Name:** `remove_from_watchlist`

**Signature:**
```python
remove_from_watchlist(
    watchlist_id: str,
    ticker: str
) -> dict
```

**Behavior:**
1. Find watchlist
2. Remove ticker if exists
3. Save and return updated watchlist

### Tool 9: Get Watchlists
**Name:** `get_watchlists`

**Signature:**
```python
get_watchlists(
    watchlist_id: str | None = None  # None = all watchlists
) -> dict
```

**Behavior:**
1. Read watchlists.json
2. Return all or specific watchlist
3. Include metadata (created date, count)

---

## Phase 4: Resources (Cross-Server Integration)

### Resource 1: Portfolio Holdings Summary
**URI:** `portfolio://holdings/summary`

**Purpose:** Expose current holdings for Market Data MCP to reference

**Returns:**
```json
{
  "tickers": ["AAPL", "GOOGL", "MSFT"],
  "positions_count": 3,
  "total_invested": 45000.00,
  "cash_balance": 10000.00,
  "last_updated": "2024-12-11T10:30:00Z"
}
```

**Educational Points:**
- **CRITICAL:** Shows how to expose persistent data as resources
- Cross-server data sharing pattern
- Read-only resource from stateful data
- Foundation for Part 3 composition

### Resource 2: Portfolio Holdings Detail
**URI:** `portfolio://holdings/detail`

**Purpose:** Full holdings data including cost basis

**Returns:** Complete holdings.json content (formatted)

**Educational Points:**
- Detailed vs summary resources
- Different granularity levels
- Security consideration: what to expose

### Resource 3: Specific Watchlist
**URI:** `portfolio://watchlist/{watchlist_id}`

**Purpose:** Access specific watchlist contents

**Returns:**
```json
{
  "name": "Technology Stocks",
  "tickers": ["AAPL", "GOOGL", "MSFT", "NVDA"],
  "count": 4,
  "created": "2024-01-01",
  "notes": "Major tech companies to monitor"
}
```

**Educational Points:**
- URI templating with parameters
- Resource discovery
- Dynamic resource generation

### Resource 4: All Watchlists Index
**URI:** `portfolio://watchlists/index`

**Purpose:** List all available watchlists

**Returns:** Array of watchlist summaries

**Educational Points:**
- Index/catalog pattern
- Resource navigation
- Metadata exposure

### Resource 5: Transaction Log
**URI:** `portfolio://transactions/recent`

**Purpose:** Recent transaction history (last 10)

**Returns:** Array of recent transactions

**Educational Points:**
- Time-based resources
- Audit trail pattern
- Historical data access

---

## Phase 5: Prompts (Portfolio Analysis)

### Prompt 1: Portfolio Analysis
**Name:** `analyze_portfolio`

**Parameters:**
- `include_suggestions: bool` (default: True)
- `focus: str` (default: "general", options: "diversification", "risk", "performance")

**Purpose:** Generate comprehensive portfolio analysis request

**Prompt Content:**
1. Current holdings summary
2. Sector/industry breakdown (requires Part 1 data)
3. Analysis request:
   - Diversification assessment
   - Risk concentration
   - Rebalancing suggestions
   - Missing sectors/opportunities

**Educational Points:**
- Stateful prompt (uses portfolio data)
- Cross-server coordination hint
- Multi-step analysis workflow

### Prompt 2: Rebalancing Suggestions
**Name:** `suggest_rebalancing`

**Parameters:**
- `target_allocation: dict[str, float]` (sector percentages)

**Purpose:** Generate rebalancing recommendations

**Prompt Content:**
1. Current portfolio allocation
2. Target allocation
3. Request specific buy/sell actions to reach target

**Educational Points:**
- Goal-oriented prompts
- Calculation guidance for AI
- Actionable output

### Prompt 3: Position Review
**Name:** `review_position`

**Parameters:**
- `ticker: str`

**Purpose:** Analyze a specific existing position

**Prompt Content:**
1. Position details (quantity, cost basis, duration held)
2. Request review:
   - Hold/sell recommendation
   - Performance vs purchase price (needs Part 1)
   - Position sizing appropriateness

**Educational Points:**
- Single-position focus
- Historical data usage
- Decision support

---

## Phase 6: Advanced Features

### Tool 10: Calculate Portfolio Value
**Name:** `calculate_portfolio_value`

**Signature:**
```python
calculate_portfolio_value() -> dict
```

**Behavior:**
1. Read current holdings
2. **Call Market Data MCP** to get current prices
3. Calculate:
   - Current market value per position
   - Total portfolio value
   - Gain/loss per position
   - Total gain/loss
   - Portfolio return percentage
4. Return comprehensive valuation

**Educational Points:**
- **CRITICAL:** Cross-server tool invocation
- Demonstrates MCP client usage within MCP server
- Data enrichment pattern
- Real-time calculation

**Implementation Note:**
This requires the Portfolio MCP to act as a **client** to the Market Data MCP:
```python
from fastmcp import Client

async def calculate_portfolio_value():
    # Load holdings
    holdings = load_holdings()
    
    # Connect to Market Data MCP
    market_client = Client({...})
    
    async with market_client:
        for holding in holdings:
            # Call market data tool
            price_data = await market_client.call_tool(
                "get_stock_price",
                {"ticker": holding["ticker"]}
            )
            # Calculate values...
```

### Tool 11: Export Portfolio
**Name:** `export_portfolio`

**Signature:**
```python
export_portfolio(
    format: str = "json"  # Future: "csv", "xlsx"
) -> str
```

**Behavior:**
1. Gather all portfolio data
2. Format according to requested format
3. Return formatted data or file path

**Educational Points:**
- Data serialization
- Multiple output formats
- Portability

### Tool 12: Import Transactions
**Name:** `import_transactions`

**Signature:**
```python
import_transactions(
    data: list[dict]
) -> dict
```

**Behavior:**
1. Validate transaction format
2. Process each transaction
3. Update holdings and transaction log
4. Return summary of imported data

**Educational Points:**
- Batch operations
- Data migration patterns
- Validation at scale

---

## Phase 7: Documentation & Testing

### Documentation Requirements
1. **README:**
   - Purpose: "Portfolio persistence layer for MCP investment tools"
   - Separation from Market Data MCP
   - How it integrates with Part 1
   - Data storage location and format
   - Backup recommendations

2. **Code Documentation:**
   - Every tool with examples
   - Data schema documentation
   - Error handling patterns
   - Thread safety notes

3. **Integration Guide:**
   - How to configure both MCPs in Claude Desktop
   - Example multi-server workflows
   - Resource reference patterns

### Testing Checklist
1. **Data Persistence:**
   - Create/read/update/delete operations
   - File corruption scenarios
   - Concurrent access (if applicable)
   - Data migration/versioning

2. **Validation:**
   - Invalid ticker formats
   - Negative quantities
   - Invalid dates
   - Missing required fields

3. **Cross-Server:**
   - Resource accessibility
   - Data format compatibility
   - Error propagation

---

## Phase 8: Preparation for Part 3 Integration

### Server Composition Patterns
Document how this server will be used in Part 3:

1. **Client-Side Composition:**
   ```json
   {
     "mcpServers": {
       "market-data": {...},
       "portfolio": {...}
     }
   }
   ```

2. **Server-Side Composition:**
   - Portfolio MCP mounts Market Data MCP
   - Or vice versa
   - Demonstrate both patterns

### Cross-Server Workflow Examples
1. **Add stock after analysis:**
   - User: "Should I buy AAPL?"
   - Claude calls `market-data_analyze_stock_for_investment("AAPL")`
   - Claude calls `portfolio_get_holdings()` to check existing
   - Claude recommends
   - User: "Yes, buy 10 shares"
   - Claude calls `portfolio_add_to_portfolio("AAPL", 10, 150.00)`

2. **Portfolio review:**
   - User: "How's my portfolio doing?"
   - Claude calls `portfolio_calculate_portfolio_value()`
   - Claude calls `market-data_analyze_stock_for_investment()` for each holding
   - Claude summarizes

---

## Technical Implementation Notes

### Data Consistency
1. **Atomic Operations:**
   - Write to temp file, then rename (atomic on most filesystems)
   - Transaction log before updating holdings
   - Rollback mechanism on errors

2. **Validation:**
   - Pre-validate before any file writes
   - Consistent validation rules across tools
   - Clear error messages

3. **Concurrency:**
   - File locking if needed
   - Or document single-user limitation
   - Future: Use SQLite for better concurrency

### Security Considerations
1. **No real money:** Clear disclaimers
2. **Data privacy:** Local storage only
3. **Input sanitization:** Prevent path traversal, injection
4. **Resource exposure:** What data to make public via resources

### Performance
1. **Caching:** Keep loaded data in memory during session
2. **Lazy loading:** Only load what's needed
3. **Batch operations:** Efficient multi-ticker operations

---

## Success Criteria

### Functional Requirements
- ✅ CRUD operations work correctly
- ✅ Data persists across server restarts
- ✅ All resources are accessible
- ✅ No data corruption scenarios
- ✅ Works with Claude Desktop

### Educational Requirements
- ✅ Clear demonstration of stateful MCP server
- ✅ Shows data persistence patterns
- ✅ Illustrates cross-server resource exposure
- ✅ Prepares for Part 3 composition
- ✅ Well-documented for learners

### Technical Requirements
- ✅ Atomic file operations
- ✅ Data validation throughout
- ✅ Proper error handling
- ✅ Type hints and documentation
- ✅ Cross-platform compatibility

---

## Future Enhancements
- Multiple portfolio support
- Performance tracking over time
- Dividend tracking
- Tax lot tracking (FIFO, LIFO, specific ID)
- Portfolio allocation charts (requires visualization)
- Goal tracking (retirement, savings targets)
- Alerts/notifications for watchlist items

---

## Dependencies
- `fastmcp` - MCP server framework
- `python` >= 3.10
- `uv` - Package manager
- Standard library only for file I/O (no database for simplicity)
- **Optional:** SQLite for advanced version

---

## Timeline Estimate
- Phase 1 (Data Layer): 1-2 hours
- Phase 2 (Portfolio Tools): 2-3 hours
- Phase 3 (Watchlist Tools): 1 hour
- Phase 4 (Resources): 1-2 hours
- Phase 5 (Prompts): 1 hour
- Phase 6 (Advanced Features): 2-3 hours
- Phase 7 (Documentation): 1-2 hours
- Phase 8 (Integration Prep): 1 hour
- Testing & Refinement: 2 hours

**Total: 12-17 hours for complete implementation**

---

## Key Differences from Part 1
| Aspect | Part 1 (Market Data) | Part 2 (Portfolio) |
|--------|---------------------|-------------------|
| **Focus** | Read-only data retrieval | Stateful CRUD operations |
| **Data Source** | External API (yfinance) | Internal persistence (JSON) |
| **State** | Stateless | Stateful |
| **Tools** | Data fetching | Data manipulation |
| **Resources** | Dynamic from API | Expose persistent data |
| **Prompts** | Analysis requests | Action recommendations |
| **Complexity** | Simpler | More complex (persistence) |

---

## Integration with Part 1

### What Part 2 Needs from Part 1
- Current stock prices (via `get_stock_price` tool)
- Company information (via `stock://{ticker}/profile` resource)
- Analysis prompts (for decision support)

### What Part 2 Provides to Part 1
- Portfolio holdings (via `portfolio://holdings/summary` resource)
- Watchlist data (via `portfolio://watchlist/{id}` resources)
- Transaction context for analysis

### Composition Pattern
```
User Question: "Should I buy more AAPL?"
    ↓
Claude orchestrates:
    1. Read portfolio://holdings/summary (Part 2)
    2. Call get_stock_price("AAPL") (Part 1)
    3. Call analyze_stock_for_investment("AAPL") (Part 1 prompt)
    4. Synthesize recommendation
    5. If yes: Call add_to_portfolio(...) (Part 2)
```

This demonstrates the **power of MCP composition**: specialized servers working together through AI orchestration.
