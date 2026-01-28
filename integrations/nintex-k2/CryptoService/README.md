# LeForge crypto-service - Nintex K2 Integration

## Overview
LeForge plugin integration for Nintex K2.

## Installation

### 1. Register REST Service Broker

1. Open **K2 Management Console**
2. Navigate to **Integration** > **Service Types**
3. Add new **REST Service Broker**
4. Upload `swagger/crypto-service.json`
5. Configure base URL and authentication

### 2. Create Service Instance

1. Go to **Service Instances**
2. Create new instance from the registered service type
3. Configure connection:
   - Base URL: Your LeForge server URL
   - Authentication: API Key
   - Header: `X-API-Key`

### 3. Generate SmartObjects

1. Navigate to **SmartObjects**
2. Click **Generate SmartObjects** from service instance
3. Select operations to expose
4. Publish SmartObjects

## SmartObject Templates

Pre-configured SmartObject templates are available in the `smartobjects/` folder.
Import these for common operations.

## Available Operations

| hash | Hash data using SHA-1, SHA-256, SHA-512, or MD5 |
| hashFile | Calculate hash/checksum of file data (base64 encoded) |
| encrypt | Encrypt data using AES-256-GCM (authenticated encryption) |
| decrypt | Decrypt AES encrypted data |
| jwtSign | Generate a JWT token |
| jwtVerify | Verify and decode a JWT token |
| jwtDecode | Decode a JWT without verification (for inspection only) |
| hmacSign | Create HMAC signature |
| hmacVerify | Verify HMAC signature (timing-safe comparison) |
| randomBytes | Generate cryptographically secure random bytes |
| uuid | Generate a UUID v4 |
| base64Encode | Encode string to Base64 |
| base64Decode | Decode Base64 string |
| hexEncode | Encode string to hexadecimal |
| hexDecode | Decode hexadecimal string |
| compareStrings | Timing-safe string comparison (prevents timing attacks) |
| deriveKey | Derive encryption key from password using PBKDF2 |
| generatePassword | Generate a secure random password |
| generateKeyPair | Generate RSA, ECDSA, or Ed25519 key pair |
| rsaEncrypt | Encrypt data using RSA public key |

## Using in K2 Forms & Workflows

### In Forms
1. Add SmartObject data source
2. Bind to form controls
3. Execute methods on form events

### In Workflows
1. Add SmartObject event
2. Configure method and parameters
3. Map inputs/outputs

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
