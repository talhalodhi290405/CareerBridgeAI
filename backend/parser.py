import pdfplumber

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    test_pdf = "test.pdf"
    print(f"Extracting text from {test_pdf}...")
    # This will fail if test.pdf doesn't exist, but it's a basic script as requested
    text = extract_text_from_pdf(test_pdf)
    if text:
        print("Extracted Text:\n", text)
    else:
        print("No text extracted or file not found.")
