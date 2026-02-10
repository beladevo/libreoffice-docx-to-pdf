from flask import Blueprint, request, jsonify, send_file, after_this_request
from .utils import (
    convert_office_to_pdf,
    download_file,
    detect_modern_office_type,
    is_legacy_office_file,
)
from .constants import SUPPORTED_EXTENSIONS
import tempfile
import os
import time
from werkzeug.utils import secure_filename
import logging
from urllib.parse import urlparse, unquote
import shutil
convert_bp = Blueprint("convert", __name__)
logger = logging.getLogger(__name__)

MODERN_EXTS = {"docx", "xlsx", "pptx"}
LEGACY_EXTS = {"doc", "xls", "ppt"}


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
        # method can come from header (binary) or form (multipart)
        method = (
            request.headers.get("method")
            or request.form.get("method", "")
        ).lower()

        # =======================
        # METHOD: file (multipart)
        # =======================
        if method == "file":
            file = request.files.get("file")
            if not file or not file.filename:
                return jsonify({"error": "No file provided"}), 400

            ext = get_extension(file.filename)
            if ext not in SUPPORTED_EXTENSIONS:
                return jsonify({"error": "Invalid file format"}), 400

            original_filename = secure_filename(file.filename)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_input:
                file.save(temp_input.name)
                temp_input_path = temp_input.name

        # =======================
        # METHOD: ms (raw binary)
        # =======================
        elif method == "ms":
            file_bytes = request.data
            if not file_bytes:
                return jsonify({"error": "No byte stream provided"}), 400

            declared_ext = (
                request.headers.get("X-File-Ext")
                or request.form.get("ext")
                or ""
            ).lower().strip()

            if declared_ext not in SUPPORTED_EXTENSIONS:
                return jsonify({
                    "error": "Invalid or missing file extension",
                    "supported": sorted(SUPPORTED_EXTENSIONS),
                }), 400

            original_filename = f"document.{declared_ext}"

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{declared_ext}") as temp_input:
                temp_input.write(file_bytes)
                temp_input_path = temp_input.name

            # -------- validate content --------
            if declared_ext in MODERN_EXTS:
                detected = detect_modern_office_type(temp_input_path)
                if detected != declared_ext:
                    return jsonify({
                        "error": "File content does not match declared extension",
                        "declared": declared_ext,
                        "detected": detected,
                    }), 400

            elif declared_ext in LEGACY_EXTS:
                if not is_legacy_office_file(temp_input_path):
                    return jsonify({
                        "error": "Invalid legacy Office file",
                        "declared": declared_ext,
                    }), 400

        # =======================
        # METHOD: url
        # =======================
        elif method == "url":
            file_url = request.form.get("fileUrl")
            if not file_url:
                return jsonify({"error": "No URL provided"}), 400

            parsed = urlparse(file_url)
            raw_name = unquote(os.path.basename(parsed.path))
            filename = secure_filename(raw_name)

            ext = get_extension(filename)
            if ext not in SUPPORTED_EXTENSIONS:
                return jsonify({"error": "Invalid file format"}), 400

            original_filename = filename
            temp_input_path = download_file(file_url, filename)

        else:
            return jsonify({"error": "Invalid method provided"}), 400

        logger.info("Received file, saved to: %s", temp_input_path)

        if not temp_input_path or not os.path.exists(temp_input_path):
            return jsonify({"error": "Input file not available"}), 400

        # =======================
        # Convert
        # =======================
        temp_output_path = convert_office_to_pdf(temp_input_path)

        if not temp_output_path or not os.path.exists(temp_output_path):
            return jsonify({"error": "Conversion failed: output missing"}), 500

        # =======================
        # Cleanup temp files
        # =======================
        @after_this_request
        def cleanup(response):
            try:
                if temp_input_path and os.path.exists(temp_input_path):
                    os.remove(temp_input_path)

                if temp_output_path and os.path.exists(temp_output_path):
                    output_dir = os.path.dirname(temp_output_path)
                    os.remove(temp_output_path)

                    if output_dir and os.path.isdir(output_dir):
                        shutil.rmtree(output_dir, ignore_errors=True)

            except Exception:
                logger.exception("Cleanup failed")
            return response
        logger.info("Scheduled cleanup of temp files")
        # =======================
        # Download filename
        # =======================
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
        logger.info("Request processed in %.2f seconds", duration)
