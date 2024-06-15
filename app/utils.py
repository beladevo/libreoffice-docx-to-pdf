import os
import subprocess
import time
import logging
import requests
import tempfile
import time

logger = logging.getLogger(__name__)
time_logger = logging.getLogger("conversion_time")

def convert_docx_to_pdf(input_path):
    start_time = time.time()
    output_path = input_path.replace(".docx", ".pdf")

    try:
        subprocess.run(
            [
                "soffice",
                "--invisible",
                "--headless",
                "--nologo",
                "--nocrashreport",
                "--nodefault",
                "--norestore",
                "--nolockcheck",
                "--convert-to",
                "pdf",
                input_path,
                "--outdir",
                os.path.dirname(input_path),
            ],
            check=True,
        )
        duration = time.time() - start_time
        time_logger.info(
            f"Conversion successful for {input_path}. Time taken: {duration:.2f} seconds"
        )
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed for {input_path}: {e}")
        raise RuntimeError(f"Conversion failed: {e}")

def download_file(url, filename = 'document.docx'):
    filename = f"{time.time()}-{filename}"
    local_filename = os.path.join(tempfile.gettempdir(), filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename
