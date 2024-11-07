import pandas as pd
import glob
import camelot as cam
import streamlit as st
from io import BytesIO

def vat_data_extraction(files, output_name, fiscal_year):
    cat = ['Particulars',
           'Sales',
           'Taxable Sales',
           'Export',
           'Non-Taxable-sales',
           'Purchase/Import',
           'Taxable Purchase',
           'Taxable Import',
           'Non-Taxable Purchase',
           'Non-Taxable Import',
           'Others',
           'Other Adjustment',
           'Total',
           'Debit-Credit',
           'Previous Month VAT Credit',
           'Net VAT Payable',
           'VAT Refund Claim',
           'VAT Refund Claim Basis']
    
    df = pd.DataFrame(cat)
    for file in files:
        file_name = file.name
        print(file_name)
        with open(file_name, "wb") as f:
            f.write(file.getbuffer())
            
        table = cam.read_pdf(file_name, pages='1', flavor='lattice', encoding='utf-8')
        tab = table[0].df

        if tab.shape[1] > 4:
            try:
                tab.iloc[6, -2] = tab.iloc[6, 3]
            except:
                tab.iloc[6, -2] = 0
            try:
                tab.iloc[7, -2] = tab.iloc[7, 3]
            except:
                tab.iloc[7, -2] = 0
            try:
                tab.iloc[11, -2] = int(tab.iloc[11, 4]) - int(tab.iloc[11, 3])
            except:
                tab.iloc[11, -2] = 0
            try:
                tab.iloc[12, -2] = int(tab.iloc[12, 4]) - int(tab.iloc[12, 3])
            except:
                tab.iloc[12, -2] = 0

        try:
            credit_table = cam.read_pdf(file_name, pages='1', flavor='stream', encoding='utf-8')[0].df
            if credit_table.shape[1] > 4:
                credit_amount = credit_table.iloc[15, 4]
                vat_claim = credit_table.iloc[17, 4]
            else:
                credit_amount = ""
                vat_claim = ""
        except:
            credit_amount = ""
            vat_claim = ""

        tab.loc[14, 2] = credit_amount
        tab.loc[17, 2] = vat_claim
        print(credit_amount, vat_claim)
        df['{} Gross Amount'.format(file_name[:7])], df['{} Tax'.format(file_name[:7])] = [tab[2], tab.iloc[:, -2]]

    # Clean data and transpose
    df = df.replace('^0 .*', 0, regex=True)
    df = df.replace('_vat_return_work', '')
    df = df.fillna(0)
    df = df.rename(columns={0: 'Particulars'})
    df1 = df.iloc[1:].T

    # Separate gross amount and vat amount into different dataframe
    df_gross = df1.filter(like="Gross Amount", axis=0)
    df_vat = df1.filter(like="Tax", axis=0)

    # Cleaning Gross amount dataframe
    df_gross.columns = cat[1:]
    df_gross = df_gross.add_suffix('_amount')

    # Cleaning VAT amount dataframe
    df_vat.columns = cat[1:]
    df_vat = df_vat.add_suffix('_vat')

    # Making same index
    df_vat.index = df_gross.index

    # Combining two dataframe and cleaning data
    result = pd.concat([df_gross, df_vat], axis=1)
    result = result.reindex(sorted(result.columns), axis=1).fillna(0)
    cols = result.columns
    result[cols] = result[cols].apply(pd.to_numeric, errors='coerce')

    # Arrange columns as specified
    ordered_columns = [
        'Particulars_amount',
        'Export_amount', 'Export_vat',
        'Non-Taxable-sales_amount',
        'Taxable Sales_amount', 'Taxable Sales_vat',
        'Non-Taxable Purchase_amount',
        'Taxable Purchase_amount', 'Taxable Purchase_vat',
        'Non-Taxable Import_amount',
        'Taxable Import_amount', 'Taxable Import_vat',
        'Total_vat'
    ]
    for col in ordered_columns:
        if col not in result.columns:
            result[col] = 0  # Add missing columns with 0 values
    
    result = result[ordered_columns + [col for col in result.columns if col not in ordered_columns]]

    output_file = BytesIO()
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        result.to_excel(writer, index=True, sheet_name='Sheet1')

    output_file.seek(0)
    
    st.success("Complete! You can download the saved file.")
    st.download_button(
        label="Download Excel file",
        data=output_file,
        file_name='{}_{}.xlsx'.format(output_name, fiscal_year),
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    return result

def vat_data_extraction_page():
    st.title("VAT Data Extraction")

    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
    output_name = st.text_input("Enter Output Name")
    fiscal_year = st.text_input("Enter Fiscal Year")

    if st.button("Extract VAT Data"):
        if uploaded_files and output_name and fiscal_year:
            result = vat_data_extraction(uploaded_files, output_name, fiscal_year)
            st.dataframe(result)
        else:
            st.error("Please provide all the required inputs and upload at least one PDF file")

def vat_main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("You must be logged in to view this page.")
        st.stop()
    vat_data_extraction_page()


if __name__ == "__main__":
    vat_main()
