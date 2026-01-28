import {
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
