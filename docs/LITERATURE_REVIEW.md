# Literature Review and Research Context

## 1. Market efficiency and adaptive behaviour

The efficient-markets framework is a useful null model, but options research needs a model of changing risk premia and participant behaviour. Lo's Adaptive Markets Hypothesis frames efficiency as an evolutionary property that can vary with market conditions rather than a permanently fixed state. This is consistent with the present study's decision to test a locked rule out of sample rather than assume a universal option premium.

**Reference:** Lo, A. W. (2004), "The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective", Journal of Portfolio Management, 30(5), 15–29.

## 2. Variance / volatility risk premia

Bollerslev, Tauchen and Zhou (2009) documented a variance-risk-premium relation in equity markets: option-implied variance can contain a risk-premium component relative to subsequent realized variance. This motivates testing multi-expiry option structures that implicitly combine long and short convexity, but it does not establish that any particular four-leg basket monetizes the premium after execution costs.

**Reference:** Bollerslev, T., Tauchen, G., & Zhou, H. (2009), "Expected Stock Returns and Variance Risk Premia", Review of Financial Studies, 22(11), 4463–4492.

## 3. Volatility surface and smile/skew

The Black-Scholes framework is a baseline rather than a complete description of listed option prices. Empirical volatility smiles/skews reflect stochastic volatility, jumps, discrete hedging, and supply/demand effects. A reverse-calendar structure can therefore produce P&L from several interacting exposures: expiry, strike, skew, convexity and time decay.

The present data, however, contain OHLC/Close prices rather than synchronized bid/ask and full implied-volatility surfaces, so Phase 2–4 do not attribute P&L to a specific volatility-surface mechanism. That attribution is reserved for future research.

## 4. Backtest overfitting and multiple testing

Backtesting a strategy after searching many alternatives creates selection bias. Bailey et al. formalized the Probability of Backtest Overfitting (PBO) problem. Bailey and López de Prado proposed the Deflated Sharpe Ratio as a diagnostic that adjusts the apparent Sharpe for non-normality and selection effects.

This study therefore locked the four-leg strategy before historical evaluation and treats the slippage/cost grid as sensitivity analysis rather than as candidate-strategy selection. Formal PBO is marked not estimable for the single frozen rule.

**References:**
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017), "The Probability of Backtest Overfitting", Journal of Computational Finance, 20(4), 39–69.
- Bailey, D. H., & López de Prado, M. (2014), "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality", SSRN 2465675.

## 5. Cross-validation for financial time series

Standard random k-fold validation leaks temporal information in financial applications. Combinatorial purged cross-validation (CPCV) was proposed to produce multiple chronological train/test paths while reducing leakage around overlapping labels. In this project, the sample is a small set of already-defined trades, so the implementation is deliberately described as a CPCV-style stability diagnostic rather than as a full predictive-model CPCV pipeline.

**Reference:** López de Prado, M. (2018), Advances in Financial Machine Learning, Wiley.

## 6. India-specific market context

The project also incorporates primary exchange documentation for expiry-day and holiday logic. NSE's current derivatives contract specification states Tuesday NIFTY 50 weekly expiry and last-Tuesday monthly expiry, with previous-trading-day adjustment for a holiday. BSE changed SENSEX weekly expiry to Thursday and monthly expiry to last Thursday for contracts expiring after 1 September 2025. The data pipeline also reconciles NIFTY's date-dependent contract lot sizes rather than treating lot size as permanently fixed.

## 7. Prior project research

Earlier MinDip research found that volatility-state prediction was more informative out of sample than direct next-day direction prediction, and that a direction-based trading candidate failed stronger CPCV-style validation. That prior work is not reused as evidence for the present four-leg rule; it is retained as research context supporting the decision to separate hypothesis generation from locked validation.
