# Product Key Distribution Bot

A Discord bot designed for automating product key fulfillment and customer support in digital goods communities.  
Originally developed as a freelance project for a small startup offering random software/game key bundles.

---

## 🚀 Features

- `/claim` — customers claim roles after providing valid order IDs  
- `/redeemkey` — users receive product keys directly via DM  
- `/replace` — staff can request account replacements, with admin approval flow  
- `/reward` — eligible users can redeem a bonus key  
- `/order` — staff can look up paid order info  
- `/note` + `/notes` — internal notes system per order  
- `loadkeys` / `pullkeys` — staff tools to manage inventory  
- `/shutdown`, `/card`, `/i` — utility/admin commands  
- Full PostgreSQL support with async queries  
- Secure role-based permission system

---

## 📦 Setup

### Requirements

- Python 3.10+
- PostgreSQL database

### 1. Clone the Repo

```bash
git clone https://github.com/BoiOG/key-automation-bot.git
cd key-automation-bot
