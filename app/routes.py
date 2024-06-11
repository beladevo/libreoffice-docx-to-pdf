from flask import Blueprint, request, jsonify, send_file
from .utils import convert_docx_to_pdf
import tempfile
import os

convert_bp = Blueprint('convert', __name__)

@convert_bp.route('/convert', methods=['POST'])
def convert():
    file = request.files.get('file')
    
    if not file:
        return jsonify({"error": "No file provided"}), 400

    if file.filename.split('.')[-1].lower() != 'docx':
        return jsonify({"error": "Invalid file format"}), 400

    temp_input_path = None
    temp_output_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_input:
            file.save(temp_input.name)
            temp_input_path = temp_input.name

        temp_output_path = convert_docx_to_pdf(temp_input_path)

        return send_file(temp_output_path, as_attachment=True, download_name='converted.pdf')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if temp_input_path and os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if temp_output_path and os.path.exists(temp_output_path):
            os.remove(temp_output_path)
