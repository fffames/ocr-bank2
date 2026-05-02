# Google Sheets Configuration

## Place your Google credentials file here

1. Download your Google Service Account credentials JSON file
2. Rename it to `credentials.json`
3. Place it in this directory: `backend/config/credentials.json`

## The file should look like:

```json
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

## Security Note

**NEVER commit this file to git!**
Add `config/credentials.json` to your `.gitignore` file.
