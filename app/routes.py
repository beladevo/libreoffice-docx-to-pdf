from flask import Blueprint, request, jsonify, send_file
from .utils import convert_docx_to_pdf, download_file
import tempfile
import os
import time
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
import logging

convert_bp = Blueprint("convert", __name__)
logger = logging.getLogger(__name__)

@convert_bp.route("/convert", methods=["POST"])
def convert():
    temp_input_path = None
    temp_output_path = None
    start_time = time.time()

    try:
        method = request.form.get('method', '')

        if method == 'file':
            file = request.files.get("file")
            if not file:
                logger.error("No file provided in the request.")
                return jsonify({"error": "No file provided"}), 400

            if file.filename.split(".")[-1].lower() != "docx":
                logger.error("Invalid file format provided.")
                return jsonify({"error": "Invalid file format"}), 400

            filename = secure_filename(file.filename)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_input:
                file.save(temp_input.name)
                temp_input_path = temp_input.name

        elif method == 'ms':
            file_bytes = request.data
            if not file_bytes:
                logger.error("No byte stream provided in the request.")
                return jsonify({"error": "No byte stream provided"}), 400

            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_input:
                temp_input.write(file_bytes)
                temp_input_path = temp_input.name

        elif method == 'url':
            file_url = request.form.get('fileUrl')
            if not file_url:
                logger.error("No URL provided in the request.")
                return jsonify({"error": "No URL provided"}), 400

            filename = secure_filename(file_url.split('/')[-1])
            temp_input_path = download_file(file_url, filename)

        else:
            logger.error("Invalid method provided.")
            return jsonify({"error": "Invalid method provided"}), 400

        logger.info(f"Received file, saved to: {temp_input_path}")

        with ThreadPoolExecutor() as executor:
            temp_output_path = executor.submit(
                convert_docx_to_pdf, temp_input_path
            ).result()

        logger.info(f"Conversion successful, sending file: {temp_output_path}")

        return send_file(
            temp_output_path, as_attachment=True, download_name="converted.pdf"
        )

    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        duration = time.time() - start_time
        logger.info(f"Request processed in {duration:.2f} seconds")
        # if temp_input_path and os.path.exists(temp_input_path):
        #     os.remove(temp_input_path)
        # if temp_output_path and os.path.exists(temp_output_path):
        #     os.remove(temp_output_path)
