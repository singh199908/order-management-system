# GitHub Authentication Setup

GitHub requires a Personal Access Token (PAT) instead of passwords for Git operations.

## Step 1: Create a Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `order-management-system`
4. Select expiration: **90 days** or **No expiration** (your choice)
5. Check these scopes:
   - ✅ `repo` (Full control of private repositories)
6. Click "Generate token"
7. **COPY THE TOKEN IMMEDIATELY** - you won't see it again!

## Step 2: Push Using the Token

When prompted for password, use the **token** instead of your GitHub password.

### Option A: Push with Token (Recommended)
```bash
cd C:\Users\aksha\OneDrive\Desktop\order_management_system
git push -u origin main
```
When asked for:
- **Username**: `singh199908`
- **Password**: Paste your Personal Access Token

### Option B: Use Token in URL (One-time)
```bash
cd C:\Users\aksha\OneDrive\Desktop\order_management_system
git remote set-url origin https://YOUR_TOKEN@github.com/singh199908/order-management-system.git
git push -u origin main
```
Replace `YOUR_TOKEN` with your actual token.

### Option C: Use Git Credential Manager (Windows)
Windows should prompt you to save credentials. Use:
- Username: `singh199908`
- Password: Your Personal Access Token

## Security Note
⚠️ Never share your Personal Access Token or commit it to Git!

