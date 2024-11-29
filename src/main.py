import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from API import generate_report, calculate_metrics

def validate_csv_structure(df):
    """
    Validates the CSV structure and returns error messages if any
    """
    errors = []
    
    # Check required columns
    required_columns = {
        'P&L Statement': ['metric', 'amount_month_usd'],
        'Personal Finance': ['Category', 'Amount', 'Date']
    }
    
    # Detect file type based on columns
    if all(col in df.columns for col in required_columns['P&L Statement']):
        file_type = 'P&L Statement'
    elif all(col in df.columns for col in required_columns['Personal Finance']):
        file_type = 'Personal Finance'
    else:
        errors.append("Unable to determine file type. Missing required columns.")
        return errors, None
    
    # Validate data types
    if file_type == 'Personal Finance':
        # Check Date format
        try:
            pd.to_datetime(df['Date'])
        except:
            errors.append("Date column contains invalid dates")
            
        # Check Amount format
        if not pd.to_numeric(df['Amount'], errors='coerce').notna().all():
            errors.append("Amount column contains non-numeric values")
            
    return errors, file_type

def analyze_personal_finance(df):
    """
    Analyze personal finance data with income and expenses
    """
    # Separate income and expenses
    df['Type'] = df['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
    
    # Calculate totals
    total_income = df[df['Amount'] > 0]['Amount'].sum()
    total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
    net_savings = total_income - total_expenses
    
    # Category analysis
    category_summary = df.groupby(['Category', 'Type'])['Amount'].sum().reset_index()
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': net_savings,
        'category_summary': category_summary
    }

def create_visualizations(df):
    """
    Create visualizations for personal finance data
    """
    figures = []
    
    # Income vs Expenses Pie Chart
    income_df = df[df['Amount'] > 0]
    expense_df = df[df['Amount'] < 0].copy()
    expense_df['Amount'] = abs(expense_df['Amount'])
    
    fig1 = px.pie(
        values=[income_df['Amount'].sum(), expense_df['Amount'].sum()],
        names=['Income', 'Expenses'],
        title='Income vs Expenses Distribution'
    )
    figures.append(fig1)
    
    # Category breakdown
    fig2 = px.bar(
        df.groupby('Category')['Amount'].sum().sort_values().reset_index(),
        x='Amount',
        y='Category',
        title='Cash Flow by Category',
        orientation='h'
    )
    figures.append(fig2)
    
    # Daily balance trend
    df_sorted = df.sort_values('Date')
    df_sorted['Cumulative Balance'] = df_sorted['Amount'].cumsum()
    
    fig3 = px.line(
        df_sorted,
        x='Date',
        y='Cumulative Balance',
        title='Balance Trend Over Time'
    )
    figures.append(fig3)
    
    return figures

def generate_ai_analysis(data):
    """
    Generate AI analysis of the financial data
    """
    prompt = (
        "As a financial advisor, analyze this personal finance data and provide insights:\n"
        f"Total Income: ${data['total_income']:,.2f}\n"
        f"Total Expenses: ${data['total_expenses']:,.2f}\n"
        f"Net Savings: ${data['net_savings']:,.2f}\n"
        "Provide budget analysis, savings recommendations, and potential areas for improvement."
    )
    
    return generate_report({"prompt": prompt})

def analyze_investment_portfolio(df):
    """
    Analyze investment portfolio data
    """
    df['Gain_Loss'] = df['Current_Value'] - df['Purchase_Price']
    df['Return_Percentage'] = (df['Gain_Loss'] / df['Purchase_Price']) * 100
    
    total_investment = df['Purchase_Price'].sum()
    current_value = df['Current_Value'].sum()
    total_gain_loss = current_value - total_investment
    avg_return = df['Annual_Return'].mean()
    
    # Asset type distribution
    type_distribution = df.groupby('Type')['Current_Value'].sum()
    
    return {
        'total_investment': total_investment,
        'current_value': current_value,
        'total_gain_loss': total_gain_loss,
        'avg_return': avg_return,
        'type_distribution': type_distribution
    }

