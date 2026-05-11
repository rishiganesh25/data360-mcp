# Salesforce Connected App Setup Guide

This guide walks you through creating a Salesforce Connected App that the Data Cloud MCP server uses to authenticate via OAuth 2.0 with PKCE.

**Time required**: ~10 minutes

---

## Prerequisites

- Admin access to a Salesforce org (or a user with "Manage Connected Apps" permission)
- The org must have **Data Cloud** enabled

---

## Step 1: Enable External Client Apps

1. Log in to your Salesforce org
2. Click the **gear icon** (top right) > **Setup**
3. In the **Quick Find** box (left sidebar), type: `External Client Apps`
4. Click **Settings** under "External Client Apps"
5. Enable **both** toggles:
   - "Allow access to External Client App consumer secrets via REST API"
   - "Allow creation of connected apps"
6. Click **Save**

---

## Step 2: Create the Connected App

1. In Setup, navigate to **External Client Apps** (left sidebar)
2. Click **New Connected App**
3. Fill in the basic info:

| Field | Value |
|---|---|
| Connected App Name | `Data Cloud MCP` |
| API Name | `Data_Cloud_MCP` (auto-populated) |
| Contact Email | Your email address |

4. Click **Next** or scroll to the OAuth section

---

## Step 3: Enable and Configure OAuth

1. Check the box: **"Enable OAuth Settings"**

2. Set the **Callback URL** to exactly:
   ```
   http://localhost:55556/Callback
   ```
   > **Warning**: Do NOT use port `55555` — it conflicts with macOS AirPlay Receiver and other services. Port `55556` is safe.

3. Add the following **OAuth Scopes** (click "Add" for each one):

   | Scope | Why it's needed |
   |---|---|
   | `Access the identity URL service (id, profile, email, address, phone)` | User identity during OAuth |
   | `Manage user data via APIs (api)` | General REST API access |
   | `Manage Data Cloud profile data (cdp_profile_api)` | Data Cloud Connect API (streams, segments, etc.) |
   | `Perform ANSI SQL queries on Data Cloud data (cdp_query_api)` | SQL queries against Data Cloud |
   | `Perform requests at any time (refresh_token, offline_access)` | Keep sessions alive |

4. Under **Security Settings**, enable all three:

   | Setting | Value |
   |---|---|
   | Require Secret for Web Server Flow | **Yes** (checked) |
   | Require Secret for Refresh Token Flow | **Yes** (checked) |
   | Require Proof Key for Code Exchange (PKCE) | **Yes** (checked) |

5. Click **Save**

---

## Step 4: Copy Your Consumer Key and Secret

After saving, you need to retrieve the credentials:

1. Go to **Setup** > search **"External Client Apps"** in Quick Find
2. Find **Data Cloud MCP** in the list and click on it
3. Navigate to: **Settings** > **OAuth Settings** > **App Settings**
4. Copy the **Consumer Key** (this is your `SF_CLIENT_ID`)
5. Click "Click to reveal" next to Consumer Secret and copy it (this is your `SF_CLIENT_SECRET`)

> **Keep these safe.** Store them in your `.env` file, never in version control.

---

## Step 5: Configure OAuth Policies

1. Go back to your Connected App page in Setup
2. Click **Manage** (button at the top)
3. Click **Edit Policies**
4. Under **OAuth Policies**, find **IP Relaxation** and change it to:
   ```
   Relax IP restrictions
   ```
5. Click **Save**

> **Why?** Without this, Salesforce blocks OAuth from localhost because it doesn't match any login IP range. This is safe for development — the PKCE flow still requires the browser login + authorization.

---

## Step 6: Assign the Connected App to Users (Optional)

By default, the Connected App is available to all users in the org. If your org uses more restrictive policies:

1. Go to **Setup** > **Permission Sets** (or **Profiles**)
2. Find the permission set assigned to your Data Cloud users
3. Under **Connected App Access**, add **Data Cloud MCP**

---

## Step 7: Verify Propagation

Connected App changes can take **5-10 minutes** to propagate across Salesforce infrastructure.

If you get `invalid_client_id` errors immediately after setup, wait 10 minutes and try again.

---

## Summary Checklist

Before moving on to the MCP server configuration, confirm:

- [ ] External Client Apps are enabled in Setup
- [ ] Connected App "Data Cloud MCP" is created
- [ ] Callback URL is exactly `http://localhost:55556/Callback`
- [ ] All 5 OAuth scopes are added
- [ ] PKCE is required
- [ ] IP Relaxation is set to "Relax IP restrictions"
- [ ] You have the Consumer Key and Consumer Secret copied
- [ ] You've waited at least 5 minutes since saving

---

## Next Steps

Return to the [README](README.md#configuration) and configure your `.env` file with the Consumer Key and Secret you just obtained.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Can't find "External Client Apps" in Setup | Your org edition may not support it. Try searching for "App Manager" instead and create a Connected App from there (same OAuth settings apply). |
| "Connected App not found" error | Wait 10 minutes for propagation. If it persists, verify the Consumer Key matches. |
| `invalid_client_id` | Double-check you copied the full Consumer Key (no trailing spaces). Also verify `SF_LOGIN_URL` matches the org where you created the app (e.g., `login.salesforce.com` vs `test.salesforce.com`). |
| `redirect_uri_mismatch` | The Callback URL in the Connected App must be **exactly** `http://localhost:55556/Callback` (case-sensitive, no trailing slash). |
| `PKCE challenge failed` | Make sure "Require Proof Key for Code Exchange" is checked. If you changed it after creation, wait 10 minutes. |
| User can't authorize the app | The user needs to be assigned to the Connected App (see Step 6) or the app must allow "All users may self-authorize". |
