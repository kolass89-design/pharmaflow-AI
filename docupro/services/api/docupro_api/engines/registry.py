"""The conversion registry: a single source of truth for the product catalog.

Every advertised tool is declared here with its accepted inputs, its option
schema, its engine and its honest limitations. The frontend builds its whole
interface from ``/api/tools``, so a tool can never appear in the UI without a
working backend implementation behind it.
"""

from __future__ import annotations

from typing import Any

from ..errors import ValidationError
from . import images, ocr, office, pdf_to, pdf_tools, word
from .models import Choice, ConversionSpec, InputSpec, OptionSpec

PDF_IN = InputSpec(("pdf",), "PDF document")
DOCX_IN = InputSpec(("docx",), "Word document (.docx)")
WORD_IN = InputSpec(("docx", "doc"), "Word document")
IMAGE_IN = InputSpec(("jpg", "jpeg", "png", "webp", "heic", "heif"), "Image", allows_batch=True)
IMAGE_ANY_IN = InputSpec(("jpg", "jpeg", "png", "webp", "heic", "heif", "gif", "bmp", "tiff"), "Image")


def _ocr_language_option(default: str = "auto") -> OptionSpec:
    return OptionSpec(
        key="ocr_language",
        label="OCR language",
        type="select",
        default=default,
        choices=tuple(Choice(code, label) for code, label in ocr.LANGUAGE_CHOICES),
        help="Choose the language of the text. Auto uses English and French when available.",
    )


def _pages_option(label: str = "Pages", required: bool = False, help_text: str | None = None) -> OptionSpec:
    return OptionSpec(
        key="pages",
        label=label,
        type="pages",
        default="",
        required=required,
        placeholder="e.g. 1-3,5,8-  (blank = all pages)",
        help=help_text or "Use page numbers and ranges, separated by commas.",
    )


def _dpi_option(default: int = 150) -> OptionSpec:
    return OptionSpec(
        key="dpi",
        label="Resolution (DPI)",
        type="number",
        default=default,
        minimum=50,
        maximum=600,
        step=10,
        help="Higher DPI means sharper images and larger files.",
        advanced=True,
    )


def _quality_option(default: int = 90, label: str = "Quality") -> OptionSpec:
    return OptionSpec(
        key="quality",
        label=label,
        type="number",
        default=default,
        minimum=30,
        maximum=100,
        step=1,
        help="Lower quality produces smaller files.",
        advanced=True,
    )


def _page_size_option(default: str = "a4") -> OptionSpec:
    return OptionSpec(
        key="page_size",
        label="Page size",
        type="select",
        default=default,
        choices=(
            Choice("a4", "A4"),
            Choice("letter", "US Letter"),
            Choice("legal", "Legal"),
            Choice("a3", "A3"),
            Choice("a5", "A5"),
        ),
    )


def _image_page_size_option() -> OptionSpec:
    return OptionSpec(
        key="page_size",
        label="Page size",
        type="select",
        default="a4",
        choices=(
            Choice("a4", "A4"),
            Choice("letter", "US Letter"),
            Choice("legal", "Legal"),
            Choice("a3", "A3"),
            Choice("a5", "A5"),
            Choice("fit", "Fit to image"),
        ),
    )


