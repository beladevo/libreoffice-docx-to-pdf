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
        # Cleanup profile
        try:
            import shutil
            shutil.rmtree(lo_profile_dir, ignore_errors=True)
        except Exception:
            logger.warning(f"Failed to cleanup LibreOffice profile: {lo_profile_dir}")
