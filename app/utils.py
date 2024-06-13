import os
import subprocess

def convert_docx_to_pdf(input_path):
    output_path = input_path.replace('.docx', '.pdf')
    try:
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', os.path.dirname(input_path), input_path], check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Conversion failed: {e}")

# import subprocess old
# import os

# def convert_docx_to_pdf(input_path):
#     output_path = input_path.replace('.docx', '.pdf')
#     subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', os.path.dirname(input_path), input_path], check=True)
#     return output_path
