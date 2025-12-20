from flask import Blueprint, request, jsonify, send_file, after_this_request
from .utils import convert_office_to_pdf, download_file
import tempfile
import os
import time
from werkzeug.utils import secure_filename
import logging
from urllib.parse import urlparse, unquote

convert_bp = Blueprint("convert", __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"doc", "docx", "xls", "xlsx", "ppt", "pptx"}

def get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()

@convert_bp.route("/convert", methods=["POST"])
def convert():
    temp_input_path = None
    temp_output_path = None
    original_filename = None
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
            original_filename = filename

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_input:
                file.save(temp_input.name)
                temp_input_path = temp_input.name

        # 'ms' (raw byte stream) method removed — accept only file uploads or URL
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
            original_filename = filename

            ext = get_extension(filename)
            if ext not in ALLOWED_EXTENSIONS:
                return jsonify({"error": "Invalid file format"}), 400

            temp_input_path = download_file(file_url, filename)

        else:
            return jsonify({"error": "Invalid method provided"}), 400

        logger.info(f"Received file, saved to: {temp_input_path}")

        if not temp_input_path or not os.path.exists(temp_input_path):
            return jsonify({"error": "Input file not available"}), 400

        temp_output_path = convert_office_to_pdf(temp_input_path)

        if not temp_output_path or not os.path.exists(temp_output_path):
            return jsonify({"error": "Conversion failed: output missing"}), 500
        # Cleanup handled in after_this_request
        @after_this_request
        def cleanup(response):
            try:
                if temp_input_path and os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                if temp_output_path and os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
            except Exception:
                logger.exception("Cleanup failed")
            return response

        # use original filename but with .pdf extension for download
        if original_filename:
            base = os.path.splitext(original_filename)[0]
            download_name = secure_filename(f"{base}.pdf")
        else:
            download_name = "converted.pdf"

        return send_file(
            temp_output_path,
            as_attachment=True,
            download_name=download_name,
        )

    except Exception as e:
        logger.exception("Conversion error")
        return jsonify({"error": str(e)}), 500

    finally:
        duration = time.time() - start_time
        logger.info(f"Request processed in {duration:.2f} seconds")