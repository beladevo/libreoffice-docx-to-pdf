from flask import Flask, request, send_file, jsonify
import os
import subprocess
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import tempfile
import time
from io import BytesIO
from urllib.parse import urlparse

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

executor = ThreadPoolExecutor(max_workers=4)

def is_valid_url(url):
    """Validate the URL to prevent security issues."""
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])

def download_docx_from_url(url):
    try:
        if not is_valid_url(url):
            raise ValueError("Invalid URL provided.")
        
        logging.info(f"Downloading DOCX file from {url}...")
        start_time = time.time()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_docx_file:
            urllib.request.urlretrieve(url, temp_docx_file.name)
            temp_docx_path = temp_docx_file.name
        end_time = time.time()
        logging.info(f"Download successful to {temp_docx_path}, Time taken: {end_time - start_time:.2f} seconds")
        return temp_docx_path
    except Exception as e:
        logging.error(f"Error downloading DOCX file: {e}")
        return None

def convert_to_pdf(temp_docx_path):
    try:
        logging.info(f"Converting {temp_docx_path} to PDF...")
        start_time = time.time()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf_file:
            pdf_path = temp_pdf_file.name
            subprocess.run(
                ['soffice', '--headless', '--convert-to', 'pdf', temp_docx_path, '--outdir', os.path.dirname(pdf_path)],
                check=True
            )
        end_time = time.time()
        logging.info(f"Conversion successful, Time taken: {end_time - start_time:.2f} seconds")
        return pdf_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess error: {e}")
        return None

@app.route('/docxToPdf', methods=['POST'])
def docx_to_pdf():
    file = request.files.get('file')
    url = request.form.get('url')

    if not file and not url:
        logging.error("No file or URL provided in the request")
        return jsonify({"error": "No file or URL provided in the request"}), 400

    try:
        if file:
            if file.filename == '':
                logging.error("No file selected for uploading")
                return jsonify({"error": "No file selected for uploading"}), 400

            if not file.filename.endswith('.docx'):
                logging.error("Unsupported file format. Please upload a DOCX file.")
                return jsonify({"error": "Unsupported file format. Please upload a DOCX file."}), 400

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_docx_file:
                file.save(temp_docx_file.name)
                temp_docx_path = temp_docx_file.name

        elif url:
            temp_docx_path = download_docx_from_url(url)
            if not temp_docx_path:
                return jsonify({"error": "Failed to download DOCX file from the provided URL"}), 500

        # Start the conversion in a separate thread
        future = executor.submit(convert_to_pdf, temp_docx_path)
        pdf_path = future.result()

        if pdf_path:
            # Clean up DOCX file after conversion
            os.remove(temp_docx_path)

            with open(pdf_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()

            # Clean up PDF file after reading
            os.remove(pdf_path)

            pdf_io = BytesIO(pdf_bytes)
            pdf_io.seek(0)

            logging.info("PDF file ready for download.")
            return send_file(
                pdf_io,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='converted.pdf'
            )
        else:
            logging.error("Failed to convert DOCX to PDF")
            return jsonify({"error": "Failed to convert DOCX to PDF"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
