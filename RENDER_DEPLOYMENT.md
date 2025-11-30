# 🚀 Deploying ForensicEDR Backend to Render

This guide will walk you through deploying the ForensicEDR Cloud Backend to [Render.com](https://render.com), a modern cloud hosting platform.

Since Render does not host MongoDB databases natively, we will use **MongoDB Atlas** (the official cloud MongoDB service) for the database.

---

## ✅ Prerequisites

1.  **GitHub Repository**: Ensure your code is pushed to GitHub (you just did this!).
2.  **Render Account**: Sign up at [dashboard.render.com](https://dashboard.render.com/).
3.  **MongoDB Atlas Account**: Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas).

---

## 1️⃣ Step 1: Set up MongoDB Atlas (Database)

1.  **Create a Cluster**:
    *   Log in to MongoDB Atlas.
    *   Click **+ Create** to create a new cluster.
    *   Select **M0 Sandbox** (Free Tier).
    *   Choose a provider (AWS) and region close to you (e.g., N. Virginia).
    *   Click **Create Deployment**.

2.  **Create a Database User**:
    *   Go to **Security** -> **Database Access**.
    *   Click **+ Add New Database User**.
    *   **Username**: `admin` (or your choice).
    *   **Password**: Click "Autogenerate Secure Password" (COPY THIS! You will need it).
    *   **Privileges**: "Read and write to any database".
    *   Click **Add User**.

3.  **Allow Network Access**:
    *   Go to **Security** -> **Network Access**.
    *   Click **+ Add IP Address**.
    *   Click **Allow Access from Anywhere** (`0.0.0.0/0`).
        *   *Note: For production, you would restrict this to Render's IPs, but "Anywhere" is easiest for initial setup.*
    *   Click **Confirm**.

4.  **Get Connection String**:
    *   Go back to **Deployment** -> **Database**.
    *   Click **Connect** on your cluster.
    *   Select **Drivers**.
    *   Copy the connection string. It looks like:
        `mongodb+srv://admin:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority`
    *   **Replace `<password>`** with the password you generated in step 2.
    *   **Save this string** - this is your `MONGODB_URI`.

---

## 2️⃣ Step 2: Deploy to Render

We have added a `render.yaml` file to your repository, which makes deployment automatic.

1.  **Create New Web Service**:
    *   Go to your [Render Dashboard](https://dashboard.render.com/).
    *   Click **New +** and select **Web Service**.
    *   Connect your GitHub account if you haven't already.
    *   Select your repository: `forensicEDR_cloud`.

2.  **Configure Service**:
    *   **Name**: `forensic-edr-backend`
    *   **Region**: Choose one close to your MongoDB cluster (e.g., Ohio or Oregon).
    *   **Branch**: `main`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
    *   **Instance Type**: Free (for testing) or Starter.

3.  **Environment Variables** (Crucial!):
    *   Scroll down to "Environment Variables" or "Advanced".
    *   Add the following variables:
        *   `MONGODB_URI`: Paste the connection string from Step 1.
        *   `AES_ENCRYPTION_KEY`: Paste your 32-byte hex key (from your local `.env`).
        *   `PYTHON_VERSION`: `3.11.9`
        *   `LOG_LEVEL`: `INFO`

4.  **Deploy**:
    *   Click **Create Web Service**.
    *   Render will start building your app. You can watch the logs.
    *   Once it says "Live", your backend is deployed! 🚀

---

## 3️⃣ Step 3: Verify Deployment

1.  **Get URL**: Copy your service URL from the top left of the Render dashboard (e.g., `https://forensic-edr-backend.onrender.com`).
2.  **Test Health Endpoint**:
    *   Visit `https://YOUR-APP-URL.onrender.com/health`
    *   You should see `{"status": "healthy", ...}`.
3.  **Test Docs**:
    *   Visit `https://YOUR-APP-URL.onrender.com/docs`
    *   You should see the Swagger UI.

---

## 4️⃣ Step 4: Update Dashboard Configuration

Once your backend is live, you will need to update your React Dashboard to point to this new URL instead of `localhost:8000`.

In your dashboard's `src/services/api.js` (when you build it):
```javascript
// Change this:
// const API_BASE_URL = 'http://localhost:8000';

// To this:
const API_BASE_URL = 'https://forensic-edr-backend.onrender.com'; // Your actual Render URL
```
