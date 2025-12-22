import os
import subprocess
import time
import logging
import requests
import tempfile
import shutil
import uuid
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .constants import SUPPORTED_EXTENSIONS
import zipfile
from typing import Optional
logger = logging.getLogger(__name__)
time_logger = logger


def _ensure_soffice():
    soffice_path = shutil.which("soffice")
    if not soffice_path:
        raise RuntimeError("LibreOffice 'soffice' executable not found in PATH")
    return soffice_path


# Detect modern Office type by inspecting ZIP content
def detect_modern_office_type(file_path: str) -> Optional[str]:
    try:
        with zipfile.ZipFile(file_path, mode="r") as z:
            names = set(z.namelist())

            if "word/document.xml" in names:
                return "docx"
            if "xl/workbook.xml" in names:
                return "xlsx"
            if "ppt/presentation.xml" in names:
                return "pptx"
    except zipfile.BadZipFile:
        return None

    return None


# Detect legacy Office file via OLE header
def is_legacy_office_file(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
        if len(header) < 8:
            return False
        return header == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"
    except Exception:
        return False


def convert_office_to_pdf(input_path: str, timeout: int = 120) -> str:
    start_time = time.time()

    base_name = os.path.basename(input_path)
    name_no_ext, ext = os.path.splitext(base_name)
    ext = ext.lstrip(".").lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: .{ext}")

    soffice_path = _ensure_soffice()

    outdir = tempfile.mkdtemp(prefix="lo-out-")
    output_path = os.path.join(outdir, f"{name_no_ext}.pdf")

    lo_profile_dir = tempfile.mkdtemp(prefix="lo-profile-")
    lo_profile_uri = f"file://{lo_profile_dir}"

    try:
        proc = subprocess.run(
            [
                soffice_path,
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
                outdir,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        duration = time.time() - start_time
        if proc.returncode != 0:
            logger.error(
                "soffice failed: rc=%s stdout=%s stderr=%s",
                proc.returncode,
                proc.stdout,
                proc.stderr,
            )
            raise RuntimeError(f"Conversion failed (rc={proc.returncode})")

        time_logger.info(
            "Conversion successful for %s. Time taken: %.2fs", input_path, duration
        )

        if not os.path.exists(output_path):
            candidates = [f for f in os.listdir(outdir) if f.lower().endswith(".pdf")]
            if candidates:
                output_path = os.path.join(outdir, candidates[0])
            else:
                raise RuntimeError("Output PDF not generated")

        return output_path

    except subprocess.TimeoutExpired as e:
        logger.exception("Conversion timed out for %s", input_path)
        raise RuntimeError("Conversion timed out") from e

    finally:
        shutil.rmtree(lo_profile_dir, ignore_errors=True)


def download_file(url, filename="document", timeout=(5, 30), max_retries=3):
    parsed = requests.utils.urlparse(url)
    raw_name = os.path.basename(parsed.path) or filename
    _, ext = os.path.splitext(raw_name)
    suffix = ext if ext else ""

    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    unique_name = f"{int(time.time())}-{uuid.uuid4().hex}{suffix}"
    local_path = os.path.join(tempfile.gettempdir(), unique_name)

    with session.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return local_path
