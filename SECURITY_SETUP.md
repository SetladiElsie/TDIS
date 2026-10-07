# 🔒 TDIS Security Setup Guide

## ⚠️ IMMEDIATE ACTION REQUIRED

Your application had exposed credentials that need to be rotated immediately.

---

## 🔴 Step 1: Rotate Exposed Passwords (DO THIS NOW!)

### 1.1 Email Password (Microsoft 365)
**Exposed:** `@MyBahumi18`

**Action Required:**
1. Log in to: https://account.microsoft.com/security
2. Go to "Security" → "Advanced security options"
3. Select "App passwords"
4. Click "Create a new app password"
5. Name it: "TDIS Application"
6. Copy the generated password
7. Update `.env` file:
   ```env
   MAIL_PASSWORD=your-new-app-password-here
   ```

**Alternative:** Change your Microsoft account password entirely:
- Go to: https://account.microsoft.com/password/change
- Set a new password

### 1.2 Database Password
**Exposed:** `Tdis@2026!Secure`

**Action Required:**

#### If using PostgreSQL:
```sql
-- Connect to PostgreSQL as admin
psql -U postgres

-- Change the password
ALTER USER tdis_user WITH PASSWORD 'NEW_SECURE_PASSWORD_HERE';
\q
```

**Generate a strong password:**
```bash
python -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for i in range(24)))"
```

**Update `.env` file:**
```env
DATABASE_URL=postgresql://tdis_user:NEW_SECURE_PASSWORD@127.0.0.1:5432/tdis_db
```

#### If using SQLite (current setup):
- No action needed, but uncomment the DATABASE_URL line in `.env` when switching back to PostgreSQL

---

## ✅ Step 2: Verify .gitignore

Check that `.env` is in `.gitignore`:

```bash
cat .gitignore | grep .env
```

**Expected output:**
```
.env
.env.local
.env.*.local
```

✅ Already configured correctly!

---

## 🧹 Step 3: Check Git History

Verify `.env` was never committed:

```bash
git log --all --full-history -- .env
```

**Expected output:** (nothing)

✅ Confirmed: `.env` was never committed to git history!

---

## 📋 Step 4: Use .env.example for Documentation

A `.env.example` file has been created with placeholder values.

**For developers:**
```bash
# Copy example to create your local .env
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Never commit `.env` to git!**

---

## 🔐 Step 5: Production Secrets Management

For production deployment, use a secrets management service instead of `.env` files:

### Option A: Azure Key Vault (Recommended for Azure)

**Setup:**
```bash
# Install Azure SDK
pip install azure-keyvault-secrets azure-identity

# Create Key Vault
az keyvault create --name tdis-keyvault --resource-group tdis-rg --location southafricanorth
```

**Store secrets:**
```bash
az keyvault secret set --vault-name tdis-keyvault --name "SECRET-KEY" --value "your-secret-key"
az keyvault secret set --vault-name tdis-keyvault --name "DB-PASSWORD" --value "your-db-password"
az keyvault secret set --vault-name tdis-keyvault --name "MAIL-PASSWORD" --value "your-mail-password"
```

**Update `config.py`:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_secret(secret_name):
    """Retrieve secret from Azure Key Vault"""
    if os.getenv('FLASK_ENV') == 'production':
        vault_url = os.getenv('AZURE_KEY_VAULT_URL')
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        return client.get_secret(secret_name).value
    return os.getenv(secret_name)

# Usage
SECRET_KEY = get_secret('SECRET_KEY')
```

### Option B: AWS Secrets Manager

**Setup:**
```bash
# Install AWS SDK
pip install boto3

# Create secret
aws secretsmanager create-secret \
    --name tdis/production \
    --secret-string '{"SECRET_KEY":"...","DB_PASSWORD":"...","MAIL_PASSWORD":"..."}'
```

**Retrieve in app:**
```python
import boto3
import json

def get_aws_secret():
    client = boto3.client('secretsmanager', region_name='af-south-1')
    response = client.get_secret_value(SecretId='tdis/production')
    return json.loads(response['SecretString'])

secrets = get_aws_secret()
SECRET_KEY = secrets['SECRET_KEY']
```

### Option C: HashiCorp Vault

**Setup:**
```bash
# Install Vault
brew install vault  # macOS
# or download from: https://www.vaultproject.io/downloads

# Start dev server
vault server -dev

# Store secrets
vault kv put secret/tdis SECRET_KEY="..." DB_PASSWORD="..." MAIL_PASSWORD="..."
```

---

## 🔒 Step 6: Additional Security Measures

### 6.1 Enable 2FA on All Accounts
- [ ] Microsoft 365 account (elsie@tia-solutions.co.za)
- [ ] Git hosting (GitHub/GitLab/Azure DevOps)
- [ ] Cloud provider (Azure/AWS)
- [ ] Database hosting

### 6.2 Restrict Database Access
**PostgreSQL:**
```sql
-- Only allow connections from application server
-- Edit pg_hba.conf
host    tdis_db    tdis_user    10.0.0.0/24    md5

-- Revoke public access
REVOKE ALL ON DATABASE tdis_db FROM PUBLIC;
```

### 6.3 Use Read-Only Database User for Reports
```sql
-- Create read-only user
CREATE USER tdis_reader WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE tdis_db TO tdis_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO tdis_reader;
```

### 6.4 Set Up IP Whitelisting
For production database and Redis:
- Only allow connections from application server IP
- Use VPN or private network where possible

---

## 📊 Password Strength Requirements

All passwords should meet these criteria:
- ✅ Minimum 16 characters (24+ recommended)
- ✅ Mix of uppercase, lowercase, numbers, symbols
- ✅ No dictionary words
- ✅ No personal information
- ✅ Unique per service
- ✅ Rotated every 90 days

**Use a password manager:** 1Password, Bitwarden, LastPass

---

## 🔄 Password Rotation Schedule

| Service | Current Rotation | Next Rotation |
|---------|-----------------|---------------|
| SECRET_KEY | 2026-12-29 | 2027-03-29 |
| Database | PENDING | 90 days after set |
| Email | PENDING | 90 days after set |
| API Keys | N/A | When implemented |

**Set calendar reminder:** Rotate passwords quarterly

---

## ✅ Security Checklist

- [x] `.env` is in `.gitignore`
- [x] `.env` was never committed to git
- [x] `.env.example` created for documentation
- [x] New SECRET_KEY generated
- [ ] **Email password rotated** ⚠️ ACTION REQUIRED
- [ ] **Database password rotated** ⚠️ ACTION REQUIRED
- [ ] 2FA enabled on critical accounts
- [ ] Password manager in use
- [ ] Calendar reminder set for rotation (90 days)

---

## 🚨 If Credentials Were Pushed to Git

If `.env` or credentials were previously pushed to a public repository:

### Immediate Actions:
1. **Assume credentials are compromised**
2. **Rotate ALL passwords immediately**
3. **Check access logs** for unauthorized access
4. **Notify security team/stakeholders**
5. **Monitor for suspicious activity**

### Remove from Git History:
```bash
# Option 1: BFG Repo-Cleaner (Recommended)
# Download from: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Option 2: git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (⚠️ WARNING: Rewrites history)
git push origin --force --all
git push origin --force --tags
```

### Verify Removal:
```bash
git log --all --full-history -- .env
# Should return nothing
```

---

## 📞 Support

**Security Concerns:** Contact your security team immediately

**Questions:** Refer to deployment documentation

**Emergency:** If you suspect a security breach, take the application offline and investigate.

---

**Last Updated:** December 29, 2026  
**Next Review:** March 29, 2027
