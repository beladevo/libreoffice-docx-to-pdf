# DOCX to PDF Converter
Flask microservice that converts Office files (Word, Excel, PowerPoint) to PDF using LibreOffice.

## Installation
```
git clone https://github.com/beladevo/libreoffice-docx-to-pdf.git
pip install -r requirements.txt
python run.py
```

## Usage

Supports: `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`

**Upload file:**
```bash
curl -X POST http://localhost:8000/convert \
  -F "method=file" \
  -F "file=@document.docx" \
  -o output.pdf
```

**Convert from URL:**
```bash
curl -X POST http://localhost:8000/convert \
  -F "method=url" \
  -F "fileUrl=https://example.com/file.xlsx" \
  -o output.pdf
```

**Raw bytes:**
```bash
curl -X POST http://localhost:8000/convert \
  -F "method=ms" \
  -F "ext=pptx" \
  --data-binary @presentation.pptx \
  -o output.pdf
```

Port defaults to 8000. Set `PORT` in `.env` to change.

## Docker
```
docker build -t beladevos/docx-pdf-converter-libreoffice
docker run -p 8000:8000 beladevos/docx-pdf-converter-libreoffice
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.
