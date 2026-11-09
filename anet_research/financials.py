"""Validate annual USD statements and calculate metrics without filling gaps."""

import pandas as pd

FINANCIAL_FIELDS = [
    "revenue", "gross_profit", "operating_income", "net_income",
    "operating_cash_flow", "capital_expenditures",
]
SOURCE_FIELDS = ["source_url", "source_reference", "verified"]
REQUIRED_COLUMNS = ["fiscal_year", *FINANCIAL_FIELDS, *SOURCE_FIELDS]


def validate_statements(frame: pd.DataFrame, *, allow_unverified: bool = False) -> pd.DataFrame:
    """Return sorted statements; verified means user-attested, not SEC fetched."""
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    data = frame[REQUIRED_COLUMNS].copy()
    years = pd.to_numeric(data["fiscal_year"], errors="coerce")
    if years.isna().any() or ((years % 1) != 0).any() or not years.between(1900, 2200).all():
        raise ValueError("Fiscal years must be integers between 1900 and 2200.")
    data["fiscal_year"] = years.astype(int)
    if data["fiscal_year"].duplicated().any():
        raise ValueError("Each fiscal year must appear only once.")
    for field in FINANCIAL_FIELDS:
        raw = data[field].map(lambda value: None if isinstance(value, str) and not value.strip() else value)
        numeric = pd.to_numeric(raw, errors="coerce")
        if (raw.notna() & numeric.isna()).any() or numeric.isin([float("inf"), -float("inf")]).any():
            raise ValueError(f"{field} must contain finite numbers or blanks.")
        data[field] = numeric.astype(float)
    if (data["revenue"] < 0).any() or (data["capital_expenditures"] < 0).any():
        raise ValueError("Revenue and capital expenditures must be nonnegative; enter capex as a positive outflow.")
    flags = data["verified"].astype("string").fillna("").str.strip().str.lower()
    if not flags.isin(["", "true", "false"]).all():
        raise ValueError("verified must be true, false, or blank.")
    data["verified"] = flags.eq("true")
    populated = data[FINANCIAL_FIELDS].notna().any(axis=1)
    sources = data[["source_url", "source_reference"]].fillna("").astype(str)
    sec_url = sources["source_url"].str.match(r"^https://(?:www\.)?sec\.gov/\S+$")
    cited = sources["source_reference"].str.strip().ne("")
    if not allow_unverified and (populated & (~data["verified"] | ~sec_url | ~cited)).any():
        raise ValueError("Populated rows require verified=true, an HTTPS SEC source URL, and a 10-K page/table reference.")
    return data.sort_values("fiscal_year").reset_index(drop=True)


def calculate_metrics(frame: pd.DataFrame, *, allow_unverified: bool = False) -> pd.DataFrame:
    """Ratios are fractions. YoY requires consecutive years and positive prior revenue."""
    data = validate_statements(frame, allow_unverified=allow_unverified)
    revenue = data["revenue"]
    denominator = revenue.where(revenue > 0)
    prior = revenue.shift(1).where(revenue.shift(1) > 0)
    consecutive = data["fiscal_year"].diff().eq(1)
    data["revenue_growth_yoy"] = (revenue.div(prior) - 1).where(consecutive)
    for output, numerator in [
        ("gross_profit_margin", "gross_profit"),
        ("operating_profit_margin", "operating_income"),
        ("net_profit_margin", "net_income"),
    ]:
        data[output] = data[numerator].div(denominator)
    data["free_cash_flow"] = data["operating_cash_flow"] - data["capital_expenditures"]
    data["free_cash_flow_margin"] = data["free_cash_flow"].div(denominator)
    return data
