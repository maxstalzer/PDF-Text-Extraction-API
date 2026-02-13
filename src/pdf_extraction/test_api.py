import requests

url = "http://127.0.0.1:8000/v1/extract-sentences"
file_path = "sample.pdf"  # Make sure this file exists!

# 'pdf_file' key must match the argument name in your FastAPI function
with open(file_path, "rb") as f:
    files = {"pdf_file": (file_path, f, "application/pdf")}
    response = requests.post(url, files=files)

print(response.json())