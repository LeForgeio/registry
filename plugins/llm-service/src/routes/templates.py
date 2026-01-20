"""
Prompt Templates Routes - Reusable prompt template system.

Provides:
- Template management (CRUD)
- Variable interpolation  
- Template library with categories
- Version control for templates
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json
import re
import logging
from pathlib import Path

router = APIRouter(prefix="/templates", tags=["Prompt Templates"])
logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================

class TemplateVariable(BaseModel):
    """Variable definition for a template."""
    name: str = Field(..., description="Variable name (without braces)")
    description: str = Field("", description="What this variable is for")
    type: str = Field("string", description="Variable type: string, number, list, object")
    default: Optional[Any] = Field(None, description="Default value")
    required: bool = Field(True, description="Whether variable is required")
    examples: List[str] = Field(default_factory=list, description="Example values")


class PromptTemplate(BaseModel):
    """A reusable prompt template."""
    id: str = Field(..., description="Unique template ID")
    name: str = Field(..., description="Human-readable name")
    description: str = Field("", description="What this template does")
    category: str = Field("general", description="Template category")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    
    # Template content
    system_prompt: Optional[str] = Field(None, description="System prompt template")
    user_prompt: str = Field(..., description="User prompt template")
    
    # Variables
    variables: List[TemplateVariable] = Field(
        default_factory=list,
        description="Variables used in the template"
    )
    
    # Metadata
    version: str = Field("1.0.0", description="Template version")
    author: Optional[str] = Field(None, description="Template author")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    # Recommended settings
    recommended_model: Optional[str] = Field(None, description="Recommended model")
    recommended_temperature: Optional[float] = Field(None, description="Recommended temperature")
    recommended_max_tokens: Optional[int] = Field(None, description="Recommended max tokens")


class RenderRequest(BaseModel):
    """Request to render a template with variables."""
    template_id: str = Field(..., description="Template ID to render")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variable values")
    validate_only: bool = Field(False, description="Only validate, don't render")


class RenderResponse(BaseModel):
    """Rendered template response."""
    system_prompt: Optional[str] = Field(None, description="Rendered system prompt")
    user_prompt: str = Field(..., description="Rendered user prompt")
    template_id: str = Field(..., description="Template used")
    variables_used: Dict[str, Any] = Field(..., description="Variables that were used")
    missing_variables: List[str] = Field(default_factory=list, description="Missing required variables")


class ExecuteRequest(BaseModel):
    """Request to execute a template (render + call LLM)."""
    template_id: str = Field(..., description="Template ID to execute")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variable values")
    provider: Optional[str] = Field(None, description="Provider to use")
    model: Optional[str] = Field(None, description="Model to use (overrides template)")
    temperature: Optional[float] = Field(None, description="Temperature (overrides template)")
    max_tokens: Optional[int] = Field(None, description="Max tokens (overrides template)")
    stream: bool = Field(False, description="Stream response")


# =============================================================================
# In-Memory Template Store (replace with DB in production)
# =============================================================================

class TemplateStore:
    """Simple in-memory template store."""
    
    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in template library."""
        builtins = [
            PromptTemplate(
                id="summarize-document",
                name="Document Summarizer",
                description="Summarize a document to key points",
                category="summarization",
                tags=["summarize", "document", "extract"],
                system_prompt="You are a skilled document analyst. Your task is to summarize documents concisely while preserving key information.",
                user_prompt="""Summarize the following document in {length} format:

Document:
{document}

Provide a {style} summary that captures:
- Main topics and themes
- Key facts and figures
- Important conclusions

Summary:""",
                variables=[
                    TemplateVariable(name="document", description="The document to summarize", required=True),
                    TemplateVariable(name="length", description="Summary length", default="brief", examples=["brief", "detailed", "bullet points"]),
                    TemplateVariable(name="style", description="Writing style", default="professional", examples=["professional", "casual", "technical"])
                ],
                recommended_temperature=0.3,
                recommended_max_tokens=500
            ),
            PromptTemplate(
                id="code-review",
                name="Code Reviewer",
                description="Review code for bugs, style, and improvements",
                category="coding",
                tags=["code", "review", "bugs", "quality"],
                system_prompt="You are an expert code reviewer with deep knowledge of best practices, security, and performance optimization.",
                user_prompt="""Review the following {language} code:

```{language}
{code}
```

Focus on:
{focus_areas}

Provide:
1. Summary of what the code does
2. Potential bugs or issues
3. Style and best practice suggestions
4. Performance considerations
5. Security concerns (if applicable)

Review:""",
                variables=[
                    TemplateVariable(name="code", description="The code to review", required=True),
                    TemplateVariable(name="language", description="Programming language", default="python"),
                    TemplateVariable(name="focus_areas", description="Areas to focus on", default="- Code quality\n- Error handling\n- Edge cases")
                ],
                recommended_temperature=0.2,
                recommended_max_tokens=1000
            ),
            PromptTemplate(
                id="data-extraction",
                name="Data Extractor",
                description="Extract structured data from unstructured text",
                category="extraction",
                tags=["extract", "data", "structured", "parse"],
                system_prompt="You are a data extraction specialist. Extract information precisely and format it as requested.",
                user_prompt="""Extract the following information from the text:

Fields to extract:
{fields}

Text:
{text}

Output format: {output_format}

Extracted data:""",
                variables=[
                    TemplateVariable(name="text", description="Text to extract from", required=True),
                    TemplateVariable(name="fields", description="Fields to extract", required=True, examples=["name, email, phone", "date, amount, description"]),
                    TemplateVariable(name="output_format", description="Output format", default="JSON", examples=["JSON", "YAML", "table"])
                ],
                recommended_temperature=0.0,
                recommended_max_tokens=500
            ),
            PromptTemplate(
                id="email-composer",
                name="Email Composer",
                description="Compose professional emails",
                category="writing",
                tags=["email", "compose", "professional", "communication"],
                system_prompt="You are an expert business communicator who writes clear, professional emails.",
                user_prompt="""Compose a {tone} email for the following situation:

Purpose: {purpose}
Recipient: {recipient}
Key points to include:
{key_points}

Additional context: {context}

Email:""",
                variables=[
                    TemplateVariable(name="purpose", description="Email purpose", required=True),
                    TemplateVariable(name="recipient", description="Who is receiving this", required=True),
                    TemplateVariable(name="key_points", description="Main points to cover", required=True),
                    TemplateVariable(name="tone", description="Email tone", default="professional", examples=["professional", "friendly", "formal", "apologetic"]),
                    TemplateVariable(name="context", description="Additional context", default="")
                ],
                recommended_temperature=0.7,
                recommended_max_tokens=500
            ),
            PromptTemplate(
                id="sql-generator",
                name="SQL Query Generator",
                description="Generate SQL queries from natural language",
                category="coding",
                tags=["sql", "database", "query", "generate"],
                system_prompt="You are a SQL expert. Generate correct, efficient SQL queries based on the requirements.",
                user_prompt="""Generate a SQL query for the following request:

Database type: {db_type}

Table schema:
{schema}

Request: {request}

Requirements:
- Use proper SQL syntax for {db_type}
- Include comments explaining the query
- Optimize for performance where possible

SQL Query:""",
                variables=[
                    TemplateVariable(name="request", description="What data to retrieve", required=True),
                    TemplateVariable(name="schema", description="Table schema definition", required=True),
                    TemplateVariable(name="db_type", description="Database type", default="PostgreSQL", examples=["PostgreSQL", "MySQL", "SQLite", "SQL Server"])
                ],
                recommended_temperature=0.0,
                recommended_max_tokens=500
            ),
            PromptTemplate(
                id="translation",
                name="Text Translator",
                description="Translate text between languages",
                category="translation",
                tags=["translate", "language", "localization"],
                system_prompt="You are a professional translator with expertise in maintaining tone, context, and cultural nuances.",
                user_prompt="""Translate the following text from {source_language} to {target_language}.

{translation_style}

Text to translate:
{text}

Translation:""",
                variables=[
                    TemplateVariable(name="text", description="Text to translate", required=True),
                    TemplateVariable(name="source_language", description="Source language", default="auto-detect"),
                    TemplateVariable(name="target_language", description="Target language", required=True),
                    TemplateVariable(name="translation_style", description="Translation style instructions", default="Maintain the original tone and style.")
                ],
                recommended_temperature=0.3,
                recommended_max_tokens=1000
            ),
            PromptTemplate(
                id="persona-chat",
                name="Persona Chat",
                description="Chat as a specific persona/character",
                category="chat",
                tags=["persona", "character", "roleplay", "chat"],
                system_prompt="""{persona_description}

Personality traits: {traits}
Speaking style: {speaking_style}

Stay in character at all times. Respond as this persona would.""",
                user_prompt="{user_message}",
                variables=[
                    TemplateVariable(name="persona_description", description="Who is this persona", required=True, examples=["You are a wise medieval wizard", "You are a friendly customer support agent"]),
                    TemplateVariable(name="traits", description="Key personality traits", default="helpful, knowledgeable"),
                    TemplateVariable(name="speaking_style", description="How they speak", default="casual and friendly"),
                    TemplateVariable(name="user_message", description="User's message", required=True)
                ],
                recommended_temperature=0.8,
                recommended_max_tokens=500
            ),
            PromptTemplate(
                id="analysis-report",
                name="Analysis Report Generator",
                description="Generate analysis reports from data",
                category="analysis",
                tags=["analysis", "report", "data", "insights"],
                system_prompt="You are a data analyst who creates insightful, actionable reports.",
                user_prompt="""Generate an analysis report for the following data:

Data:
{data}

Analysis focus: {focus}
Report format: {format}
Target audience: {audience}

Include:
- Executive summary
- Key findings
- Trends and patterns
- Recommendations

Report:""",
                variables=[
                    TemplateVariable(name="data", description="Data to analyze", required=True),
                    TemplateVariable(name="focus", description="What to focus the analysis on", default="general overview"),
                    TemplateVariable(name="format", description="Report format", default="structured", examples=["structured", "narrative", "bullet points"]),
                    TemplateVariable(name="audience", description="Who will read this", default="business stakeholders")
                ],
                recommended_temperature=0.4,
                recommended_max_tokens=1500
            )
        ]
        
        for template in builtins:
            template.created_at = datetime.utcnow().isoformat()
            template.author = "FlowForge"
            self._templates[template.id] = template
    
    def get(self, template_id: str) -> Optional[PromptTemplate]:
        return self._templates.get(template_id)
    
    def list(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[PromptTemplate]:
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tag:
            templates = [t for t in templates if tag in t.tags]
        
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower() 
                or search_lower in t.description.lower()
                or any(search_lower in tag.lower() for tag in t.tags)
            ]
        
        return templates
    
    def create(self, template: PromptTemplate) -> PromptTemplate:
        if template.id in self._templates:
            raise ValueError(f"Template {template.id} already exists")
        template.created_at = datetime.utcnow().isoformat()
        template.updated_at = template.created_at
        self._templates[template.id] = template
        return template
    
    def update(self, template_id: str, updates: Dict[str, Any]) -> Optional[PromptTemplate]:
        if template_id not in self._templates:
            return None
        template = self._templates[template_id]
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        template.updated_at = datetime.utcnow().isoformat()
        return template
    
    def delete(self, template_id: str) -> bool:
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    def get_categories(self) -> List[str]:
        return list(set(t.category for t in self._templates.values()))
    
    def get_tags(self) -> List[str]:
        tags = set()
        for t in self._templates.values():
            tags.update(t.tags)
        return sorted(tags)


