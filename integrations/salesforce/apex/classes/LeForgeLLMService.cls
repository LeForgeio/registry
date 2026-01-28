/**
 * LeForge LLM Service - Salesforce Apex Invocable Actions
 * Provides AI-powered text generation, chat, classification, and more
 * for use in Salesforce Flow Builder.
 * 
 * @author LeForge Team
 * @version 2.0.0
 */
public class LeForgeLLMService {
    
    private static final String NAMED_CREDENTIAL = 'callout:LeForge_API';
    
    // ============================================
    // CHAT ACTION
    // ============================================
    
    @InvocableMethod(label='Chat with AI' 
                     description='Send a message to LeForge AI and get a response' 
                     category='LeForge')
    public static List<ChatResponse> chat(List<ChatRequest> requests) {
        List<ChatResponse> responses = new List<ChatResponse>();
        
        for (ChatRequest req : requests) {
            ChatResponse res = new ChatResponse();
            try {
                HttpRequest httpReq = new HttpRequest();
                httpReq.setEndpoint(NAMED_CREDENTIAL + '/chat');
                httpReq.setMethod('POST');
                httpReq.setHeader('Content-Type', 'application/json');
                httpReq.setTimeout(120000); // 2 minute timeout for AI responses
                
                Map<String, Object> body = new Map<String, Object>{
                    'message' => req.message
                };
                if (String.isNotBlank(req.systemPrompt)) {
                    body.put('system_prompt', req.systemPrompt);
                }
                if (req.maxTokens != null) {
                    body.put('max_tokens', req.maxTokens);
                }
                if (req.temperature != null) {
                    body.put('temperature', req.temperature);
                }
                httpReq.setBody(JSON.serialize(body));
                
                Http http = new Http();
                HttpResponse httpRes = http.send(httpReq);
                
                if (httpRes.getStatusCode() == 200) {
                    Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(httpRes.getBody());
                    res.response = (String) result.get('response');
                    res.tokensUsed = (Integer) result.get('tokens_used');
                    res.success = true;
                } else {
                    res.success = false;
                    res.errorMessage = 'HTTP ' + httpRes.getStatusCode() + ': ' + httpRes.getBody();
                }
            } catch (Exception e) {
                res.success = false;
                res.errorMessage = e.getMessage();
            }
            responses.add(res);
        }
        return responses;
    }
    
    public class ChatRequest {
        @InvocableVariable(label='Message' description='The message to send to the AI' required=true)
        public String message;
        
        @InvocableVariable(label='System Prompt' description='Instructions for how the AI should behave')
        public String systemPrompt;
        
        @InvocableVariable(label='Max Tokens' description='Maximum tokens in response (default: 512)')
        public Integer maxTokens;
        
        @InvocableVariable(label='Temperature' description='Creativity level 0-2 (default: 0.7)')
        public Decimal temperature;
    }
    
    public class ChatResponse {
        @InvocableVariable(label='AI Response' description='The response from the AI')
        public String response;
        
        @InvocableVariable(label='Tokens Used' description='Number of tokens consumed')
        public Integer tokensUsed;
        
        @InvocableVariable(label='Success' description='Whether the operation succeeded')
        public Boolean success;
        
        @InvocableVariable(label='Error Message' description='Error details if failed')
        public String errorMessage;
    }
}
