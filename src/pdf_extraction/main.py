import pymupdf
import re
import unicodedata
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="DTU PDF Extractor (Max Performance)")

# --- COMPILED PATTERNS ---
# 1. Fix Hyphenation ("config- \n ured" -> "configured")
RE_HYPHEN = re.compile(r'(\w+)-\s*\n\s*(\w+)')

# 2. Fix Broken URLs ("scholia. \n toolforge")
RE_URL = re.compile(r'(http[s]?://\S+?)\.\s*\n\s*([a-z0-9])')

# 3. Fix Punctuation Spacing ("queried ." -> "queried.")
RE_PUNCT_SPACE = re.compile(r'\s+([.!?])')

# 4. Split Sentences
RE_SPLIT = re.compile(r'(?<=[.!?])\s+')

def clean_and_split_text(raw_text: str) -> list[str]:
    """
    Optimized pipeline with C-accelerated string ops.
    """
    # 1. Unicode Normalization (Fast C-lib)
    text = unicodedata.normalize("NFKD", raw_text)

    # 2. Structural Fixes (Regex)
    text = RE_HYPHEN.sub(r'\1\2', text)
    text = RE_URL.sub(r'\1.\2', text)

    # 3. Whitespace Normalization (Fastest Python Method)
    # Replaces re.sub(r'\s+', ' ')
    text = " ".join(text.split())

    # 4. Punctuation Cleanup
    text = RE_PUNCT_SPACE.sub(r'\1', text)

    # 5. Split
    sentences = RE_SPLIT.split(text)

    # 6. Filter
    return [s.strip() for s in sentences if len(s.strip()) > 10 and not s.isdigit()]

@app.post("/v1/extract-sentences")
async def extract_sentences(pdf_file: UploadFile = File(...)):
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type.")

    try:
        content = await pdf_file.read()
        
        # Open PDF from memory
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            
            all_text_list = []
            
            for page in doc:
                # sort=True is the bottleneck (~300ms) but REQUIRED for 2-column accuracy.
                # It forces the C engine to calculate reading order geometrically.
                blocks = page.get_text("blocks", sort=True)
                
                for b in blocks:
                    # b[6] is block type (0=text, 1=image). We only want text.
                    if b[6] == 0:
                        block_text = b[4].strip()
                        
                        # --- HEADER LOGIC (O(1) Cost) ---
                        # If a block is a header (short, capital, no punctuation),
                        # force a period so it doesn't merge with the next sentence.
                        if len(block_text) < 100 and block_text and block_text[0].isupper():
                            if block_text[-1] not in ".!:;?":
                                block_text += "."
                        
                        all_text_list.append(block_text)

        # Join once
        full_text = "\n".join(all_text_list)

        sentences = clean_and_split_text(full_text)

        # Return JSONResponse to skip Pydantic validation overhead
        return JSONResponse(content={"sentences": sentences})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # If on Linux/Mac, uvicorn uses uvloop automatically for extra speed.
    uvicorn.run(app, host="0.0.0.0", port=8000)