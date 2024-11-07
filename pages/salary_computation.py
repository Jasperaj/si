import streamlit as st
import pandas as pd

def calculate_tax(income, status, social_security_contribution):
    tax = 0
    tax_details = []
    if status == 'Individual':
        slabs = [(500000, 0.01), (200000, 0.10), (300000, 0.20), (1000000, 0.30), (float('inf'), 0.36)]
        if social_security_contribution > 0:
            slabs[0] = (500000, 0.00)  # Changing the first slab rate to 0% if Social Security contribution exists
    else:
        slabs = [(600000, 0.01), (200000, 0.10), (300000, 0.20), (900000, 0.30), (float('inf'), 0.36)]
        if social_security_contribution > 0:
            slabs[0] = (600000, 0.00)  # Changing the first slab rate to 0% if Social Security contribution exists

    for slab, rate in slabs:
        if income > slab:
            tax_slab = slab * rate
            tax_details.append((slab, rate * 100, tax_slab))
            tax += tax_slab
            income -= slab
        else:
            tax_slab = income * rate
            tax_details.append((income, rate * 100, tax_slab))
            tax += tax_slab
            break
    return tax, tax_details

def main():
    st.title("Nepal Personal Income Tax Calculator")
    
    # User Inputs
    st.header("Personal Information")
    resident_status = st.selectbox("Resident Status", ["Resident", "Non-Resident"])
    income = st.number_input("Annual Income (NPR)", min_value=0, value=0, step=1000)
    status = st.selectbox("Filing Status", ["Individual", "Couple"])
    
    st.header("Deductions")
    col1, col2 = st.columns(2)
    
    with col1:
        retirement_contribution = st.number_input("Contribution to Retirement Payment (NPR)", min_value=0, max_value=300000, step=1000)
        social_security_contribution = st.number_input("Social Security Fund Contribution (NPR)", min_value=0, max_value=500000, step=1000)
        donation = st.number_input("Donation to tax-exempt entities (NPR)", min_value=0, max_value=100000, step=1000)
        insurance_premium = st.number_input("Insurance Premium (NPR)", min_value=0, max_value=40000, step=1000)
        health_insurance_premium = st.number_input("Health Insurance Premium (NPR)", min_value=0, max_value=20000, step=1000)
        
    with col2:
        remote_area_allowance = st.number_input("Remote Area Allowance (NPR)", min_value=0, max_value=50000, step=1000)
        pension_income = st.number_input("Pension Income (NPR)", min_value=0, value=0, step=1000)
        house_insurance_premium = st.number_input("House Insurance Premium (NPR)", min_value=0, max_value=5000, step=100)
        foreign_allowance = st.number_input("Foreign Allowance (NPR)", min_value=0, value=0, step=1000)
        handicapped_allowance = st.number_input("Handicapped Allowance (NPR)", min_value=0, value=0, step=1000)
        medical_tax_credit = st.number_input("Medical Tax Credit (NPR)", min_value=0, max_value=750, step=50)
        
    female_tax_rebate = st.checkbox("Female Individual")

    # Initial Calculation of Deductible Limits
    one_third_income = income / 3
    max_retirement_social_deduction = min(one_third_income, retirement_contribution + social_security_contribution)
    retirement_contribution = min(retirement_contribution, max_retirement_social_deduction)
    social_security_contribution = min(social_security_contribution, max_retirement_social_deduction - retirement_contribution)

    # Calculations
    deductions = (retirement_contribution +
                  social_security_contribution +
                  donation +
                  insurance_premium +
                  health_insurance_premium +
                  remote_area_allowance +
                  house_insurance_premium +
                  medical_tax_credit)

    deductions += 0.25 * pension_income if pension_income else 0
    deductions += 0.50 * 500000 if handicapped_allowance else 0  # Assuming first tax slab is 500,000
    deductions += 0.75 * foreign_allowance if foreign_allowance else 0
    deductions = min(deductions, income)

    taxable_income = income - deductions

    if resident_status == "Non-Resident":
        tax = taxable_income * 0.25
        tax_details = [(taxable_income, 25, tax)]
    else:
        tax, tax_details = calculate_tax(taxable_income, status, social_security_contribution)
        if female_tax_rebate:
            tax *= 0.90
    
    # Displaying Breakdown
    st.header("Income and Deduction Breakdown")
    st.write(f"**Total Income:** NPR {income}")
    
    deduction_details = [
        ("Retirement Contribution", retirement_contribution),
        ("Social Security Fund Contribution", social_security_contribution),
        ("Donation", donation),
        ("Insurance Premium", insurance_premium),
        ("Health Insurance Premium", health_insurance_premium),
        ("Remote Area Allowance", remote_area_allowance),
        ("Pension Income Deduction (25%)", 0.25 * pension_income if pension_income else 0),
        ("House Insurance Premium", house_insurance_premium),
        ("Foreign Allowance Deduction (75%)", 0.75 * foreign_allowance if foreign_allowance else 0),
        ("Handicapped Allowance Deduction (50% of first slab)", 0.50 * 500000 if handicapped_allowance else 0),
        ("Medical Tax Credit", medical_tax_credit)
    ]
    
    deduction_df = pd.DataFrame(deduction_details, columns=["Deduction Type", "Amount (NPR)"])
    deduction_df.loc['Total'] = deduction_df.sum(numeric_only=True)
    st.write(deduction_df)

    st.header("Tax Computation Table")
    st.write("The following table shows how the tax is computed at each income level:")
    tax_details_df = pd.DataFrame(tax_details, columns=["Income Level (NPR)", "Tax Rate (%)", "Tax Amount (NPR)"])
    tax_details_df.loc['Total'] = tax_details_df.sum(numeric_only=True)
    st.write(tax_details_df)
    
    st.header("Net Tax Payable")
    st.write(f"**Total Tax Payable:** NPR {tax}")

if __name__ == "__main__":
    main()
