#!/usr/bin/env python3
"""
LeForge Integration Generator

Generates platform-specific integration packages from plugin forgehook.json manifests.

Supported Platforms:
- Power Automate (OpenAPI Custom Connector)
- Nintex Workflow Cloud (OpenAPI Xtension)
- Nintex K2 (Swagger + SmartObject templates)
- n8n (TypeScript npm package)
- OutSystems (REST specs)
- Mendix (REST specs + Java action stubs)

Usage:
    python generate-integrations.py [options]

Options:
    --platform PLATFORM    Generate for specific platform only
    --plugin PLUGIN        Generate for specific plugin only
    --output DIR           Output directory (default: ../integrations)
    --verbose              Enable verbose output
"""

import json
import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Constants
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent
PLUGINS_DIR = ROOT_DIR / "plugins"
INTEGRATIONS_DIR = ROOT_DIR / "integrations"

SUPPORTED_PLATFORMS = [
    "power-automate",
    "nintex-cloud", 
    "nintex-k2",
    "n8n",
    "outsystems",
    "mendix",
    "salesforce",
    "servicenow"
]

SUPPORTED_PLUGINS = [
    "llm-service",
    "formula-engine",
    "streaming-file-service",
    "crypto-service"
]

# Brand colors for each plugin
PLUGIN_COLORS = {
    "llm-service": "#6366f1",      # Indigo
    "formula-engine": "#10b981",   # Emerald
    "streaming-file-service": "#f59e0b",  # Amber
    "crypto-service": "#ef4444"    # Red
}


def load_forgehook(plugin_name: str) -> Optional[Dict[str, Any]]:
    """Load forgehook.json for a plugin."""
    forgehook_path = PLUGINS_DIR / plugin_name / "forgehook.json"
    if not forgehook_path.exists():
        print(f"Warning: forgehook.json not found for {plugin_name}")
        return None
    
    with open(forgehook_path, "r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_operation_id(path: str, method: str) -> str:
    """Convert path to a valid operation ID."""
    # Remove path parameters and special characters
    clean = re.sub(r'\{[^}]+\}', '', path)
    clean = re.sub(r'[^a-zA-Z0-9]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    
    # Capitalize and prepend method
    parts = [p.capitalize() for p in clean.split('_') if p]
    return method.capitalize() + ''.join(parts)


def generate_action_name(path: str, method: str) -> str:
    """Generate a human-readable action name from path and method."""
    # Remove leading slash and path parameters
    clean = re.sub(r'\{[^}]+\}', '', path).strip('/')
    
    # Split by slashes and capitalize
    parts = [p.replace('-', ' ').replace('_', ' ').title() for p in clean.split('/') if p]
    
    # Add method prefix for non-standard operations
    if method.upper() == "DELETE":
        return "Delete " + " ".join(parts) if parts else "Delete"
    elif method.upper() == "PUT":
        return "Update " + " ".join(parts) if parts else "Update"
    elif method.upper() == "GET":
        if not parts:
            return "List All"
        return "Get " + " ".join(parts)
    elif method.upper() == "POST":
        return " ".join(parts) if parts else "Create"
    
    return " ".join(parts) if parts else method.capitalize()


def generate_openapi_20(forgehook: Dict[str, Any], plugin_name: str) -> Dict[str, Any]:
    """Generate OpenAPI 2.0 (Swagger) spec from forgehook.json."""
    info = forgehook.get("info", {})
    endpoints = forgehook.get("endpoints", [])
    
    swagger = {
        "swagger": "2.0",
        "info": {
            "title": f"LeForge {info.get('name', plugin_name)}",
            "description": info.get("description", "LeForge plugin"),
            "version": info.get("version", "1.0.0"),
            "contact": {
                "name": "LeForge Support",
                "url": "https://LeForge.io"
            }
        },
        "host": "{{HOST}}",
        "basePath": "/api/v1",
        "schemes": ["https"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "api_key": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "LeForge API Key"
            }
        },
        "security": [{"api_key": []}],
        "paths": {},
        "definitions": {}
    }
    
    # Group endpoints by path
    paths = {}
    for endpoint in endpoints:
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET").lower()
        
        if path not in paths:
            paths[path] = {}
        
        # Generate action name from path if not provided
        action_name = endpoint.get("name") or generate_action_name(path, method.upper())
        
        operation = {
            "operationId": sanitize_operation_id(path, method),
            "summary": action_name,
            "description": endpoint.get("description", ""),
            "tags": [endpoint.get("category", "General")],
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "schema": {
                        "type": "object"
                    }
                },
                "400": {
                    "description": "Bad request"
                },
                "401": {
                    "description": "Unauthorized"
                },
                "500": {
                    "description": "Internal server error"
                }
            }
        }
        
        # Add request body for POST/PUT/PATCH
        if method in ["post", "put", "patch"]:
            request_body = endpoint.get("requestBody", {})
            if request_body:
                operation["parameters"].append({
                    "in": "body",
                    "name": "body",
                    "description": "Request body",
                    "required": True,
                    "schema": convert_to_swagger_schema(request_body)
                })
        
        # Add path parameters
        path_params = re.findall(r'\{([^}]+)\}', path)
        for param in path_params:
            operation["parameters"].append({
                "in": "path",
                "name": param,
                "type": "string",
                "required": True,
                "description": f"Path parameter: {param}"
            })
        
        # Add query parameters
        query_params = endpoint.get("queryParams", [])
        for param in query_params:
            operation["parameters"].append({
                "in": "query",
                "name": param.get("name", ""),
                "type": param.get("type", "string"),
                "required": param.get("required", False),
                "description": param.get("description", "")
            })
        
        paths[path][method] = operation
    
    swagger["paths"] = paths
    return swagger


