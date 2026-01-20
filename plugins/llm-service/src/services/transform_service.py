"""
Transform Service - LLM-powered data transformation.

Provides intelligent data transformation using LLMs for tasks that
require understanding context, semantics, and complex mappings.
"""
import json
import re
from typing import Optional, List, Dict, Any, Union
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from ..config import settings


class TransformServiceError(Exception):
    """Custom exception for transform service errors."""
    def __init__(self, message: str, code: str = "TRANSFORM_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class TransformService:
    """
    Service for LLM-powered data transformations.
    
    Use when you need:
    - Context-aware transformations
    - Schema inference from unstructured data
    - Intelligent field mapping
    - Data cleaning with understanding
    """

    def __init__(self):
        self.base_url = settings.vllm_base_url.rstrip("/v1").rstrip("/")
        self.api_key = settings.vllm_api_key or "EMPTY"
        self.model = settings.default_model
        self.timeout = settings.request_timeout

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=10.0)
        )

        logger.info(f"TransformService initialized with model={self.model}")

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.1,
        model: Optional[str] = None
    ) -> str:
        """Call the LLM with a prompt."""
        model = model or self.model

        try:
            response = await self.http_client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a data transformation assistant. Always output valid JSON when requested. Be precise and follow instructions exactly."
                        },
                        {"role": "user", "content": prompt}
                    ],
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
            raise TransformServiceError(
                message=f"LLM API error: {e.response.status_code}",
                code="LLM_API_ERROR",
                details={"status_code": e.response.status_code}
            )
        except Exception as e:
            raise TransformServiceError(
                message=f"LLM call failed: {str(e)}",
                code="LLM_CALL_ERROR"
            )

    def _detect_format(self, data: Union[str, dict, list]) -> str:
        """Detect the format of input data."""
        if isinstance(data, dict):
            return "json"
        if isinstance(data, list):
            return "json"
        
        text = str(data).strip()
        
        # Try JSON
        try:
            json.loads(text)
            return "json"
        except:
            pass
        
        # Check for XML
        if text.startswith("<?xml") or (text.startswith("<") and text.endswith(">")):
            return "xml"
        
        # Check for YAML-like structure
        if re.match(r'^[\w-]+:\s*\S', text, re.MULTILINE):
            return "yaml"
        
        # Check for CSV
        lines = text.split("\n")
        if len(lines) > 1:
            first_line = lines[0]
            if "," in first_line and all("," in line or line.strip() == "" for line in lines[:5]):
                return "csv"
        
        # Check for markdown
        if re.search(r'^#{1,6}\s|\*\*|\[.*\]\(.*\)', text):
            return "markdown"
        
        return "text"

    def _serialize_data(self, data: Union[str, dict, list]) -> str:
        """Serialize data to string for prompt."""
        if isinstance(data, str):
            return data
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _parse_json_response(self, text: str) -> Union[dict, list]:
        """Parse JSON from LLM response."""
        text = text.strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON in text
        for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
            json_match = re.search(pattern, text)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
        
        raise TransformServiceError(
            message="Failed to parse JSON from LLM response",
            code="JSON_PARSE_ERROR",
            details={"response_preview": text[:200]}
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def transform(
        self,
        data: Union[str, dict, list],
        instruction: str,
        input_format: Optional[str] = None,
        output_format: str = "json",
        examples: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform data using natural language instructions.
        
        Args:
            data: Input data (string, dict, or list)
            instruction: Natural language transformation instruction
            input_format: Input format (auto-detected if not specified)
            output_format: Desired output format
            examples: Few-shot examples
            model: Model to use
            
        Returns:
            Dictionary with transformed data
        """
        # Detect input format if not specified
        detected_format = input_format or self._detect_format(data)
        
        # Serialize input
        data_str = self._serialize_data(data)
        
        # Build prompt
        prompt_parts = [
            f"Transform the following {detected_format} data according to these instructions:",
            f"\nInstructions: {instruction}",
            f"\nInput data:\n```{detected_format}\n{data_str}\n```"
        ]
        
        # Add examples if provided
        if examples:
            prompt_parts.append("\nExamples of similar transformations:")
            for i, ex in enumerate(examples[:3], 1):
                prompt_parts.append(f"\nExample {i}:")
                prompt_parts.append(f"Input: {self._serialize_data(ex.get('input', ''))}")
                prompt_parts.append(f"Output: {self._serialize_data(ex.get('output', ''))}")
        
        # Specify output format
        prompt_parts.append(f"\nOutput the result as valid {output_format}.")
        if output_format == "json":
            prompt_parts.append("Return only the JSON, no explanations.")
        
        prompt = "\n".join(prompt_parts)
        
        # Call LLM
        result_text = await self._call_llm(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,
            model=model
        )
        
        # Parse result based on output format
        if output_format == "json":
            result = self._parse_json_response(result_text)
        else:
            result = result_text.strip()
        
        return {
            "result": result,
            "input_format": detected_format,
            "output_format": output_format,
            "model": model or self.model,
        }

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def transform_to_schema(
        self,
        data: Union[str, dict, list],
        target_schema: dict,
        source_schema: Optional[dict] = None,
        mapping_hints: Optional[Dict[str, str]] = None,
        fill_defaults: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform data to match a target JSON schema.
        
        Args:
            data: Input data
            target_schema: JSON Schema of desired output
            source_schema: JSON Schema of input (optional)
            mapping_hints: Explicit field mappings
            fill_defaults: Fill missing fields with defaults
            model: Model to use
            
        Returns:
            Dictionary with transformed data and mapping info
        """
        data_str = self._serialize_data(data)
        schema_str = json.dumps(target_schema, indent=2)
        
        prompt_parts = [
            "Transform the input data to match the target JSON schema.",
            f"\nInput data:\n```json\n{data_str}\n```",
            f"\nTarget schema:\n```json\n{schema_str}\n```"
        ]
        
        if mapping_hints:
            hints_str = json.dumps(mapping_hints, indent=2)
            prompt_parts.append(f"\nUse these field mappings:\n```json\n{hints_str}\n```")
        
        if fill_defaults:
            prompt_parts.append("\nFor any required fields that cannot be mapped, provide sensible default values.")
        
        prompt_parts.append("""
Output a JSON object with:
1. "result": the transformed data matching the target schema
2. "mappings": object showing how each target field was derived (e.g., {"target_field": "source_field"})
3. "defaults_used": array of fields that used default values

Return only valid JSON.""")
        
        prompt = "\n".join(prompt_parts)
        
        result_text = await self._call_llm(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,
            model=model
        )
        
        parsed = self._parse_json_response(result_text)
        
        # Extract components
        result = parsed.get("result", parsed)
        mappings = parsed.get("mappings", {})
        defaults_used = parsed.get("defaults_used", [])
        
        # Validate against schema (basic check)
        validation_passed = self._basic_schema_validate(result, target_schema)
        
        return {
            "result": result,
            "mappings_used": mappings,
            "fields_filled": defaults_used if defaults_used else None,
            "validation_passed": validation_passed,
            "model": model or self.model,
        }

    def _basic_schema_validate(self, data: Any, schema: dict) -> bool:
        """Basic schema validation (checks required fields)."""
        if not isinstance(schema, dict):
            return True
            
        schema_type = schema.get("type")
        
        if schema_type == "object":
            if not isinstance(data, dict):
                return False
            required = schema.get("required", [])
            return all(field in data for field in required)
        
        if schema_type == "array":
            return isinstance(data, list)
        
        return True

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def convert_format(
        self,
        data: str,
        source_format: Optional[str] = None,
        target_format: str = "json",
        infer_structure: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert data between formats.
        
        Args:
            data: Input data as string
            source_format: Source format (auto-detected if not specified)
            target_format: Target format
            infer_structure: Use LLM to infer structure from unstructured input
            model: Model to use
            
        Returns:
            Dictionary with converted data
        """
        detected_format = source_format or self._detect_format(data)
        
        # For simple conversions, try programmatic approach first
        if not infer_structure and detected_format == "json" and target_format in ["yaml", "xml"]:
            try:
                return await self._programmatic_convert(data, detected_format, target_format)
            except:
                pass  # Fall back to LLM
        
        prompt_parts = [
            f"Convert the following {detected_format} data to {target_format} format.",
            f"\nInput ({detected_format}):\n```\n{data}\n```"
        ]
        
        if infer_structure and detected_format == "text":
            prompt_parts.append("\nInfer the structure from the text and create a well-organized output.")
        
        format_instructions = {
            "json": "Output valid JSON.",
            "yaml": "Output valid YAML with proper indentation.",
            "xml": "Output valid XML with proper tags.",
            "csv": "Output CSV with a header row.",
            "markdown": "Output formatted markdown.",
            "html": "Output valid HTML.",
            "sql": "Output SQL INSERT statements."
        }
        
        prompt_parts.append(f"\n{format_instructions.get(target_format, 'Output the converted data.')}")
        prompt_parts.append("Return only the converted data, no explanations.")
        
        prompt = "\n".join(prompt_parts)
        
        result_text = await self._call_llm(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,
            model=model
        )
        
        # Clean up result
        result = result_text.strip()
        
        # Remove markdown code blocks if present
        code_match = re.search(r'```(?:\w+)?\s*([\s\S]*?)```', result)
        if code_match:
            result = code_match.group(1).strip()
        
        # Try to infer schema if converting to JSON
        inferred_schema = None
        if target_format == "json" and infer_structure:
            try:
                parsed = json.loads(result)
                inferred_schema = self._infer_schema(parsed)
            except:
                pass
        
        return {
            "result": result,
            "source_format": detected_format,
            "target_format": target_format,
            "inferred_schema": inferred_schema,
            "model": model or self.model,
        }

    async def _programmatic_convert(
        self,
        data: str,
        source_format: str,
        target_format: str
    ) -> Dict[str, Any]:
        """Attempt programmatic format conversion without LLM."""
        import yaml
        
        # Parse source
        if source_format == "json":
            parsed = json.loads(data)
        elif source_format == "yaml":
            parsed = yaml.safe_load(data)
        else:
            raise ValueError(f"Unsupported source format: {source_format}")
        
        # Convert to target
        if target_format == "json":
            result = json.dumps(parsed, indent=2)
        elif target_format == "yaml":
            result = yaml.dump(parsed, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported target format: {target_format}")
        
        return {
            "result": result,
            "source_format": source_format,
            "target_format": target_format,
            "inferred_schema": None,
            "model": "programmatic",
        }

    def _infer_schema(self, data: Any, max_depth: int = 3) -> dict:
        """Infer a basic JSON schema from data."""
        if max_depth <= 0:
            return {"type": "any"}
        
        if data is None:
            return {"type": "null"}
        if isinstance(data, bool):
            return {"type": "boolean"}
        if isinstance(data, int):
            return {"type": "integer"}
        if isinstance(data, float):
            return {"type": "number"}
        if isinstance(data, str):
            return {"type": "string"}
        
        if isinstance(data, list):
            if len(data) == 0:
                return {"type": "array", "items": {}}
            # Infer from first item
            return {
                "type": "array",
                "items": self._infer_schema(data[0], max_depth - 1)
            }
        
        if isinstance(data, dict):
            properties = {}
            for key, value in list(data.items())[:20]:  # Limit to 20 properties
                properties[key] = self._infer_schema(value, max_depth - 1)
            return {
                "type": "object",
                "properties": properties
            }
        
        return {"type": "any"}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def clean_data(
        self,
        data: Union[str, dict, list],
        operations: List[str],
        locale: str = "en-US",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean and normalize data.
        
        Args:
            data: Input data
            operations: List of cleaning operations
            locale: Locale for formatting
            model: Model to use
            
        Returns:
            Dictionary with cleaned data
        """
        data_str = self._serialize_data(data)
        ops_str = ", ".join(operations)
        
        operation_descriptions = {
            "trim": "Remove leading/trailing whitespace",
            "normalize_whitespace": "Replace multiple spaces with single space",
            "fix_encoding": "Fix encoding issues and special characters",
            "standardize_dates": f"Standardize dates to ISO format (locale: {locale})",
            "standardize_phones": f"Standardize phone numbers (locale: {locale})",
            "standardize_addresses": "Standardize address formatting",
            "deduplicate": "Remove duplicate records",
            "fill_missing": "Fill missing values with sensible defaults",
            "fix_typos": "Fix obvious typos in text fields",
            "normalize_case": "Normalize text case (title case for names, etc.)"
        }
        
        ops_desc = "\n".join(f"- {op}: {operation_descriptions.get(op, op)}" for op in operations)
        
        prompt = f"""Clean and normalize the following data by applying these operations:
{ops_desc}

Input data:
```json
{data_str}
```

Output a JSON object with:
1. "result": the cleaned data
2. "changes": array of strings describing each change made

Return only valid JSON."""
        
        result_text = await self._call_llm(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,
            model=model
        )
        
        parsed = self._parse_json_response(result_text)
        
        result = parsed.get("result", parsed)
        changes = parsed.get("changes", [])
        
        # Count removed records if deduplicate was requested
        records_removed = None
        if "deduplicate" in operations:
            if isinstance(data, list) and isinstance(result, list):
                records_removed = len(data) - len(result)
        
        return {
            "result": result,
            "changes_made": changes,
            "records_removed": records_removed,
            "model": model or self.model,
        }

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.ConnectError),
        reraise=True
    )
    async def merge_data(
        self,
        sources: List[Union[str, dict, list]],
        merge_strategy: str = "smart",
        key_fields: Optional[List[str]] = None,
        conflict_resolution: str = "merge",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Intelligently merge multiple data sources.
        
        Args:
            sources: List of data sources to merge
            merge_strategy: 'union', 'intersection', 'left', or 'smart'
            key_fields: Fields to use as merge keys
            conflict_resolution: How to resolve conflicts
            model: Model to use
            
        Returns:
            Dictionary with merged data
        """
        sources_str = "\n---\n".join(
            f"Source {i+1}:\n```json\n{self._serialize_data(s)}\n```"
            for i, s in enumerate(sources)
        )
        
        prompt_parts = [
            f"Merge the following {len(sources)} data sources.",
            f"\n{sources_str}",
            f"\nMerge strategy: {merge_strategy}"
        ]
        
        if key_fields:
            prompt_parts.append(f"Key fields for matching: {', '.join(key_fields)}")
        
        strategy_descriptions = {
            "union": "Include all records from all sources",
            "intersection": "Only include records that appear in all sources",
            "left": "Use first source as base, add matching data from others",
            "smart": "Intelligently determine the best way to merge based on data structure"
        }
        
        conflict_descriptions = {
            "first": "Use value from first source",
            "last": "Use value from last source",
            "merge": "Try to merge conflicting values intelligently",
            "ask": "Flag conflicts for review"
        }
        
        prompt_parts.append(f"\nStrategy meaning: {strategy_descriptions.get(merge_strategy, merge_strategy)}")
        prompt_parts.append(f"Conflict resolution: {conflict_descriptions.get(conflict_resolution, conflict_resolution)}")
        
        prompt_parts.append("""

Output a JSON object with:
1. "result": the merged data
2. "conflicts_resolved": number of conflicts that were resolved
3. "merge_report": brief summary of the merge

Return only valid JSON.""")
        
        prompt = "\n".join(prompt_parts)
        
        result_text = await self._call_llm(
            prompt=prompt,
            max_tokens=4096,
            temperature=0.1,
            model=model
        )
        
        parsed = self._parse_json_response(result_text)
        
        return {
            "result": parsed.get("result", parsed),
            "sources_merged": len(sources),
            "conflicts_resolved": parsed.get("conflicts_resolved", 0),
            "merge_report": parsed.get("merge_report"),
            "model": model or self.model,
        }


# Singleton instance
_transform_service: Optional[TransformService] = None


def get_transform_service() -> TransformService:
    """Get or create the transform service singleton."""
    global _transform_service
    if _transform_service is None:
        _transform_service = TransformService()
    return _transform_service


async def close_transform_service():
    """Close the transform service."""
    global _transform_service
    if _transform_service:
        await _transform_service.close()
        _transform_service = None
