/**
 * LeForge Formula Engine - Salesforce Apex Invocable Actions
 * Evaluate Excel-compatible formulas in Salesforce Flows
 * 
 * @author LeForge Team
 * @version 1.0.0
 */
public class LeForgeFormulaService {
    
    private static final String NAMED_CREDENTIAL = 'callout:LeForge_API/formula';
    
    // ============================================
    // EVALUATE FORMULA ACTION
    // ============================================
    
    @InvocableMethod(label='Evaluate Formula' 
                     description='Evaluate an Excel-compatible formula' 
                     category='LeForge')
    public static List<FormulaResponse> evaluate(List<FormulaRequest> requests) {
        List<FormulaResponse> responses = new List<FormulaResponse>();
        
        for (FormulaRequest req : requests) {
            FormulaResponse res = new FormulaResponse();
            try {
                HttpRequest httpReq = new HttpRequest();
                httpReq.setEndpoint(NAMED_CREDENTIAL + '/evaluate');
                httpReq.setMethod('POST');
                httpReq.setHeader('Content-Type', 'application/json');
                httpReq.setTimeout(30000);
                
                Map<String, Object> body = new Map<String, Object>{
                    'formula' => req.formula
                };
                
                // Parse variables from JSON string if provided
                if (String.isNotBlank(req.variablesJson)) {
                    try {
                        Map<String, Object> vars = (Map<String, Object>) JSON.deserializeUntyped(req.variablesJson);
                        body.put('variables', vars);
                    } catch (Exception e) {
                        res.success = false;
                        res.errorMessage = 'Invalid variables JSON: ' + e.getMessage();
                        responses.add(res);
                        continue;
                    }
                }
                
                httpReq.setBody(JSON.serialize(body));
                
                Http http = new Http();
                HttpResponse httpRes = http.send(httpReq);
                
                if (httpRes.getStatusCode() == 200) {
                    Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(httpRes.getBody());
                    Object evalResult = result.get('result');
                    res.result = String.valueOf(evalResult);
                    res.resultType = (String) result.get('type');
                    
                    // Also populate typed results
                    if (evalResult instanceof Decimal || evalResult instanceof Integer || evalResult instanceof Double) {
                        res.numericResult = Decimal.valueOf(String.valueOf(evalResult));
                    } else if (evalResult instanceof Boolean) {
                        res.booleanResult = (Boolean) evalResult;
                    }
                    
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
    
    public class FormulaRequest {
        @InvocableVariable(label='Formula' description='Formula to evaluate (e.g., =SUM(1,2,3) or =IF(x>10,"High","Low"))' required=true)
        public String formula;
        
        @InvocableVariable(label='Variables JSON' description='JSON object with variable values (e.g., {"x": 15, "y": 20})')
        public String variablesJson;
    }
    
    public class FormulaResponse {
        @InvocableVariable(label='Result' description='Formula result as string')
        public String result;
        
        @InvocableVariable(label='Numeric Result' description='Result as number (if applicable)')
        public Decimal numericResult;
        
        @InvocableVariable(label='Boolean Result' description='Result as boolean (if applicable)')
        public Boolean booleanResult;
        
        @InvocableVariable(label='Result Type' description='Type of result (number, string, boolean, array)')
        public String resultType;
        
        @InvocableVariable(label='Success')
        public Boolean success;
        
        @InvocableVariable(label='Error Message')
        public String errorMessage;
    }
}
