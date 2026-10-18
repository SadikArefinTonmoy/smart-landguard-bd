import os
import re
import unicodedata
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from docx import Document
from PIL import Image
from pypdf import PdfReader

try:
    import pytesseract
except Exception:  # pragma: no cover - optional OCR dependency can be missing in local environments
    pytesseract = None

FIELD_ALIASES: Dict[str, List[str]] = {
    "owner_name": [
        "owner name",
        "registered owner",
        "name of owner",
        "seller name",
        "property owner",
        "মালিকের নাম", "জমির মালিক", "মালিক", "দলিলের মালিক",
    ],
    "mouza": ["mouza", "mouja", "মৌজা"],
    "khatian_number": ["khatian number", "khatian no", "khatian", "khatiyan number", "khatiyan no", "খতিয়ান নং", "খতিয়ান নং", "খতিয়ান নম্বর", "খতিয়ান নম্বর", "খতিয়ান", "খতিয়ান"],
    "dag_number": ["dag number", "dag no", "dag", "দাগ নং", "দাগ নম্বর", "দাগ"],
    "land_area": ["land area", "plot area", "total area", "area of land", "area", "জমির পরিমাণ", "জমির আয়তন", "পরিমাণ"],
}


def normalize_value(value: Optional[str]) -> str:
    if value is None:
        return ""
    cleaned = re.sub(r"\s+", " ", str(value).strip())
    # Preserve Bengali and other Unicode letters. Never use substring matching
    # for legal names or survey identifiers: "Rahim" must not match "Rahima".
    cleaned = unicodedata.normalize('NFKC', cleaned).casefold()
    cleaned = cleaned.translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))
    # Unicode combining marks form essential parts of Bengali syllables.
    cleaned = ''.join(ch if unicodedata.category(ch)[0] in 'LMN' else ' ' for ch in cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


def clean_field_value(value: str) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", value.strip())
    # Preserve decimals, survey ID separators and fractions: '1.26' must NOT
    # turn into '1 26', which otherwise creates a false ambiguous-area result.
    cleaned = cleaned.replace(';', ',')
    return cleaned.strip()


def normalize_numeric_value(value: Optional[str], context: str = "") -> Tuple[str, bool, str]:
    if value is None:
        return "", False, "No numeric value provided."

    text = str(value).strip()
    if not text:
        return "", False, "No numeric value provided."

    text = text.lower().replace("bigha", " ").replace("bighas", " ")
    text = text.translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))
    numeric_fragment = re.sub(r"[^0-9,\.\s]", " ", text)
    numeric_fragment = re.sub(r"\s+", " ", numeric_fragment).strip()

    if not numeric_fragment:
        return "", False, "No numeric value found."

    if re.fullmatch(r"\d+\s+\d{1,3}", numeric_fragment):
        whole, fraction = numeric_fragment.split()
        candidate = f"{whole}.{fraction}"
        reason = "Detected a space-delimited decimal pattern. This can be ambiguous and should be reviewed by a human when the unit is a land area."
        if context.lower() in {"land_area", "area", "plot area", "total area", "area of land"}:
            return candidate, True, reason
        return candidate, True, "Detected an ambiguous numeric format that may require human review."

    if re.fullmatch(r"\d+\.\d+", numeric_fragment):
        return numeric_fragment, False, "Decimal value normalized successfully."

    if re.fullmatch(r"\d+", numeric_fragment):
        return numeric_fragment, False, "Whole number normalized successfully."

    if re.fullmatch(r"\d+,\d+", numeric_fragment):
        return numeric_fragment.replace(",", "."), False, "Comma decimal separator normalized to a decimal point."

    if re.fullmatch(r"\d+\s+\d+\s+\d+", numeric_fragment):
        parts = numeric_fragment.split()
        candidate = ".".join(parts)
        return candidate, True, "Multiple numeric groups were detected; this value may be ambiguous and should be reviewed by a human."

    return numeric_fragment, False, "Numeric value was normalized as text without a clear decimal pattern."


