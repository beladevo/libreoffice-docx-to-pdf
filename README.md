# DOCX to PDF Converter
This is a Flask-based microservice that converts DOCX files to PDF format using LibreOffice.

## Installation
```
git clone https://github.com/beladevo/libreoffice-docx-to-pdf.git
pip install -r requirements.txt
python run.py
```

## Usage
* Upload a DOCX file to the /convert endpoint to convert it to PDF.
* The converted PDF file will be available for download.

## Docker
```
docker build -t beladevos/docx-pdf-converter-libreoffice
docker run -p 5000:5000 beladevos/docx-pdf-converter-libreoffice
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.