def create_investment_visualizations(df):
    """
    Create visualizations for investment portfolio
    """
    figures = []
    
    # Asset Type Distribution Pie Chart
    fig1 = px.pie(
        df,
        values='Current_Value',
        names='Type',
        title='Portfolio Distribution by Asset Type'
    )
    figures.append(fig1)
    
    # Returns by Asset Bar Chart
    fig2 = px.bar(
        df,
        x='Asset',
        y='Annual_Return',
        color='Type',
        title='Annual Returns by Asset'
    )
    figures.append(fig2)
    
    # Gain/Loss Waterfall
    fig3 = go.Figure(go.Waterfall(
        name="Portfolio",
        orientation="v",
        measure=["relative"] * len(df),
        x=df['Asset'],
        y=df['Gain_Loss'],
        text=df['Gain_Loss'].round(2),
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    fig3.update_layout(title="Gain/Loss by Asset")
    figures.append(fig3)
    
    return figures

def clean_and_validate_data(df, analysis_type):
    """
    Clean and validate data based on analysis type
    """
    try:
        if analysis_type == "Personal Finance":
            # Clean Date column
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Check for and remove rows with invalid dates
            invalid_dates = df['Date'].isna()
            if invalid_dates.any():
                st.warning(f"Found {invalid_dates.sum()} rows with invalid dates. These rows will be excluded.")
                df = df.dropna(subset=['Date'])
            
            # Clean Amount column
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            
            # Check for and remove rows with invalid amounts
            invalid_amounts = df['Amount'].isna()
            if invalid_amounts.any():
                st.warning(f"Found {invalid_amounts.sum()} rows with invalid amounts. These rows will be excluded.")
                df = df.dropna(subset=['Amount'])
            
        elif analysis_type == "Investment Portfolio":
            # Clean Purchase_Date
            df['Purchase_Date'] = pd.to_datetime(df['Purchase_Date'], errors='coerce')
            
            # Clean numeric columns
            numeric_columns = ['Purchase_Price', 'Current_Value', 'Annual_Return']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove rows with any invalid data
            initial_rows = len(df)
            df = df.dropna()
            if len(df) < initial_rows:
                st.warning(f"Removed {initial_rows - len(df)} rows with invalid data.")
        
        return df
    
    except Exception as e:
        raise ValueError(f"Error cleaning data: {str(e)}")

def main():
    st.set_page_config(layout="wide")
    
    st.title("Financial Analysis Dashboard")
    
    # Create sidebar for analysis type selection
    st.sidebar.header("Analysis Options")
    analysis_type = st.sidebar.selectbox(
        "Choose Analysis Type",
        ["Select Type...", "Profit & Loss Statement", "Personal Finance", "Investment Portfolio"]
    )
    
    # Show sample data option
    use_sample_data = st.sidebar.checkbox("Use Sample Data")
    
    if analysis_type == "Select Type...":
        st.info("Please select an analysis type from the sidebar to begin.")
        return
    
    try:
        if use_sample_data:
            if analysis_type == "Profit & Loss Statement":
                df = pd.read_csv("sample_data/profit_loss.csv")
            elif analysis_type == "Personal Finance":
                df = pd.read_csv("sample_data/personal_finance.csv")
            else:  # Investment Portfolio
                df = pd.read_csv("sample_data/investment_portfolio.csv")
            st.success("Using sample data for demonstration")
        else:
            uploaded_file = st.file_uploader(f"Upload your {analysis_type} CSV file", type=["csv"])
            if not uploaded_file:
                st.warning("Please upload a CSV file or use sample data")
                return
            df = pd.read_csv(uploaded_file)
        
        # Clean and validate the data
        df = clean_and_validate_data(df, analysis_type)
        
        # Display raw data with download option
        st.subheader("Raw Data")
        st.dataframe(df)
        
        # Add download button for cleaned data
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download cleaned data as CSV",
            data=csv,
            file_name="cleaned_data.csv",
            mime="text/csv"
        )
        
        # Rest of your analysis code...
        if analysis_type == "Profit & Loss Statement":
            pnl_data = df.to_dict('records')
            metrics = calculate_metrics(pnl_data)
            
            st.header("Financial Metrics")
            metrics_df = pd.DataFrame(list(metrics.items()), 
                                    columns=['Metric', 'Value'])
            st.dataframe(metrics_df)
            
            if st.button("Generate P&L Insights"):
                with st.spinner("Analyzing..."):
                    report = generate_report(metrics)
                    st.write(report)
                    
        elif analysis_type == "Personal Finance":
            analysis = analyze_personal_finance(df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Income", f"${analysis['total_income']:,.2f}")
            with col2:
                st.metric("Total Expenses", f"${analysis['total_expenses']:,.2f}")
            with col3:
                st.metric("Net Savings", f"${analysis['net_savings']:,.2f}")
            
            figures = create_visualizations(df)
            for fig in figures:
                st.plotly_chart(fig, use_container_width=True)
                
        else:  # Investment Portfolio
            analysis = analyze_investment_portfolio(df)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Investment", f"${analysis['total_investment']:,.2f}")
            with col2:
                st.metric("Current Value", f"${analysis['current_value']:,.2f}")
            with col3:
                st.metric("Total Gain/Loss", f"${analysis['total_gain_loss']:,.2f}")
            with col4:
                st.metric("Average Return", f"{analysis['avg_return']:.2f}%")
            
            figures = create_investment_visualizations(df)
            for fig in figures:
                st.plotly_chart(fig, use_container_width=True)
        
        # Common Q&A section
        st.header("Ask Questions About Your Data")
        user_question = st.text_input("What would you like to know about your financial data?")
        if user_question and st.button("Get Answer"):
            with st.spinner("Analyzing..."):
                question_prompt = (
                    f"Based on the {analysis_type} data provided, please answer this question:\n"
                    f"{user_question}\n"
                    "Provide a detailed, analytical response."
                )
                answer = generate_report({"prompt": question_prompt})
                st.write(answer)
                
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.error("Please ensure your CSV file matches the required format:")
        if analysis_type == "Personal Finance":
            st.code("""
Expected CSV format:
Category,Amount,Date
Salary,5000,2024-03-01
Rent,-1800,2024-03-02
            """)
        elif analysis_type == "Investment Portfolio":
            st.code("""
Expected CSV format:
Asset,Type,Purchase_Date,Purchase_Price,Current_Value,Annual_Return
AAPL,Stock,2024-03-01,150.25,180.50,20.13
            """)
        else:
            st.code("""
Expected CSV format:
metric,amount_month_usd
Total Revenue,250000
            """)

if __name__ == "__main__":
    main() 