def extract_text_from_file(filename: str, file_bytes: bytes) -> Tuple[str, Optional[str]]:
    extension = os.path.splitext(filename or "")[1].lower()

    try:
        if extension == ".pdf":
            reader = PdfReader(BytesIO(file_bytes))
            if len(reader.pages) > 20:
                return "", "Only documents with at most 20 pages are supported."
            pages: List[str] = []
            for page in reader.pages:
                content = page.extract_text() or ""
                pages.append(content[:100_000])
            return "\n".join(pages)[:200_000], None

        if extension == ".docx":
            document = Document(BytesIO(file_bytes))
            paragraphs = [paragraph.text[:2000] for paragraph in document.paragraphs[:1000] if paragraph.text.strip()]
            return "\n".join(paragraphs)[:200_000], None

        if extension in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
            if not shutil_which("tesseract") or pytesseract is None:
                return "", "OCR is not available because Tesseract or the OCR runtime is not installed and configured on this system."
            Image.MAX_IMAGE_PIXELS = 20_000_000
            image = Image.open(BytesIO(file_bytes))
            image.verify()
            image = Image.open(BytesIO(file_bytes))
            languages = set(pytesseract.get_languages(config=''))
            selected = 'ben+eng' if {'ben', 'eng'} <= languages else ('ben' if 'ben' in languages else 'eng')
            text = pytesseract.image_to_string(image, lang=selected, timeout=8)
            return text, None

        if extension in {".txt"}:
            return file_bytes.decode("utf-8", errors="ignore"), None
    except Exception as exc:  # pragma: no cover - real-world parsing errors are handled below
        return "", "File could not be parsed safely. Please upload a supported readable file."

    return "", "Unsupported file type for local extraction."


def shutil_which(command: str) -> Optional[str]:
    import shutil

    return shutil.which(command)


def _extract_field_value(text: str, aliases: List[str]) -> Optional[str]:
    """Read a labelled value from ONE line, avoiding capture of the next field.

    Conservative by design: unlabelled OCR fragments are not evidence.
    """
    ordered = sorted(aliases, key=len, reverse=True)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for alias in ordered:
            # Require start of a line (not a substring inside another value).
            match = re.match(rf"(?i)^{re.escape(alias)}(?:\s+(?:no\.?|number|নং|নম্বর))?\s*[:：=\-]?\s*(.+?)\s*$", line)
            if not match:
                continue
            candidate = re.split(r'\s+[|]\s+', match.group(1), maxsplit=1)[0]
            candidate = clean_field_value(candidate)
            if candidate:
                return candidate[:120]
    return None


def _extract_supporting_evidence(text: str, field_name: str, value: str) -> str:
    """Return only the actual labelled source line, never a cross-line fragment."""
    aliases = sorted(FIELD_ALIASES.get(field_name, []), key=len, reverse=True)
    for line in text.splitlines():
        candidate = line.strip()
        for alias in aliases:
            if re.match(rf"(?i)^{re.escape(alias)}(?:\s+(?:no\.?|number|নং|নম্বর))?\s*[:：=\-]?\s*", candidate):
                if value.casefold() in candidate.casefold():
                    return candidate[:180]
    return 'Source label/value line was not located; please check the original document.'


def extract_property_fields(text: str) -> Dict[str, Optional[str]]:
    extracted: Dict[str, Optional[str]] = {}
    for field_name, aliases in FIELD_ALIASES.items():
        extracted[field_name] = _extract_field_value(text, aliases)
    return extracted


def is_field_match(expected: Optional[str], actual: Optional[str]) -> bool:
    if not expected or not actual:
        return False
    left, right = normalize_value(expected), normalize_value(actual)
    # Empty normalized values never count as matches.
    return bool(left and right and left == right)



def detect_area_unit(value: Optional[str]) -> str:
    """Known land-area units must never be silently treated as equivalent."""
    normalized = unicodedata.normalize('NFKC', str(value or '')).casefold()
    units = {
        'bigha': (r'\bbighas?\b', 'বিঘা'),
        'katha': (r'\bkathas?\b', 'কাঠা'),
        'acre': (r'\bacres?\b', 'একর'),
        'decimal': (r'\bdecimals?\b', 'শতক', 'শতাংশ'),
        'sqft': (r'\bsq\.?\s*ft\b', r'\bsquare\s+feet\b', 'বর্গফুট'),
        'hectare': (r'\bhectares?\b', 'হেক্টর'),
    }
    found = []
    for unit, markers in units.items():
        if any((re.search(m, normalized) if m.startswith('\\b') else m in normalized) for m in markers):
            found.append(unit)
    return found[0] if len(found) == 1 else ('unknown' if not found else 'ambiguous')

