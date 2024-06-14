from flask import Blueprint, request, jsonify, send_file
from .utils import convert_docx_to_pdf
import tempfile
import os
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
import logging

convert_bp = Blueprint("convert", __name__)
logger = logging.getLogger(__name__)

TEMP_DIR = os.getenv('TEMP_DIR', '/home/temp')

@convert_bp.route("/convert", methods=["POST"])
def convert():
    temp_input_path = None
    temp_output_path = None

    try:
        file = request.files.get("file")

        if not file:
            logger.error("No file provided in the request.")
            return jsonify({"error": "No file provided"}), 400

        if file.filename.split(".")[-1].lower() != "docx":
            logger.error("Invalid file format provided.")
            return jsonify({"error": "Invalid file format"}), 400

        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", dir=TEMP_DIR) as temp_input:
            file.save(temp_input.name)
            temp_input_path = temp_input.name

        with ThreadPoolExecutor() as executor:
            temp_output_path = executor.submit(
                convert_docx_to_pdf, temp_input_path
            ).result()

        return send_file(
            temp_output_path, as_attachment=True, download_name="converted.pdf"
        )

    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return jsonify({"error": str(e)}), 500

    # finally:
    #     if temp_input_path and os.path.exists(temp_input_path):
    #         os.remove(temp_input_path)
    #     if temp_output_path and os.path.exists(temp_output_path):
    #         os.remove(temp_output_path)
