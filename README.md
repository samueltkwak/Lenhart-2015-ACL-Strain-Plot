# ACL Model Visualization

Interactive 3D visualization of ACL strain based on the Lenhart (2015) model.

## Files to upload to GitHub:

1. `app.py` - Main Dash application
2. `requirements.txt` - Python dependencies  
3. `Procfile` - For deployment
4. `runtime.txt` - Python version
5. `data.txt` - Your ACL data file (tab-separated)
6. `README.md` - This file

## Setup Instructions:

### Step 1: Upload to GitHub
1. Go to github.com and sign in
2. Click "New repository" 
3. Name it something like "acl-model-app"
4. Make it Public
5. Upload all files listed above

### Step 2: Update Data URL
1. After uploading, edit `app.py`
2. Find the line: `DATA_URL = "https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO-NAME/main/data.txt"`
3. Replace YOUR-USERNAME with your GitHub username
4. Replace YOUR-REPO-NAME with your repository name
5. Save the changes

### Step 3: Deploy on Render
1. Go to render.com and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Click "Deploy"
5. Wait 2-3 minutes
6. Get your public URL!

## Usage:
- Use the three sliders to control knee kinematics
- View real-time ACL strain changes in 3D
- Share the public URL with anyone!
