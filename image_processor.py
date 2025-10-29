"""
Image processing module for extracting and describing images from PDFs
"""
import base64
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from PIL import Image
import ollama

from config import LOGGING

# Set up logging
logging.basicConfig(level=getattr(logging, LOGGING["level"]), format=LOGGING["format"])
logger = logging.getLogger(__name__)


class PDFImageProcessor:
    """Extract and describe images from PDF files using vision models"""
    
    def __init__(self, vision_model: str = "llava", min_image_size: int = 1000):
        self.vision_model = vision_model
        self.min_image_size = min_image_size  # Minimum image size in bytes
        self.ollama_client = ollama
        
    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract all images from a PDF file"""
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image data
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image['image']
                        image_ext = base_image['ext']
                        
                        # Skip very small images (likely icons or decorative elements)
                        if len(image_bytes) < self.min_image_size:
                            continue
                        
                        # Convert to PIL Image
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        
                        # Create image metadata
                        image_info = {
                            'page_number': page_num + 1,
                            'image_index': img_index,
                            'format': image_ext,
                            'size_bytes': len(image_bytes),
                            'dimensions': pil_image.size,
                            'image_data': image_bytes,
                            'pil_image': pil_image
                        }
                        
                        images.append(image_info)
                        logger.debug(f"Extracted image {img_index} from page {page_num + 1}: {pil_image.size} {image_ext}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
                        continue
            
            doc.close()
            logger.info(f"Extracted {len(images)} images from {pdf_path}")
            return images
            
        except Exception as e:
            logger.error(f"Failed to extract images from {pdf_path}: {e}")
            return []
    
    def image_to_base64(self, pil_image: Image.Image, format: str = "PNG") -> str:
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        # Convert to RGB if necessary (for JPEG compatibility)
        if pil_image.mode not in ("RGB", "L"):
            pil_image = pil_image.convert("RGB")
        pil_image.save(buffer, format=format)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    def describe_image_with_ollama(self, pil_image: Image.Image, context: str = "scientific paper") -> str:
        """Generate description of image using Ollama vision model"""
        try:
            # Convert image to base64
            img_base64 = self.image_to_base64(pil_image)
            
            # Create a scientific-focused prompt
            prompt = f"""Analyze this image from a {context}. Provide a detailed description focusing on:
1. What type of figure/diagram/chart this is
2. Key data, labels, or text visible in the image
3. Scientific content, methodology, or results shown
4. Any important numerical values or trends

Be concise but thorough, focusing on scientifically relevant information."""
            
            # Call Ollama with vision model
            response = self.ollama_client.generate(
                model=self.vision_model,
                prompt=prompt,
                images=[img_base64],
                options={
                    'temperature': 0.1,  # Low temperature for consistent descriptions
                    'num_predict': 200   # Limit response length
                }
            )
            
            description = response['response'].strip()
            logger.debug(f"Generated image description: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Failed to describe image with Ollama: {e}")
            return f"[Image description failed: {str(e)}]"
    
    def process_pdf_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF and generate descriptions"""
        logger.info(f"Processing images in {pdf_path}")
        
        # Extract images
        images = self.extract_images_from_pdf(pdf_path)
        
        if not images:
            logger.info(f"No images found in {pdf_path}")
            return []
        
        # Generate descriptions for each image
        processed_images = []
        for i, image_info in enumerate(images):
            logger.info(f"Describing image {i+1}/{len(images)} from page {image_info['page_number']}")
            
            try:
                # Generate description
                description = self.describe_image_with_ollama(image_info['pil_image'])
                
                # Create processed image record
                processed_image = {
                    'page_number': image_info['page_number'],
                    'image_index': image_info['image_index'],
                    'format': image_info['format'],
                    'size_bytes': image_info['size_bytes'],
                    'dimensions': image_info['dimensions'],
                    'description': description,
                    'type': 'image_description'
                }
                
                processed_images.append(processed_image)
                
            except Exception as e:
                logger.error(f"Failed to process image {i+1}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(processed_images)} images from {pdf_path}")
        return processed_images
    
    def create_image_text_chunks(self, processed_images: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert image descriptions into text chunks for embedding"""
        chunks = []
        
        for image in processed_images:
            # Create descriptive text content
            content = f"""[IMAGE from page {image['page_number']}]
Image Type: Figure/Diagram ({image['format']}, {image['dimensions'][0]}x{image['dimensions'][1]})
Description: {image['description']}
"""
            
            # Create metadata for this image chunk
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'content_type': 'image_description',
                'page_number': image['page_number'],
                'image_index': image['image_index'],
                'image_format': image['format'],
                'image_dimensions': image['dimensions']
            })
            
            chunk = {
                'content': content,
                'metadata': chunk_metadata
            }
            
            chunks.append(chunk)
        
        return chunks


def test_image_processing():
    """Test the image processing functionality"""
    print("🖼️ Testing Image Processing with Ollama Vision")
    print("=" * 50)
    
    processor = PDFImageProcessor()
    
    # Test on one of the PDFs
    test_pdf = "papers/1.pdf"
    if Path(test_pdf).exists():
        print(f"Processing images in: {test_pdf}")
        
        # Extract and describe images
        processed_images = processor.process_pdf_images(test_pdf)
        
        print(f"\n📊 Results:")
        print(f"Images processed: {len(processed_images)}")
        
        # Show first description as example
        if processed_images:
            first_image = processed_images[0]
            print(f"\n📄 Example description (Page {first_image['page_number']}):")
            print(f"Format: {first_image['format']}")
            print(f"Size: {first_image['dimensions']}")
            print(f"Description: {first_image['description']}")
        
        # Convert to text chunks
        fake_metadata = {"filename": "test.pdf", "title": "Test Document"}
        chunks = processor.create_image_text_chunks(processed_images, fake_metadata)
        print(f"\nText chunks created: {len(chunks)}")
        
    else:
        print(f"❌ Test PDF not found: {test_pdf}")


if __name__ == "__main__":
    test_image_processing()