SPECS: list[ConversionSpec] = [
    # ---------------------------------------------------------------- PDF tools
    ConversionSpec(
        id="pdf-to-word",
        category="pdf",
        title="PDF to Word",
        subtitle="Editable .docx",
        description="Rebuild an editable Word document with paragraphs, headings, tables and images kept in place. Scanned PDFs are handled with OCR.",
        input=PDF_IN,
        output_kind="document",
        output_label="Word document",
        output_extension="docx",
        engine="pdf2docx + OCR",
        run=pdf_to.pdf_to_word,
        options=(
            OptionSpec(
                key="mode",
                label="Conversion mode",
                type="select",
                default="auto",
                choices=(
                    Choice("auto", "Automatic (recommended)"),
                    Choice("layout", "Keep layout (digital PDFs)"),
                    Choice("ocr", "OCR (scanned PDFs)"),
                ),
                help="Automatic detects scanned pages and chooses OCR only when needed.",
            ),
            _ocr_language_option(),
        ),
        limitations=(
            "Complex multi-column layouts and mathematical formulas may not be reconstructed exactly.",
            "Scanned documents are rebuilt from OCR text, so fonts and spacing will differ from the scan.",
        ),
        keywords=("docx", "word", "editable", "office"),
        featured=True,
        estimated_seconds=12,
    ),
    ConversionSpec(
        id="pdf-to-jpeg",
        category="pdf",
        title="PDF to JPEG",
        subtitle="Page images",
        description="Render every page as a high quality JPEG image. Choose the resolution and get a ZIP for multi-page files.",
        input=PDF_IN,
        output_kind="image",
        output_label="JPEG images",
        output_extension="jpg",
        engine="MuPDF renderer",
        run=pdf_to.pdf_to_jpeg,
        options=(
            _pages_option(),
            _dpi_option(150),
            _quality_option(88),
            OptionSpec(key="zip", label="Bundle pages as ZIP", type="boolean", default=True, advanced=True),
        ),
        zip_multiple=True,
        limitations=("Text is no longer selectable in image output.",),
        keywords=("jpg", "image", "render", "picture"),
        featured=True,
        estimated_seconds=8,
    ),
    ConversionSpec(
        id="pdf-to-png",
        category="pdf",
        title="PDF to PNG",
        subtitle="Lossless page images",
        description="Render pages as lossless PNG images that stay crisp at high resolution.",
        input=PDF_IN,
        output_kind="image",
        output_label="PNG images",
        output_extension="png",
        engine="MuPDF renderer",
        run=pdf_to.pdf_to_png,
        options=(
            _pages_option(),
            _dpi_option(150),
            OptionSpec(key="zip", label="Bundle pages as ZIP", type="boolean", default=True, advanced=True),
        ),
        zip_multiple=True,
        limitations=("PNG files are larger than JPEG for photographic pages.",),
        keywords=("png", "image", "render"),
        estimated_seconds=9,
    ),
    ConversionSpec(
        id="pdf-to-searchable",
        category="pdf",
        title="Scanned PDF to searchable PDF",
        subtitle="Add an OCR text layer",
        description="Run OCR over scanned pages and add an invisible text layer so the document can be searched, selected and copied.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Searchable PDF",
        output_extension="pdf",
        engine="Tesseract / ONNX OCR",
        run=pdf_to.pdf_to_searchable,
        options=(
            _ocr_language_option(),
            _dpi_option(300),
            OptionSpec(
                key="force",
                label="Re-run OCR on pages that already have text",
                type="boolean",
                default=False,
                advanced=True,
            ),
        ),
        limitations=(
            "OCR accuracy depends on scan quality; handwriting and unusual fonts are not reliable.",
            "The visual appearance of the page is unchanged.",
        ),
        keywords=("ocr", "scan", "search", "text layer"),
        featured=True,
        estimated_seconds=25,
    ),
    ConversionSpec(
        id="pdf-to-text",
        category="pdf",
        title="PDF to Text",
        subtitle="Plain .txt",
        description="Extract the text of a PDF into a clean UTF-8 text file with optional page markers.",
        input=PDF_IN,
        output_kind="text",
        output_label="Text file",
        output_extension="txt",
        engine="MuPDF text extraction",
        run=pdf_to.pdf_to_text,
        options=(
            _pages_option(),
            OptionSpec(key="page_markers", label="Include page markers", type="boolean", default=True),
            OptionSpec(
                key="ocr_fallback",
                label="Use OCR for pages without text",
                type="boolean",
                default=False,
                help="Slower, but works for scanned documents.",
            ),
            _ocr_language_option(),
        ),
        limitations=("Layout, images and formatting are not part of plain text output.",),
        keywords=("txt", "extract", "copy", "plain text"),
        offline_capable=False,
        featured=True,
        estimated_seconds=3,
    ),
    ConversionSpec(
        id="pdf-extract-images",
        category="pdf",
        title="Extract images from PDF",
        subtitle="Original embedded images",
        description="Pull the original pictures embedded in a PDF, without re-rendering the pages.",
        input=PDF_IN,
        output_kind="image",
        output_label="Images (ZIP)",
        output_extension="zip",
        engine="MuPDF image extraction",
        run=pdf_to.pdf_extract_images,
        limitations=(
            "Only true embedded images are extracted; vector graphics and full-page scans stored as "
            "masks may be skipped.",
        ),
        keywords=("images", "pictures", "extract"),
        estimated_seconds=6,
    ),
    ConversionSpec(
        id="pdf-to-single-pages",
        category="pdf",
        title="Split PDF into single pages",
        subtitle="One PDF per page",
        description="Create separate PDF files for every page of a document, delivered together in a ZIP archive.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="PDF files (ZIP)",
        output_extension="zip",
        engine="MuPDF",
        run=pdf_to.pdf_to_single_pages,
        keywords=("split", "separate", "pages"),
        estimated_seconds=5,
    ),
    ConversionSpec(
        id="merge-pdf",
        category="pdf",
        title="Merge PDFs",
        subtitle="Combine several files",
        description="Combine multiple PDF documents into a single file, in the order you choose, with optional bookmarks.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Merged PDF",
        output_extension="pdf",
        engine="MuPDF",
        min_files=2,
        max_files=20,
        run=pdf_tools.merge_pdf,
        options=(
            OptionSpec(key="add_bookmarks", label="Add a bookmark per source file", type="boolean", default=True),
        ),
        limitations=("Encrypted PDFs must be unlocked before merging.",),
        keywords=("combine", "join", "concatenate"),
        featured=True,
        estimated_seconds=6,
    ),
    ConversionSpec(
        id="split-pdf",
        category="pdf",
        title="Split PDF",
        subtitle="By page or range",
        description="Split a document into one file per page, into fixed-size chunks, or by custom page ranges.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="PDF files",
        output_extension="zip",
        engine="MuPDF",
        run=pdf_tools.split_pdf,
        options=(
            OptionSpec(
                key="split_mode",
                label="Split method",
                type="select",
                default="each",
                choices=(
                    Choice("each", "One file per page"),
                    Choice("chunks", "Fixed number of pages per file"),
                    Choice("ranges", "Custom ranges"),
                ),
            ),
            OptionSpec(
                key="chunk_size",
                label="Pages per file",
                type="number",
                default=10,
                minimum=1,
                maximum=500,
            ),
            OptionSpec(
                key="ranges",
                label="Ranges",
                type="text",
                default="",
                placeholder="1-3; 4-6; 7",
                help="Separate each output file with a semicolon.",
            ),
        ),
        keywords=("split", "separate", "chunks"),
        featured=True,
        estimated_seconds=5,
    ),
    ConversionSpec(
        id="extract-pages",
        category="pdf",
        title="Extract pages",
        subtitle="Keep only what you need",
        description="Select pages and rebuild a new PDF containing exactly those pages, in your chosen order.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="PDF with selected pages",
        output_extension="pdf",
        engine="MuPDF",
        run=pdf_tools.extract_pages,
        options=(_pages_option(required=True),),
        keywords=("extract", "select", "pages"),
        estimated_seconds=3,
    ),
    ConversionSpec(
        id="delete-pages",
        category="pdf",
        title="Delete pages",
        subtitle="Remove unwanted pages",
        description="Remove specific pages from a PDF and download the cleaned document.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Cleaned PDF",
        output_extension="pdf",
        engine="MuPDF",
        run=pdf_tools.delete_pages,
        options=(_pages_option(required=True),),
        keywords=("delete", "remove", "pages"),
        estimated_seconds=3,
    ),
    ConversionSpec(
        id="reorder-pages",
        category="pdf",
        title="Reorder pages",
        subtitle="Rearrange the document",
        description="Change the order of pages by listing the new sequence, for example 3,1,2.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Reordered PDF",
        output_extension="pdf",
        engine="MuPDF",
        run=pdf_tools.reorder_pages,
        options=(
            OptionSpec(
                key="pages",
                label="New page order",
                type="pages",
                default="",
                required=True,
                placeholder="e.g. 3,1,2",
                help="List every page exactly once.",
            ),
        ),
        keywords=("order", "rearrange", "organise"),
        estimated_seconds=3,
    ),
    ConversionSpec(
        id="rotate-pdf",
        category="pdf",
        title="Rotate pages",
        subtitle="Fix orientation",
        description="Rotate all pages or a selection by 90, 180 or 270 degrees.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Rotated PDF",
        output_extension="pdf",
        engine="MuPDF",
        run=pdf_tools.rotate_pages,
        options=(
            OptionSpec(
                key="angle",
                label="Rotation",
                type="select",
                default="90",
                choices=(Choice("90", "90° clockwise"), Choice("180", "180°"), Choice("270", "90° counter-clockwise")),
            ),
            _pages_option(),
        ),
        keywords=("rotate", "orientation", "landscape"),
        estimated_seconds=3,
    ),
    ConversionSpec(
        id="compress-pdf",
        category="pdf",
        title="Compress PDF",
        subtitle="Smaller file, same pages",
        description="Reduce file size by recompressing images and cleaning redundant objects. Text stays selectable.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Compressed PDF",
        output_extension="pdf",
        engine="MuPDF optimiser",
        run=pdf_tools.compress_pdf,
        options=(
            OptionSpec(
                key="preset",
                label="Compression level",
                type="select",
                default="balanced",
                choices=(
                    Choice("light", "Light — best quality"),
                    Choice("balanced", "Balanced — recommended"),
                    Choice("strong", "Strong — smallest file"),
                ),
            ),
        ),
        limitations=("Documents that are already optimised may shrink very little.",),
        keywords=("compress", "shrink", "size", "optimise"),
        featured=True,
        estimated_seconds=8,
    ),
    ConversionSpec(
        id="protect-pdf",
        category="pdf",
        title="Protect PDF",
        subtitle="Password and permissions",
        description="Encrypt a PDF with AES-256 and decide whether readers may print or copy content.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Protected PDF",
        output_extension="pdf",
        engine="MuPDF encryption",
        run=pdf_tools.protect_pdf,
        options=(
            OptionSpec(
                key="password",
                label="Open password",
                type="password",
                default="",
                required=True,
                placeholder="At least 4 characters",
                help="Needed to open the document. It is never stored on our servers.",
            ),
            OptionSpec(
                key="owner_password",
                label="Owner password (optional)",
                type="password",
                default="",
                advanced=True,
                help="Controls permissions; defaults to the open password.",
            ),
            OptionSpec(
                key="permissions",
                label="Allow readers to",
                type="select",
                default="print",
                choices=(
                    Choice("view", "View only"),
                    Choice("print", "View and print"),
                    Choice("all", "View, print, copy and annotate"),
                ),
            ),
        ),
        limitations=("A forgotten password cannot be recovered. Keep a safe copy of the original file.",),
        keywords=("password", "encrypt", "security", "aes"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="unlock-pdf",
        category="pdf",
        title="Unlock PDF",
        subtitle="Remove a password you own",
        description="Remove password protection from a PDF by supplying the correct password. Only use this on documents you are authorized to modify.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Unlocked PDF",
        output_extension="pdf",
        engine="MuPDF encryption",
        run=pdf_tools.unlock_pdf,
        options=(
            OptionSpec(
                key="password",
                label="Current password",
                type="password",
                default="",
                required=True,
                help="Only works with the valid password.",
            ),
        ),
        limitations=("Without the correct password the file cannot be unlocked.",),
        keywords=("unlock", "decrypt", "password"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="page-numbers",
        category="pdf",
        title="Add page numbers",
        subtitle="Number every page",
        description="Stamp page numbers at the top or bottom of the page in a style of your choice.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Numbered PDF",
        output_extension="pdf",
        engine="MuPDF",
        run=pdf_tools.add_page_numbers,
        options=(
            OptionSpec(
                key="position",
                label="Position",
                type="select",
                default="bottom-center",
                choices=(
                    Choice("bottom-center", "Bottom centre"),
                    Choice("bottom-right", "Bottom right"),
                    Choice("bottom-left", "Bottom left"),
                    Choice("top-center", "Top centre"),
                    Choice("top-right", "Top right"),
                    Choice("top-left", "Top left"),
                ),
            ),
            OptionSpec(
                key="style",
                label="Format",
                type="select",
                default="n",
                choices=(
                    Choice("n", "1, 2, 3"),
                    Choice("n-of-total", "1 / 10"),
                    Choice("page-n", "Page 1 of 10"),
                    Choice("dash", "- 1 -"),
                ),
            ),
            OptionSpec(key="start_at", label="First page number", type="number", default=1, minimum=0, maximum=9999),
            OptionSpec(
                key="font_size",
                label="Font size",
                type="number",
                default=10,
                minimum=6,
                maximum=36,
                advanced=True,
            ),
        ),
        keywords=("numbering", "stamp", "footer"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="watermark-pdf",
        category="pdf",
        title="Watermark PDF",
        subtitle="Confidential, Draft, sample…",
        description="Add a diagonal or footer watermark to some or all pages with adjustable opacity.",
        input=PDF_IN,
        output_kind="pdf",
        output_label="Watermarked PDF",
        output_extension="pdf",
        engine="MuPDF",
        run=pdf_tools.watermark_pdf,
        options=(
            OptionSpec(key="text", label="Watermark text", type="text", default="CONFIDENTIAL", required=True),
            OptionSpec(
                key="layout",
                label="Layout",
                type="select",
                default="diagonal",
                choices=(Choice("diagonal", "Diagonal across the page"), Choice("footer", "Footer line")),
            ),
            OptionSpec(key="opacity", label="Opacity", type="number", default=0.18, minimum=0.03, maximum=1, step=0.01),
            OptionSpec(
                key="angle", label="Angle", type="number", default=45, minimum=-90, maximum=90, step=1, advanced=True
            ),
            OptionSpec(
                key="font_size", label="Font size", type="number", default=54, minimum=8, maximum=220, advanced=True
            ),
            OptionSpec(
                key="color", label="Colour", type="text", default="#94a3b8", advanced=True, placeholder="#94a3b8"
            ),
            _pages_option(),
        ),
        keywords=("watermark", "stamp", "confidential", "draft"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="pdf-to-excel",
        category="pdf",
        title="PDF to Excel",
        subtitle="Detect tables",
        description="Detect ruled tables in a PDF and export them as editable worksheets.",
        input=PDF_IN,
        output_kind="spreadsheet",
        output_label="Excel workbook",
        output_extension="xlsx",
        engine="MuPDF table detection",
        run=pdf_to.pdf_to_excel,
        limitations=(
            "Works best with ruled tables. Merged cells, nested tables and scanned pages without OCR "
            "may not be detected.",
        ),
        keywords=("xlsx", "excel", "table", "spreadsheet", "data"),
        estimated_seconds=12,
    ),
    # --------------------------------------------------------------- Word tools
    ConversionSpec(
        id="word-to-pdf",
        category="word",
        title="Word to PDF",
        subtitle="Fixed, shareable layout",
        description="Convert .docx (and legacy .doc) files to PDF while keeping page size, tables, images and fonts.",
        input=WORD_IN,
        output_kind="pdf",
        output_label="PDF document",
        output_extension="pdf",
        engine="LibreOffice / built-in renderer",
        run=word.word_to_pdf,
        limitations=(
            "Legacy .doc files require the LibreOffice renderer on the server.",
            "If LibreOffice is not installed, a built-in renderer is used: headers, footers and exact page breaks may differ.",
        ),
        keywords=("pdf", "docx", "doc", "export"),
        featured=True,
        estimated_seconds=10,
    ),
    ConversionSpec(
        id="word-to-jpeg",
        category="word",
        title="Word to JPEG",
        subtitle="Page images",
        description="Render each page of a Word document as a JPEG image.",
        input=WORD_IN,
        output_kind="image",
        output_label="JPEG images",
        output_extension="jpg",
        engine="LibreOffice + MuPDF",
        run=word.word_to_jpeg,
        options=(
            _dpi_option(150),
            OptionSpec(key="zip", label="Bundle pages as ZIP", type="boolean", default=True, advanced=True),
        ),
        zip_multiple=True,
        keywords=("jpg", "image", "preview"),
        estimated_seconds=14,
    ),
    ConversionSpec(
        id="word-to-png",
        category="word",
        title="Word to PNG",
        subtitle="Page images",
        description="Render each page of a Word document as a lossless PNG image.",
        input=WORD_IN,
        output_kind="image",
        output_label="PNG images",
        output_extension="png",
        engine="LibreOffice + MuPDF",
        run=word.word_to_png,
        options=(
            _dpi_option(150),
            OptionSpec(key="zip", label="Bundle pages as ZIP", type="boolean", default=True, advanced=True),
        ),
        zip_multiple=True,
        keywords=("png", "image", "preview"),
        estimated_seconds=14,
    ),
    ConversionSpec(
        id="word-to-text",
        category="word",
        title="Word to Text",
        subtitle="Clean .txt",
        description="Extract paragraphs and table content from a Word document into plain UTF-8 text.",
        input=WORD_IN,
        output_kind="text",
        output_label="Text file",
        output_extension="txt",
        engine="python-docx",
        run=word.word_to_text,
        keywords=("txt", "extract", "plain text"),
        estimated_seconds=3,
    ),
    ConversionSpec(
        id="word-to-html",
        category="word",
        title="Word to HTML",
        subtitle="Ready-to-publish page",
        description="Turn a Word document into a clean, responsive HTML page with inline styles and embedded images.",
        input=DOCX_IN,
        output_kind="html",
        output_label="HTML page",
        output_extension="html",
        engine="Mammoth",
        run=word.word_to_html,
        limitations=("Complex Word tables and headers/footers may be simplified in HTML output.",),
        keywords=("html", "web", "publish"),
        estimated_seconds=4,
    ),
    # -------------------------------------------------------------- Image tools
    ConversionSpec(
        id="image-to-pdf",
        category="image",
        title="Images to PDF",
        subtitle="JPG, PNG, WebP, HEIC",
        description="Combine one or many images into a PDF with A4, Letter or image-sized pages, margins and custom order.",
        input=InputSpec(
            ("jpg", "jpeg", "png", "webp", "heic", "heif", "gif", "bmp", "tiff"), "Images", allows_batch=True
        ),
        output_kind="pdf",
        output_label="PDF document",
        output_extension="pdf",
        engine="MuPDF + Pillow",
        min_files=1,
        max_files=20,
        run=images.images_to_pdf,
        options=(
            _image_page_size_option(),
            OptionSpec(
                key="orientation",
                label="Orientation",
                type="select",
                default="auto",
                choices=(
                    Choice("auto", "Automatic"),
                    Choice("portrait", "Portrait"),
                    Choice("landscape", "Landscape"),
                ),
            ),
            OptionSpec(key="margin", label="Margin (mm)", type="number", default=10, minimum=0, maximum=50, step=1),
            OptionSpec(
                key="fit_mode",
                label="Image fit",
                type="select",
                default="contain",
                choices=(
                    Choice("contain", "Fit inside the page"),
                    Choice("cover", "Fill the page (crop)"),
                    Choice("stretch", "Stretch to the page"),
                ),
                advanced=True,
            ),
            _quality_option(88, "Image quality"),
            OptionSpec(
                key="order",
                label="Page order",
                type="text",
                default="",
                placeholder="e.g. 3,1,2",
                help="Leave blank to keep the upload order.",
                advanced=True,
            ),
        ),
        keywords=("jpg", "png", "webp", "heic", "photos", "combine"),
        featured=True,
        estimated_seconds=7,
    ),
    ConversionSpec(
        id="image-to-word",
        category="image",
        title="Image to Word",
        subtitle="OCR to editable .docx",
        description="Read the text in a photo or scan and build an editable Word document with reconstructed paragraphs.",
        input=IMAGE_IN,
        output_kind="document",
        output_label="Word document",
        output_extension="docx",
        engine="Tesseract / ONNX OCR + python-docx",
        run=images.image_to_word,
        options=(
            _ocr_language_option(),
            OptionSpec(
                key="include_image",
                label="Append the original image",
                type="boolean",
                default=False,
                advanced=True,
            ),
        ),
        limitations=(
            "OCR cannot reproduce the original formatting, fonts or images faithfully.",
            "Handwriting and low-resolution photos reduce accuracy.",
        ),
        keywords=("ocr", "docx", "scan", "editable", "text"),
        estimated_seconds=15,
    ),
    ConversionSpec(
        id="image-to-text",
        category="image",
        title="Image to Text (OCR)",
        subtitle="Copyable text",
        description="Extract the words from an image into a plain text file, with the language of your choice.",
        input=IMAGE_IN,
        output_kind="text",
        output_label="Text file",
        output_extension="txt",
        engine="Tesseract / ONNX OCR",
        run=images.image_to_text,
        options=(_ocr_language_option(),),
        limitations=("OCR accuracy depends on image quality, contrast and font.",),
        keywords=("ocr", "extract", "copy", "text"),
        estimated_seconds=12,
    ),
    ConversionSpec(
        id="image-convert",
        category="image",
        title="Convert image format",
        subtitle="JPEG, PNG, WebP",
        description="Convert between JPEG, PNG and WebP, with white background flattening for transparency.",
        input=IMAGE_ANY_IN,
        output_kind="image",
        output_label="Images",
        output_extension="png",
        engine="Pillow",
        max_files=20,
        run=images.image_convert,
        options=(
            OptionSpec(
                key="target_format",
                label="Output format",
                type="select",
                default="png",
                choices=(Choice("png", "PNG"), Choice("jpeg", "JPEG"), Choice("webp", "WebP")),
            ),
            _quality_option(90),
        ),
        keywords=("png", "jpeg", "jpg", "webp", "convert"),
        featured=True,
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="image-resize",
        category="image",
        title="Resize image",
        subtitle="Exact or proportional",
        description="Resize by percentage, by width, by longest edge or to exact dimensions, without distortion.",
        input=IMAGE_ANY_IN,
        output_kind="image",
        output_label="Images",
        output_extension="png",
        engine="Pillow",
        max_files=20,
        run=images.image_resize,
        options=(
            OptionSpec(
                key="mode",
                label="Resize method",
                type="select",
                default="max_edge",
                choices=(
                    Choice("max_edge", "Longest edge"),
                    Choice("percent", "Percentage"),
                    Choice("width", "Width"),
                    Choice("exact", "Exact size"),
                ),
            ),
            OptionSpec(key="width", label="Width (px)", type="number", default=1920, minimum=16, maximum=20000),
            OptionSpec(key="height", label="Height (px)", type="number", default=1080, minimum=16, maximum=20000),
            OptionSpec(key="percent", label="Percentage (%)", type="number", default=50, minimum=1, maximum=400),
            OptionSpec(key="keep_aspect", label="Keep aspect ratio", type="boolean", default=True),
            OptionSpec(
                key="target_format",
                label="Output format",
                type="select",
                default="keep",
                choices=(
                    Choice("keep", "Keep original"),
                    Choice("jpeg", "JPEG"),
                    Choice("png", "PNG"),
                    Choice("webp", "WebP"),
                ),
            ),
        ),
        keywords=("resize", "scale", "dimensions", "width"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="image-compress",
        category="image",
        title="Compress image",
        subtitle="Smaller photos",
        description="Shrink photos for email or the web with adjustable quality and an optional maximum size.",
        input=IMAGE_ANY_IN,
        output_kind="image",
        output_label="Compressed images",
        output_extension="jpg",
        engine="Pillow",
        max_files=20,
        run=images.image_compress,
        options=(
            OptionSpec(
                key="target_format",
                label="Output format",
                type="select",
                default="jpeg",
                choices=(Choice("jpeg", "JPEG"), Choice("webp", "WebP")),
            ),
            OptionSpec(key="quality", label="Quality", type="number", default=70, minimum=20, maximum=95),
            OptionSpec(
                key="max_edge",
                label="Maximum longest edge (px, 0 = keep)",
                type="number",
                default=0,
                minimum=0,
                maximum=12000,
                advanced=True,
            ),
        ),
        keywords=("compress", "optimise", "size", "web"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="image-rotate",
        category="image",
        title="Rotate image",
        subtitle="Fix orientation",
        description="Rotate an image by 90, 180 or 270 degrees, optionally mirrored.",
        input=IMAGE_ANY_IN,
        output_kind="image",
        output_label="Images",
        output_extension="png",
        engine="Pillow",
        max_files=20,
        run=images.image_rotate,
        options=(
            OptionSpec(
                key="angle",
                label="Rotation",
                type="select",
                default="90",
                choices=(Choice("90", "90° clockwise"), Choice("180", "180°"), Choice("270", "90° counter-clockwise")),
            ),
            OptionSpec(key="flip", label="Mirror horizontally", type="boolean", default=False),
        ),
        keywords=("rotate", "turn", "mirror"),
        estimated_seconds=3,
    ),
    # -------------------------------------------------------------- Other tools
    ConversionSpec(
        id="excel-to-pdf",
        category="other",
        title="Excel to PDF",
        subtitle="Spreadsheets, printable",
        description="Render an Excel workbook as PDF, keeping sheets, cell values and table structure.",
        input=InputSpec(("xlsx",), "Excel workbook"),
        output_kind="pdf",
        output_label="PDF document",
        output_extension="pdf",
        engine="LibreOffice / HTML layout",
        run=office.xlsx_to_pdf,
        limitations=(
            "Very large sheets are trimmed in the built-in fallback renderer (2,000 rows per sheet).",
            "Charts and macros are not rendered by the fallback engine.",
        ),
        keywords=("xlsx", "excel", "spreadsheet", "print"),
        estimated_seconds=12,
    ),
    ConversionSpec(
        id="powerpoint-to-pdf",
        category="other",
        title="PowerPoint to PDF",
        subtitle="Slides as a document",
        description="Convert .pptx presentations into PDF slides.",
        input=InputSpec(("pptx",), "PowerPoint presentation"),
        output_kind="pdf",
        output_label="PDF document",
        output_extension="pdf",
        engine="LibreOffice",
        run=office.pptx_to_pdf,
        limitations=("Requires the LibreOffice renderer on the server.",),
        keywords=("pptx", "slides", "presentation"),
        estimated_seconds=15,
    ),
    ConversionSpec(
        id="csv-to-excel",
        category="other",
        title="CSV to Excel",
        subtitle="Real spreadsheet",
        description="Turn a CSV file into a formatted .xlsx workbook with detected numbers and a frozen header.",
        input=InputSpec(("csv",), "CSV file"),
        output_kind="spreadsheet",
        output_label="Excel workbook",
        output_extension="xlsx",
        engine="openpyxl",
        run=office.csv_to_xlsx,
        options=(OptionSpec(key="detect_numbers", label="Detect numbers and dates", type="boolean", default=True),),
        keywords=("csv", "excel", "xlsx", "convert"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="excel-to-csv",
        category="other",
        title="Excel to CSV",
        subtitle="Plain data",
        description="Export each worksheet of an .xlsx workbook to a UTF-8 CSV file.",
        input=InputSpec(("xlsx",), "Excel workbook"),
        output_kind="spreadsheet",
        output_label="CSV files",
        output_extension="csv",
        engine="openpyxl",
        run=office.xlsx_to_csv,
        keywords=("xlsx", "csv", "data", "export"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="text-to-pdf",
        category="other",
        title="Text to PDF",
        subtitle="Neat, printable page",
        description="Lay out a plain text file as a clean, printable PDF with Unicode support.",
        input=InputSpec(("txt", "md"), "Text file"),
        output_kind="pdf",
        output_label="PDF document",
        output_extension="pdf",
        engine="MuPDF Story",
        run=office.text_to_pdf,
        options=(_page_size_option(),),
        keywords=("txt", "text", "pdf", "print"),
        estimated_seconds=4,
    ),
    ConversionSpec(
        id="html-to-pdf",
        category="other",
        title="HTML to PDF",
        subtitle="Web page archive",
        description="Convert an HTML file into a paginated PDF. Remote resources are intentionally not loaded.",
        input=InputSpec(("html", "htm"), "HTML file"),
        output_kind="pdf",
        output_label="PDF document",
        output_extension="pdf",
        engine="MuPDF Story",
        run=office.html_to_pdf,
        options=(_page_size_option(),),
        limitations=(
            "External images, scripts and remote stylesheets are stripped for privacy and safety.",
            "JavaScript-rendered content is not executed.",
        ),
        keywords=("html", "web", "page", "archive"),
        estimated_seconds=5,
    ),
]

REGISTRY: dict[str, ConversionSpec] = {spec.id: spec for spec in SPECS}
assert len(REGISTRY) == len(SPECS), "duplicate conversion ids"


def get_spec(spec_id: str) -> ConversionSpec | None:
    return REGISTRY.get(spec_id)


def list_specs() -> list[ConversionSpec]:
    return list(SPECS)


def availability(spec: ConversionSpec) -> tuple[bool, str | None]:
    """Whether a tool can run on this host right now."""
    if spec.id in {"powerpoint-to-pdf"}:
        from .office_render import libreoffice_available

        if not libreoffice_available():
            return False, "The LibreOffice renderer is not installed on this server."
    if spec.id in {"pdf-to-searchable", "image-to-word", "image-to-text"}:
        if ocr.ocr_backend() is None:
            return False, "OCR is not available on this server."
    return True, None


def public_catalog() -> dict[str, Any]:
    languages = ocr.available_languages()
    tools = []
    for spec in SPECS:
        data = spec.public()
        available, reason = availability(spec)
        data["available"] = available
        data["unavailableReason"] = reason
        for option in data["options"]:
            if option["key"] == "ocr_language" and languages:
                option["choices"] = languages
                if not any(c["value"] == option.get("default") for c in languages):
                    option["default"] = languages[0]["value"]
        tools.append(data)
    return {
        "tools": tools,
        "categories": [
            {"id": "pdf", "label": "PDF tools", "description": "Convert, edit and secure PDF documents"},
            {"id": "word", "label": "Word tools", "description": "Work with .docx and .doc documents"},
            {"id": "image", "label": "Image tools", "description": "Convert, resize and OCR images"},
            {"id": "other", "label": "Other formats", "description": "Spreadsheets, slides, text and HTML"},
        ],
    }


def _coerce(option: OptionSpec, value: Any) -> Any:
    if value is None:
        return option.default
    if option.type == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
    if option.type == "number":
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"“{option.label}” must be a number.", code="invalid_option", details={"option": option.key}
            ) from exc
        if option.minimum is not None and number < option.minimum:
            number = option.minimum
        if option.maximum is not None and number > option.maximum:
            number = option.maximum
        return int(number) if float(number).is_integer() else number
    if option.type == "select":
        allowed = {choice.value for choice in option.choices}
        text = str(value)
        if option.key == "ocr_language" and text == "auto":
            return text
        if allowed and text not in allowed:
            raise ValidationError(
                f"“{option.label}” has an invalid value.",
                code="invalid_option",
                details={"option": option.key, "allowed": sorted(allowed)},
            )
        return text
    text = str(value)
    limit = 128 if option.type == "password" else 500
    if option.key == "pages" and len(text) > 2000:
        raise ValidationError("The page selection is too long.", code="invalid_option")
    return text[:limit]


def validate_options(spec: ConversionSpec, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Coerce and validate client-supplied options against the spec schema."""
    raw = raw or {}
    if not isinstance(raw, dict):
        raise ValidationError("Options must be an object.", code="invalid_request")
    unknown = set(raw) - {o.key for o in spec.options}
    if unknown:
        raise ValidationError(
            "Unknown conversion options were supplied.",
            code="invalid_option",
            details={"unknown": sorted(unknown)},
        )
    resolved: dict[str, Any] = {}
    for option in spec.options:
        if option.key in raw:
            value = _coerce(option, raw[option.key])
        else:
            value = option.default
        if option.required and (value is None or str(value).strip() == ""):
            raise ValidationError(
                f"“{option.label}” is required.", code="missing_option", details={"option": option.key}
            )
        resolved[option.key] = value
    return resolved


def redact_options(options: dict[str, Any]) -> dict[str, Any]:
    """Never echo secrets back to the client or into logs."""
    return {k: ("••••••" if k in {"password", "owner_password"} and v else v) for k, v in options.items()}
