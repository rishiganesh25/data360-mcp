# Salesforce Connected App Setup Guide

This guide walks you through creating a Salesforce Connected App for the MCP Data Cloud Server.

## Prerequisites

- Access to a Salesforce org with appropriate permissions

## Step-by-Step Setup

### 1. Enable External Client Apps

1. Login to Salesforce → Setup → Search for "External Client Apps" using Quick Find
2. Under "External Client Apps" on the left pane, choose 'Settings'
3. Enable the following options:
   - "Allow access to External Client App consumer secrets via REST API"
   - "Allow creation of connected apps"
4. Click "Save"

### 2. Create New Connected App

1. Click "New Connected App"
2. Fill in the basic information:
   - **Connected App Name**: MCP
   - **API Name**: MCP (or use the default pre-populated value)
   - **Contact Email**: Your email address

### 3. Configure OAuth Settings

1. Under the "API" heading, check the box for "Enable OAuth Settings"
2. **Callback URL**: 
   - `http://localhost:55556/Callback`
    Please DO NOT use port 55555 as this may run into issues. 

3. **OAuth Scopes**: Add all of the scopes.

4. **Security Settings**:
   - Require Secret for Web Server Flow: **true**
   - Require Secret for Refresh Token Flow: **true**
   - Require Proof Key for Code Exchange (PKCE) extension for Supported Authorization Flows: **true**


5. Click "Save" and note down the Consumer Key and Secret

### 4. Configure OAuth Policies

1. At the top of your newly created connected app, click "Manage"
2. Navigate to Policies → OAuth policies
3. Select "Edit Policies"
4. Change "IP Relaxation" to "Relax IP restrictions"
5. Click "Save"

### 5. Enable Password Flow (Optional)

1. In Setup, search for "OAuth and OpenID Connect Settings"
2. Turn on password flow

## Retrieving Client Credentials

To view the Client ID and Client Secret of your connected app:

1. Search for "External Client Apps" in the Setup page
2. Look for the connected app you just created
3. Click on Settings > Oauth Settings > App Settings > Consumer Key and Secret

## Important Notes

- The callback URL you configure in the connected app must match the `SF_CALLBACK_URL` environment variable
- Keep your Client ID and Secret secure and never commit it to version control

## Troubleshooting

If you encounter issues:

1. Verify that the connected app is enabled
2. Check that the callback URL matches exactly (including case sensitivity)
3. Ensure all required OAuth scopes are selected
4. Verify that IP restrictions are relaxed if you're testing from different networks
5. Ensure that you are not using port 55555 in your callback URL
