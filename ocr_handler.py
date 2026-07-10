"""OCR support for scanned documents"""

import os
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from logger import get_logger
from errors import OCRError

logger = get_logger(__name__)


class OCRHandler:
    """Handle OCR for scanned documents"""
    
    def __init__(self):
        if not OCR_AVAILABLE:
            logger.warning("Tesseract not available - OCR functionality disabled")
        self.available = OCR_AVAILABLE
    
    def extract_text_from_image(self, image_path, language='eng'):
        """Extract text from image using Tesseract OCR"""
        if not self.available:
            raise OCRError('OCR not available', details={'tesseract': 'not installed'})
        
        try:
            # Open image
            img = Image.open(image_path)
            
            # Preprocess image if needed
            img = self._preprocess_image(img)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(img, lang=language)
            
            logger.info(f"OCR extraction successful for {image_path}")
            return text
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise OCRError(f'OCR extraction failed: {str(e)}')
    
    def extract_text_from_pdf_images(self, pdf_path):
        """Extract text from PDF with scanned images"""
        if not self.available:
            raise OCRError('OCR not available')
        
        try:
            from pdf2image import convert_from_path
            
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            extracted_text = []
            for idx, image in enumerate(images):
                try:
                    text = pytesseract.image_to_string(image)
                    extracted_text.append({
                        'page': idx + 1,
                        'text': text
                    })
                except Exception as e:
                    logger.warning(f"OCR failed on page {idx + 1}: {str(e)}")
                    extracted_text.append({
                        'page': idx + 1,
                        'text': '',
                        'error': str(e)
                    })
            
            logger.info(f"OCR extraction successful for {pdf_path} ({len(images)} pages)")
            return extracted_text
        
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {str(e)}")
            raise OCRError(f'PDF OCR extraction failed: {str(e)}')
    
    def _preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Increase contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)
            
            # Upscale if small
            if image.size[0] < 200:
                image = image.resize(
                    (image.size[0] * 3, image.size[1] * 3),
                    Image.Resampling.LANCZOS
                )
            
            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    def is_scanned_pdf(self, pdf_path):
        """Check if PDF is scanned (image-based) or text-based"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                # Try to extract text from first page
                if len(reader.pages) > 0:
                    text = reader.pages[0].extract_text()
                    
                    # If very little text, likely scanned
                    return len(text.strip()) < 50
            
            return False
        except Exception as e:
            logger.warning(f"Could not determine if PDF is scanned: {str(e)}")
            return False


# Global OCR handler
ocr_handler = OCRHandler()
