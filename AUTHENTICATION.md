# 🔐 Kalshi API Authentication Setup

## How Kalshi Authentication Works

Kalshi uses **cryptographic key-based authentication** instead of simple API key/secret pairs. You'll receive:

1. **API Key** (UUID format like `e1414b25-061c-467d-a365-6e07fcc08d90`)
2. **Private Key File** (`.pem` file - downloaded once only!)

## Step-by-Step Setup

### 1. Get Your Kalshi API Credentials

1. Go to https://kalshi.com/settings/api
2. Click **"Create New API Key"** (or use existing)
3. You'll receive:
   - **API Key ID** (copy this)
   - **Private Key Download** button (⚠️ **Download immediately - shown only once!**)

### 2. Save the Private Key File

```powershell
# The downloaded file is usually named something like:
# kalshi-api-key-<timestamp>.pem

# Save it to your project directory as:
kalshi_private_key.pem
```

**Important:** Keep this file secure! Add it to `.gitignore` (already done ✅)

### 3. Update Your `.env` File

```env
KALSHI_API_KEY=e1414b25-061c-467d-a365-6e07fcc08d90  # Your API key
KALSHI_PRIVATE_KEY_PATH=kalshi_private_key.pem        # Path to your .pem file
KALSHI_ENV=demo  # Start with 'demo' for sandbox testing
```

### 4. Verify Setup

```powershell
# Test authentication
python test_api.py
```

**Expected output:**
```
✅ Private key loaded from kalshi_private_key.pem
✅ Balance: $10,000.00  # Demo account balance
✅ Found 50+ markets
```

## File Structure

```
Kalshi Trading/
├── .env                      # Your config (API key reference)
├── kalshi_private_key.pem    # Your private key (gitignored)
├── kalshi_auth.py            # Authentication module
└── kalshi_bot.py             # Main bot
```

## Troubleshooting

### ❌ "Private key file not found"

```powershell
# Check file exists
ls kalshi_private_key.pem

# If not, download from Kalshi and save with exact name:
# kalshi_private_key.pem
```

### ❌ "Failed to load private key"

- Ensure the file is a valid PEM format
- Check it starts with `-----BEGIN PRIVATE KEY-----`
- Re-download from Kalshi if corrupted

### ❌ "Authentication failed" (401)

- API key might be revoked - check Kalshi dashboard
- Regenerate key pair if needed

### ❌ "Token expired"

- Normal! Tokens expire after 5 minutes
- Bot automatically generates fresh tokens for each request

## Security Best Practices

✅ **DO:**
- Keep `kalshi_private_key.pem` private
- Use `.gitignore` to exclude it from version control (already set up)
- Regenerate keys if compromised
- Start with `KALSHI_ENV=demo` for testing

❌ **DON'T:**
- Share your private key file
- Commit it to GitHub
- Email or message it
- Store it in cloud folders without encryption

## How It Works Under the Hood

```python
# The bot uses JWT (JSON Web Tokens) signed with your private key:

from kalshi_auth import KalshiAuth

auth = KalshiAuth(
    api_key="e1414b25-061c-467d-a365-6e07fcc08d90",
    private_key_path="kalshi_private_key.pem"
)

# Generates signed JWT token for each request
headers = auth.get_auth_headers()
# {'Authorization': 'Bearer eyJ...'}
```

## Ready to Trade?

Once you have your private key set up:

```powershell
# 1. Test connection
python test_api.py

# 2. Run full validation
python setup_check.py

# 3. Start the bot!
python kalshi_bot.py
```

---

**Questions?** Check Kalshi API docs: https://kalshi.com/docs
