"""Restrictive file inspection before handing bytes to document parsers."""
from io import BytesIO
from pathlib import PurePath
from zipfile import ZipFile, BadZipFile

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 3
MAX_PDF_PAGES = 20
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.png', '.jpg', '.jpeg'}

def validate_file(upload):
    name = (upload.filename or '').replace('\\', '/')
    # Avoid reflecting paths supplied by the client.
    name = PurePath(name).name[:120]
    extension = '.' + name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError('Unsupported file type. Use PDF, DOCX, PNG or JPG.')
    data = upload.stream.read(MAX_FILE_BYTES + 1)
    if not data or len(data) > MAX_FILE_BYTES:
        raise ValueError('Each document must be nonempty and at most 10 MB.')
    if extension == '.pdf' and not data.startswith(b'%PDF-'):
        raise ValueError('Invalid PDF file signature.')
    if extension == '.png' and not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Invalid PNG file signature.')
    if extension in {'.jpg', '.jpeg'} and not data.startswith(b'\xff\xd8\xff'):
        raise ValueError('Invalid JPEG file signature.')
    if extension == '.docx':
        try:
            with ZipFile(BytesIO(data)) as archive:
                names = archive.namelist()
                if 'word/document.xml' not in names or len(names) > 2000 or sum(i.file_size for i in archive.infolist()) > 40 * 1024 * 1024:
                    raise ValueError('Invalid or oversized DOCX file.')
        except BadZipFile:
            raise ValueError('Invalid DOCX file.')
    return name, data
