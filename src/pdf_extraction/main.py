from fastapi import FastAPI, File, UploadFile, HTTPException
import pymupdf  # PyMuPDF

app = FastAPI()

@app.post("/v1/extract-sentences")
async def extract_sentences(pdf_file: UploadFile = File(...)):
    # 1. Validate File Type
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    try:
        # 2. Read the file into memory
        file_content = await pdf_file.read()

        # 3. Open the PDF from the memory stream
        # "stream" allows us to open bytes directly without saving to disk first
        doc = pymupdf.open(stream=file_content, filetype="pdf")

        extracted_text = ""
        for page in doc:
            extracted_text += page.get_text()

        # 1. Capture the page count while the document is still open
        page_count = len(doc)

        # 2. NOW close the document
        doc.close()

        # 3. Return the data
        return {
            "filename": pdf_file.filename,
            "page_count": page_count,  # Use the variable we saved earlier
            "content": extracted_text
        }

    except Exception as e:
        # Catch errors (e.g., corrupted PDF)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)