"""
Vision Service - Image processing and vision-language model integration.

Handles image loading, preprocessing, and inference with vision models
like LLaVA, Qwen-VL, or other multimodal LLMs.
"""
import base64
import io
import re
from typing import Optional, List, Dict, Any, Tuple
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available. Image preprocessing will be limited.")

from ..config import settings


class VisionServiceError(Exception):
    """Custom exception for vision service errors."""
    def __init__(self, message: str, code: str = "VISION_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class VisionService:
    """
    Service for vision-language model operations.
    
    Supports:
    - OCR with vision models (intelligent text extraction)
    - Image description
    - Structured data extraction from images
    - Image comparison
    """

    def __init__(self):
        self.base_url = settings.vllm_base_url.rstrip("/v1").rstrip("/")
        self.api_key = settings.vllm_api_key or "EMPTY"
        self.vision_model = settings.vision_model
        self.timeout = settings.request_timeout
        self.max_image_size = settings.max_image_size_mb * 1024 * 1024

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=10.0)
        )

        logger.info(f"VisionService initialized with model={self.vision_model}")

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def _load_image_from_url(self, url: str) -> Tuple[bytes, str]:
        """Load image from URL."""
        try:
            response = await self.http_client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "image/png")
            media_type = content_type.split(";")[0].strip()
            
            return response.content, media_type
        except httpx.HTTPError as e:
            raise VisionServiceError(
                message=f"Failed to load image from URL: {str(e)}",
                code="IMAGE_LOAD_ERROR",
                details={"url": url}
            )

    def _decode_base64_image(self, base64_data: str) -> bytes:
        """Decode base64 image data."""
        # Remove data URL prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]
        
        try:
            return base64.b64decode(base64_data)
        except Exception as e:
            raise VisionServiceError(
                message=f"Invalid base64 image data: {str(e)}",
                code="INVALID_BASE64"
            )

    def _preprocess_image(
        self,
        image_bytes: bytes,
        max_size: int = 2048,
        quality: int = 85
    ) -> Tuple[bytes, str]:
        """
        Preprocess image for model input.
        
        - Resize if too large
        - Convert to RGB if necessary
        - Compress if needed
        """
        if not PIL_AVAILABLE:
            return image_bytes, "image/png"

        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            # Resize if too large
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=quality)
            return output.getvalue(), "image/jpeg"
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image_bytes, "image/png"

    def _build_image_content(
        self,
        image_bytes: bytes,
        media_type: str = "image/png"
    ) -> Dict[str, Any]:
        """Build image content for vision model API."""
        base64_data = base64.b64encode(image_bytes).decode("utf-8")
        
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{base64_data}"
            }
        }

    async def _call_vision_model(
        self,
        prompt: str,
        image_content: Dict[str, Any],
        max_tokens: int = 1024,
        temperature: float = 0.1,
        model: Optional[str] = None
    ) -> str:
        """Call the vision model with image and prompt."""
        model = model or self.vision_model
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_content
                ]
            }
        ]

        try:
            response = await self.http_client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except httpx.HTTPStatusError as e:
            raise VisionServiceError(
                message=f"Vision model API error: {e.response.status_code}",
                code="VISION_API_ERROR",
                details={"status_code": e.response.status_code}
            )
        except Exception as e:
            raise VisionServiceError(
                message=f"Vision model call failed: {str(e)}",
                code="VISION_CALL_ERROR"
            )

    async def prepare_image(
        self,
        url: Optional[str] = None,
        base64_data: Optional[str] = None,
        media_type: str = "image/png"
    ) -> Tuple[bytes, str]:
        """
        Prepare image from various input sources.
        
        Returns (image_bytes, media_type)
        """
        if url:
            image_bytes, media_type = await self._load_image_from_url(url)
        elif base64_data:
            image_bytes = self._decode_base64_image(base64_data)
        else:
            raise VisionServiceError(
                message="No image provided. Specify either url or base64.",
                code="NO_IMAGE"
            )
        
        # Check size
        if len(image_bytes) > self.max_image_size:
            raise VisionServiceError(
                message=f"Image too large. Maximum size: {settings.max_image_size_mb}MB",
                code="IMAGE_TOO_LARGE",
                details={
                    "size_bytes": len(image_bytes),
                    "max_bytes": self.max_image_size
                }
            )
        
        return image_bytes, media_type

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def ocr(
        self,
        image_bytes: bytes,
        media_type: str = "image/png",
        output_format: str = "text",
        detail_level: str = "medium",
        preserve_layout: bool = False,
        language_hints: Optional[List[str]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform OCR using vision-language model.
        
        Args:
            image_bytes: Raw image bytes
            media_type: Image MIME type
            output_format: 'text', 'structured', or 'markdown'
            detail_level: 'low', 'medium', or 'high'
            preserve_layout: Try to preserve original layout
            language_hints: Hint languages for better recognition
            model: Vision model to use
            
        Returns:
            Dictionary with extracted text and metadata
        """
        # Preprocess image based on detail level
        max_size = {"low": 1024, "medium": 1536, "high": 2048}.get(detail_level, 1536)
        processed_bytes, processed_type = self._preprocess_image(image_bytes, max_size)
        
        image_content = self._build_image_content(processed_bytes, processed_type)
        
        # Build OCR prompt based on settings
        prompt_parts = ["Extract all text from this image."]
        
        if preserve_layout:
            prompt_parts.append("Preserve the original layout and formatting as much as possible.")
        
        if language_hints:
            prompt_parts.append(f"The text may be in: {', '.join(language_hints)}.")
        
        if output_format == "structured":
            prompt_parts.append("""
Output in this exact format:
REGION 1:
Text: [extracted text]
Confidence: [high/medium/low]
Position: [description like 'top-left', 'center', etc.]

REGION 2:
... and so on for each distinct text region.""")
        elif output_format == "markdown":
            prompt_parts.append("Format the output as markdown, using headers, lists, and formatting as appropriate.")
        else:
            prompt_parts.append("Output only the extracted text, nothing else.")
        
        prompt = " ".join(prompt_parts)
        
        # Call vision model
        max_tokens = {"low": 512, "medium": 1024, "high": 2048}.get(detail_level, 1024)
        result_text = await self._call_vision_model(
            prompt=prompt,
            image_content=image_content,
            max_tokens=max_tokens,
            temperature=0.1,
            model=model
        )
        
        # Parse result based on format
        regions = None
        if output_format == "structured":
            regions = self._parse_structured_ocr(result_text)
            text = "\n".join(r["text"] for r in regions)
        else:
            text = result_text.strip()
        
        # Count words
        word_count = len(text.split()) if text else 0
        
        # Estimate confidence based on word count and text quality
        confidence = min(0.95, 0.7 + (word_count / 100) * 0.1) if word_count > 0 else 0.3
        
        return {
            "text": text,
            "regions": regions,
            "confidence": confidence,
            "word_count": word_count,
            "model": model or self.vision_model,
        }

    def _parse_structured_ocr(self, text: str) -> List[Dict[str, Any]]:
        """Parse structured OCR output into regions."""
        regions = []
        current_region = {}
        
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            
            if line.lower().startswith("region"):
                if current_region.get("text"):
                    regions.append(current_region)
                current_region = {}
            elif line.lower().startswith("text:"):
                current_region["text"] = line[5:].strip()
            elif line.lower().startswith("confidence:"):
                conf_str = line[11:].strip().lower()
                conf_map = {"high": 0.9, "medium": 0.7, "low": 0.5}
                current_region["confidence"] = conf_map.get(conf_str, 0.7)
            elif line.lower().startswith("position:"):
                current_region["position"] = line[9:].strip()
        
        if current_region.get("text"):
            regions.append(current_region)
        
        # If parsing failed, create single region
        if not regions and text:
            regions = [{
                "text": text,
                "confidence": 0.8,
                "position": "full"
            }]
        
        return regions

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def describe(
        self,
        image_bytes: bytes,
        media_type: str = "image/png",
        prompt: Optional[str] = None,
        max_length: int = 200,
        focus: str = "general",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a description of an image.
        
        Args:
            image_bytes: Raw image bytes
            media_type: Image MIME type
            prompt: Custom prompt for description
            max_length: Maximum tokens for description
            focus: What to focus on ('general', 'objects', 'text', 'people', 'scene')
            model: Vision model to use
            
        Returns:
            Dictionary with description and metadata
        """
        processed_bytes, processed_type = self._preprocess_image(image_bytes)
        image_content = self._build_image_content(processed_bytes, processed_type)
        
        # Build prompt based on focus
        if prompt:
            full_prompt = prompt
        else:
            focus_prompts = {
                "general": "Describe this image in detail.",
                "objects": "List and describe all objects visible in this image.",
                "text": "Describe this image, focusing on any text or writing visible.",
                "people": "Describe the people in this image, including their actions and expressions.",
                "scene": "Describe the scene, setting, and environment in this image."
            }
            full_prompt = focus_prompts.get(focus, focus_prompts["general"])
        
        result_text = await self._call_vision_model(
            prompt=full_prompt,
            image_content=image_content,
            max_tokens=max_length,
            temperature=0.3,
            model=model
        )
        
        # Try to detect objects mentioned
        objects = self._extract_objects_from_description(result_text)
        
        return {
            "description": result_text.strip(),
            "objects_detected": objects,
            "model": model or self.vision_model,
        }

    def _extract_objects_from_description(self, description: str) -> List[str]:
        """Extract likely objects from a description using simple heuristics."""
        # Common object words to look for
        object_patterns = [
            r'\b(car|truck|bus|bicycle|motorcycle)\b',
            r'\b(person|man|woman|child|people)\b',
            r'\b(dog|cat|bird|animal)\b',
            r'\b(tree|plant|flower|grass)\b',
            r'\b(building|house|office|store)\b',
            r'\b(table|chair|desk|furniture)\b',
            r'\b(computer|phone|laptop|screen)\b',
            r'\b(book|paper|document|text)\b',
            r'\b(food|drink|bottle|cup)\b',
        ]
        
        objects = set()
        description_lower = description.lower()
        
        for pattern in object_patterns:
            matches = re.findall(pattern, description_lower)
            objects.update(matches)
        
        return list(objects)[:10]  # Limit to 10 objects

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def extract_fields(
        self,
        image_bytes: bytes,
        media_type: str = "image/png",
        fields: List[str] = None,
        document_type: Optional[str] = None,
        schema: Optional[dict] = None,
        examples: Optional[List[dict]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured fields from an image.
        
        Args:
            image_bytes: Raw image bytes
            media_type: Image MIME type
            fields: Field names to extract
            document_type: Type hint (e.g., 'invoice', 'receipt')
            schema: JSON schema for validation
            examples: Few-shot examples
            model: Vision model to use
            
        Returns:
            Dictionary with extracted fields
        """
        processed_bytes, processed_type = self._preprocess_image(image_bytes, max_size=2048)
        image_content = self._build_image_content(processed_bytes, processed_type)
        
        # Build extraction prompt
        fields_str = ", ".join(fields) if fields else "all relevant fields"
        
        prompt_parts = [
            f"Extract the following information from this {'document' if document_type else 'image'}:",
            f"Fields to extract: {fields_str}"
        ]
        
        if document_type:
            prompt_parts.insert(0, f"This is a {document_type}.")
        
        if examples:
            prompt_parts.append("\nExamples:")
            for ex in examples[:3]:  # Limit to 3 examples
                prompt_parts.append(f"Input fields: {list(ex.keys())}")
                prompt_parts.append(f"Output: {ex}")
        
        prompt_parts.append("""
Output in this exact JSON format:
{
  "field_name": "extracted_value",
  ...
}

If a field cannot be found, use null.""")
        
        prompt = "\n".join(prompt_parts)
        
        result_text = await self._call_vision_model(
            prompt=prompt,
            image_content=image_content,
            max_tokens=1024,
            temperature=0.1,
            model=model
        )
        
        # Parse JSON from response
        extracted = self._parse_json_from_text(result_text)
        
        # Build fields list with confidence
        field_list = []
        for name, value in extracted.items():
            field_list.append({
                "name": name,
                "value": value,
                "confidence": 0.85 if value is not None else 0.5,
            })
        
        # Calculate overall confidence
        non_null_count = sum(1 for f in field_list if f["value"] is not None)
        confidence = non_null_count / len(field_list) if field_list else 0.5
        
        return {
            "fields": field_list,
            "raw_data": extracted,
            "document_type": document_type,
            "confidence": confidence,
            "model": model or self.vision_model,
        }

    def _parse_json_from_text(self, text: str) -> dict:
        """Extract JSON from text that may contain other content."""
        import json
        
        # Try to find JSON in the text
        text = text.strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Return empty dict if parsing fails
        logger.warning(f"Failed to parse JSON from vision model output: {text[:200]}")
        return {}


# Singleton instance
_vision_service: Optional[VisionService] = None


def get_vision_service() -> VisionService:
    """Get or create the vision service singleton."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service


async def close_vision_service():
    """Close the vision service."""
    global _vision_service
    if _vision_service:
        await _vision_service.close()
        _vision_service = None
