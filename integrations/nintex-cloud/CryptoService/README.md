# FlowForge crypto-service - Nintex Workflow Cloud Xtension

## Overview
FlowForge plugin Xtension for Nintex Workflow Cloud.

## Installation

1. Go to **Nintex Workflow Cloud** > **Settings** > **Xtensions**
2. Click **Add Xtension**
3. Choose **Add custom connector**
4. Upload `crypto-service.swagger.json`
5. Configure authentication (API Key)
6. Click **Publish**

## Configuration

### API Key Setup
1. In the Xtension settings, select **API Key** authentication
2. Set header name: `X-API-Key`
3. Enter your FlowForge API key

### Base URL
Update the host in the Swagger file to your FlowForge instance URL.

## Available Actions

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

## Usage in Workflows

After publishing the Xtension:
1. Open workflow designer
2. Find actions under **FlowForge** category
3. Drag and drop actions into your workflow
4. Configure action parameters

## Support

For issues or questions, visit [FlowForge Support](https://flowforge.io/support)
