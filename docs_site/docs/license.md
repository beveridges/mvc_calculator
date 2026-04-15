# License System

## Overview

MVC Calculator uses a **hardware-locked** licence. The application stores your entitlement on disk (see [Where your licence is stored](#where-your-licence-is-stored)) and checks it when you start the app.

You can unlock the software in one of these ways:

| Method | Typical use |
|--------|-------------|
| **Activation code** | You receive a code from support or your institution; you redeem it in the app (**Help** → **Licence manager...**). |
| **License file (`license.key`)** | You receive a `license.key` attachment by email and place it in the [recommended folder](#installing-a-license-key-file). The first successful run **imports** it into your entitlement store. |
| **Pre-installed entitlement** | Some institutional builds (for example HFMDD) ship with an entitlement already bundled; no separate file is needed if the bundle matches your machine and region. |

!!! note "Spelling"
    The menu uses **Licence** (British spelling) to match the application.

---

## Activating with an activation code

This is the **preferred** flow when your organisation or Moviolabs issues you an **activation code** instead of (or in addition to) a `license.key` file.

### Steps

1. Start MVC Calculator.
2. Open **Help** → **Licence manager...**
3. Enter your **activation code** in the field provided.
4. Choose the control that submits the code (for example **Activate**). The app contacts the activation service, receives a signed licence payload, and saves it as **`entitlement.json`** in your [user data folder](#where-your-licence-is-stored).
5. If activation succeeds, restart the application if prompted. Your licence is validated automatically on the next start.

### If activation is unavailable

If you see a message that the **activation service URL is not configured** (or similar), your build may not include server settings for online activation. In that case use the [email-based `license.key`](#installing-a-license-key-file) method, or contact **support@moviolabs.com** with your Hardware ID and country.

---

## Requesting a licence (before you can activate or install a file)

### For @hfmdd.de users

If you have an `@hfmdd.de` email address:

1. Send an email to **support@moviolabs.com** from your `@hfmdd.de` account.
2. Your licence may be sent **automatically** via email (as a `license.key` file or with activation instructions), depending on current process.
3. Follow either [activation code](#activating-with-an-activation-code) or [license file](#installing-a-license-key-file) instructions below.

### For other users

1. Go to **Help** → **Request License...** in the application menu.
2. **Copy the email template** (it includes your Hardware ID and Country).
3. Send it to **support@moviolabs.com**.
4. Wait for either an **activation code** or a **`license.key`** attachment, then follow the matching section above.

The dialog includes:

- Your **Hardware ID (HWID)** — unique to this computer  
- Your **Country** — detected from system settings  

!!! note
    You can also email **support@moviolabs.com** directly; include your Hardware ID and country code if you do not use the template.

---

## Installing a license key file

Use this when you receive a **`license.key`** file (for example as an email attachment). You do **not** need to convert it manually: on first successful validation, the app can **migrate** the key into **`entitlement.json`**.

### Step 1: Receive the file

You should receive a file named **`license.key`**.

### Step 2: Save the file

1. Download the attachment.
2. Save it as **`license.key`** (exact name) in one of the locations below.
3. Restart the application.

### Step 3: Recommended location (Windows)

Persistent location (recommended — survives updates):

```
%APPDATA%\MVC_Calculator\license.key
```

*(Typically `C:\Users\YourName\AppData\Roaming\MVC_Calculator\license.key`.)*

To open the folder:

1. Press <kbd>Win</kbd> + <kbd>R</kbd>
2. Type: `%APPDATA%\MVC_Calculator`
3. Press <kbd>Enter</kbd>
4. Place **`license.key`** here

### Alternative locations

The application also discovers `license.key` in legacy locations (for example next to the executable or in a portable folder). For new installs, prefer the **recommended** path above.

### Linux

Use the persistent data area for your user, for example:

```
~/.local/share/MVC_Calculator/license.key
```

---

## Where your licence is stored

After activation or migration, the active credential is normally stored as **`entitlement.json`**:

| Platform | Typical path |
|----------|----------------|
| **Windows** | `%APPDATA%\MVC_Calculator\entitlement.json` |
| **Linux** | `~/.local/share/MVC_Calculator/entitlement.json` |

A legacy **`license.key`** in the same base folder may still be present; the app uses the entitlement record for validation once migration has occurred.

---

## Licence validation

### When things work

The application starts with no licence error, and licensed features are available.

### Common messages

**Entitlement / licence missing**  
The app could not find a valid entitlement or migratable `license.key`. Use **Help** → **Licence manager...** with an activation code, or install `license.key` as described above.

**Hardware mismatch**  
The licence is not valid for this computer (HWID does not match).

**Country mismatch**  
The licence was issued for a different country than the one detected on this machine.

**Expired licence**  
The licence has passed its expiration date.

**Wildcard / institutional rules**  
Some institutional keys are restricted (for example to `@hfmdd.de` email domains). If you see a message about domain or wildcard rules, contact your administrator or **support@moviolabs.com**.

---

## Troubleshooting licence issues

### Activation failed or “activation service not configured”

- Confirm you typed the activation code correctly.
- If the build cannot reach the activation service, use a **`license.key`** from support if available, or email **support@moviolabs.com** with your HWID and country.

### Licence file not found

1. Confirm the file is named exactly **`license.key`** (not `license.key.txt`).
2. Use the [recommended Windows path](#step-3-recommended-location-windows) or Linux path above.
3. Ensure you have permission to read the folder.
4. Restart the application after moving the file.

### Hardware ID mismatch

Licences are tied to hardware. For a new PC, request a new licence or activation code from support.

### Country mismatch

Possible causes: VPN, travel, or region settings. Try without VPN; if the issue persists, contact support with your actual country.

### Expired licence

Contact **support@moviolabs.com** for renewal.

---

## Licence transfer

**Generally:** Licences are hardware-locked and not casually transferable.

- **New computer:** Request a new licence or activation code.
- **Major hardware change:** May require a new licence — contact support.
- **Institutional / site licences:** Ask your administrator or support.

---

## Support

- **Email:** support@moviolabs.com  
- **Include:** Your email, exact error text, application version (from **About**), and steps you tried.

---

## Frequently asked questions

**Q: Should I use an activation code or a `license.key` file?**  
A: Use whichever support gave you. Both result in a validated entitlement once successful.

**Q: Can I use my licence on multiple computers?**  
A: Not with a standard single-machine licence. Ask support about multi-seat or institutional options.

**Q: What happens if I reinstall Windows?**  
A: If hardware is unchanged, your HWID may be the same; you may need to reinstall `license.key` or re-enter an activation code. Keep backups of your entitlement or key if your policy allows.

**Q: How long does a licence last?**  
A: Depends on the licence type (some are perpetual, others time-limited).

**Q: Can I share my licence with colleagues?**  
A: No — licences are issued for specific use as agreed with Moviolabs.
