<div align="center">

# 🔒 Safety Policy

**Risk management and recommendation validation**

[![Safety](https://img.shields.io/badge/Safety-Policy%20Enabled-FF6B6B)](./safety_policy.md)

</div>

---

## Overview

The Trading Research Assistant safety policy is designed to protect users from potentially dangerous or unfounded trading recommendations. The system includes multiple levels of validation before issuing recommendations.

## Safety Principles

### 1. Context Validation

Each recommendation must be based on:
- Sufficient historical data (minimum 200 candles)
- Current technical indicators
- News context (if available)

### 2. Data Validation

The system validates:
- Timeframe correctness (only allowed values)
- Sufficient data volume
- Symbol and parameter validity

### 3. Risk Constraints

Recommendations must include:
- Confidence level from 0.0 to 1.0
- Brief rationale
- Detailed rationale

## Safety Components

### Constraints (`core/policies/constraints.py`)

Module defines constraints and validation:

- **Minimum candles**: 200 (configurable via `RUNTIME_MARKET_DATA_WINDOW_CANDLES`)
- **Allowed timeframes**: 1m, 5m, 15m, 30m, 1h, 4h, 1d
- **Symbol validation**: format checking (e.g., EURUSD, GBPUSD)

### Safety Policy (`core/policies/safety_policy.py`)

Main safety policy validates recommendations before issuing:

1. **Confidence check**: Recommendations with low confidence (< 0.3) may be rejected
2. **Rationale check**: Recommendation must contain rationale
3. **Context check**: Recommendation must match current market context

## Safety Settings

Safety settings are in `src/app/settings.py`:

```python
# Minimum candles for analysis
RUNTIME_MARKET_DATA_WINDOW_CANDLES=300

# Interval between LLM calls (protection against overload)
RUNTIME_LLM_CALL_INTERVAL_SECONDS=300

# Enable/disable LLM (for testing without LLM)
RUNTIME_LLM_ENABLED=true
```

## Trade Journal

The system maintains a journal of all recommendations and their outcomes:

- **JournalEntry**: Record of decision made (CALL, PUT, SKIP)
- **Outcome**: Trade outcome (WIN, LOSS, DRAW, VOID)

This allows:
- Tracking recommendation effectiveness
- Analyzing patterns
- Improving the system based on real data

## Usage Recommendations

### For Users

1. **Always verify recommendations**: The system provides recommendations, but the final decision is yours
2. **Use the journal**: Keep track of all trades for analysis
3. **Start with small amounts**: Test the system on small positions
4. **Monitor confidence**: Recommendations with low confidence require special attention

### For Developers

1. **Don't disable checks**: Safety policy is an important part of the system
2. **Extend validation**: Add new checks as needed
3. **Log rejections**: Track cases when recommendations are rejected
4. **Test edge cases**: Check behavior with insufficient data

## Liability Limitations

⚠️ **Important**: Trading Research Assistant is a research and analysis tool, not an automated trading system.

- The system does not guarantee recommendation profitability
- All trading decisions are made by the user independently
- The user bears full responsibility for their trading decisions
- It is recommended to use the system in combination with your own analysis

## Future Improvements

Planned safety improvements:

- [ ] Dynamic risk assessment based on volatility
- [ ] Correlation check with historical data
- [ ] Integration with risk management policies
- [ ] Automatic position size limiting
- [ ] Warnings about unusual market conditions

---

<div align="center">

[📖 Overview](./overview.md) • [🏗️ Architecture](./architecture.md) • [📚 Usage Guide](./usage_guide.md) • [🔧 Troubleshooting](./troubleshooting.md)

</div>