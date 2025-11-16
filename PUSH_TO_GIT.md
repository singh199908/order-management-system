# Push to GitHub/GitLab - Quick Guide

## Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `order-management-system`
3. Choose **Private** (recommended) or Public
4. **DO NOT** initialize with README, .gitignore, or license
5. Click "Create repository"

## Step 2: Push Your Code

After creating the repository, run these commands:

### For GitHub:
```bash
cd C:\Users\aksha\OneDrive\Desktop\order_management_system
git remote add origin https://github.com/YOUR_USERNAME/order-management-system.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### For GitLab:
```bash
cd C:\Users\aksha\OneDrive\Desktop\order_management_system
git remote add origin https://gitlab.com/YOUR_USERNAME/order-management-system.git
git branch -M main
git push -u origin main
```

## If You Need to Authenticate

- **GitHub**: You may need a Personal Access Token (Settings → Developer settings → Personal access tokens)
- **GitLab**: Use your username and password, or set up an access token

