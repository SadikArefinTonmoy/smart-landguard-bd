# Smart LandGuard BD 2.0 — Full Fresh Package (2026)

**Start with `START_HERE_FRESH_PROJECT_BN.txt`** (Bangla).

Run from project root in Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\START_HERE_WINDOWS.ps1
```

Then, in two **separate terminals**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_Backend.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_Frontend.ps1
```

Site: http://localhost:4173 — API: http://localhost:8000/api/health

The safe setup checks whether an **existing Docker PostgreSQL database** should be preserved, and will not delete old volumes or rewrite present `.env` files. If an encryption key is missing but encrypted documents still exist, setup refuses to create a new key. For old accounts on the selected database, reuse the existing login; new accounts are not copied from other databases.

This is a synthetic demo platform, **not connected to Bangladesh government records** or approved for production use.

Original engineering documentation remains under `docs/`.

## Phase 7 — Buyer view and multi-device LAN demo

This is a **non-government, synthetic-data prototype**. See `PHASE7_FINAL_LAN_SETUP_BN.txt` for the full Bengali setup guide. For multi-device access on a trusted Windows Private Wi-Fi network, first preserve existing `.env` files and make sure the existing Docker PostgreSQL container is running. From the main PC, stop earlier local servers and run `powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_LAN.ps1`. Open the displayed `http://<MAIN_PC_LAN_IP>:4173` URL on another device. Flask/PostgreSQL remain loopback-only behind Vite's same-origin `/api` proxy. The launcher sets the exact LAN origin for CSRF checking in its child server processes. If Private Windows Firewall blocks port 4173, the owner can explicitly opt into the subnet-limited rule using an elevated PowerShell with `-AddFirewallRule`. Never port-forward this application or use real sensitive documents over LAN HTTP.

For an **existing working installation**, prefer `APPLY_PHASE7_TO_EXISTING.ps1 -ExistingProject "D:\\land2\\Smart_LandGuard_BD_2.0"` from a **separately extracted** new ZIP. This copies only whitelisted source files and preserves root/backend `.env`, the Python virtual environment, encrypted document storage and existing Docker volumes.
