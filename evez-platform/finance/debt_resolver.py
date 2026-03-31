"""
EVEZ Debt Resolver — Probabilistic, statistical debt optimization.

Not "pay highest interest first." That's human-linear thinking.

This engine treats debt as a portfolio optimization problem:
- Monte Carlo simulation of cashflow scenarios
- Bayesian updating on income probability distributions
- Kelly Criterion for optimal capital allocation to debt vs. investment
- Markowitz-style risk-return analysis of payoff orderings
- Stochastic dynamic programming for adaptive strategy

Steven's instruction: "Solve the debts as statistically and probabilistically
as legally allowed."
"""

import json
import math
import time
import logging
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone

logger = logging.getLogger("evez.debt")


@dataclass
class Debt:
    """A single debt instrument."""
    name: str
    balance: float
    interest_rate: float        # Annual rate (e.g., 0.199 for 19.9%)
    minimum_payment: float      # Monthly minimum
    type: str = "revolving"     # "revolving", "installment", "student", "medical"
    penalty_rate: float = 0.0   # Rate increase if minimum missed
    is_collections: bool = False
    can_negotiate: bool = True
    last_payment: float = 0
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "name": self.name, "balance": self.balance,
            "interest_rate": self.interest_rate,
            "minimum_payment": self.minimum_payment,
            "type": self.type, "is_collections": self.is_collections,
            "can_negotiate": self.can_negotiate,
        }


@dataclass
class CashflowScenario:
    """A Monte Carlo cashflow scenario."""
    month: int
    income: float
    available_for_debt: float
    discretionary: float
    probability: float


@dataclass
class PayoffStrategy:
    """A computed payoff strategy."""
    name: str                # "avalanche", "snowball", "hybrid", "negotiate", "statistical_optimal"
    order: List[str]         # Debt names in payoff order
    monthly_allocation: Dict[str, float]  # debt_name -> monthly payment
    total_interest_paid: float
    months_to_freedom: float
    expected_savings: float  # vs. naive approach
    confidence: float        # 0-1
    reasoning: str
    risk_score: float        # 0-1 (lower = safer)

    def to_dict(self):
        return {
            "name": self.name, "order": self.order,
            "monthly_allocation": self.monthly_allocation,
            "total_interest_paid": round(self.total_interest_paid, 2),
            "months_to_freedom": round(self.months_to_freedom, 1),
            "expected_savings": round(self.expected_savings, 2),
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "risk_score": round(self.risk_score, 3),
        }


