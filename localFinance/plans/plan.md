# Part 1: Market Data MCP - Implementation Plan

## Overview
A read-only financial data MCP server focused on investment research and analysis. This server demonstrates all three MCP primitives (tools, resources, prompts) while providing real-world financial data via yfinance.

## Educational Goals
- Introduce MCP fundamentals: tools, resources, and prompts
- Show practical financial data API integration
- Demonstrate dynamic resource templates with URI parameters
- Teach prompt engineering with live data injection
- Set foundation for multi-server composition (Part 3)

---

## Current State (Already Implemented)

### Tools
1. ✅ `get_stock_price(ticker: str)` - Current stock price lookup
2. ✅ `get_historical_data(ticker: str, period: str)` - Historical price data
3. ✅ `compare_stocks(ticker1: str, ticker2: str)` - Side-by-side comparison

### Infrastructure
- FastMCP server setup
- yfinance integration
- Basic error handling

---

## Phase 1: Add Core Tool (News Data)

### New Tool: `get_stock_news`
**Purpose:** Fetch recent news articles for investment research

**Signature:**
```
get_stock_news(ticker: str, max_articles: int = 5) -> list[dict]
```

**Returns:**
- Article title
- Publisher name
- Publication link
- Publish timestamp

**Educational Points:**
- Shows API response transformation
- Demonstrates optional parameters with defaults
- Real-world news sentiment analysis use case

**Implementation Notes:**
- Use `yf.Ticker(ticker).news`
- Limit results to prevent token overflow
- Handle missing/malformed news data gracefully
- Return structured dict for easy consumption

---

## Phase 2: Implement Resources

### Resource 1: Stock Profile (Dynamic Template)
**URI Pattern:** `stock://{ticker}/profile`

**Purpose:** Provide comprehensive company information as an addressable resource

**Data Points to Include:**
- Company long name
- Sector and industry classification
- Business description/summary
- Key statistics:
  - Market capitalization
  - P/E ratio (trailing)
  - 52-week high/low range
  - Current price
  - Average volume
  - Beta (volatility measure)
  - Forward dividend yield (if applicable)

**Educational Points:**
- Demonstrates URI templating with `{ticker}` parameter
- Shows dynamic resource generation
- Resource vs Tool distinction: Resources are addressable data, tools are actions
- Teaches resource discovery patterns

**Implementation Notes:**
- Use `yf.Ticker(ticker).info` dictionary
- Format as readable text or JSON (consider both options)
- Handle tickers without certain data (e.g., no dividend)
- Add resource description for client discovery
- Consider adding MIME type hints

### Resource 2: Market Summary (Static/Time-based)
**URI Pattern:** `market://summary/daily`

**Purpose:** Provide daily market overview snapshot

**Data Points to Include:**
- Major indices (S&P 500, NASDAQ, DOW) current values and changes
- Top gainers (3-5 stocks)
- Top losers (3-5 stocks)
- Most active by volume
- Market breadth indicators

**Educational Points:**
- Shows static resource (no URI parameters)
- Time-based data that refreshes
- Aggregated data from multiple sources
- Resource as a "dashboard" pattern

**Implementation Notes:**
- May need to cache to avoid rate limits
- Consider using yfinance to fetch index data: `^GSPC`, `^IXIC`, `^DJI`
- Handle market hours vs after-hours
- Consider adding last_updated timestamp

### Resource 3: Watchlist (Optional - Static Data)
**URI Pattern:** `watchlist://default`

**Purpose:** Pre-configured list of interesting stocks for monitoring

**Data Points:**
- List of 10-15 diverse tickers (FAANG, emerging tech, value stocks)
- Brief description of why each is interesting
- Sector representation

**Educational Points:**
- Simplest resource type (static content)
- Shows curation concept
- Foundation for Part 2's custom watchlists

**Implementation Notes:**
- Hardcoded list, no yfinance calls needed
- Could be JSON or formatted text
- Easy to understand for beginners

---

## Phase 3: Implement Prompts

### Prompt 1: Stock Investment Analysis (Primary)
**Name:** `analyze_stock_for_investment`

