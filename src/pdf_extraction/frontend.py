import streamlit as st
import requests

# CONSTANTS
BACKEND_URL = "http://127.0.0.1:8000/v1/extract-sentences"

st.set_page_config(page_title="PDF Extractor", page_icon="📄")

st.title("📄 PDF Text Extractor")
st.write("Upload a PDF to extract its text via the FastAPI backend.")

# 1. File Uploader Widget
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Show some file details
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
    st.write(file_details)

    # 2. Button to trigger extraction
    if st.button("Extract Text"):
        with st.spinner("Extracting text..."):
            try:
                # Prepare the file for the request
                files = {"pdf_file": (uploaded_file.name, uploaded_file, "application/pdf")}
                
                # Send POST request to FastAPI
                response = requests.post(BACKEND_URL, files=files)
                
                # Check for successful response
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("Extraction Complete!")
                    
                    # Display Metadata
                    col1, col2 = st.columns(2)
                    col1.metric("Filename", data.get("filename", "Unknown"))
                    col2.metric("Page Count", data.get("page_count", 0))
                    
                    # Display Content
                    st.subheader("Extracted Content:")
                    st.text_area("Raw Text", data.get("content", ""), height=300)
                    
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend. Is FastAPI running?")
            except Exception as e:
                st.error(f"An error occurred: {e}")