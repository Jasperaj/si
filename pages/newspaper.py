import streamlit as st
import time
import requests

# Function to download and save the PDF of Kantipur newspaper
def download_kantipur():
    today = time.localtime()
    date_str = '{}-{}-{}'.format(str(today.tm_year), str(today.tm_mon).zfill(2), str(today.tm_mday).zfill(2))
    url = f'https://epaper.ekantipur.com/kantipur/download/{date_str}'
    response = requests.get(url)

    if response.status_code == 200:
        with open('ekantipur-{}.pdf'.format(str(date_str)), 'wb') as f:
            f.write(response.content)
        return 'ktmpost {}.pdf'.format(str(date_str))
    else:
        st.error("Failed to download Kantipur newspaper.")
        return None

# Function to download and save the PDF of Kathmandu Post newspaper
def download_kathmandupost():
    today = time.localtime()
    date_str = '{}-{}-{}'.format(str(today.tm_year), str(today.tm_mon).zfill(2), str(today.tm_mday).zfill(2))
    url = f'https://epaper.ekantipur.com/kathmandupost/download/{date_str}'
    response = requests.get(url)

    if response.status_code == 200:
        with open('ktmpost {}.pdf'.format(str(date_str)), 'wb') as f:
            f.write(response.content)
        return 'ktmpost {}.pdf'.format(str(date_str))
    else:
        st.error("Failed to download Kathmandu Post newspaper.")
        return None

# Main function for the Streamlit app
def newspaper_main():
    st.title("Newspaper Viewer")

    option = st.selectbox("Choose a newspaper to view:", ("Kantipur", "Kathmandu Post"))

    if st.button("View"):
        if option == "Kantipur":
            pdf_file = download_kantipur()
        else:
            pdf_file = download_kathmandupost()

        if pdf_file:
            st.success(f"{option} loaded successfully!")
            with open(pdf_file, "rb") as file:
                base64_pdf = file.read()
                st.download_button(
                    label=f"Preview of {option}",
                    data=base64_pdf,
                    file_name=pdf_file,
                    mime="application/pdf"
                )

# Run the main function
if __name__ == "__main__":
    newspaper_main()
