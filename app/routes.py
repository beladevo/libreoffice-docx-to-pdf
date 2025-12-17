from flask import Blueprint, request, jsonify, send_file
from .utils import convert_office_to_pdf, download_file
import tempfile
import os
import time
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
import logging
from urllib.parse import urlparse, unquote

convert_bp = Blueprint("convert", __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"doc", "docx", "xls", "xlsx", "ppt", "pptx"}

def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower()

@convert_bp.route("/convert", methods=["POST"])
def convert():
    temp_input_path = None
    temp_output_path = None
    start_time = time.time()

    try:
        method = request.form.get("method", "")

        if method == "file":
            file = request.files.get("file")
            if not file or not file.filename:
                return jsonify({"error": "No file provided"}), 400

            ext = get_extension(file.filename)
            if ext not in ALLOWED_EXTENSIONS:
                return jsonify({"error": "Invalid file format"}), 400

            filename = secure_filename(file.filename)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_input:
                file.save(temp_input.name)
                temp_input_path = temp_input.name

        elif method == "ms":
            file_bytes = request.data
            ext = request.form.get("ext", "docx").lower()

            if not file_bytes:
                return jsonify({"error": "No byte stream provided"}), 400

            if ext not in ALLOWED_EXTENSIONS:
                return jsonify({"error": "Invalid file format"}), 400

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_input:
                temp_input.write(file_bytes)
                temp_input_path = temp_input.name

        elif method == "url":
            file_url = request.form.get("fileUrl")
            if not file_url:
                return jsonify({"error": "No URL provided"}), 400

            parsed = urlparse(file_url)
            raw_name = unquote(os.path.basename(parsed.path))
            filename = secure_filename(raw_name)

            ext = get_extension(filename)
            if ext not in ALLOWED_EXTENSIONS:
                return jsonify({"error": "Invalid file format"}), 400

            temp_input_path = download_file(file_url, filename)

        else:
            return jsonify({"error": "Invalid method provided"}), 400

        logger.info(f"Received file, saved to: {temp_input_path}")

        with ThreadPoolExecutor() as executor:
            temp_output_path = executor.submit(
                convert_office_to_pdf, temp_input_path
            ).result()

        return send_file(
            temp_output_path,
            as_attachment=True,
            download_name="converted.pdf",
        )

    except Exception as e:
        logger.exception("Conversion error")
        return jsonify({"error": str(e)}), 500

    finally:
        duration = time.time() - start_time
        logger.info(f"Request processed in {duration:.2f} seconds")