def compare_extracted_values(user_input: Dict[str, Any], extracted_fields: Dict[str, Optional[str]]) -> Dict[str, Any]:
    compare_map = {
        "owner_name": user_input.get("propertyOwnerName") or "",
        "mouza": user_input.get("mouza") or "",
        "khatian_number": user_input.get("khatianNumber") or "",
        "dag_number": user_input.get("dagNumber") or "",
        "land_area": user_input.get("landArea") or "",
    }

    matched: List[Dict[str, str]] = []
    mismatched: List[Dict[str, str]] = []
    ambiguous: List[Dict[str, str]] = []
    not_extracted: List[Dict[str, str]] = []

    for field_name, user_value in compare_map.items():
        actual_value = extracted_fields.get(field_name)
        if not user_value and not actual_value:
            continue

        if not user_value or not actual_value:
            not_extracted.append({
                "field": field_name,
                "expected": str(user_value or "").strip(),
            })
            continue

        if field_name == "land_area":
            expected_num, expected_ambiguous, expected_reason = normalize_numeric_value(user_value, "land_area")
            actual_num, actual_ambiguous, actual_reason = normalize_numeric_value(actual_value, "land_area")

            if expected_ambiguous or actual_ambiguous:
                ambiguous.append({
                    "field": field_name,
                    "expected": str(user_value or "").strip(),
                    "actual": str(actual_value).strip(),
                    "reason": expected_reason if expected_ambiguous else actual_reason,
                })
                continue

            expected_unit = detect_area_unit(user_value)
            actual_unit = detect_area_unit(actual_value)
            if expected_unit == 'ambiguous' or actual_unit == 'ambiguous' or (expected_unit == 'unknown') != (actual_unit == 'unknown'):
                ambiguous.append({
                    'field': field_name,
                    'expected': str(user_value).strip(),
                    'actual': str(actual_value).strip(),
                    'reason': 'Land area unit missing or unclear; a human must confirm the measurement unit.',
                })
                continue
            if expected_unit != actual_unit:
                mismatched.append({
                    'field': field_name,
                    'expected': str(user_value).strip(),
                    'actual': str(actual_value).strip(),
                    'reason': 'Land area units differ; no automatic conversion was performed.',
                })
                continue
            if expected_num == actual_num:
                matched.append({
                    "field": field_name,
                    "value": str(actual_value),
                    "normalized": expected_num,
                })
            else:
                mismatched.append({
                    "field": field_name,
                    "expected": str(user_value or "").strip(),
                    "actual": str(actual_value),
                    "normalized_expected": expected_num,
                    "normalized_actual": actual_num,
                })
            continue

        if is_field_match(user_value, actual_value):
            matched.append({
                "field": field_name,
                "value": str(actual_value),
            })
        else:
            mismatched.append({
                "field": field_name,
                "expected": str(user_value or "").strip(),
                "actual": str(actual_value),
            })

    return {
        "matched": matched,
        "mismatched": mismatched,
        "ambiguous": ambiguous,
        "not_extracted": not_extracted,
    }


def analyze_document_for_evidence(user_input: Dict[str, Any], file_name: str, file_bytes: bytes) -> Dict[str, Any]:
    extracted_text, extraction_error = extract_text_from_file(file_name, file_bytes)
    if extraction_error:
        return {
            "filename": file_name,
            "status": "unreadable",
            "message": extraction_error,
            "extracted_fields": {},
            "field_evidence": {},
            "comparison": {"matched": [], "mismatched": [], "ambiguous": [], "not_extracted": []},
        }

    if not extracted_text or not extracted_text.strip():
        return {
            "filename": file_name,
            "status": "unreadable",
            "message": "No readable text could be extracted from this file.",
            "extracted_fields": {},
            "field_evidence": {},
            "comparison": {"matched": [], "mismatched": [], "ambiguous": [], "not_extracted": []},
        }

    extracted_fields = extract_property_fields(extracted_text)
    field_evidence: Dict[str, str] = {}
    for field_name, value in extracted_fields.items():
        if value:
            field_evidence[field_name] = _extract_supporting_evidence(extracted_text, field_name, value)

    comparison = compare_extracted_values(user_input, extracted_fields)
    readable = bool(any(value for value in extracted_fields.values()))
    status = "success" if readable else "unreadable"
    message = "Text extracted and compared successfully." if readable else "No recognizable land-record fields were found in the uploaded document."

    return {
        "filename": file_name,
        "status": status,
        "message": message,
        "extracted_fields": extracted_fields,
        "field_evidence": field_evidence,
        "comparison": comparison,
    }
