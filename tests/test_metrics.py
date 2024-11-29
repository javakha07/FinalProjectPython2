import pytest
from src.metrics import calculate_metrics

def test_calculate_metrics():
    # Test data
    test_data = [
        {"metric": "Total Revenue", "amount_month_usd": "100000"},
        {"metric": "Gross Profit", "amount_month_usd": "40000"},
        {"metric": "Operating Profit (EBIT)", "amount_month_usd": "30000"}
    ]
    
    # Calculate metrics
    metrics = calculate_metrics(test_data)
    
    # Assert expected results
    assert metrics["Gross Profit Margin"] == 40.0
    assert metrics["Operating Profit Margin"] == 30.0

def test_calculate_metrics_zero_revenue():
    test_data = [
        {"metric": "Total Revenue", "amount_month_usd": "0"},
        {"metric": "Gross Profit", "amount_month_usd": "0"}
    ]
    
    metrics = calculate_metrics(test_data)
    assert metrics["Gross Profit Margin"] == 0.0