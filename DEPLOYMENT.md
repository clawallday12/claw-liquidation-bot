# Railway Deployment Guide

## Status
✅ Code committed to local git
✅ Railway account created ($5 free credit)
✅ GitHub account ready (clawallday12)
🔲 GitHub repo created
🔲 Code pushed to GitHub
🔲 Railway connected + deployed
🔲 Bot running 24/7

## Next Steps (3 manual steps)

### Step 1: Create GitHub Repository
Go to https://github.com/new and create a repo:
- **Name:** claw-liquidation-bot
- **Description:** Autonomous liquidation bot (Aave, Compound)
- **Visibility:** Private (contains sensitive config paths)
- **Do NOT initialize** with README

### Step 2: Push Code to GitHub
Run these commands from the workspace:

```powershell
cd C:\Users\firas\.openclaw\workspace

# Add GitHub as remote
git remote add origin https://github.com/clawallday12/claw-liquidation-bot.git

# Push to main branch
git branch -M main
git push -u origin main
```

When prompted for credentials:
- Username: clawallday12
- Password: Use GitHub personal access token or password

### Step 3: Deploy to Railway
1. Go to https://railway.app
2. Login with GitHub (already set up)
3. Click "New Project" → "Deploy from GitHub"
4. Select: clawallday12/claw-liquidation-bot
5. Railway will auto-detect Dockerfile
6. Add environment variables:
   - `WALLET_ADDRESS`: 0xA8297c4B031022D8d8e3Ce76322139A0120D6931
   - `PRIVATE_KEY`: [from config/autonomous-identity.json]
   - `RPC_URL`: https://eth.public.blastapi.io
7. Click "Deploy"

## Monitoring

Once deployed, monitor in Railway dashboard:
- **Logs:** Real-time execution logs
- **Metrics:** CPU, memory, network
- **Deployments:** Version history

## Environment Variables

The bot will read from Railway environment variables:
```python
import os
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
RPC_URL = os.getenv('RPC_URL')
```

## Troubleshooting

### Bot exits immediately
- Check logs in Railway dashboard
- Verify RPC_URL is accessible
- Check WALLET_ADDRESS is valid

### No revenue generated
- Monitor is running but no liquidations found
- This is expected (depends on market conditions)
- Check Aave health factors are above 1.0

### High memory usage
- Reduce check frequency in code
- Optimize blockchain queries

## Auto-Scaling

Railway automatically scales based on usage. With $5 credit:
- Estimated uptime: 30-40 days at low resource usage
- Estimated uptime: 5-10 days if checking frequently

## Next Revenue Streams (Post-Deployment)

Once liquidation bot is running:
1. Deploy data aggregation pipeline (whale tracking)
2. Set up Twitter automation (daily posts)
3. Launch Substack (premium research)
4. Create API service (monetized research)

---

**Estimated time to get running:** 15 minutes
**When to expect first revenue:** 1-7 days (depends on liquidation opportunities)
