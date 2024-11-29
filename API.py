import csv
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise RuntimeError("The OPENAI_API_KEY environment variable is not set in .env file.")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY


def csv_to_json(file_path):
    """
    Transforms CSV file into JSON.
    :param file_path: Path to the CSV file.
    :return: JSON data as a list of dictionaries.
    """
    data = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' was not found.")
    except Exception as e:
        raise RuntimeError(f"An error occurred while reading the CSV file: {e}")
    return data


def calculate_metrics(pnl_data):
    """
    Calculates financial analytical metrics based on formulas.
    :param pnl_data: JSON data as a list of dictionaries (P&L structure).
    :return: Calculated metrics as a dictionary.
    """
    metrics_dict = {}
    for item in pnl_data:
        try:
            metric_name = item.get('metric', '').strip()
            amount = item.get('amount_month_usd')
            # Handle different data types
            if isinstance(amount, str):
                amount = amount.replace(',', '').strip()
            elif isinstance(amount, (int, float)):
                amount = float(amount)
            else:
                amount = 0.0
            metrics_dict[metric_name] = float(amount) if amount else 0.0
        except (ValueError, KeyError):
            metrics_dict[metric_name] = 0.0

    calculated_metrics = {}
    total_revenue = metrics_dict.get("Total Revenue", 0.0)
    net_profit_before_tax = metrics_dict.get("Net Profit Before Tax", 0.0)

    try:
        calculated_metrics["Gross Profit Margin"] = (
            (metrics_dict.get("Gross Profit", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Operating Profit Margin"] = (
            (metrics_dict.get("Operating Profit (EBIT)", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Net Profit Margin"] = (
            (metrics_dict.get("Net Profit After Tax", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["COGS Percentage"] = (
            (metrics_dict.get("Total COGS", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Operating Expense Ratio"] = (
            (metrics_dict.get("Total Operating Expenses", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Marketing Efficiency"] = (
            metrics_dict.get("Total Revenue", 0.0) / metrics_dict.get("Marketing & Advertising", 1.0)
            if metrics_dict.get("Marketing & Advertising", 0.0) else 0.0
        )
        calculated_metrics["Salaries & Wages Percentage"] = (
            (metrics_dict.get("Salaries & Wages", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Interest Coverage Ratio"] = (
            metrics_dict.get("Operating Profit (EBIT)", 0.0) / metrics_dict.get("Interest Expense", 1.0)
            if metrics_dict.get("Interest Expense", 0.0) else 0.0
        )
        calculated_metrics["Depreciation Percentage"] = (
            (metrics_dict.get("Depreciation", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Other Expenses Percentage"] = (
            (metrics_dict.get("Other Expenses", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Net Other Income Percentage"] = (
            (metrics_dict.get("Net Other Income/Expense", 0.0) / total_revenue) * 100
            if total_revenue else 0.0
        )
        calculated_metrics["Income Tax Percentage"] = (
            (metrics_dict.get("Income Tax Expense", 0.0) / net_profit_before_tax) * 100
            if net_profit_before_tax else 0.0
        )
    except ZeroDivisionError:
        raise ValueError("Division by zero encountered in metric calculations.")

    return calculated_metrics


def generate_report(data):
    """
    Generates a report with insights and recommendations based on data.
    :param data: Dictionary containing either metrics or a prompt.
    :return: AI-generated report as a string.
    """
    if "prompt" in data:
        prompt = data["prompt"]
    else:
        prompt = (
            "You are a financial analyst. Based on the following financial metrics, generate a report that includes "
            "insights on the current state of the business and actionable recommendations for improvement. "
            "\n\nMetrics:\n"
        )
        for metric, value in data.items():
            prompt += f"{metric}: {value:.2f}\n"

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial advisor providing clear, actionable insights."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        raise RuntimeError(f"OpenAI API error: {e}")


if __name__ == "__main__":
    # Example usage
    csv_file_path = "Profit_and_Loss_Statement.csv"  # Replace with your actual file path
    try:
        json_data = csv_to_json(csv_file_path)
        metrics = calculate_metrics(json_data)
        report = generate_report(metrics)
        print("\nGenerated Report:\n")
        print(report)
    except Exception as e:
        print(f"Error: {e}")

        
