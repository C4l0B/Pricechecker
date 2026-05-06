"""
Roblox Limited Item Price Monitor
==================================
Monitora se você continua sendo o menor preço (best price) de um item limitado
no catálogo do Roblox e notifica via webhook no Discord se alguém vender mais barato.
"""

import requests
import time
import os
from datetime import datetime

# ============================================================
# ⚙️  CONFIGURAÇÕES (lidas das variáveis de ambiente)
# ============================================================

ASSET_ID        = int(os.environ.get("ASSET_ID", "24112667"))
SEU_USER_ID     = int(os.environ.get("SEU_USER_ID", "393034516"))
SEU_USERNAME    = os.environ.get("SEU_USERNAME", "caiobfofo")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1501422989403492473/4Z1sjcl2-BXUMsXloo1QVYGm62gODw3ROcEsF2cf_eZ-PhRFzrJf_QKDw1hITDSJbI7M")
INTERVALO       = int(os.environ.get("INTERVALO_SEGUNDOS", "60"))

# ============================================================

ECONOMY_API = "https://economy.roblox.com"
CATALOG_API = "https://catalog.roblox.com"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_resellers(asset_id):
    try:
        r = requests.get(
            f"{ECONOMY_API}/v1/assets/{asset_id}/resellers?limit=10",
            timeout=10
        )
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"[{now()}] ⚠️  Erro ao buscar revendedores: {e}", flush=True)
        return None


def get_item_name(asset_id):
    try:
        r = requests.post(
            f"{CATALOG_API}/v1/catalog/items/details",
            json={"items": [{"itemType": "Asset", "id": asset_id}]},
            timeout=10
        )
        r.raise_for_status()
        items = r.json().get("data", [])
        if items:
            return items[0].get("name", f"Item #{asset_id}")
    except Exception:
        pass
    return f"Item #{asset_id}"


def send_discord_alert(item_name, best, asset_id):
    best_price       = best["price"]
    best_seller_name = best.get("seller", {}).get("name", "Desconhecido")
    item_url         = f"https://www.roblox.com/catalog/{asset_id}"

    embed = {
        "title": "🚨 Alguém listou mais barato que você!",
        "description": (
            f"**{item_name}** — você não é mais o best price!\n\n"
            f"**Menor preço atual:** {best_price:,} R$ — vendido por **{best_seller_name}**\n\n"
            f"[🔗 Ver no catálogo]({item_url})"
        ),
        "color": 0xFF4444,
        "footer": {"text": f"Roblox Price Monitor • {now()}"},
    }

    try:
        r = requests.post(DISCORD_WEBHOOK, json={
            "username": "Roblox Price Monitor",
            "embeds": [embed]
        }, timeout=10)
        if r.status_code == 204:
            print(f"[{now()}] ✅ Alerta enviado ao Discord!", flush=True)
        else:
            print(f"[{now()}] ⚠️  Discord status {r.status_code}: {r.text}", flush=True)
    except Exception as e:
        print(f"[{now()}] ❌ Falha ao enviar alerta: {e}", flush=True)


def send_discord_ok(item_name, best, asset_id):
    item_url = f"https://www.roblox.com/catalog/{asset_id}"
    embed = {
        "title": "✅ Você é o best price novamente!",
        "description": (
            f"**{item_name}** — seu listing de **{best['price']:,} R$** é o menor!\n\n"
            f"[🔗 Ver no catálogo]({item_url})"
        ),
        "color": 0x44FF88,
        "footer": {"text": f"Roblox Price Monitor • {now()}"},
    }
    try:
        requests.post(DISCORD_WEBHOOK, json={
            "username": "Roblox Price Monitor",
            "embeds": [embed]
        }, timeout=10)
    except Exception:
        pass


def main():
    print("=" * 55, flush=True)
    print("  🎮 Roblox Limited Price Monitor", flush=True)
    print("=" * 55, flush=True)

    item_name = get_item_name(ASSET_ID)

    print(f"  Item:     {item_name}", flush=True)
    print(f"  Asset ID: {ASSET_ID}", flush=True)
    print(f"  Usuário:  {SEU_USERNAME} (ID: {SEU_USER_ID})", flush=True)
    print(f"  Intervalo: {INTERVALO}s", flush=True)
    print("=" * 55, flush=True)
    print(f"[{now()}] 🚀 Monitoramento iniciado...\n", flush=True)

    i_am_best_price = True

    while True:
        resellers = get_resellers(ASSET_ID)

        if resellers is None:
            time.sleep(INTERVALO)
            continue

        if not resellers:
            print(f"[{now()}] ℹ️  Nenhum revendedor encontrado.", flush=True)
            time.sleep(INTERVALO)
            continue

        best           = resellers[0]
        best_seller_id = best.get("seller", {}).get("id")
        best_seller    = best.get("seller", {}).get("name", "?")
        best_price     = best["price"]

        sou_eu = (best_seller_id == SEU_USER_ID)

        if sou_eu:
            print(f"[{now()}] ✅ Você é o best price — {best_price:,} R$", flush=True)
            if not i_am_best_price:
                send_discord_ok(item_name, best, ASSET_ID)
            i_am_best_price = True
        else:
            print(f"[{now()}] 🚨 SUPERADO! {best_price:,} R$ por {best_seller}", flush=True)
            if i_am_best_price:
                send_discord_alert(item_name, best, ASSET_ID)
            i_am_best_price = False

        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
