import {
    IExecuteFunctions,
    INodeExecutionData,
    INodeType,
    INodeTypeDescription,
    NodeOperationError,
} from 'n8n-workflow';

export class LeForgeStreamingFileService implements INodeType {
    description: INodeTypeDescription = {
        displayName: 'LeForge streaming-file-service',
        name: 'LeForgeStreamingFileService',
        icon: 'file:LeForge.svg',
        group: ['transform'],
        version: 1,
        subtitle: '={{$parameter["operation"]}}',
        description: 'LeForge plugin',
        defaults: {
            name: 'LeForge streaming-file-service',
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
                "description": "Initialize a chunked upload session. Returns uploadId for subsequent chunk uploads.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Upload a single chunk. Supports resume - re-upload failed chunks.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Complete chunked upload - assembles chunks and verifies integrity.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Get upload progress - which chunks received, resume point.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Cancel and cleanup an incomplete upload.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Stream download with Range header support for resume.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Initialize chunked download - get download manifest.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Stream upload directly to cloud storage (S3/Azure/GCS) without storing locally.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Stream download from cloud storage to local or another destination.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Copy files between cloud providers (S3 to Azure, GCS to S3, etc.).",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Generate presigned URLs for direct browser uploads/downloads.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Split large PDF into smaller files by page ranges.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Merge multiple PDFs into one.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Compress files (zip, gzip, tar.gz) with streaming.",
                "action": "operation"
        },
        {
                "name": "operation",
                "value": "operation",
                "description": "Extract compressed archives with streaming.",
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
