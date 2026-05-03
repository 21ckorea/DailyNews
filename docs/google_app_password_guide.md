# Google App Password Creation Guide

To send emails using Python and Gmail, you must use an **App Password** instead of your regular account password for security reasons.

## Steps

1. **Google Account Management**: Go to [Google Account](https://myaccount.google.com/).
2. **Security Menu**: Click the **[Security]** tab on the left.
3. **2-Step Verification**: Ensure **[2-Step Verification]** is turned ON.
4. **Search for App Passwords**: 
    - Go to the bottom of the 2-Step Verification menu and find **[App passwords]**.
    - Or search for "App passwords" in the top search bar.
5. **Create App**:
    - Enter a name (e.g., `Daily News Python`) and click **[Create]**.
6. **Copy Password**: Copy the **16-character password** in the yellow box (ignore spaces).
7. **Update Config**: Paste the password into the `sender_password` field in `config.yaml`.
