import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from .utils import convert_docx_to_pdf

convert_bp = Blueprint('convert', __name__)

@convert_bp.route('/convert', methods=['POST'])
def convert():
    file = request.files.get('file')
    
    if not file:
        return jsonify({"error": "No file provided"}), 400

    if file.filename.split('.')[-1].lower() != 'docx':
        return jsonify({"error": "Invalid file format"}), 400

    try:
        filename = secure_filename(file.filename)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_input_path = os.path.join(temp_dir, filename)
            file.save(temp_input_path)

            with ThreadPoolExecutor() as executor:
                temp_output_path = executor.submit(convert_docx_to_pdf, temp_input_path).result()

            return send_file(temp_output_path, as_attachment=True, download_name='converted.pdf')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)