# Global store instance
_store = TemplateStore()


# =============================================================================
# Helper Functions
# =============================================================================

def render_template(template: str, variables: Dict[str, Any]) -> str:
    """Render a template string with variables."""
    result = template
    for name, value in variables.items():
        # Handle different value types
        if isinstance(value, list):
            value = "\n".join(str(v) for v in value)
        elif isinstance(value, dict):
            value = json.dumps(value, indent=2)
        
        # Replace {variable} patterns
        result = result.replace(f"{{{name}}}", str(value))
    
    return result


def extract_variables(template: str) -> List[str]:
    """Extract variable names from a template string."""
    pattern = r'\{(\w+)\}'
    return list(set(re.findall(pattern, template)))


def validate_variables(
    template: PromptTemplate,
    provided: Dict[str, Any]
) -> tuple[Dict[str, Any], List[str]]:
    """Validate and fill in variables. Returns (final_vars, missing_required)."""
    final_vars = {}
    missing = []
    
    for var in template.variables:
        if var.name in provided:
            final_vars[var.name] = provided[var.name]
        elif var.default is not None:
            final_vars[var.name] = var.default
        elif var.required:
            missing.append(var.name)
    
    return final_vars, missing


# =============================================================================
# Endpoints
# =============================================================================

@router.get("")
async def list_templates(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List available prompt templates.
    
    Filter by category, tag, or search query.
    """
    templates = _store.list(category=category, tag=tag, search=search)
    return {
        "count": len(templates),
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "tags": t.tags,
                "version": t.version
            }
            for t in templates
        ]
    }


@router.get("/categories")
async def list_categories():
    """List all template categories."""
    return {"categories": _store.get_categories()}


@router.get("/tags")
async def list_tags():
    """List all template tags."""
    return {"tags": _store.get_tags()}


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID."""
    template = _store.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return template


@router.post("")
async def create_template(template: PromptTemplate):
    """
    Create a new prompt template.
    
    Template IDs must be unique. Variables in the template should
    be enclosed in curly braces: {variable_name}
    """
    try:
        created = _store.create(template)
        return {"status": "created", "template": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{template_id}")
async def update_template(template_id: str, updates: Dict[str, Any]):
    """Update an existing template."""
    updated = _store.update(template_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return {"status": "updated", "template": updated}


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """Delete a template."""
    deleted = _store.delete(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return {"status": "deleted", "template_id": template_id}


@router.post("/render")
async def render_prompt(request: RenderRequest):
    """
    Render a template with provided variables.
    
    Returns the rendered system and user prompts ready for LLM use.
    """
    template = _store.get(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {request.template_id}")
    
    # Validate and fill variables
    final_vars, missing = validate_variables(template, request.variables)
    
    if request.validate_only:
        return {
            "valid": len(missing) == 0,
            "missing_variables": missing,
            "variables_used": final_vars
        }
    
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required variables: {missing}"
        )
    
    # Render templates
    rendered_user = render_template(template.user_prompt, final_vars)
    rendered_system = None
    if template.system_prompt:
        rendered_system = render_template(template.system_prompt, final_vars)
    
    return RenderResponse(
        system_prompt=rendered_system,
        user_prompt=rendered_user,
        template_id=template.id,
        variables_used=final_vars,
        missing_variables=[]
    )


@router.post("/execute")
async def execute_template(request: ExecuteRequest):
    """
    Execute a template: render and send to LLM.
    
    Combines template rendering with LLM completion in one call.
    """
    from ..config import get_settings
    from ..providers import ProviderFactory
    
    template = _store.get(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {request.template_id}")
    
    # Validate and fill variables
    final_vars, missing = validate_variables(template, request.variables)
    
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required variables: {missing}"
        )
    
    # Render templates
    rendered_user = render_template(template.user_prompt, final_vars)
    rendered_system = None
    if template.system_prompt:
        rendered_system = render_template(template.system_prompt, final_vars)
    
    # Get LLM settings
    settings = get_settings()
    factory = ProviderFactory()
    
    provider_name = request.provider or settings.default_provider
    try:
        provider = factory.get(provider_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Provider not available: {e}")
    
    # Build messages
    messages = []
    if rendered_system:
        messages.append({"role": "system", "content": rendered_system})
    messages.append({"role": "user", "content": rendered_user})
    
    # Determine parameters (request overrides template recommendations)
    model = request.model or template.recommended_model
    temperature = request.temperature if request.temperature is not None else (template.recommended_temperature or 0.7)
    max_tokens = request.max_tokens or template.recommended_max_tokens or 1024
    
    try:
        if request.stream:
            # Return streaming response
            from fastapi.responses import StreamingResponse
            
            async def generate():
                async for chunk in provider.chat_stream(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            response = await provider.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "template_id": template.id,
                "rendered_prompt": {
                    "system": rendered_system,
                    "user": rendered_user
                },
                "variables_used": final_vars,
                "response": {
                    "content": response.content,
                    "model": model or provider.config.default_model,
                    "provider": provider_name
                }
            }
            
    except Exception as e:
        logger.error(f"Template execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_template(template_content: str):
    """
    Analyze a template string.
    
    Returns extracted variables and validation info.
    """
    variables = extract_variables(template_content)
    
    return {
        "variables": variables,
        "variable_count": len(variables),
        "template_length": len(template_content),
        "suggestions": [
            f"Add descriptions for variables: {variables}" if variables else "No variables found in template"
        ]
    }


@router.post("/import")
async def import_templates(templates: List[PromptTemplate]):
    """
    Import multiple templates at once.
    """
    results = {"created": [], "errors": []}
    
    for template in templates:
        try:
            _store.create(template)
            results["created"].append(template.id)
        except ValueError as e:
            results["errors"].append({"id": template.id, "error": str(e)})
    
    return results


@router.get("/export/all")
async def export_all_templates():
    """Export all templates as JSON."""
    templates = _store.list()
    return {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "count": len(templates),
        "templates": [t.model_dump() for t in templates]
    }