**Parameters:**
- `ticker: str` (required)
- `investment_horizon: str` (default: "medium-term", options: "short-term", "medium-term", "long-term")
- `risk_tolerance: str` (default: "moderate", options: "conservative", "moderate", "aggressive")

**Purpose:** Generate a structured analysis request that injects live financial data

**Prompt Content Should Include:**
1. Company context (name, sector, industry)
2. Current financial metrics from yfinance:
   - Current price
   - Market cap
   - P/E ratio
   - 52-week range
   - Dividend yield (if any)
   - Recent earnings data
3. Analysis framework request:
   - Valuation assessment
   - Risk factors specific to sector
   - Growth potential indicators
   - Buy/Hold/Avoid recommendation with rationale

**Educational Points:**
- Shows dynamic prompt generation with live data
- Demonstrates structured prompt engineering
- Parameter customization for different user scenarios
- How prompts guide AI behavior systematically

**Implementation Notes:**
- Fetch fresh data from yfinance at prompt generation time
- Format numbers for readability (comma separators, rounding)
- Handle missing data gracefully (e.g., no P/E for unprofitable companies)
- Return as list of PromptMessage objects
- Consider adding SystemMessage for context setting

### Prompt 2: Stock Comparison Analysis
**Name:** `compare_stocks`

**Parameters:**
- `ticker1: str` (required)
- `ticker2: str` (required)
- `comparison_focus: str` (default: "general", options: "valuation", "growth", "risk", "general")

**Purpose:** Generate side-by-side comparison analysis request

**Prompt Content Should Include:**
1. Both companies' basic info
2. Key metrics in table format:
   - Current prices
   - Market caps
   - P/E ratios
   - Revenue growth
   - Debt levels
   - Profit margins
3. Comparison framework:
   - Relative valuation
   - Competitive positioning
   - Risk comparison
   - Better fit for different investment profiles

**Educational Points:**
- Multi-parameter prompts
- Structured data presentation in prompts
- Comparative analysis patterns
- How to format complex data for AI consumption

### Prompt 3: Portfolio-Aware Analysis (Cross-Server Pattern)
**Name:** `analyze_for_existing_portfolio`

**Parameters:**
- `ticker: str` (required)
- `portfolio_resource: str` (default: "portfolio://holdings/summary")

**Purpose:** Analyze a stock in context of existing portfolio holdings

**Prompt Content Should Include:**
1. Stock data (same as Prompt 1)
2. **Instructions to AI** to first read the portfolio resource
3. Analysis framework:
   - Diversification impact
   - Sector/industry overlap analysis
   - Risk adjustment for portfolio
   - Position sizing recommendation

**Educational Points:**
- **CRITICAL:** Shows cross-server resource reference pattern
- Documents how MCP composition works at client level
- Prompt doesn't fetch portfolio data itself - instructs AI to do so
- Sets up Part 3 composition demonstration

**Implementation Notes:**
- Add clear documentation in prompt text about expected resource
- This prompt is "portfolio-aware" but doesn't require Part 2 to function
- The AI client (Claude) will orchestrate the cross-server calls
- Include fallback text if portfolio resource unavailable

### Prompt 4: News Sentiment Analysis (Optional)
**Name:** `analyze_news_sentiment`

**Parameters:**
- `ticker: str` (required)

**Purpose:** Analyze sentiment from recent news articles

**Prompt Content Should Include:**
1. List of recent news headlines and publishers
2. Publication timestamps
3. Analysis request:
   - Overall sentiment (bullish/neutral/bearish)
   - Key themes identified
   - Potential price impact
   - News reliability assessment

**Educational Points:**
- Integrating tool output (news) into prompts
- Real-world NLP use case
- Time-sensitive analysis

---

## Phase 4: Documentation & Educational Enhancements

### Code Documentation
1. **Docstrings:** Every tool, resource, and prompt needs comprehensive docstrings
   - Purpose
   - Parameters with types and defaults
   - Return value structure
   - Example usage
   - Educational notes

2. **Inline Comments:** Explain key concepts
   - Why resource vs tool
   - URI pattern choices
   - Data transformation logic
   - Error handling strategies

3. **README Updates:** Add sections for:
   - What is MCP and why it matters
   - Tools vs Resources vs Prompts explanation
   - How to test each component
   - Example workflows
   - Connection to Parts 2 & 3

