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

logger = logging.getLogger(__name__)
time_logger = logger


def _ensure_soffice():
    soffice_path = shutil.which("soffice")
    if not soffice_path:
        raise RuntimeError("LibreOffice 'soffice' executable not found in PATH")
    return soffice_path


def convert_office_to_pdf(input_path: str, timeout: int = 120) -> str:
    start_time = time.time()

    base_name = os.path.basename(input_path)
    name_no_ext, ext = os.path.splitext(base_name)
    ext = ext.lstrip(".").lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: .{ext}")

    soffice_path = _ensure_soffice()

    # output to a temp directory to avoid permission issues in input dir
    outdir = tempfile.mkdtemp(prefix="lo-out-")
    output_path = os.path.join(outdir, f"{name_no_ext}.pdf")

    # LibreOffice profile isolated per request
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

    # retry session
    session = requests.Session()
    retries = Retry(total=max_retries, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504))
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
                    f.flush()

    return local_path