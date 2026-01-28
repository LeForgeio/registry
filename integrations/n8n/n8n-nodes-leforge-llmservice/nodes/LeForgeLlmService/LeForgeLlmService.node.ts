import {
    IExecuteFunctions,
    INodeExecutionData,
    INodeType,
    INodeTypeDescription,
    NodeOperationError,
} from 'n8n-workflow';

export class LeForgeLlmService implements INodeType {
    description: INodeTypeDescription = {
        displayName: 'LeForge llm-service',
        name: 'LeForgeLlmService',
        icon: 'file:LeForge.svg',
        group: ['transform'],
        version: 1,
        subtitle: '={{$parameter["operation"]}}',
        description: 'LeForge plugin',
        defaults: {
            name: 'LeForge llm-service',
        },
        inputs: ['main'],
        outputs: ['main'],
        credentials: [
            {
                name: 'LeForgeApi',
                required: true,
            },
        ],
        properties: [
            {
                displayName: 'Operation',
                name: 'operation',
                type: 'options',
                noDataExpression: true,
                options: [
        {
                "name": "operation",
                "value": "operation",
                "description": "List available LLM providers",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Configure a provider with API credentials",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "List available models for a provider",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Check provider health status",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Chat with a specific provider",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Generate embeddings with a specific provider",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Universal chat endpoint with provider selection",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Chat completion (vLLM/default provider)",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Simple chat with just a message",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Text generation/completion",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Generate text embeddings",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Classify text into categories",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Extract named entities from text",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Summarize text content",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Vision-based OCR from images",
                "action": "operation"
        }
],
                default: 'operation',
            },
            // Add more properties per operation here
        ],
    };

    async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
        const items = this.getInputData();
        const returnData: INodeExecutionData[] = [];
        
        const credentials = await this.getCredentials('LeForgeApi');
        const baseUrl = credentials.baseUrl as string;
        const operation = this.getNodeParameter('operation', 0) as string;
        
        for (let i = 0; i < items.length; i++) {
            try {
                // Implement operation logic here
                const response = await this.helpers.httpRequest({
                    method: 'POST',
                    url: `${baseUrl}/api/v1/${operation}`,
                    json: true,
                    body: {},
                });
                
                returnData.push({
                    json: response,
                });
            } catch (error) {
                if (this.continueOnFail()) {
                    returnData.push({
                        json: {
                            error: error.message,
                        },
                    });
                    continue;
                }
                throw new NodeOperationError(this.getNode(), error as Error, { itemIndex: i });
            }
        }
        
        return [returnData];
    }
}