### Testing & Validation
1. **Manual Testing Checklist:**
   - Each tool with valid/invalid tickers
   - Each resource with different parameters
   - Each prompt with various parameter combinations
   - Error cases (network failures, invalid data, rate limits)

2. **Example Interactions:** Document real usage scenarios
   - "Find me an undervalued tech stock"
   - "Compare AAPL vs MSFT for my portfolio"
   - "What's the sentiment on TSLA this week?"

### Configuration Examples
1. **Claude Desktop Config:**
   ```json
   {
     "mcpServers": {
       "market-data": {
         "command": "uv",
         "args": ["run", "c:/git/mcpKoulutus/demot/localFinance/main.py"]
       }
     }
   }
   ```

2. **Standalone Testing:** How to test without Claude Desktop

---

## Phase 5: Preparation for Part 2 Integration

### Design Considerations
1. **Resource Naming Conventions:**
   - Use clear prefixes: `stock://`, `market://`, `watchlist://`
   - Consistent with what Part 2 will use: `portfolio://`

2. **Data Format Standards:**
   - Establish JSON schemas for common data structures
   - Document expected formats for cross-server consumption

3. **Documentation for Composition:**
   - Add section explaining how this server will compose with portfolio server
   - Diagram showing client-side vs server-side composition
   - Example scenarios requiring both servers

### Cross-Server Reference Examples
Document patterns like:
```
"To analyze stocks for your portfolio, this server provides analysis
while the Portfolio MCP (Part 2) maintains your holdings. The AI client
coordinates between both servers automatically."
```

---

## Technical Implementation Notes

### Error Handling Strategy
1. **Network Issues:** Graceful degradation when yfinance unavailable
2. **Invalid Tickers:** Clear error messages with suggestions
3. **Rate Limiting:** Implement caching where appropriate
4. **Missing Data:** Handle stocks without certain metrics (P/E, dividends, etc.)
5. **Type Safety:** Validate all inputs before passing to yfinance

### Performance Considerations
1. **Caching:** Consider caching market summary (updates every 5-10 minutes)
2. **Batch Requests:** When comparing stocks, fetch data efficiently
3. **Timeout Handling:** Set reasonable timeouts for yfinance calls
4. **Resource Limits:** Prevent excessive API calls in single request

### Data Quality
1. **Data Validation:** Verify yfinance responses before returning
2. **Formatting:** Consistent number formatting (decimals, percentages, currency)
3. **Timestamps:** Include data freshness indicators
4. **Disclaimers:** Note that data is for educational purposes

---

## Success Criteria

### Functional Requirements
- ✅ All tools return accurate, formatted data
- ✅ All resources are addressable and return valid content
- ✅ All prompts generate well-structured analysis requests
- ✅ Error handling prevents crashes
- ✅ Works with Claude Desktop configuration

### Educational Requirements
- ✅ Code is well-documented and beginner-friendly
- ✅ Clear examples of tools, resources, and prompts
- ✅ Demonstrates practical financial use case
- ✅ Sets up Part 3 composition patterns
- ✅ README explains MCP concepts clearly

### Technical Requirements
- ✅ FastMCP best practices followed
- ✅ Type hints throughout
- ✅ Proper async/await usage
- ✅ No hardcoded paths or credentials
- ✅ Works cross-platform (Windows/Mac/Linux)

---

## Future Enhancements (Post Part 1)
- Advanced charting data
- Technical indicators (RSI, MACD, etc.)
- Options chain data
- Earnings calendar
- Sector/industry screening
- Real-time vs delayed data handling
- WebSocket support for streaming prices

---

## Dependencies
- `fastmcp` - MCP server framework
- `yfinance` - Yahoo Finance API wrapper
- `python` >= 3.10
- `uv` - Package manager

---

## Timeline Estimate
- Phase 1 (News Tool): 30 minutes
- Phase 2 (Resources): 1-2 hours
- Phase 3 (Prompts): 1-2 hours
- Phase 4 (Documentation): 1 hour
- Phase 5 (Integration Prep): 30 minutes
- Testing & Refinement: 1 hour

**Total: 5-7 hours for complete implementation**
