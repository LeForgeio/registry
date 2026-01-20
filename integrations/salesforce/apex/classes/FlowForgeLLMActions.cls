/**
 * FlowForge LLM Service - Additional Invocable Actions
 * Classify, Summarize, and Extract Entities
 * 
 * @author FlowForge Team
 * @version 2.0.0
 */
public class FlowForgeLLMActions {
    
    private static final String NAMED_CREDENTIAL = 'callout:FlowForge_API';
    
    // ============================================
    // CLASSIFY TEXT ACTION
    // ============================================
    
    @InvocableMethod(label='Classify Text' 
                     description='Classify text into one of the provided categories' 
                     category='FlowForge')
    public static List<ClassifyResponse> classify(List<ClassifyRequest> requests) {
        List<ClassifyResponse> responses = new List<ClassifyResponse>();
        
        for (ClassifyRequest req : requests) {
            ClassifyResponse res = new ClassifyResponse();
            try {
                HttpRequest httpReq = new HttpRequest();
                httpReq.setEndpoint(NAMED_CREDENTIAL + '/classify');
                httpReq.setMethod('POST');
                httpReq.setHeader('Content-Type', 'application/json');
                httpReq.setTimeout(60000);
                
                // Parse categories from comma-separated string
                List<String> categories = new List<String>();
                if (String.isNotBlank(req.categories)) {
                    for (String cat : req.categories.split(',')) {
                        categories.add(cat.trim());
                    }
                }
                
                Map<String, Object> body = new Map<String, Object>{
                    'text' => req.text,
                    'categories' => categories
                };
                httpReq.setBody(JSON.serialize(body));
                
                Http http = new Http();
                HttpResponse httpRes = http.send(httpReq);
                
                if (httpRes.getStatusCode() == 200) {
                    Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(httpRes.getBody());
                    res.category = (String) result.get('category');
                    res.confidence = (Decimal) result.get('confidence');
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
    
    public class ClassifyRequest {
        @InvocableVariable(label='Text' description='Text to classify' required=true)
        public String text;
        
        @InvocableVariable(label='Categories' description='Comma-separated list of categories' required=true)
        public String categories;
    }
    
    public class ClassifyResponse {
        @InvocableVariable(label='Category' description='Predicted category')
        public String category;
        
        @InvocableVariable(label='Confidence' description='Confidence score 0-1')
        public Decimal confidence;
        
        @InvocableVariable(label='Success')
        public Boolean success;
        
        @InvocableVariable(label='Error Message')
        public String errorMessage;
    }
}
