/**
 * LeForge Crypto Service - Additional Actions
 * Decrypt, Hash, Generate Key
 * 
 * @author LeForge Team
 * @version 1.0.0
 */
public class LeForgeCryptoActions {
    
    private static final String NAMED_CREDENTIAL = 'callout:LeForge_API/crypto';
    
    // ============================================
    // DECRYPT ACTION
    // ============================================
    
    @InvocableMethod(label='Decrypt Data' 
                     description='Decrypt data that was encrypted by LeForge' 
                     category='LeForge')
    public static List<DecryptResponse> decrypt(List<DecryptRequest> requests) {
        List<DecryptResponse> responses = new List<DecryptResponse>();
        
        for (DecryptRequest req : requests) {
            DecryptResponse res = new DecryptResponse();
            try {
                HttpRequest httpReq = new HttpRequest();
                httpReq.setEndpoint(NAMED_CREDENTIAL + '/decrypt');
                httpReq.setMethod('POST');
                httpReq.setHeader('Content-Type', 'application/json');
                httpReq.setTimeout(30000);
                
                Map<String, Object> body = new Map<String, Object>{
                    'encrypted' => req.encryptedData,
                    'key' => req.decryptionKey,
                    'iv' => req.iv
                };
                if (String.isNotBlank(req.tag)) {
                    body.put('tag', req.tag);
                }
                if (String.isNotBlank(req.algorithm)) {
                    body.put('algorithm', req.algorithm);
                }
                httpReq.setBody(JSON.serialize(body));
                
                Http http = new Http();
                HttpResponse httpRes = http.send(httpReq);
                
                if (httpRes.getStatusCode() == 200) {
                    Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(httpRes.getBody());
                    Map<String, Object> data = (Map<String, Object>) result.get('data');
                    res.decrypted = (String) data.get('decrypted');
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
    
    public class DecryptRequest {
        @InvocableVariable(label='Encrypted Data' description='Data to decrypt' required=true)
        public String encryptedData;
        
        @InvocableVariable(label='Decryption Key' description='Key used for encryption' required=true)
        public String decryptionKey;
        
        @InvocableVariable(label='IV' description='Initialization vector from encryption' required=true)
        public String iv;
        
        @InvocableVariable(label='Tag' description='Authentication tag from encryption')
        public String tag;
        
        @InvocableVariable(label='Algorithm' description='Encryption algorithm used')
        public String algorithm;
    }
    
    public class DecryptResponse {
        @InvocableVariable(label='Decrypted Data' description='Original plaintext data')
        public String decrypted;
        
        @InvocableVariable(label='Success')
        public Boolean success;
        
        @InvocableVariable(label='Error Message')
        public String errorMessage;
    }
}
