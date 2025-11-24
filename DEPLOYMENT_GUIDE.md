# Free Deployment Guide - Render.com

This guide will help you deploy your group chat application to Render.com for free.

## Prerequisites
1. GitHub account
2. Render.com account (free)
3. Your code pushed to GitHub

## Step 1: Push Code to GitHub

```bash
cd /Users/dhyeydesai/Desktop/USC_MATERIAL/SEM3_MATERIAL/DSCI560/final/final
git add .
git commit -m "Prepare for deployment"
git push origin main
```

## Step 2: Deploy on Render

### Option A: Using Render Dashboard (Recommended)

1. Go to https://render.com and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `groupchat-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `cd groupchat_app_src/backend && pip install -r requirements.txt`
   - **Start Command**: `cd groupchat_app_src/backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `groupchat_app_src/backend`

5. Add Environment Variables:
   - `DATABASE_URL`: (Will be set when you create a database)
   - `JWT_SECRET`: Generate a random secret
   - `JWT_EXPIRE_MINUTES`: `43200`
   - `LLM_API_BASE`: Your LLM API URL (or leave default)
   - `LLM_MODEL`: `llama-3-8b-instruct`
   - `APP_HOST`: `0.0.0.0`
   - `APP_PORT`: `$PORT` (Render sets this automatically)

6. Create a PostgreSQL Database:
   - Click "New +" → "PostgreSQL"
   - Name it `groupchat-db`
   - Copy the Internal Database URL
   - Update your service's `DATABASE_URL` environment variable

### Option B: Using render.yaml (Auto-deploy)

1. Push the `render.yaml` file to your repo
2. In Render dashboard, click "New +" → "Blueprint"
3. Connect your repository
4. Render will auto-detect and deploy

## Step 3: Update Database Connection

Since Render uses PostgreSQL (not MySQL), you'll need to update the database URL format:

The `DATABASE_URL` from Render will look like:
```
postgresql://user:pass@host:5432/dbname
```

But your code expects MySQL format. You have two options:

### Option 1: Use PostgreSQL (Recommended - Free on Render)
Update `db.py` to support both MySQL and PostgreSQL:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+asyncmy://chatuser:chatpass@localhost:3306/groupchat")

# Auto-detect database type
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
```

And add to `requirements.txt`:
```
asyncpg
```

### Option 2: Use MySQL (Requires paid service)
- Use Railway.app (free tier supports MySQL)
- Or use a free MySQL service like PlanetScale or Aiven

## Step 4: Deploy Frontend

For the frontend, you can:
1. Deploy to Vercel (free) or Netlify (free)
2. Update the API URL in `frontend/app.js` to point to your Render backend URL
3. Or serve the frontend from the same Render service (update `app.py` to serve static files)

## Step 5: Update CORS

Make sure your `app.py` has CORS configured to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Alternative: Railway.app (Supports MySQL)

Railway.app also offers a free tier and supports MySQL:

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Railway will auto-detect and deploy
6. Add a MySQL database from the dashboard
7. Set environment variables

## Notes

- Free tier on Render: 750 hours/month (enough for 24/7 if it's the only service)
- Free tier may spin down after inactivity (takes ~30 seconds to wake up)
- Database backups are recommended (Render offers this)
- For production, consider upgrading to paid tier for better performance

## Troubleshooting

- Check logs in Render dashboard if deployment fails
- Ensure all environment variables are set
- Verify database connection string format
- Check that port is set to `$PORT` (Render requirement)

