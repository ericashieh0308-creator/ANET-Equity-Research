# Twelve-month price target and rating framework

**Current conclusion: NOT RATED. Target, upside/downside and per-share fair value
remain BLOCKED.** This is a documented implementation framework, not a fabricated target.

## Reference price: one gap resolved

The [market register](../data/integrated/market_reference.json) records two
corroborating accessible historical-price tables:

- [Stock Analysis](https://stockanalysis.com/stocks/anet/history/), Historical Data / Close; identifies S&P Global Market Intelligence as its data source.
- [ChartExchange](https://chartexchange.com/symbol/nyse-anet/historical/), ANET Historical Prices / Close.

Both show **USD 170.80 on November 6, 2026**, regular-session close, NYSE ANET,
16:00 America/New_York (EST). Both also show **USD 203.59 on September 30, 2026**.
Reviewed November 8 (US Eastern date). These are corroborated vendor historical
closes, not a claim of official exchange-feed certification. Quote banners,
after-hours quotes and vendor market-cap/PE fields are not model inputs.
The official Arista IR stock page rendered “Loading stock data” rather than a
numeric quote, so its search snippet was not used as verified evidence.

The November close is the latest completed session before the Sunday research
date. The September close supplies dated context for an award schedule but cannot
resolve missing vesting/proceeds/service-cost inputs. The November quote is not
silently applied to September dilution or a September EV bridge.

## Dates and target mechanics

1. Establish evidence-supported operating assumptions, WACC/terminal economics,
   a complete dated equity bridge and a defensible dilution policy.
2. Distinguish September 30, 2026 retrospective operating EV from an equity fair
   value on the research date. Later-filed information makes the existing DCF
   retrospective, not an investable September backtest.
3. A twelve-month target horizon is **November 8, 2027** relative to the November 8,
   2026 research date (a horizon date, not an assumed trading session). Revalue the
   remaining FCFF at that horizon; reconcile distributions, retained cash, claims,
   dilution and capital allocation to the same date. Establish a horizon-specific
   annual/stub schedule before calculating anything. Do not multiply an equity
   price by (1 + WACC), or apply a September-to-September roll to this November horizon.
4. Once supported, price return = target / reference close − 1. Total shareholder
   return additionally requires sourced/justified distributions; none are assumed.

A complete bridge could unlock **illustrative** per-share scenario outputs, but
would not validate the operating assumptions or establish a twelve-month target.
Current share-price availability alone unlocks neither equity value nor upside.

## Transparent Buy/Hold/Sell policy without invented cutoffs

`target_and_rating()` takes explicit analyst-policy thresholds and all evidence
gates. With all gates satisfied: Buy if supported twelve-month price return is
above the documented buy hurdle; Sell if below the documented sell hurdle; Hold
otherwise (including the boundaries). Hurdles are policy judgments, not sourced
financial facts; buy must exceed sell. Thresholds remain unset until supported
by a stated risk/uncertainty rationale. This project does not claim a bank's
rating policy or impose arbitrary percentage cutoffs.

Gates: supported operating assumptions; supported WACC and terminal economics;
verified equity bridge; point-in-time dilution; horizon-specific revaluation;
verified reference price/date alignment; documented rating thresholds. A missing
gate returns null target/return and NOT RATED. NOT RATED is not Hold. Synthetic
unit tests exercise thresholds and missing-data behavior; these are not ANET outputs.

See [rating policy inputs](../data/integrated/rating_policy.json) and
[readiness output](../model_outputs/integrated/valuation_readiness.json) for the
exact missing gates. Unvalidated operating rates, excess liquidity/asset adjustments,
claim classification, award completeness/proceeds and forward-horizon balances
currently prevent a defensible target or recommendation.
