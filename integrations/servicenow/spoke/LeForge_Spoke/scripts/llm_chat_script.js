/**
 * LeForge LLM Chat - Action Script
 * ServiceNow Flow Designer Action implementation
 */
(function execute(inputs, outputs) {
    
    var restMessage = new sn_ws.RESTMessageV2('LeForge_LLM', 'chat');
    
    // Get connection configuration
    var config = getConnectionConfig(inputs.connection_alias || 'LeForge_connection');
    restMessage.setStringParameterNoEscape('endpoint', config.endpoint);
    restMessage.setStringParameterNoEscape('api_key', config.api_key);
    
    // Set request parameters
    restMessage.setStringParameterNoEscape('message', inputs.message);
    restMessage.setStringParameterNoEscape('system_prompt', inputs.system_prompt || '');
    restMessage.setStringParameterNoEscape('max_tokens', inputs.max_tokens || 512);
    restMessage.setStringParameterNoEscape('temperature', inputs.temperature || 0.7);
    
    try {
        var response = restMessage.execute();
        var httpStatus = response.getStatusCode();
        var responseBody = response.getBody();
        
        if (httpStatus == 200) {
            var result = JSON.parse(responseBody);
            outputs.response = result.response || result.message?.content;
            outputs.tokens_used = result.tokens_used || result.usage?.total_tokens;
            outputs.success = true;
        } else {
            outputs.success = false;
            outputs.error_message = 'HTTP ' + httpStatus + ': ' + responseBody;
        }
    } catch (ex) {
        outputs.success = false;
        outputs.error_message = ex.getMessage();
    }
    
})(inputs, outputs);

/**
 * Get connection configuration from alias
 */
function getConnectionConfig(aliasName) {
    var config = {
        endpoint: 'https://api.LeForge.io/api/v1',
        api_key: ''
    };
    
    var gr = new GlideRecord('sys_alias');
    gr.addQuery('name', aliasName);
    gr.query();
    
    if (gr.next()) {
        var configStr = gr.getValue('configuration');
        if (configStr) {
            try {
                var aliasConfig = JSON.parse(configStr);
                config.endpoint = aliasConfig.endpoint || config.endpoint;
                config.api_key = aliasConfig.api_key || '';
            } catch (e) {
                // Use defaults
            }
        }
    }
    
    return config;
}
