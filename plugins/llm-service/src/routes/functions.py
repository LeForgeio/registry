"""
Function Calling Routes - Structured function/tool calling API.

Provides dedicated endpoints for:
- Function calling with tool definitions
- Structured JSON output with schema validation
- Parallel function calls
- Function execution with results
"""
from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import logging

from ..config import get_settings
from ..providers import ProviderFactory

router = APIRouter(prefix="/functions", tags=["Function Calling"])
logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class FunctionParameter(BaseModel):
    """Function parameter definition."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, number, boolean, array, object)")
    description: str = Field("", description="Parameter description")
    required: bool = Field(True, description="Whether parameter is required")
    enum: Optional[List[str]] = Field(None, description="Allowed values for enum type")
    items: Optional[Dict[str, Any]] = Field(None, description="Array item schema")
    properties: Optional[Dict[str, Any]] = Field(None, description="Object properties schema")


class FunctionDefinition(BaseModel):
    """Definition of a callable function/tool."""
    name: str = Field(..., description="Function name")
    description: str = Field(..., description="What the function does")
    parameters: List[FunctionParameter] = Field(
        default_factory=list, 
        description="Function parameters"
    )
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop: Dict[str, Any] = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.items:
                prop["items"] = param.items
            if param.properties:
                prop["properties"] = param.properties
            
            properties[param.name] = prop
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.to_openai_format()["parameters"]
        }


class FunctionCall(BaseModel):
    """A function call made by the model."""
    name: str = Field(..., description="Function name")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")
    id: Optional[str] = Field(None, description="Call ID for tracking")


class FunctionResult(BaseModel):
    """Result of a function execution."""
    call_id: str = Field(..., description="ID of the function call")
    name: str = Field(..., description="Function name")
    result: Any = Field(..., description="Function return value")
    error: Optional[str] = Field(None, description="Error message if failed")


class ChatMessage(BaseModel):
    """Chat message with optional function call."""
    role: str = Field(..., description="Message role: system, user, assistant, function")
    content: Optional[str] = Field(None, description="Message content")
    name: Optional[str] = Field(None, description="Function name (for function role)")
    function_call: Optional[FunctionCall] = Field(None, description="Function call (for assistant)")


class FunctionCallRequest(BaseModel):
    """Request for function calling completion."""
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    functions: List[FunctionDefinition] = Field(..., description="Available functions")
    model: Optional[str] = Field(None, description="Model to use")
    provider: Optional[str] = Field(None, description="Provider to use")
    function_call: Optional[Union[str, Dict[str, str]]] = Field(
        "auto",
        description="Function call mode: 'auto', 'none', or {'name': 'function_name'}"
    )
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(1024, ge=1, description="Maximum tokens")
    parallel_tool_calls: bool = Field(True, description="Allow parallel function calls")


class FunctionCallResponse(BaseModel):
    """Response from function calling completion."""
    message: ChatMessage = Field(..., description="Assistant message")
    function_calls: List[FunctionCall] = Field(
        default_factory=list,
        description="Function calls made by the model"
    )
    finish_reason: str = Field(..., description="Completion finish reason")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")


class ContinueWithResultsRequest(BaseModel):
    """Continue conversation after function execution."""
    messages: List[ChatMessage] = Field(..., description="Conversation messages including function results")
    functions: List[FunctionDefinition] = Field(..., description="Available functions")
    function_results: List[FunctionResult] = Field(..., description="Results from executed functions")
    model: Optional[str] = Field(None, description="Model to use")
    provider: Optional[str] = Field(None, description="Provider to use")
    max_tokens: int = Field(1024, ge=1, description="Maximum tokens")


# =============================================================================
# JSON Mode Models  
# =============================================================================

class JSONSchemaProperty(BaseModel):
    """JSON Schema property definition."""
    type: str = Field(..., description="Property type")
    description: Optional[str] = Field(None, description="Property description")
    enum: Optional[List[str]] = Field(None, description="Allowed values")
    items: Optional[Dict[str, Any]] = Field(None, description="Array items schema")
    properties: Optional[Dict[str, Any]] = Field(None, description="Nested object properties")
    required: Optional[List[str]] = Field(None, description="Required nested properties")


class JSONSchema(BaseModel):
    """JSON Schema definition for structured output."""
    type: str = Field("object", description="Root type (usually object)")
    properties: Dict[str, JSONSchemaProperty] = Field(..., description="Object properties")
    required: List[str] = Field(default_factory=list, description="Required properties")
    additionalProperties: bool = Field(False, description="Allow additional properties")


class JSONModeRequest(BaseModel):
    """Request for JSON mode completion."""
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    schema_: JSONSchema = Field(..., alias="schema", description="Expected JSON schema")
    model: Optional[str] = Field(None, description="Model to use")
    provider: Optional[str] = Field(None, description="Provider to use")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(2048, ge=1, description="Maximum tokens")
    strict: bool = Field(True, description="Strict schema validation")


class JSONModeResponse(BaseModel):
    """Response from JSON mode completion."""
    data: Dict[str, Any] = Field(..., description="Parsed JSON response")
    raw_content: str = Field(..., description="Raw response text")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    schema_valid: bool = Field(..., description="Whether response matches schema")
    validation_errors: List[str] = Field(default_factory=list, description="Schema validation errors")


# =============================================================================
# Function Calling Endpoints
# =============================================================================

@router.post("/call", response_model=FunctionCallResponse)
async def function_call_completion(request: FunctionCallRequest):
    """
    Generate a completion that may include function calls.
    
    The model will analyze the conversation and available functions,
    then either respond with text or request function calls.
    
    Use 'auto' for function_call to let the model decide,
    'none' to disable function calling, or specify a function name
    to force a specific function call.
    """
    settings = get_settings()
    factory = ProviderFactory()
    
    # Get provider
    provider_name = request.provider or settings.default_provider
    try:
        provider = factory.get(provider_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Provider not available: {e}")
    
    # Check capability
    if not provider.capabilities.function_calling:
        raise HTTPException(
            status_code=400, 
            detail=f"Provider {provider_name} does not support function calling"
        )
    
    # Convert functions to provider format
    tools = []
    for func in request.functions:
        if provider_name in ("openai", "azure"):
            tools.append({
                "type": "function",
                "function": func.to_openai_format()
            })
        elif provider_name == "anthropic":
            tools.append(func.to_anthropic_format())
        else:
            tools.append(func.to_openai_format())
    
    # Convert messages
    messages = []
    for msg in request.messages:
        m = {"role": msg.role, "content": msg.content or ""}
        if msg.name:
            m["name"] = msg.name
        if msg.function_call:
            m["function_call"] = {
                "name": msg.function_call.name,
                "arguments": json.dumps(msg.function_call.arguments)
            }
        messages.append(m)
    
    try:
        # Call provider with tools
        response = await provider.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=tools,
            tool_choice=request.function_call
        )
        
        # Parse function calls from response
        function_calls = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                function_calls.append(FunctionCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                    id=tc.id
                ))
        
        # Build response message
        assistant_msg = ChatMessage(
            role="assistant",
            content=response.content,
            function_call=function_calls[0] if len(function_calls) == 1 else None
        )
        
        return FunctionCallResponse(
            message=assistant_msg,
            function_calls=function_calls,
            finish_reason=response.finish_reason or "stop",
            model=request.model or provider.config.default_model,
            provider=provider_name
        )
        
    except Exception as e:
        logger.error(f"Function call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue")
async def continue_with_results(request: ContinueWithResultsRequest):
    """
    Continue the conversation after executing function calls.
    
    Pass the original messages plus the function results,
    and the model will generate a response using those results.
    """
    settings = get_settings()
    factory = ProviderFactory()
    
    provider_name = request.provider or settings.default_provider
    try:
        provider = factory.get(provider_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Provider not available: {e}")
    
    # Build messages with function results
    messages = []
    for msg in request.messages:
        m = {"role": msg.role, "content": msg.content or ""}
        if msg.name:
            m["name"] = msg.name
        messages.append(m)
    
    # Add function results as tool response messages
    for result in request.function_results:
        if provider_name in ("openai", "azure"):
            messages.append({
                "role": "tool",
                "tool_call_id": result.call_id,
                "content": json.dumps(result.result) if not isinstance(result.result, str) else result.result
            })
        else:
            # Generic format
            messages.append({
                "role": "function",
                "name": result.name,
                "content": json.dumps(result.result) if not isinstance(result.result, str) else result.result
            })
    
    try:
        response = await provider.chat(
            messages=messages,
            model=request.model,
            max_tokens=request.max_tokens,
            tools=[f.to_openai_format() for f in request.functions]
        )
        
        return {
            "message": {
                "role": "assistant",
                "content": response.content
            },
            "finish_reason": response.finish_reason or "stop",
            "model": request.model or provider.config.default_model,
            "provider": provider_name
        }
        
    except Exception as e:
        logger.error(f"Continue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# JSON Mode Endpoints
# =============================================================================

@router.post("/json", response_model=JSONModeResponse)
async def json_mode_completion(request: JSONModeRequest):
    """
    Generate a completion constrained to valid JSON matching a schema.
    
    The model will output valid JSON that conforms to the provided schema.
    Use this for structured data extraction, form filling, or any task
    requiring predictable output format.
    """
    settings = get_settings()
    factory = ProviderFactory()
    
    provider_name = request.provider or settings.default_provider
    try:
        provider = factory.get(provider_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Provider not available: {e}")
    
    # Check capability
    if not provider.capabilities.json_mode:
        raise HTTPException(
            status_code=400,
            detail=f"Provider {provider_name} does not support JSON mode"
        )
    
    # Build system prompt with schema
    schema_dict = request.schema_.model_dump(by_alias=True)
    schema_prompt = f"""You must respond with valid JSON that matches this schema:
```json
{json.dumps(schema_dict, indent=2)}
```

Rules:
- Output ONLY valid JSON, no other text
- Include all required fields
- Use correct types for each field
- Do not include fields not in the schema"""
    
    # Prepend schema instruction to messages
    messages = [{"role": "system", "content": schema_prompt}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content or ""})
    
    try:
        response = await provider.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format={"type": "json_object"}
        )
        
        raw_content = response.content.strip()
        
        # Parse JSON
        try:
            # Handle markdown code blocks
            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                raw_content = "\n".join(lines[1:-1])
            
            data = json.loads(raw_content)
            schema_valid = True
            validation_errors = []
            
            # Basic schema validation
            if request.strict:
                for required_field in request.schema_.required:
                    if required_field not in data:
                        schema_valid = False
                        validation_errors.append(f"Missing required field: {required_field}")
                
                for field, value in data.items():
                    if field in request.schema_.properties:
                        prop = request.schema_.properties[field]
                        # Type checking
                        expected_type = prop.type
                        actual_type = type(value).__name__
                        type_map = {
                            "string": "str",
                            "number": ("int", "float"),
                            "integer": "int",
                            "boolean": "bool",
                            "array": "list",
                            "object": "dict"
                        }
                        expected = type_map.get(expected_type, expected_type)
                        if isinstance(expected, tuple):
                            if actual_type not in expected:
                                schema_valid = False
                                validation_errors.append(
                                    f"Field '{field}' expected {expected_type}, got {actual_type}"
                                )
                        elif actual_type != expected:
                            schema_valid = False
                            validation_errors.append(
                                f"Field '{field}' expected {expected_type}, got {actual_type}"
                            )
            
        except json.JSONDecodeError as e:
            data = {}
            schema_valid = False
            validation_errors = [f"Invalid JSON: {e}"]
        
        return JSONModeResponse(
            data=data,
            raw_content=response.content,
            model=request.model or provider.config.default_model,
            provider=provider_name,
            schema_valid=schema_valid,
            validation_errors=validation_errors
        )
        
    except Exception as e:
        logger.error(f"JSON mode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_structured_data(
    text: str,
    fields: Dict[str, str],
    model: Optional[str] = None,
    provider: Optional[str] = None
):
    """
    Extract structured data from text into specified fields.
    
    Simplified endpoint for common extraction tasks.
    
    Example:
    ```
    POST /functions/extract
    {
        "text": "John Smith, 35 years old, lives in New York",
        "fields": {
            "name": "Person's full name",
            "age": "Age as a number",
            "city": "City of residence"
        }
    }
    ```
    """
    settings = get_settings()
    factory = ProviderFactory()
    
    provider_name = provider or settings.default_provider
    try:
        llm_provider = factory.get(provider_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Provider not available: {e}")
    
    # Build schema from fields
    properties = {}
    for field_name, description in fields.items():
        properties[field_name] = {"type": "string", "description": description}
    
    schema_dict = {
        "type": "object",
        "properties": properties,
        "required": list(fields.keys())
    }
    
    prompt = f"""Extract the following information from the text and return as JSON:

Fields to extract:
{json.dumps(fields, indent=2)}

Text:
{text}

Return only valid JSON matching this schema:
{json.dumps(schema_dict, indent=2)}"""
    
    try:
        response = await llm_provider.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.0,
            response_format={"type": "json_object"} if llm_provider.capabilities.json_mode else None
        )
        
        # Parse response
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {"raw": content, "parse_error": True}
        
        return {
            "extracted": data,
            "source_text": text[:200] + "..." if len(text) > 200 else text,
            "model": model or llm_provider.config.default_model,
            "provider": provider_name
        }
        
    except Exception as e:
        logger.error(f"Extract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/schemas/examples")
async def get_schema_examples():
    """
    Get example JSON schemas for common use cases.
    """
    return {
        "person": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Full name"},
                "age": {"type": "integer", "description": "Age in years"},
                "email": {"type": "string", "description": "Email address"},
                "occupation": {"type": "string", "description": "Job title"}
            },
            "required": ["name"]
        },
        "sentiment_analysis": {
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                    "description": "Overall sentiment"
                },
                "confidence": {"type": "number", "description": "Confidence 0-1"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key phrases"
                }
            },
            "required": ["sentiment", "confidence"]
        },
        "product_review": {
            "type": "object",
            "properties": {
                "rating": {"type": "integer", "description": "Rating 1-5"},
                "pros": {"type": "array", "items": {"type": "string"}},
                "cons": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string", "description": "Brief summary"},
                "recommend": {"type": "boolean"}
            },
            "required": ["rating", "summary", "recommend"]
        },
        "event": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "date": {"type": "string", "description": "ISO date format"},
                "time": {"type": "string", "description": "HH:MM format"},
                "location": {"type": "string"},
                "participants": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "date"]
        }
    }


@router.get("/functions/examples")
async def get_function_examples():
    """
    Get example function definitions for common use cases.
    """
    return {
        "weather": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": [
                {
                    "name": "location",
                    "type": "string",
                    "description": "City and state/country",
                    "required": True
                },
                {
                    "name": "unit",
                    "type": "string",
                    "description": "Temperature unit",
                    "required": False,
                    "enum": ["celsius", "fahrenheit"]
                }
            ]
        },
        "search": {
            "name": "search_database",
            "description": "Search a database for records",
            "parameters": [
                {
                    "name": "query",
                    "type": "string",
                    "description": "Search query",
                    "required": True
                },
                {
                    "name": "filters",
                    "type": "object",
                    "description": "Filter criteria",
                    "required": False,
                    "properties": {
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "category": {"type": "string"}
                    }
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "description": "Max results",
                    "required": False
                }
            ]
        },
        "send_email": {
            "name": "send_email",
            "description": "Send an email to a recipient",
            "parameters": [
                {
                    "name": "to",
                    "type": "string",
                    "description": "Recipient email address",
                    "required": True
                },
                {
                    "name": "subject",
                    "type": "string",
                    "description": "Email subject",
                    "required": True
                },
                {
                    "name": "body",
                    "type": "string",
                    "description": "Email body content",
                    "required": True
                },
                {
                    "name": "cc",
                    "type": "array",
                    "description": "CC recipients",
                    "required": False,
                    "items": {"type": "string"}
                }
            ]
        }
    }
