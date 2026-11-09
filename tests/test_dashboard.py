from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_empty_dashboard_renders():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.sidebar.radio[0].set_value("Verified CSV").run()
    assert not app.exception
    assert "No verified financial figures loaded" in app.warning[0].value


def test_populated_dashboard_renders(monkeypatch):
    """Inject synthetic statements in memory; never save them as research data."""
    import pandas as pd
    from anet_research.financials import REQUIRED_COLUMNS

    synthetic = pd.DataFrame([
        [2023, 100, 60, 30, 20, 25, 5, "https://www.sec.gov/example", "Synthetic test only", True],
        [2024, 120, 72, 36, 24, 35, 5, "https://www.sec.gov/example", "Synthetic test only", True],
    ], columns=REQUIRED_COLUMNS)
    monkeypatch.setattr(pd, "read_csv", lambda *args, **kwargs: synthetic.copy())
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.sidebar.radio[0].set_value("Verified CSV").run()
    assert not app.exception
    assert len(app.metric) == 3
    assert app.metric[0].value == "120.00"
    assert len(app.get("plotly_chart")) == 2
    app.sidebar.multiselect[0].set_value([]).run()
    assert not app.exception
    assert app.warning[0].value == "Select at least one fiscal year."
