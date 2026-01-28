/**
 * LeForge Crypto Service - Salesforce Apex Invocable Actions
 * Provides encryption, decryption, hashing, and key generation
 * for use in Salesforce Flow Builder.
 * 
 * @author LeForge Team
 * @version 1.0.0
 */
public class LeForgeCryptoService {
    
    private static final String NAMED_CREDENTIAL = 'callout:LeForge_API/crypto';
    
    // ============================================
    // ENCRYPT ACTION
    // ============================================
    
    @InvocableMethod(label='Encrypt Data' 
                     description='Encrypt sensitive data using AES encryption' 
                     category='LeForge')
    public static List<EncryptResponse> encrypt(List<EncryptRequest> requests) {
        List<EncryptResponse> responses = new List<EncryptResponse>();
        
        for (EncryptRequest req : requests) {
            EncryptResponse res = new EncryptResponse();
            try {
                HttpRequest httpReq = new HttpRequest();
                httpReq.setEndpoint(NAMED_CREDENTIAL + '/encrypt');
                httpReq.setMethod('POST');
                httpReq.setHeader('Content-Type', 'application/json');
                httpReq.setTimeout(30000);
                
                Map<String, Object> body = new Map<String, Object>{
                    'data' => req.data,
                    'key' => req.encryptionKey
                };
                if (String.isNotBlank(req.algorithm)) {
                    body.put('algorithm', req.algorithm);
                }
                httpReq.setBody(JSON.serialize(body));
                
                Http http = new Http();
                HttpResponse httpRes = http.send(httpReq);
                
                if (httpRes.getStatusCode() == 200) {
                    Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(httpRes.getBody());
                    Map<String, Object> data = (Map<String, Object>) result.get('data');
                    res.encrypted = (String) data.get('encrypted');
                    res.iv = (String) data.get('iv');
                    res.tag = (String) data.get('tag');
                    res.algorithm = (String) data.get('algorithm');
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
    
    public class EncryptRequest {
        @InvocableVariable(label='Data' description='Data to encrypt' required=true)
        public String data;
        
        @InvocableVariable(label='Encryption Key' description='Key for encryption (hex or base64)' required=true)
        public String encryptionKey;
        
        @InvocableVariable(label='Algorithm' description='Encryption algorithm (default: aes-256-gcm)')
        public String algorithm;
    }
    
    public class EncryptResponse {
        @InvocableVariable(label='Encrypted Data' description='Encrypted data (base64)')
        public String encrypted;
        
        @InvocableVariable(label='IV' description='Initialization vector (save for decryption)')
        public String iv;
        
        @InvocableVariable(label='Tag' description='Authentication tag (save for decryption)')
        public String tag;
        
        @InvocableVariable(label='Algorithm' description='Algorithm used')
        public String algorithm;
        
        @InvocableVariable(label='Success')
        public Boolean success;
        
        @InvocableVariable(label='Error Message')
        public String errorMessage;
    }
}
