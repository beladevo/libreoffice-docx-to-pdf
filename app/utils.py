import os
import subprocess
import time
import logging
import requests
import tempfile
import shutil

logger = logging.getLogger(__name__)
time_logger = logging.getLogger("conversion_time")

SUPPORTED_EXTENSIONS = {"doc", "docx", "xls", "xlsx", "ppt", "pptx"}


def convert_office_to_pdf(input_path: str) -> str:
    start_time = time.time()

    base, ext = os.path.splitext(input_path)
    ext = ext.lstrip(".").lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: .{ext}")

    output_path = base + ".pdf"

    # Tạo LibreOffice profile riêng cho request
    lo_profile_dir = tempfile.mkdtemp(prefix="lo-profile-")
    lo_profile_uri = f"file://{lo_profile_dir}"

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
                "-env:UNO_JAVA_JFW_ENV_JREHOME=false",
                f"-env:UserInstallation={lo_profile_uri}",
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
            f"Conversion successful for {input_path}. Time taken: {duration:.2f}s"
        )

        if not os.path.exists(output_path):
            raise RuntimeError("Output PDF not generated")

        return output_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed for {input_path}: {e}")
        raise RuntimeError(f"Conversion failed: {e}")

    finally:
        shutil.rmtree(lo_profile_dir, ignore_errors=True)


def download_file(url, filename="document"):
    filename = f"{time.time()}-{filename}"
    local_filename = os.path.join(tempfile.gettempdir(), filename)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return local_filename