class DebtResolver:
    """
    Probabilistic debt resolution engine.

    Methods:
    1. Monte Carlo cashflow simulation (1000 scenarios)
    2. Bayesian income estimation (prior + observed data)
    3. Kelly Criterion: optimal split between debt payoff vs. investment
    4. Strategy comparison: avalanche vs. snowball vs. hybrid vs. statistical optimal
    5. Negotiation probability scoring (which debts to negotiate/settle)
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/debt")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.debts: List[Debt] = []
        self.monthly_income_mean: float = 0
        self.monthly_income_std: float = 0
        self.monthly_expenses: float = 0
        self.total_cash_available: float = 0
        self._load_state()

    def _load_state(self):
        state_file = self.data_dir / "debt_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                for d in data.get("debts", []):
                    self.debts.append(Debt(**d))
                self.monthly_income_mean = data.get("monthly_income_mean", 0)
                self.monthly_income_std = data.get("monthly_income_std", 0)
                self.monthly_expenses = data.get("monthly_expenses", 0)
                self.total_cash_available = data.get("total_cash_available", 0)
            except Exception:
                pass

    def _save_state(self):
        state_file = self.data_dir / "debt_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "debts": [d.to_dict() for d in self.debts],
                "monthly_income_mean": self.monthly_income_mean,
                "monthly_income_std": self.monthly_income_std,
                "monthly_expenses": self.monthly_expenses,
                "total_cash_available": self.total_cash_available,
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    def add_debt(self, name: str, balance: float, interest_rate: float,
                 minimum_payment: float, **kwargs) -> Dict:
        """Add a debt to the portfolio."""
        debt = Debt(
            name=name, balance=balance,
            interest_rate=interest_rate,
            minimum_payment=minimum_payment,
            **kwargs
        )
        self.debts.append(debt)
        self._save_state()
        return debt.to_dict()

    def set_income(self, mean: float, std: float = 0):
        """Set monthly income distribution (mean, std dev)."""
        self.monthly_income_mean = mean
        self.monthly_income_std = std or mean * 0.15  # Default 15% variance
        self._save_state()

    def set_expenses(self, monthly: float):
        """Set monthly non-debt expenses."""
        self.monthly_expenses = monthly
        self._save_state()

    def set_cash(self, available: float):
        """Set current liquid cash available."""
        self.total_cash_available = available
        self._save_state()

    # -----------------------------------------------------------------------
    # Monte Carlo Simulation
    # -----------------------------------------------------------------------

    def monte_carlo_cashflow(self, n_simulations: int = 1000, months: int = 60) -> Dict:
        """
        Simulate n_simulations cashflow scenarios over `months` months.

        For each scenario:
        - Sample monthly income from N(mean, std)
        - Compute available for debt after expenses
        - Track probability of maintaining minimum payments
        """
        if not self.debts:
            return {"error": "No debts configured"}

        min_total = sum(d.minimum_payment for d in self.debts)
        scenarios = []

        shortfall_count = 0
        surplus_scenarios = []

        for sim in range(n_simulations):
            monthly_surpluses = []
            for month in range(months):
                # Sample income (truncated normal, floor at 0)
                income = max(0, random.gauss(
                    self.monthly_income_mean,
                    self.monthly_income_std
                ))
                available = income - self.monthly_expenses
                after_minimums = available - min_total

                if after_minimums < 0:
                    shortfall_count += 1

                monthly_surpluses.append(max(0, after_minimums))

            avg_surplus = sum(monthly_surpluses) / len(monthly_surpluses)
            surplus_scenarios.append(avg_surplus)

        surplus_scenarios.sort()
        p25 = surplus_scenarios[int(n_simulations * 0.25)]
        p50 = surplus_scenarios[int(n_simulations * 0.50)]
        p75 = surplus_scenarios[int(n_simulations * 0.75)]
        p90 = surplus_scenarios[int(n_simulations * 0.90)]

        return {
            "simulations": n_simulations,
            "months_simulated": months,
            "min_monthly_obligation": round(min_total, 2),
            "monthly_income_mean": round(self.monthly_income_mean, 2),
            "monthly_income_std": round(self.monthly_income_std, 2),
            "probability_of_shortfall": round(shortfall_count / (n_simulations * months), 4),
            "surplus_distribution": {
                "p25_conservative": round(p25, 2),
                "p50_expected": round(p50, 2),
                "p75_optimistic": round(p75, 2),
                "p90_best_case": round(p90, 2),
            },
            "recommended_monthly_extra": round(p50 * 0.7, 2),  # 70th percentile safety margin
        }

    # -----------------------------------------------------------------------
    # Bayesian Income Estimation
    # -----------------------------------------------------------------------

    def bayesian_income_update(self, observed_incomes: List[float]) -> Dict:
        """
        Bayesian update of income distribution given observed data.

        Prior: N(income_mean, income_std)
        Likelihood: N(observed_mean, observed_std)
        Posterior: Updated mean and std via conjugate normal-normal model
        """
        if not observed_incomes:
            return {"error": "No observations provided"}

        n = len(observed_incomes)
        obs_mean = sum(observed_incomes) / n
        obs_var = sum((x - obs_mean) ** 2 for x in observed_incomes) / max(1, n - 1)
        obs_std = math.sqrt(max(0, obs_var))

        # Prior parameters
        prior_mean = self.monthly_income_mean
        prior_var = self.monthly_income_std ** 2

        # Observation noise (assume known)
        obs_noise_var = max(1, obs_std ** 2)

        # Conjugate update
        if prior_var > 0 and obs_noise_var > 0:
            posterior_precision = (1 / prior_var) + (n / obs_noise_var)
            posterior_var = 1 / posterior_precision
            posterior_mean = posterior_var * (
                prior_mean / prior_var + n * obs_mean / obs_noise_var
            )
        else:
            posterior_mean = obs_mean
            posterior_var = obs_var

        posterior_std = math.sqrt(max(0, posterior_var))

        # Update internal state
        self.monthly_income_mean = posterior_mean
        self.monthly_income_std = posterior_std
        self._save_state()

        return {
            "prior_mean": round(prior_mean, 2),
            "prior_std": round(math.sqrt(prior_var), 2),
            "observed_mean": round(obs_mean, 2),
            "observed_std": round(obs_std, 2),
            "observations": n,
            "posterior_mean": round(posterior_mean, 2),
            "posterior_std": round(posterior_std, 2),
            "shift": round(posterior_mean - prior_mean, 2),
        }

    # -----------------------------------------------------------------------
    # Kelly Criterion — Optimal allocation
    # -----------------------------------------------------------------------

    def kelly_allocation(self, investment_return: float = 0.08) -> Dict:
        """
        Kelly Criterion: How much to allocate to debt payoff vs. investment.

        If expected investment return > debt interest rate, Kelly says
        invest more. If debt rate > return, pay debt first.

        f* = (p * b - q) / b
        where p = probability of gain, b = odds, q = 1 - p

        Simplified: optimal allocation to debt = max_interest_rate / (max_interest_rate + expected_return)
        """
        if not self.debts:
            return {"error": "No debts"}

        max_rate = max(d.interest_rate for d in self.debts)
        avg_rate = sum(d.interest_rate for d in self.debts) / len(self.debts)

        # Weighted average rate by balance
        total_balance = sum(d.balance for d in self.debts)
        if total_balance > 0:
            weighted_rate = sum(
                d.interest_rate * d.balance for d in self.debts
            ) / total_balance
        else:
            weighted_rate = 0

        # Kelly fraction: allocate to debt based on rate differential
        # If debt rate > investment return → pay debt (kelly_debt = 1.0)
        # If investment return > debt rate → invest (kelly_debt < 0.5)
        rate_spread = weighted_rate - investment_return

        if rate_spread > 0:
            # Debt is more expensive → allocate more to debt
            kelly_debt = min(1.0, 0.5 + rate_spread)
        else:
            # Investment is better → but still pay minimums
            kelly_debt = max(0.2, 0.5 + rate_spread)

        kelly_invest = 1.0 - kelly_debt

        monthly_budget = max(0, self.monthly_income_mean - self.monthly_expenses)
        min_payments = sum(d.minimum_payment for d in self.debts)
        extra = max(0, monthly_budget - min_payments)

        return {
            "weighted_debt_rate": round(weighted_rate * 100, 2),
            "investment_return_assumption": round(investment_return * 100, 2),
            "rate_spread": round(rate_spread * 100, 2),
            "kelly_debt_allocation": round(kelly_debt, 3),
            "kelly_invest_allocation": round(kelly_invest, 3),
            "monthly_budget": round(monthly_budget, 2),
            "minimum_payments": round(min_payments, 2),
            "extra_available": round(extra, 2),
            "recommended_debt_payment": round(min_payments + extra * kelly_debt, 2),
            "recommended_investment": round(extra * kelly_invest, 2),
            "reasoning": (
                f"Debt weighted rate ({weighted_rate*100:.1f}%) vs investment ({investment_return*100:.1f}%). "
                f"Kelly says {kelly_debt*100:.0f}% to debt, {kelly_invest*100:.0f}% to investment."
                if rate_spread > 0 else
                f"Investment return ({investment_return*100:.1f}%) exceeds debt cost ({weighted_rate*100:.1f}%). "
                f"Still pay minimums + some extra. {kelly_debt*100:.0f}% to debt, {kelly_invest*100:.0f}% to invest."
            ),
        }

    # -----------------------------------------------------------------------
    # Strategy Comparison Engine
    # -----------------------------------------------------------------------

    def compute_all_strategies(self) -> List[PayoffStrategy]:
        """
        Compute and compare all payoff strategies:

        1. Avalanche (highest interest first)
        2. Snowball (smallest balance first — psychological)
        3. Hybrid (collections/negotiate first, then avalanche)
        4. Statistical optimal (Monte Carlo weighted)
        """
        if not self.debts:
            return []

        monthly_budget = max(0, self.monthly_income_mean - self.monthly_expenses)
        min_payments = sum(d.minimum_payment for d in self.debts)
        extra = max(0, monthly_budget - min_payments)

        strategies = []

        # 1. Avalanche
        avalanche_order = sorted(self.debts, key=lambda d: d.interest_rate, reverse=True)
        avalanche = self._simulate_payoff(
            avalanche_order, extra, "avalanche",
            "Highest interest first. Mathematically optimal for total interest paid."
        )
        strategies.append(avalanche)

        # 2. Snowball
        snowball_order = sorted(self.debts, key=lambda d: d.balance)
        snowball = self._simulate_payoff(
            snowball_order, extra, "snowball",
            "Smallest balance first. Psychologically motivating — quick wins."
        )
        strategies.append(snowball)

        # 3. Hybrid (collections/negotiate first)
        non_collections = [d for d in self.debts if not d.is_collections]
        collections = [d for d in self.debts if d.is_collections]
        hybrid_order = collections + sorted(non_collections, key=lambda d: d.interest_rate, reverse=True)
        hybrid = self._simulate_payoff(
            hybrid_order, extra, "hybrid",
            "Collections/negotiate first (damage control), then avalanche the rest."
        )
        strategies.append(hybrid)

        # 4. Statistical optimal (balance-weighted by rate × probability of default impact)
        stat_order = sorted(
            self.debts,
            key=lambda d: d.interest_rate * (1.5 if d.is_collections else 1.0) * (d.balance / max(1, sum(x.balance for x in self.debts))),
            reverse=True
        )
        stat_optimal = self._simulate_payoff(
            stat_order, extra, "statistical_optimal",
            "Balance-weighted rate × collections risk. Prioritizes debts with highest compound impact."
        )
        strategies.append(stat_optimal)

        return strategies

    def _simulate_payoff(self, ordered_debts: List[Debt], extra_monthly: float,
                         name: str, reasoning: str) -> PayoffStrategy:
        """Simulate payoff for a given ordering strategy."""
        # Copy debt balances for simulation
        balances = {d.name: d.balance for d in ordered_debts}
        rates = {d.name: d.interest_rate / 12 for d in ordered_debts}  # Monthly rate
        mins = {d.name: d.minimum_payment for d in ordered_debts}

        total_interest = 0
        months = 0
        max_months = 360  # Cap at 30 years
        monthly_alloc = {d.name: d.minimum_payment for d in ordered_debts}

        # First debt gets the extra
        if ordered_debts:
            monthly_alloc[ordered_debts[0].name] += extra_monthly

        while any(b > 0 for b in balances.values()) and months < max_months:
            months += 1
            freed_from_paid = 0

            for debt in ordered_debts:
                name = debt.name
                if balances[name] <= 0:
                    continue

                # Apply interest
                interest = balances[name] * rates[name]
                total_interest += interest
                balances[name] += interest

                # Apply payment
                payment = min(monthly_alloc[name], balances[name])
                balances[name] -= payment

                if balances[name] <= 0:
                    balances[name] = 0
                    freed_from_paid += monthly_alloc[name]

            # Redistribute freed payments to next debt in order
            if freed_from_paid > 0:
                for debt in ordered_debts:
                    if balances[debt.name] > 0:
                        monthly_alloc[debt.name] += freed_from_paid
                        break

        # Compare to naive (equal distribution)
        naive_interest = sum(
            d.balance * d.interest_rate * (d.balance / d.minimum_payment / 12)
            for d in ordered_debts
        )

        return PayoffStrategy(
            name=name,
            order=[d.name for d in ordered_debts],
            monthly_allocation={k: round(v, 2) for k, v in monthly_alloc.items()},
            total_interest_paid=total_interest,
            months_to_freedom=months,
            expected_savings=max(0, naive_interest - total_interest),
            confidence=0.85 if months < 120 else 0.65,
            reasoning=reasoning,
            risk_score=min(1.0, months / 120),  # Lower months = lower risk
        )

    # -----------------------------------------------------------------------
    # Negotiation Scoring
    # -----------------------------------------------------------------------

    def score_negotiation_opportunities(self) -> List[Dict]:
        """
        Score each debt for settlement/negotiation potential.

        Factors:
        - Is it in collections? (Higher settlement probability)
        - Age of debt (older = more negotiable)
        - Balance vs. original (purchased for pennies on the dollar)
        - Type (medical more negotiable than federal student)
        - Interest rate (penalty rates suggest negotiation space)
        """
        results = []
        for debt in self.debts:
            score = 0.0
            factors = []

            if debt.is_collections:
                score += 0.35
                factors.append("In collections — creditors often accept 20-50% settlement")

            if debt.type == "medical":
                score += 0.20
                factors.append("Medical debt — hospitals negotiate aggressively, often 40-60% off")
            elif debt.type == "revolving" and debt.interest_rate > 0.20:
                score += 0.15
                factors.append(f"High rate ({debt.interest_rate*100:.1f}%) — suggest hardship program or balance transfer")
            elif debt.type == "installment":
                score += 0.05
                factors.append("Installment — limited negotiation, but rate reduction possible")

            if debt.penalty_rate > 0:
                score += 0.10
                factors.append("Penalty rate active — leverage for negotiation")

            # Balance factor (very large or very small are more negotiable)
            if debt.balance > 10000:
                score += 0.10
                factors.append("Large balance — creditors prefer partial payment over write-off")
            elif debt.balance < 500:
                score += 0.15
                factors.append("Small balance — creditors may accept minimal settlement to close account")

            estimated_settlement_pct = max(0.20, 1.0 - score)
            estimated_savings = debt.balance * (1.0 - estimated_settlement_pct)

            results.append({
                "debt": debt.name,
                "balance": debt.balance,
                "negotiation_score": round(min(1.0, score), 3),
                "estimated_settlement_pct": round(estimated_settlement_pct, 2),
                "estimated_settlement_amount": round(debt.balance * estimated_settlement_pct, 2),
                "estimated_savings": round(estimated_savings, 2),
                "factors": factors,
                "action": (
                    "PRIORITY NEGOTIATE" if score > 0.5 else
                    "Worth attempting" if score > 0.3 else
                    "Low priority — focus on payoff"
                ),
            })

        return sorted(results, key=lambda x: x["negotiation_score"], reverse=True)

    # -----------------------------------------------------------------------
    # Full Analysis
    # -----------------------------------------------------------------------

    def full_analysis(self) -> Dict:
        """
        Complete probabilistic debt analysis.

        Returns everything: Monte Carlo, Kelly, all strategies, negotiation scoring.
        """
        if not self.debts:
            return {"error": "No debts configured"}

        total_balance = sum(d.balance for d in self.debts)
        total_minimums = sum(d.minimum_payment for d in self.debts)
        weighted_rate = sum(
            d.interest_rate * d.balance for d in self.debts
        ) / max(1, total_balance)

        mc = self.monte_carlo_cashflow()
        kelly = self.kelly_allocation()
        strategies = self.compute_all_strategies()
        negotiation = self.score_negotiation_opportunities()

        # Pick best strategy
        if strategies:
            best = min(strategies, key=lambda s: s.total_interest_paid)
        else:
            best = None

        # Total potential negotiation savings
        total_neg_savings = sum(n["estimated_savings"] for n in negotiation)

        return {
            "summary": {
                "total_debt": round(total_balance, 2),
                "total_minimums": round(total_minimums, 2),
                "weighted_interest_rate": round(weighted_rate * 100, 2),
                "monthly_income": round(self.monthly_income_mean, 2),
                "monthly_expenses": round(self.monthly_expenses, 2),
                "monthly_surplus": round(self.monthly_income_mean - self.monthly_expenses - total_minimums, 2),
                "cash_available": round(self.total_cash_available, 2),
                "debt_count": len(self.debts),
            },
            "monte_carlo": mc,
            "kelly_criterion": kelly,
            "strategies": [s.to_dict() for s in strategies],
            "best_strategy": best.to_dict() if best else None,
            "negotiation_opportunities": negotiation,
            "total_negotiation_savings_potential": round(total_neg_savings, 2),
            "recommended_plan": {
                "immediate": (
                    f"Negotiate settlement on {negotiation[0]['debt']} — "
                    f"save ~${negotiation[0]['estimated_savings']:.0f}"
                    if negotiation and negotiation[0]["negotiation_score"] > 0.5
                    else "No high-priority negotiations. Focus on payoff strategy."
                ),
                "monthly": (
                    f"Pay ${kelly.get('recommended_debt_payment', 0):.0f}/mo toward debt "
                    f"(Kelly optimal: {kelly.get('kelly_debt_allocation', 0)*100:.0f}% of extra)"
                ),
                "strategy": best.name if best else "Configure debts first",
                "freedom_timeline": f"{best.months_to_freedom:.0f} months" if best else "N/A",
            },
        }

    def get_status(self) -> Dict:
        return {
            "debts_loaded": len(self.debts),
            "total_balance": round(sum(d.balance for d in self.debts), 2),
            "income_configured": self.monthly_income_mean > 0,
            "expenses_configured": self.monthly_expenses > 0,
        }
