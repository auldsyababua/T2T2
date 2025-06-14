import hashlib
import io
from typing import List

import boto3
import pytesseract
import torch
from open_clip import create_model_and_transforms
from PIL import Image

from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class ImageService:
    def __init__(
        self, s3_bucket: str, aws_access_key_id: str, aws_secret_access_key: str
    ):
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        # Initialize CLIP model
        self.clip_model, self.preprocess, _ = create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        self.clip_model.eval()

    def _calculate_file_hash(self, image_data: bytes) -> str:
        """Calculate SHA-256 hash of image data."""
        return hashlib.sha256(image_data).hexdigest()

    async def process_image(self, image_data: bytes) -> dict:
        """Process an image: extract text, generate embeddings, and upload to S3."""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(image_data)

            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size

            # Extract text using OCR
            ocr_text = await self.extract_text_ocr(image)

            # Generate CLIP embedding
            img_embedding = await self.generate_clip_embedding(image_data)

            # Upload to S3
            s3_key = f"images/{file_hash}.jpg"
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=image_data,
                ContentType="image/jpeg",
            )

            s3_url = f"https://{self.s3_bucket}.s3.amazonaws.com/{s3_key}"

            return {
                "file_hash": file_hash,
                "s3_url": s3_url,
                "ocr_text": ocr_text,
                "img_embedding": img_embedding,
                "width": width,
                "height": height,
            }
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise

    async def extract_text_ocr(self, image: Image.Image) -> str:
        """Extract text from image using Tesseract OCR."""
        try:
            # Convert image to grayscale for better OCR
            if image.mode != "L":
                image = image.convert("L")

            # Perform OCR
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"Error performing OCR: {str(e)}")
            raise

    async def generate_clip_embedding(self, image_data: bytes) -> List[float]:
        """Generate CLIP embedding for an image."""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))

            # Preprocess image
            image_input = self.preprocess(image).unsqueeze(0)

            # Generate embedding
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
                image_features = image_features / image_features.norm(
                    dim=-1, keepdim=True
                )

            # Convert to list
            return image_features[0].numpy().tolist()
        except Exception as e:
            logger.error(f"Error generating CLIP embedding: {str(e)}")
            raise
