import json
from pathlib import Path
from mistralai import Mistral, DocumentURLChunk, ImageURLChunk, TextChunk

api_key = "jYMyrth466WouCOlPfiDhIwtrvR7vXCx" # Replace with your API key
client = Mistral(api_key=api_key)


def parse_pdf(filepath: str, json: bool = True) -> dict:
    # Verify PDF file exists
    pdf_file = Path(filepath)
    assert pdf_file.is_file()

    # Upload PDF file to Mistral's OCR service
    uploaded_file = client.files.upload(
        file={
            "file_name": pdf_file.stem,
            "content": pdf_file.read_bytes(),
        },
        purpose="ocr",
    )

    # Get URL for the uploaded file
    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

    # Process PDF with OCR, including embedded images
    pdf_response = client.ocr.process(
        document=DocumentURLChunk(document_url=signed_url.url),
        model="mistral-ocr-latest",
        include_image_base64=True
    )

    if json:
        # Convert response to JSON format
        response_dict = json.loads(pdf_response.model_dump_json())

        return response_dict
    else:
        return pdf_response
