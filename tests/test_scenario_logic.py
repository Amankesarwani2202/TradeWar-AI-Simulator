import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app


def test_tariff_change_affects_scenario_output():
    df = app.generate_trade_data()
    scenario_up = app.build_country_scenario(df, "China", "Electronics", 25, "US")
    scenario_down = app.build_country_scenario(df, "China", "Electronics", -10, "US")

    assert scenario_up["trade_change_pct"] < 0
    assert scenario_down["trade_change_pct"] > 0
    assert scenario_up["predicted_export_bn"] < scenario_up["baseline_export_bn"]
    assert scenario_down["predicted_export_bn"] > scenario_down["baseline_export_bn"]

    impact = scenario_up["impact_df"]
    assert not impact.empty
    assert (impact["change_bn"] != 0).any()


def test_explanation_contains_economic_concept():
    df = app.generate_trade_data()
    scenario = app.build_country_scenario(df, "China", "Electronics", 25, "US")
    explanation = app.build_teaching_explanation(scenario, 25)
    assert "elasticity" in explanation.lower() or "trade diversion" in explanation.lower()
    assert "tariff" in explanation.lower()


def test_explanation_reflects_tariff_direction():
    df = app.generate_trade_data()
    scenario_up = app.build_country_scenario(df, "India", "Textiles", 15, "EU")
    scenario_down = app.build_country_scenario(df, "India", "Textiles", -10, "EU")
    explanation_up = app.build_teaching_explanation(scenario_up, 15)
    explanation_down = app.build_teaching_explanation(scenario_down, -10)

    assert "increase" in explanation_up.lower() or "higher" in explanation_up.lower()
    assert "cut" in explanation_down.lower() or "reduce" in explanation_down.lower()


def test_horizon_changes_scenario_projection():
    df = app.generate_trade_data()
    short_horizon = app.build_country_scenario(df, "China", "Electronics", 25, "US", projection_horizon=1)
    longer_horizon = app.build_country_scenario(df, "China", "Electronics", 25, "US", projection_horizon=5)

    assert short_horizon["predicted_export_bn"] != longer_horizon["predicted_export_bn"]


def test_scenario_network_changes_with_tariff():
    base_graph, _, _ = app.build_trade_network()
    positive = app.build_scenario_trade_network(base_graph, "China", "Electronics", 25, "US")
    negative = app.build_scenario_trade_network(base_graph, "China", "Electronics", -10, "US")

    positive_weight = positive[0]["China"]["US"]["weight"]
    negative_weight = negative[0]["China"]["US"]["weight"]
    assert positive_weight != negative_weight


def test_financial_summary_has_expected_fields():
    summary = app.build_financial_summary("India", "SPY", None)
    assert "country" in summary
    assert "market_snapshot" in summary
    assert "demographics" in summary


def test_policy_shock_changes_scenario_outlook():
    base = app.build_policy_shock_summary("None", 0)
    shocked = app.build_policy_shock_summary("Post-9/11 US financial stabilization", 8)
    assert "No historical policy shock" in base
    assert "Historical scenario" in shocked
    assert "8%" in shocked or "-8%" in shocked