def convert_to_swagger_schema(schema: Any) -> Dict[str, Any]:
    """Convert forgehook schema to Swagger schema format."""
    if not schema:
        return {"type": "object"}
    
    # Handle string schema references
    if isinstance(schema, str):
        return {"type": "string", "description": schema}
    
    result = {"type": schema.get("type", "object")}
    
    if result["type"] == "object" and "properties" in schema:
        result["properties"] = {}
        for prop_name, prop_def in schema.get("properties", {}).items():
            result["properties"][prop_name] = convert_to_swagger_schema(prop_def)
        
        if "required" in schema:
            result["required"] = schema["required"]
    
    elif result["type"] == "array" and "items" in schema:
        result["items"] = convert_to_swagger_schema(schema["items"])
    
    if "description" in schema:
        result["description"] = schema["description"]
    
    if "enum" in schema:
        result["enum"] = schema["enum"]
    
    if "default" in schema:
        result["default"] = schema["default"]
    
    return result


def generate_openapi_30(forgehook: Dict[str, Any], plugin_name: str) -> Dict[str, Any]:
    """Generate OpenAPI 3.0 spec from forgehook.json."""
    info = forgehook.get("info", {})
    endpoints = forgehook.get("endpoints", [])
    
    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": f"LeForge {info.get('name', plugin_name)}",
            "description": info.get("description", "LeForge plugin"),
            "version": info.get("version", "1.0.0"),
            "contact": {
                "name": "LeForge Support",
                "url": "https://LeForge.io"
            }
        },
        "servers": [
            {
                "url": "https://{{HOST}}/api/v1",
                "description": "LeForge API Server"
            }
        ],
        "security": [{"ApiKeyAuth": []}],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "LeForge API Key"
                }
            },
            "schemas": {}
        },
        "paths": {},
        "tags": []
    }
    
    # Collect unique tags
    tags_set = set()
    
    # Group endpoints by path
    paths = {}
    for endpoint in endpoints:
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET").lower()
        category = endpoint.get("category", "General")
        tags_set.add(category)
        
        if path not in paths:
            paths[path] = {}
        
        operation = {
            "operationId": sanitize_operation_id(path, method),
            "summary": endpoint.get("name", ""),
            "description": endpoint.get("description", ""),
            "tags": [category],
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                },
                "400": {"description": "Bad request"},
                "401": {"description": "Unauthorized"},
                "500": {"description": "Internal server error"}
            }
        }
        
        # Add request body for POST/PUT/PATCH
        if method in ["post", "put", "patch"]:
            request_body = endpoint.get("requestBody", {})
            if request_body:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": request_body
                        }
                    }
                }
        
        # Add path parameters
        path_params = re.findall(r'\{([^}]+)\}', path)
        for param in path_params:
            operation["parameters"].append({
                "in": "path",
                "name": param,
                "schema": {"type": "string"},
                "required": True,
                "description": f"Path parameter: {param}"
            })
        
        # Add query parameters  
        query_params = endpoint.get("queryParams", [])
        for param in query_params:
            operation["parameters"].append({
                "in": "query",
                "name": param.get("name", ""),
                "schema": {"type": param.get("type", "string")},
                "required": param.get("required", False),
                "description": param.get("description", "")
            })
        
        paths[path][method] = operation
    
    openapi["paths"] = paths
    openapi["tags"] = [{"name": tag, "description": f"{tag} operations"} for tag in sorted(tags_set)]
    
    return openapi


# =============================================================================
# Power Automate Generator
# =============================================================================

