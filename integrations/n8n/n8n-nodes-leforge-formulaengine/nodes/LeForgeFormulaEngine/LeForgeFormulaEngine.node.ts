import {
    IExecuteFunctions,
    INodeExecutionData,
    INodeType,
    INodeTypeDescription,
    NodeOperationError,
} from 'n8n-workflow';

export class LeForgeFormulaEngine implements INodeType {
    description: INodeTypeDescription = {
        displayName: 'LeForge formula-engine',
        name: 'LeForgeFormulaEngine',
        icon: 'file:LeForge.svg',
        group: ['transform'],
        version: 1,
        subtitle: '={{$parameter["operation"]}}',
        description: 'LeForge plugin',
        defaults: {
            name: 'LeForge formula-engine',
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
                options: [],
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
