import os
import subprocess
import time
import logging

logger = logging.getLogger(__name__)
time_logger = logging.getLogger('conversion_time')

def convert_docx_to_pdf(input_path):
    start_time = time.time()
    output_path = input_path.replace('.docx', '.pdf')

    try:
        subprocess.run(['soffice', '--invisible', '--headless', '--convert-to', 'pdf', input_path, '--outdir', os.path.dirname(input_path)], check=True)
        duration = time.time() - start_time
        print(f"Conversion successful for {input_path}. Time taken: {duration:.2f} seconds")
        time_logger.info(f"Conversion successful for {input_path}. Time taken: {duration:.2f} seconds")
        return output_path
    except subprocess.CalledProcessError as e:

        logger.error(f"Conversion failed for {input_path}: {e}")
        raise RuntimeError(f"Conversion failed: {e}")
