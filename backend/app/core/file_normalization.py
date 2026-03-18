"""
File Normalization Service

Converts various file formats (PDF, PNG, HEIC, etc.) to standardized JPEG
for consistent viewing and parsing.

Dependencies:
    - Pillow (PIL): pip install Pillow
    - pdf2image: pip install pdf2image
    - poppler-utils: sudo apt-get install poppler-utils (system package)
"""
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Optional
import logging
import mimetypes

logger = logging.getLogger(__name__)


class FileNormalizationService:
    """
    Service for normalizing document files to JPEG format.

    Features:
        - Convert PDF pages to JPEG
        - Convert images (PNG, HEIC, TIFF, etc.) to JPEG
        - Resize to max dimension while preserving aspect ratio
        - Optimize for web viewing and parsing services

    Configuration:
        - TARGET_FORMAT: JPEG (universal compatibility)
        - MAX_DIMENSION: 2048px (good balance quality/size)
        - JPEG_QUALITY: 85% (visually lossless, good compression)
        - DPI: 200 (for PDF conversion)
    """

    TARGET_FORMAT = "JPEG"
    MAX_DIMENSION = 2048  # Max width or height in pixels
    JPEG_QUALITY = 85     # Quality 0-100
    DPI = 200             # DPI for PDF conversion

    def __init__(self):
        pass

    def normalize_file(
        self,
        input_path: str,
        output_path: str,
        page_number: int = 1
    ) -> Tuple[str, int, int]:
        """
        Convert file to normalized JPEG.

        Args:
            input_path: Absolute path to original file
            output_path: Absolute path to save normalized file
            page_number: For multi-page PDFs (1-indexed)

        Returns:
            (normalized_path, width, height)

        Raises:
            ValueError: If file type unsupported
            IOError: If file cannot be read/written
            FileNotFoundError: If input file doesn't exist
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Detect file type
        mime_type = self._detect_mime_type(input_path)
        logger.debug(f"Normalizing {input_path.name} (MIME: {mime_type})")

        # Convert to PIL Image
        if mime_type == "application/pdf":
            image = self._pdf_to_image(input_path, page_number)
        elif mime_type.startswith("image/"):
            image = self._load_image(input_path)
        else:
            raise ValueError(
                f"Unsupported file type: {mime_type}. "
                f"Supported: PDF, JPEG, PNG, HEIC, TIFF, GIF, BMP, WEBP"
            )

        # Convert to RGB (JPEG doesn't support transparency)
        image = self._convert_to_rgb(image)

        # Resize if needed
        image = self._resize_if_needed(image)

        # Save as JPEG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(
            output_path,
            "JPEG",
            quality=self.JPEG_QUALITY,
            optimize=True,
            progressive=True  # Progressive loading for web
        )

        logger.info(
            f"Normalized {input_path.name} → {output_path.name} "
            f"({image.width}x{image.height}, {mime_type})"
        )

        return str(output_path), image.width, image.height

    def normalize_pdf_multi_page(
        self,
        input_path: str,
        output_dir: str,
        base_filename: str
    ) -> List[Tuple[str, int, int]]:
        """
        Convert multi-page PDF to multiple JPEGs.

        Args:
            input_path: Absolute path to PDF
            output_dir: Directory to save JPEGs
            base_filename: Base name (will add _p1, _p2, etc.)

        Returns:
            List of (normalized_path, width, height) for each page

        Raises:
            ValueError: If not a PDF
            IOError: If PDF cannot be read
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"PDF not found: {input_path}")

        mime_type = self._detect_mime_type(input_path)
        if mime_type != "application/pdf":
            raise ValueError(f"Not a PDF file: {input_path} (MIME: {mime_type})")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert all PDF pages to images
        logger.info(f"Converting PDF {input_path.name} to images...")

        try:
            import pdf2image
        except ImportError:
            raise ImportError(
                "pdf2image not installed. Install with: pip install pdf2image\n"
                "Also requires poppler-utils: sudo apt-get install poppler-utils"
            )

        images = pdf2image.convert_from_path(
            input_path,
            dpi=self.DPI,
            fmt='ppm'  # Fast intermediate format
        )

        results = []
        for idx, image in enumerate(images, start=1):
            output_path = output_dir / f"{base_filename}_p{idx}.jpg"

            # Process image
            image = self._convert_to_rgb(image)
            image = self._resize_if_needed(image)

            # Save
            image.save(
                output_path,
                "JPEG",
                quality=self.JPEG_QUALITY,
                optimize=True
            )

            results.append((str(output_path), image.width, image.height))
            logger.info(f"  Page {idx}/{len(images)} → {output_path.name}")

        logger.info(f"PDF conversion complete: {len(images)} pages")
        return results

    def _detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type from file extension"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"

    def _load_image(self, file_path: Path) -> Image:
        """Load image file using PIL"""
        try:
            return Image.open(file_path)
        except Exception as e:
            raise IOError(f"Failed to load image {file_path.name}: {e}")

    def _pdf_to_image(self, pdf_path: Path, page_number: int) -> Image:
        """Convert single PDF page to PIL Image"""
        try:
            import pdf2image
        except ImportError:
            raise ImportError(
                "pdf2image not installed. Install with: pip install pdf2image\n"
                "Also requires poppler-utils: sudo apt-get install poppler-utils"
            )

        try:
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=self.DPI,
                first_page=page_number,
                last_page=page_number
            )
            if not images:
                raise ValueError(f"PDF page {page_number} not found")
            return images[0]
        except Exception as e:
            raise IOError(f"Failed to convert PDF page {page_number}: {e}")

    def _convert_to_rgb(self, image: Image) -> Image:
        """
        Convert image to RGB color space (required for JPEG).

        Handles transparency by placing image on white background.
        """
        if image.mode == "RGB":
            return image

        if image.mode in ("RGBA", "LA"):
            # Create white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            # Paste image using alpha channel as mask
            background.paste(image, mask=image.split()[-1])
            return background

        elif image.mode == "P":
            # Palette mode - convert to RGBA first then to RGB
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            return background

        else:
            # Other modes (L, CMYK, etc.) - direct conversion
            return image.convert("RGB")

    def _resize_if_needed(self, image: Image) -> Image:
        """
        Resize image if larger than MAX_DIMENSION.

        Maintains aspect ratio. Uses LANCZOS resampling for best quality.
        """
        width, height = image.size

        if width <= self.MAX_DIMENSION and height <= self.MAX_DIMENSION:
            return image

        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = self.MAX_DIMENSION
            new_height = int(height * (self.MAX_DIMENSION / width))
        else:
            new_height = self.MAX_DIMENSION
            new_width = int(width * (self.MAX_DIMENSION / height))

        logger.debug(f"Resizing {width}x{height} → {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/tiff",
            "image/webp",
            "image/heic",
            "image/heif"
        ]

    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported"""
        mime_type = self._detect_mime_type(Path(file_path))
        return mime_type in self.get_supported_formats()


# Global instance
file_normalization = FileNormalizationService()