def generate_power_automate(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate Power Automate custom connector package."""
    platform_dir = output_dir / "power-automate" / format_connector_name(plugin_name)
    platform_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI 2.0 spec (Power Automate prefers Swagger)
    swagger = generate_openapi_20(forgehook, plugin_name)
    
    # Add Power Automate specific extensions
    swagger["x-ms-connector-metadata"] = [
        {
            "propertyName": "Website",
            "propertyValue": "https://LeForge.io"
        },
        {
            "propertyName": "Privacy policy",
            "propertyValue": "https://LeForge.io/privacy"
        },
        {
            "propertyName": "Categories",
            "propertyValue": "AI;Productivity"
        }
    ]
    
    # Save Swagger spec
    swagger_path = platform_dir / "apiDefinition.swagger.json"
    with open(swagger_path, "w", encoding="utf-8") as f:
        json.dump(swagger, f, indent=2)
    
    # Generate apiProperties.json
    api_properties = {
        "properties": {
            "connectionParameters": {
                "api_key": {
                    "type": "securestring",
                    "uiDefinition": {
                        "displayName": "API Key",
                        "description": "Your LeForge API Key",
                        "tooltip": "Enter your LeForge API Key",
                        "constraints": {
                            "required": "true",
                            "clearText": False
                        }
                    }
                }
            },
            "iconBrandColor": PLUGIN_COLORS.get(plugin_name, "#6366f1"),
            "capabilities": [],
            "policyTemplateInstances": []
        }
    }
    
    api_props_path = platform_dir / "apiProperties.json"
    with open(api_props_path, "w", encoding="utf-8") as f:
        json.dump(api_properties, f, indent=2)
    
    # Generate README
    readme = generate_power_automate_readme(forgehook, plugin_name)
    readme_path = platform_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ Power Automate connector: {platform_dir}")


def generate_power_automate_readme(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate README for Power Automate connector."""
    info = forgehook.get("info", {})
    return f"""# LeForge {info.get('name', plugin_name)} - Power Automate Connector

## Overview
{info.get('description', 'LeForge plugin connector for Microsoft Power Automate.')}

## Installation

### Method 1: Import from file
1. Go to **Power Automate** > **Data** > **Custom connectors**
2. Click **+ New custom connector** > **Import an OpenAPI file**
3. Select `apiDefinition.swagger.json` from this folder
4. Configure the connector settings
5. Click **Create connector**

### Method 2: Import from URL
1. Host this connector on a web server
2. Use the URL to import directly

## Configuration

After importing the connector:

1. Click **Test** tab
2. Create a new connection
3. Enter your LeForge API Key
4. Test a simple operation

## Available Actions

| Action | Description |
|--------|-------------|
{generate_actions_table(forgehook)}

## Authentication

This connector uses API Key authentication:
- Header name: `X-API-Key`
- Get your API key from LeForge dashboard

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
"""


# =============================================================================
# Nintex Workflow Cloud Generator
# =============================================================================

def generate_nintex_cloud(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate Nintex Workflow Cloud Xtension package."""
    platform_dir = output_dir / "nintex-cloud" / format_connector_name(plugin_name)
    platform_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI 2.0 spec with Nintex extensions
    swagger = generate_openapi_20(forgehook, plugin_name)
    
    # Add Nintex-specific extensions
    for path, methods in swagger.get("paths", {}).items():
        for method, operation in methods.items():
            # Add Nintex summary extension for action names
            operation["x-ntx-summary"] = operation.get("summary", "")
            operation["x-ntx-visibility"] = "important"
    
    # Save Swagger spec
    swagger_path = platform_dir / f"{plugin_name}.swagger.json"
    with open(swagger_path, "w", encoding="utf-8") as f:
        json.dump(swagger, f, indent=2)
    
    # Generate README
    readme = generate_nintex_cloud_readme(forgehook, plugin_name)
    readme_path = platform_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ Nintex Cloud Xtension: {platform_dir}")


def generate_nintex_cloud_readme(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate README for Nintex Cloud Xtension."""
    info = forgehook.get("info", {})
    return f"""# LeForge {info.get('name', plugin_name)} - Nintex Workflow Cloud Xtension

## Overview
{info.get('description', 'LeForge plugin Xtension for Nintex Workflow Cloud.')}

## Installation

1. Go to **Nintex Workflow Cloud** > **Settings** > **Xtensions**
2. Click **Add Xtension**
3. Choose **Add custom connector**
4. Upload `{plugin_name}.swagger.json`
5. Configure authentication (API Key)
6. Click **Publish**

## Configuration

### API Key Setup
1. In the Xtension settings, select **API Key** authentication
2. Set header name: `X-API-Key`
3. Enter your LeForge API key

### Base URL
Update the host in the Swagger file to your LeForge instance URL.

## Available Actions

{generate_actions_table(forgehook)}

## Usage in Workflows

After publishing the Xtension:
1. Open workflow designer
2. Find actions under **LeForge** category
3. Drag and drop actions into your workflow
4. Configure action parameters

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
"""


# =============================================================================
# Nintex K2 Generator
# =============================================================================

def generate_nintex_k2(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate Nintex K2 Service Broker and SmartObject templates."""
    platform_dir = output_dir / "nintex-k2" / format_connector_name(plugin_name)
    swagger_dir = platform_dir / "swagger"
    smartobj_dir = platform_dir / "smartobjects"
    
    swagger_dir.mkdir(parents=True, exist_ok=True)
    smartobj_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate Swagger spec for REST Service Broker
    swagger = generate_openapi_20(forgehook, plugin_name)
    swagger_path = swagger_dir / f"{plugin_name}.json"
    with open(swagger_path, "w", encoding="utf-8") as f:
        json.dump(swagger, f, indent=2)
    
    # Generate SmartObject template XML for each major operation
    info = forgehook.get("info", {})
    endpoints = forgehook.get("endpoints", [])
    
    for endpoint in endpoints[:5]:  # Generate for top 5 endpoints
        smartobj_xml = generate_smartobject_xml(endpoint, plugin_name, info)
        operation_id = sanitize_operation_id(endpoint.get("path", ""), endpoint.get("method", "GET"))
        xml_path = smartobj_dir / f"{operation_id}.xml"
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(smartobj_xml)
    
    # Generate README
    readme = generate_nintex_k2_readme(forgehook, plugin_name)
    readme_path = platform_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ Nintex K2 Service Broker: {platform_dir}")


def generate_smartobject_xml(endpoint: Dict[str, Any], plugin_name: str, info: Dict[str, Any]) -> str:
    """Generate SmartObject template XML for K2."""
    operation_id = sanitize_operation_id(endpoint.get("path", ""), endpoint.get("method", "GET"))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<SmartObjectDefinition xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Name>{operation_id}</Name>
  <DisplayName>LeForge {info.get('name', plugin_name)} - {endpoint.get('name', operation_id)}</DisplayName>
  <Description>{endpoint.get('description', '')}</Description>
  <SystemName>LeForge.{format_connector_name(plugin_name)}.{operation_id}</SystemName>
  <ServiceInstance>LeForge_{format_connector_name(plugin_name)}</ServiceInstance>
  <Methods>
    <Method>
      <Name>Execute</Name>
      <Type>Execute</Type>
      <Description>Execute {endpoint.get('name', 'operation')}</Description>
      <Parameters>
        <!-- Define input parameters based on endpoint -->
      </Parameters>
      <ReturnProperties>
        <!-- Define output properties based on response -->
      </ReturnProperties>
    </Method>
  </Methods>
</SmartObjectDefinition>
"""


def generate_nintex_k2_readme(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate README for Nintex K2 integration."""
    info = forgehook.get("info", {})
    return f"""# LeForge {info.get('name', plugin_name)} - Nintex K2 Integration

## Overview
{info.get('description', 'LeForge plugin integration for Nintex K2.')}

## Installation

### 1. Register REST Service Broker

1. Open **K2 Management Console**
2. Navigate to **Integration** > **Service Types**
3. Add new **REST Service Broker**
4. Upload `swagger/{plugin_name}.json`
5. Configure base URL and authentication

### 2. Create Service Instance

1. Go to **Service Instances**
2. Create new instance from the registered service type
3. Configure connection:
   - Base URL: Your LeForge server URL
   - Authentication: API Key
   - Header: `X-API-Key`

### 3. Generate SmartObjects

1. Navigate to **SmartObjects**
2. Click **Generate SmartObjects** from service instance
3. Select operations to expose
4. Publish SmartObjects

## SmartObject Templates

Pre-configured SmartObject templates are available in the `smartobjects/` folder.
Import these for common operations.

## Available Operations

{generate_actions_table(forgehook)}

## Using in K2 Forms & Workflows

### In Forms
1. Add SmartObject data source
2. Bind to form controls
3. Execute methods on form events

### In Workflows
1. Add SmartObject event
2. Configure method and parameters
3. Map inputs/outputs

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
"""


# =============================================================================
# n8n Generator
# =============================================================================

def generate_n8n(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate n8n custom node TypeScript package."""
    package_name = f"n8n-nodes-LeForge-{plugin_name.replace('-', '')}"
    platform_dir = output_dir / "n8n" / package_name
    nodes_dir = platform_dir / "nodes" / f"LeForge{format_class_name(plugin_name)}"
    credentials_dir = platform_dir / "credentials"
    
    nodes_dir.mkdir(parents=True, exist_ok=True)
    credentials_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate package.json
    package_json = generate_n8n_package_json(forgehook, plugin_name, package_name)
    with open(platform_dir / "package.json", "w", encoding="utf-8") as f:
        json.dump(package_json, f, indent=2)
    
    # Generate tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2019",
            "module": "commonjs",
            "lib": ["ES2019"],
            "declaration": True,
            "strict": True,
            "noImplicitAny": True,
            "strictNullChecks": True,
            "noImplicitThis": True,
            "alwaysStrict": True,
            "noUnusedLocals": False,
            "noUnusedParameters": False,
            "noImplicitReturns": True,
            "noFallthroughCasesInSwitch": False,
            "inlineSourceMap": True,
            "inlineSources": True,
            "experimentalDecorators": True,
            "emitDecoratorMetadata": True,
            "outDir": "./dist",
            "rootDir": "./"
        },
        "include": ["nodes/**/*", "credentials/**/*"],
        "exclude": ["node_modules"]
    }
    with open(platform_dir / "tsconfig.json", "w", encoding="utf-8") as f:
        json.dump(tsconfig, f, indent=2)
    
    # Generate credentials file
    credentials_ts = generate_n8n_credentials(plugin_name)
    with open(credentials_dir / "LeForgeApi.credentials.ts", "w", encoding="utf-8") as f:
        f.write(credentials_ts)
    
    # Generate main node file
    node_ts = generate_n8n_node(forgehook, plugin_name)
    class_name = f"LeForge{format_class_name(plugin_name)}"
    with open(nodes_dir / f"{class_name}.node.ts", "w", encoding="utf-8") as f:
        f.write(node_ts)
    
    # Generate node description JSON
    node_json = generate_n8n_node_json(forgehook, plugin_name)
    with open(nodes_dir / f"{class_name}.node.json", "w", encoding="utf-8") as f:
        json.dump(node_json, f, indent=2)
    
    # Generate README
    readme = generate_n8n_readme(forgehook, plugin_name, package_name)
    with open(platform_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ n8n node package: {platform_dir}")


def generate_n8n_package_json(forgehook: Dict[str, Any], plugin_name: str, package_name: str) -> Dict[str, Any]:
    """Generate package.json for n8n node."""
    info = forgehook.get("info", {})
    class_name = f"LeForge{format_class_name(plugin_name)}"
    
    return {
        "name": package_name,
        "version": info.get("version", "1.0.0"),
        "description": f"n8n node for LeForge {info.get('name', plugin_name)}",
        "keywords": ["n8n", "n8n-community-node-package", "LeForge", plugin_name],
        "license": "MIT",
        "homepage": "https://LeForge.io",
        "author": {
            "name": "LeForge",
            "email": "support@LeForge.io"
        },
        "repository": {
            "type": "git",
            "url": "https://github.com/LeForgeio/registry.git"
        },
        "main": "dist/index.js",
        "scripts": {
            "build": "tsc && gulp build:icons",
            "dev": "tsc --watch",
            "format": "prettier nodes credentials --write",
            "lint": "eslint nodes credentials --ext .ts --fix",
            "prepublishOnly": "npm run build"
        },
        "files": [
            "dist"
        ],
        "n8n": {
            "n8nNodesApiVersion": 1,
            "credentials": [
                "dist/credentials/LeForgeApi.credentials.js"
            ],
            "nodes": [
                f"dist/nodes/{class_name}/{class_name}.node.js"
            ]
        },
        "devDependencies": {
            "@types/node": "^18.0.0",
            "n8n-workflow": "^1.0.0",
            "typescript": "^5.0.0",
            "gulp": "^4.0.0"
        }
    }


def generate_n8n_credentials(plugin_name: str) -> str:
    """Generate n8n credentials TypeScript file."""
    return '''import {
    IAuthenticateGeneric,
    ICredentialType,
    INodeProperties,
} from 'n8n-workflow';

export class LeForgeApi implements ICredentialType {
    name = 'LeForgeApi';
    displayName = 'LeForge API';
    documentationUrl = 'https://LeForge.io/docs/api';
    
    properties: INodeProperties[] = [
        {
            displayName: 'API Key',
            name: 'apiKey',
            type: 'string',
            typeOptions: {
                password: true,
            },
            default: '',
            required: true,
            description: 'Your LeForge API Key',
        },
        {
            displayName: 'Base URL',
            name: 'baseUrl',
            type: 'string',
            default: 'https://api.LeForge.io',
            required: true,
            description: 'The base URL of your LeForge instance',
        },
    ];
    
    authenticate: IAuthenticateGeneric = {
        type: 'generic',
        properties: {
            headers: {
                'X-API-Key': '={{$credentials.apiKey}}',
            },
        },
    };
}
'''


def generate_n8n_node(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate n8n node TypeScript file."""
    info = forgehook.get("info", {})
    endpoints = forgehook.get("endpoints", [])
    class_name = f"LeForge{format_class_name(plugin_name)}"
    
    # Generate operations
    operations = []
    for endpoint in endpoints[:15]:  # Limit to 15 operations
        op_name = endpoint.get("name", "").replace(" ", "").lower()
        op_name = re.sub(r'[^a-z0-9]', '', op_name) or "operation"
        operations.append({
            "name": endpoint.get("name", op_name),
            "value": op_name,
            "description": endpoint.get("description", ""),
            "action": endpoint.get("name", op_name)
        })
    
    operations_code = json.dumps(operations, indent=8)
    
    return f'''import {{
    IExecuteFunctions,
    INodeExecutionData,
    INodeType,
    INodeTypeDescription,
    NodeOperationError,
}} from 'n8n-workflow';

export class {class_name} implements INodeType {{
    description: INodeTypeDescription = {{
        displayName: 'LeForge {info.get("name", plugin_name)}',
        name: 'LeForge{format_class_name(plugin_name)}',
        icon: 'file:LeForge.svg',
        group: ['transform'],
        version: 1,
        subtitle: '={{{{$parameter["operation"]}}}}',
        description: '{info.get("description", "LeForge plugin").replace("'", "\\'")}',
        defaults: {{
            name: 'LeForge {info.get("name", plugin_name)}',
        }},
        inputs: ['main'],
        outputs: ['main'],
        credentials: [
            {{
                name: 'LeForgeApi',
                required: true,
            }},
        ],
        properties: [
            {{
                displayName: 'Operation',
                name: 'operation',
                type: 'options',
                noDataExpression: true,
                options: {operations_code},
                default: '{operations[0]["value"] if operations else "operation"}',
            }},
            // Add more properties per operation here
        ],
    }};

    async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {{
        const items = this.getInputData();
        const returnData: INodeExecutionData[] = [];
        
        const credentials = await this.getCredentials('LeForgeApi');
        const baseUrl = credentials.baseUrl as string;
        const operation = this.getNodeParameter('operation', 0) as string;
        
        for (let i = 0; i < items.length; i++) {{
            try {{
                // Implement operation logic here
                const response = await this.helpers.httpRequest({{
                    method: 'POST',
                    url: `${{baseUrl}}/api/v1/${{operation}}`,
                    json: true,
                    body: {{}},
                }});
                
                returnData.push({{
                    json: response,
                }});
            }} catch (error) {{
                if (this.continueOnFail()) {{
                    returnData.push({{
                        json: {{
                            error: error.message,
                        }},
                    }});
                    continue;
                }}
                throw new NodeOperationError(this.getNode(), error as Error, {{ itemIndex: i }});
            }}
        }}
        
        return [returnData];
    }}
}}
'''


def generate_n8n_node_json(forgehook: Dict[str, Any], plugin_name: str) -> Dict[str, Any]:
    """Generate n8n node description JSON."""
    info = forgehook.get("info", {})
    return {
        "node": f"n8n-nodes-LeForge-{plugin_name}",
        "nodeVersion": "1.0",
        "codexVersion": "1.0",
        "categories": ["Productivity", "AI"],
        "resources": {
            "credentialDocumentation": [
                {
                    "url": "https://LeForge.io/docs/api"
                }
            ],
            "primaryDocumentation": [
                {
                    "url": "https://LeForge.io/docs"
                }
            ]
        }
    }


def generate_n8n_readme(forgehook: Dict[str, Any], plugin_name: str, package_name: str) -> str:
    """Generate README for n8n node package."""
    info = forgehook.get("info", {})
    return f"""# {package_name}

n8n community node for LeForge {info.get('name', plugin_name)}.

{info.get('description', '')}

## Installation

### Community Nodes (Recommended)

1. Go to **Settings** > **Community Nodes**
2. Click **Install**
3. Enter `{package_name}`
4. Agree to the risks
5. Click **Install**

### Manual Installation

```bash
npm install {package_name}
```

Then restart n8n.

## Configuration

1. Add LeForge credentials:
   - Go to **Credentials** > **Add Credential**
   - Search for "LeForge"
   - Enter your API Key and Base URL

2. Use the node in your workflows

## Operations

{generate_actions_table(forgehook)}

## Compatibility

- n8n version: 0.200.0+
- Node.js version: 18+

## Resources

- [LeForge Documentation](https://LeForge.io/docs)
- [n8n Community Nodes Documentation](https://docs.n8n.io/integrations/community-nodes/)

## License

MIT
"""


# =============================================================================
# OutSystems Generator
# =============================================================================

def generate_outsystems(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate OutSystems integration files."""
    platform_dir = output_dir / "outsystems" / format_connector_name(plugin_name)
    platform_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI 3.0 spec (OutSystems prefers this)
    openapi = generate_openapi_30(forgehook, plugin_name)
    openapi_path = platform_dir / f"{plugin_name}-openapi.json"
    with open(openapi_path, "w", encoding="utf-8") as f:
        json.dump(openapi, f, indent=2)
    
    # Generate README with integration instructions
    readme = generate_outsystems_readme(forgehook, plugin_name)
    with open(platform_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ OutSystems integration: {platform_dir}")


def generate_outsystems_readme(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate README for OutSystems integration."""
    info = forgehook.get("info", {})
    return f"""# LeForge {info.get('name', plugin_name)} - OutSystems Integration

## Overview
{info.get('description', 'LeForge plugin integration for OutSystems.')}

## Integration Methods

### Method 1: Consume REST API (Recommended)

1. Open **Service Studio**
2. Go to **Logic** > **Integrations** > **REST**
3. Right-click and select **Consume REST API**
4. Choose **Add Single Method** or **Add Multiple Methods**
5. Paste endpoints from the OpenAPI spec

### Method 2: Import OpenAPI Spec

1. Open **Integration Studio**
2. Create new extension
3. Import `{plugin_name}-openapi.json`
4. Publish extension

## Configuration

### Base URL
Set the base URL to your LeForge instance in the REST API configuration.

### Authentication
1. Create a Site Property for the API Key
2. Add `X-API-Key` header to all REST calls
3. Use the Site Property value

## Server Actions

For each operation, create a Server Action wrapper:

```
ServerAction: LeForge_{info.get('name', plugin_name).replace(' ', '')}_Operation
    Input: 
        - RequestData (Structure)
    Output:
        - ResponseData (Structure)
        - Success (Boolean)
        - ErrorMessage (Text)
    
    Logic:
        1. Call REST API
        2. Handle response/errors
        3. Return results
```

## Available Operations

{generate_actions_table(forgehook)}

## Best Practices

1. **Caching**: Cache responses where appropriate
2. **Error Handling**: Always handle API errors gracefully
3. **Timeouts**: Set appropriate timeout values
4. **Logging**: Log API calls for debugging

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
"""


# =============================================================================
# Mendix Generator
# =============================================================================

def generate_mendix(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate Mendix integration files."""
    platform_dir = output_dir / "mendix" / format_connector_name(plugin_name)
    platform_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI 3.0 spec
    openapi = generate_openapi_30(forgehook, plugin_name)
    openapi_path = platform_dir / f"{plugin_name}-openapi.json"
    with open(openapi_path, "w", encoding="utf-8") as f:
        json.dump(openapi, f, indent=2)
    
    # Generate Java action stubs
    java_dir = platform_dir / "javasource" / "LeForge" / "actions"
    java_dir.mkdir(parents=True, exist_ok=True)
    
    endpoints = forgehook.get("endpoints", [])
    for endpoint in endpoints[:10]:  # Generate for top 10 endpoints
        java_code = generate_mendix_java_action(endpoint, plugin_name, forgehook.get("info", {}))
        operation_id = sanitize_operation_id(endpoint.get("path", ""), endpoint.get("method", "GET"))
        java_path = java_dir / f"{operation_id}.java"
        with open(java_path, "w", encoding="utf-8") as f:
            f.write(java_code)
    
    # Generate README
    readme = generate_mendix_readme(forgehook, plugin_name)
    with open(platform_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ Mendix integration: {platform_dir}")


def generate_mendix_java_action(endpoint: Dict[str, Any], plugin_name: str, info: Dict[str, Any]) -> str:
    """Generate Mendix Java action stub."""
    operation_id = sanitize_operation_id(endpoint.get("path", ""), endpoint.get("method", "GET"))
    return f'''package LeForge.actions;

import com.mendix.systemwideinterfaces.core.IContext;
import com.mendix.webui.CustomJavaAction;
import com.mendix.systemwideinterfaces.core.IMendixObject;

/**
 * LeForge {info.get('name', plugin_name)} - {endpoint.get('name', operation_id)}
 * 
 * {endpoint.get('description', '')}
 * 
 * @author LeForge Generator
 */
public class {operation_id} extends CustomJavaAction<String> {{
    
    private String baseUrl;
    private String apiKey;
    private String requestBody;
    
    public {operation_id}(IContext context, String baseUrl, String apiKey, String requestBody) {{
        super(context);
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.requestBody = requestBody;
    }}
    
    @Override
    public String executeAction() throws Exception {{
        // TODO: Implement API call
        // Use Mendix's REST call capabilities or Apache HttpClient
        
        String endpoint = baseUrl + "{endpoint.get('path', '/')}";
        
        // Make HTTP request
        // Parse response
        // Return result
        
        return ""; // Replace with actual response
    }}
    
    @Override
    public String toString() {{
        return "LeForge {operation_id}";
    }}
}}
'''


def generate_mendix_readme(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate README for Mendix integration."""
    info = forgehook.get("info", {})
    return f"""# LeForge {info.get('name', plugin_name)} - Mendix Integration

## Overview
{info.get('description', 'LeForge plugin integration for Mendix.')}

## Integration Methods

### Method 1: Consume REST Service (Recommended)

1. Open **Mendix Studio Pro**
2. Go to project directory
3. Right-click **App** > **Add other** > **Consumed REST service**
4. Import `{plugin_name}-openapi.json`
5. Configure base URL and authentication

### Method 2: Java Actions

Use the provided Java action stubs in `javasource/LeForge/actions/`:

1. Copy Java files to your project's javasource folder
2. Implement the API call logic
3. Expose as microflow activities

## Configuration

### Constants
Create these constants in your Mendix app:

- `LeForge.BaseUrl` - Your LeForge instance URL
- `LeForge.ApiKey` - Your API key

### Request Handling
Use Mendix's **Call REST** activity with:
- Method: POST/GET as appropriate
- URL: `$LeForge.BaseUrl + '/api/v1/endpoint'`
- Headers: `X-API-Key: $LeForge.ApiKey`

## Available Operations

{generate_actions_table(forgehook)}

## Microflow Example

```
Microflow: ACT_LeForge_Chat
    Input: Message (String)
    
    1. Create JSON structure for request
    2. Call REST (POST /api/v1/chat)
    3. Parse JSON response
    4. Return response text
```

## Marketplace Publishing

To publish as a Marketplace module:

1. Create module in Studio Pro
2. Add all integrations
3. Export as .mpk file
4. Upload to Marketplace

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
"""


# =============================================================================
# Salesforce Generator
# =============================================================================

def generate_salesforce(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate Salesforce External Services and Apex integration files."""
    platform_dir = output_dir / "salesforce" / format_connector_name(plugin_name)
    external_services_dir = platform_dir / "external-services"
    apex_dir = platform_dir / "apex" / "classes"
    
    external_services_dir.mkdir(parents=True, exist_ok=True)
    apex_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI 3.0 spec for External Services
    openapi = generate_salesforce_openapi(forgehook, plugin_name)
    openapi_path = external_services_dir / f"LeForge_{format_connector_name(plugin_name)}.yaml"
    with open(openapi_path, "w", encoding="utf-8") as f:
        import yaml
        yaml.dump(openapi, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    # Generate Apex Invocable class
    apex_code = generate_salesforce_apex(forgehook, plugin_name)
    class_name = f"LeForge{format_connector_name(plugin_name)}Service"
    apex_path = apex_dir / f"{class_name}.cls"
    with open(apex_path, "w", encoding="utf-8") as f:
        f.write(apex_code)
    
    # Generate Apex metadata
    apex_meta = '''<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>59.0</apiVersion>
    <status>Active</status>
</ApexClass>
'''
    with open(apex_dir / f"{class_name}.cls-meta.xml", "w", encoding="utf-8") as f:
        f.write(apex_meta)
    
    # Generate README
    readme = generate_salesforce_readme(forgehook, plugin_name)
    with open(platform_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ Salesforce integration: {platform_dir}")


def generate_salesforce_openapi(forgehook: Dict[str, Any], plugin_name: str) -> Dict[str, Any]:
    """Generate Salesforce-compatible OpenAPI 3.0 spec."""
    info = forgehook.get("info", {})
    endpoints = forgehook.get("endpoints", [])
    
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": f"LeForge {info.get('name', plugin_name)}",
            "description": info.get("description", "LeForge plugin"),
            "version": info.get("version", "1.0.0")
        },
        "servers": [
            {"url": "https://{instance}/api/v1", "variables": {"instance": {"default": "api.LeForge.io"}}}
        ],
        "paths": {},
        "components": {
            "securitySchemes": {
                "ApiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
            }
        },
        "security": [{"ApiKey": []}]
    }
    
    for endpoint in endpoints[:10]:
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET").lower()
        
        if path not in openapi["paths"]:
            openapi["paths"][path] = {}
        
        operation = {
            "operationId": sanitize_operation_id(path, method),
            "summary": endpoint.get("name", ""),
            "description": endpoint.get("description", ""),
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {"application/json": {"schema": {"type": "object"}}}
                }
            }
        }
        
        if method in ["post", "put", "patch"]:
            operation["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": {"type": "object"}}}
            }
        
        openapi["paths"][path][method] = operation
    
    return openapi


def generate_salesforce_apex(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate Salesforce Apex Invocable class."""
    info = forgehook.get("info", {})
    class_name = f"LeForge{format_connector_name(plugin_name)}Service"
    endpoints = forgehook.get("endpoints", [])
    
    # Get first endpoint for example
    first_endpoint = endpoints[0] if endpoints else {"name": "Execute", "path": "/execute", "method": "POST"}
    
    return f'''/**
 * LeForge {info.get('name', plugin_name)} - Salesforce Apex Invocable Actions
 * {info.get('description', '')}
 * 
 * @author LeForge Generator
 * @version {info.get('version', '1.0.0')}
 */
public class {class_name} {{
    
    private static final String NAMED_CREDENTIAL = 'callout:LeForge_API';
    
    @InvocableMethod(label='{first_endpoint.get("name", "Execute")}' 
                     description='{first_endpoint.get("description", "Execute LeForge operation")[:200]}' 
                     category='LeForge')
    public static List<Response> execute(List<Request> requests) {{
        List<Response> responses = new List<Response>();
        
        for (Request req : requests) {{
            Response res = new Response();
            try {{
                HttpRequest httpReq = new HttpRequest();
                httpReq.setEndpoint(NAMED_CREDENTIAL + '{first_endpoint.get("path", "/")}');
                httpReq.setMethod('{first_endpoint.get("method", "POST")}');
                httpReq.setHeader('Content-Type', 'application/json');
                httpReq.setTimeout(120000);
                
                if (String.isNotBlank(req.requestBody)) {{
                    httpReq.setBody(req.requestBody);
                }}
                
                Http http = new Http();
                HttpResponse httpRes = http.send(httpReq);
                
                if (httpRes.getStatusCode() == 200) {{
                    res.responseBody = httpRes.getBody();
                    res.success = true;
                }} else {{
                    res.success = false;
                    res.errorMessage = 'HTTP ' + httpRes.getStatusCode() + ': ' + httpRes.getBody();
                }}
            }} catch (Exception e) {{
                res.success = false;
                res.errorMessage = e.getMessage();
            }}
            responses.add(res);
        }}
        return responses;
    }}
    
    public class Request {{
        @InvocableVariable(label='Request Body (JSON)' required=false)
        public String requestBody;
    }}
    
    public class Response {{
        @InvocableVariable(label='Response Body')
        public String responseBody;
        
        @InvocableVariable(label='Success')
        public Boolean success;
        
        @InvocableVariable(label='Error Message')
        public String errorMessage;
    }}
}}
'''


def generate_salesforce_readme(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate README for Salesforce integration."""
    info = forgehook.get("info", {})
    return f"""# LeForge {info.get('name', plugin_name)} - Salesforce Integration

## Overview
{info.get('description', 'LeForge plugin integration for Salesforce.')}

## Installation

### External Services
1. Go to **Setup** > **External Services**
2. Click **Add an External Service**
3. Upload `external-services/LeForge_{format_connector_name(plugin_name)}.yaml`
4. Configure Named Credential

### Apex Package
Deploy using Salesforce CLI:
```bash
sfdx force:source:deploy -p apex/
```

## Configuration

Create Named Credential:
1. **Setup** > **Named Credentials**
2. Create new: LeForge_API
3. URL: https://your-instance.LeForge.io/api/v1
4. Authentication: Custom Header (X-API-Key)

## Available Operations

{generate_actions_table(forgehook)}

## Support

Visit [LeForge Support](https://LeForge.io/support)
"""


# =============================================================================
# ServiceNow Generator
# =============================================================================

def generate_servicenow(forgehook: Dict[str, Any], plugin_name: str, output_dir: Path):
    """Generate ServiceNow IntegrationHub Spoke files."""
    platform_dir = output_dir / "servicenow" / format_connector_name(plugin_name)
    spoke_dir = platform_dir / "spoke"
    actions_dir = spoke_dir / "actions"
    
    actions_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate spoke definition
    spoke_xml = generate_servicenow_spoke_xml(forgehook, plugin_name)
    with open(spoke_dir / "sys_hub_spoke.xml", "w", encoding="utf-8") as f:
        f.write(spoke_xml)
    
    # Generate action definitions
    endpoints = forgehook.get("endpoints", [])
    for endpoint in endpoints[:5]:
        action_xml = generate_servicenow_action_xml(endpoint, plugin_name, forgehook.get("info", {}))
        operation_id = sanitize_operation_id(endpoint.get("path", ""), endpoint.get("method", "GET")).lower()
        with open(actions_dir / f"{operation_id}.xml", "w", encoding="utf-8") as f:
            f.write(action_xml)
    
    # Generate README
    readme = generate_servicenow_readme(forgehook, plugin_name)
    with open(platform_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"  ✓ ServiceNow integration: {platform_dir}")


def generate_servicenow_spoke_xml(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate ServiceNow spoke definition XML."""
    info = forgehook.get("info", {})
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<unload>
    <sys_hub_spoke action="INSERT_OR_UPDATE">
        <active>true</active>
        <description>{info.get('description', 'LeForge plugin')}</description>
        <name>LeForge {info.get('name', plugin_name)}</name>
        <sys_id>LeForge_{plugin_name.replace("-", "_")}_spoke</sys_id>
        <vendor>LeForge</vendor>
        <version>{info.get('version', '1.0.0')}</version>
    </sys_hub_spoke>
</unload>
'''


def generate_servicenow_action_xml(endpoint: Dict[str, Any], plugin_name: str, info: Dict[str, Any]) -> str:
    """Generate ServiceNow action definition XML."""
    operation_id = sanitize_operation_id(endpoint.get("path", ""), endpoint.get("method", "GET"))
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<unload>
    <sys_hub_action_type_definition action="INSERT_OR_UPDATE">
        <access>public</access>
        <active>true</active>
        <category>LeForge</category>
        <description>{endpoint.get('description', '')}</description>
        <internal_name>LeForge_{operation_id.lower()}</internal_name>
        <label>{endpoint.get('name', operation_id)}</label>
        <name>LeForge {endpoint.get('name', operation_id)}</name>
        <spoke>LeForge_{plugin_name.replace("-", "_")}_spoke</spoke>
        <sys_id>LeForge_action_{operation_id.lower()}</sys_id>
        <inputs>
            <input>
                <internal_name>request_body</internal_name>
                <label>Request Body (JSON)</label>
                <mandatory>false</mandatory>
                <type>string</type>
            </input>
        </inputs>
        <outputs>
            <output>
                <internal_name>response</internal_name>
                <label>Response</label>
                <type>string</type>
            </output>
            <output>
                <internal_name>success</internal_name>
                <label>Success</label>
                <type>boolean</type>
            </output>
        </outputs>
    </sys_hub_action_type_definition>
</unload>
'''


def generate_servicenow_readme(forgehook: Dict[str, Any], plugin_name: str) -> str:
    """Generate README for ServiceNow integration."""
    info = forgehook.get("info", {})
    return f"""# LeForge {info.get('name', plugin_name)} - ServiceNow Integration

## Overview
{info.get('description', 'LeForge plugin integration for ServiceNow.')}

## Installation

1. Import the Update Set from the `spoke/` folder
2. Configure Connection Alias with your LeForge API details
3. LeForge actions will appear in Flow Designer

## Available Operations

{generate_actions_table(forgehook)}

## Support

Visit [LeForge Support](https://LeForge.io/support)
"""


# =============================================================================
# Utility Functions
# =============================================================================

def format_connector_name(plugin_name: str) -> str:
    """Format plugin name for connector naming."""
    return plugin_name.replace("-", "_").title().replace("_", "")


def format_class_name(plugin_name: str) -> str:
    """Format plugin name for class naming."""
    parts = plugin_name.split("-")
    return "".join(p.capitalize() for p in parts)


def generate_actions_table(forgehook: Dict[str, Any]) -> str:
    """Generate markdown table of actions from forgehook."""
    endpoints = forgehook.get("endpoints", [])
    exports = forgehook.get("exports", [])
    lines = []
    
    # Handle API-style endpoints (llm-service, etc.)
    for endpoint in endpoints[:20]:  # Limit to 20 for readability
        # Generate name from path if not provided
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET")
        name = endpoint.get("name") or generate_action_name(path, method)
        desc = endpoint.get("description", "")[:60]
        if len(endpoint.get("description", "")) > 60:
            desc += "..."
        lines.append(f"| {name} | {desc} |")
    
    # Handle embedded exports (crypto-service, etc.)
    for export in exports[:20]:
        name = export.get("name", "Unknown")
        desc = export.get("description", "")[:60]
        if len(export.get("description", "")) > 60:
            desc += "..."
        lines.append(f"| {name} | {desc} |")
    
    return "\n".join(lines) if lines else "| No actions defined | |"


# =============================================================================
# Main Generator
# =============================================================================

def generate_integrations(
    plugins: Optional[List[str]] = None,
    platforms: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False
):
    """Generate integrations for specified plugins and platforms."""
    plugins = plugins or SUPPORTED_PLUGINS
    platforms = platforms or SUPPORTED_PLATFORMS
    output_dir = output_dir or INTEGRATIONS_DIR
    
    generators = {
        "power-automate": generate_power_automate,
        "nintex-cloud": generate_nintex_cloud,
        "nintex-k2": generate_nintex_k2,
        "n8n": generate_n8n,
        "outsystems": generate_outsystems,
        "mendix": generate_mendix,
        "salesforce": generate_salesforce,
        "servicenow": generate_servicenow,
    }
    
    print(f"\n{'='*60}")
    print("LeForge Integration Generator")
    print(f"{'='*60}\n")
    print(f"Plugins: {', '.join(plugins)}")
    print(f"Platforms: {', '.join(platforms)}")
    print(f"Output: {output_dir}\n")
    
    for plugin_name in plugins:
        print(f"\n📦 Processing {plugin_name}...")
        
        forgehook = load_forgehook(plugin_name)
        if not forgehook:
            print(f"  ⚠ Skipping - no forgehook.json found")
            continue
        
        for platform in platforms:
            if platform in generators:
                try:
                    generators[platform](forgehook, plugin_name, output_dir)
                except Exception as e:
                    print(f"  ✗ {platform}: {e}")
                    if verbose:
                        import traceback
                        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Generation complete!")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Generate LeForge platform integrations")
    parser.add_argument("--platform", choices=SUPPORTED_PLATFORMS, help="Generate for specific platform only")
    parser.add_argument("--plugin", choices=SUPPORTED_PLUGINS, help="Generate for specific plugin only")
    parser.add_argument("--output", type=Path, default=INTEGRATIONS_DIR, help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    plugins = [args.plugin] if args.plugin else None
    platforms = [args.platform] if args.platform else None
    
    generate_integrations(
        plugins=plugins,
        platforms=platforms,
        output_dir=args.output,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
