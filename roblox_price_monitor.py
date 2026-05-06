"""
Roblox Limited Price Monitor
==============================
Funciona com limiteds clássicos E UGC limiteds.
"""

import requests
import time
import os
from datetime import datetime

# ============================================================
# ⚙️  CONFIGURAÇÕES (lidas das variáveis de ambiente)
# ============================================================

ASSET_ID        = int(os.environ.get("ASSET_ID", "24112667"))
SEU_USER_ID     = str(os.environ.get("SEU_USER_ID", "393034516"))
SEU_USERNAME    = os.environ.get("SEU_USERNAME", "caiobfofo")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1501422989403492473/4Z1sjcl2-BXUMsXloo1QVYGm62gODw3ROcEsF2cf_eZ-PhRFzrJf_QKDw1hITDSJbI7M")
ROBLOSECURITY   = os.environ.get("ROBLOSECURITY", "")
INTERVALO       = int(os.environ.get("INTERVALO_SEGUNDOS", "60"))

# ============================================================

ECONOMY_API     = "https://economy.roblox.com"
MARKETPLACE_API = "https://apis.roblox.com/marketplace-sales"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_auth_headers():
    return {"Cookie": f".ROBLOSECURITY={ROBLOSECURITY}"}


def get_collectible_id_and_name(asset_id):
    url = f"{ECONOMY_API}/v2/assets/{asset_id}/details"
    try:
        r = requests.get(url, headers=get_auth_headers(), timeout=10)
        r.raise_for_status()
        data = r.json()
        collectible_id = data.get("CollectibleItemId")
        item_name      = data.get("Name", f"Item #{asset_id}")
        return collectible_id, item_name
    except Exception as e:
        print(f"[{now()}] ⚠️  Erro ao buscar detalhes do item: {e}", flush=True)
        return None, f"Item #{asset_id}"


def get_resellers(collectible_id):
    url = f"{MARKETPLACE_API}/v1/item/{collectible_id}/resellers?limit=10"
    try:
        r = requests.get(url, headers=get_auth_headers(), timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"[{now()}] ⚠️  Erro ao buscar revendedores: {e}", flush=True)
        return None


def get_username(user_id):
    """Busca o username pelo userId para exibir no log."""
    try:
        r = requests.get(f"https://users.roblox.com/v1/users/{user_id}", timeout=5)
        return r.json().get("name", str(user_id))
    except Exception:
        return str(user_id)


def send_discord_alert(item_name, best, asset_id):
    best_price       = best.get("price", "?")
    best_seller_name = best.get("sellerName", best.get("sellerId", "Desconhecido"))
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
            f"**{item_name}** — seu listing de **{best.get('price', '?'):,} R$** é o menor!\n\n"
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
        print(f"[{now()}] ✅ Confirmação de best price enviada ao Discord!", flush=True)
    except Exception as e:
        print(f"[{now()}] ❌ Falha ao enviar confirmação: {e}", flush=True)


def main():
    print("=" * 55, flush=True)
    print("  🎮 Roblox Limited Price Monitor", flush=True)
    print("=" * 55, flush=True)

    collectible_id, item_name = get_collectible_id_and_name(ASSET_ID)

    if not collectible_id:
        print(f"[{now()}] ❌ Não foi possível obter o collectibleItemId.", flush=True)
        return

    print(f"  Item:           {item_name}", flush=True)
    print(f"  Asset ID:       {ASSET_ID}", flush=True)
    print(f"  Collectible ID: {collectible_id}", flush=True)
    print(f"  Usuário:        {SEU_USERNAME} (ID: {SEU_USER_ID})", flush=True)
    print(f"  Intervalo:      {INTERVALO}s", flush=True)
    print(f"  Cookie:         {'✅ definido' if ROBLOSECURITY else '❌ ausente'}", flush=True)
    print("=" * 55, flush=True)
    print(f"[{now()}] 🚀 Monitoramento iniciado...\n", flush=True)

    i_am_best_price = None

    while True:
        resellers = get_resellers(collectible_id)

        if resellers is None:
            time.sleep(INTERVALO)
            continue

        if not resellers:
            print(f"[{now()}] ℹ️  Nenhum revendedor encontrado.", flush=True)
            time.sleep(INTERVALO)
            continue

        best        = resellers[0]
        # O campo correto confirmado pelo debug é "sellerId" na raiz do objeto
        seller_id   = str(best.get("sellerId", ""))
        seller_name = best.get("sellerName", seller_id)
        best_price  = best.get("price", 0)

        sou_eu = (seller_id == SEU_USER_ID)

        if sou_eu:
            print(f"[{now()}] ✅ Você é o best price — {best_price:,} R$", flush=True)
            if i_am_best_price is False:
                send_discord_ok(item_name, best, ASSET_ID)
            i_am_best_price = True
        else:
            print(f"[{now()}] 🚨 SUPERADO! {best_price:,} R$ por {seller_name} (ID: {seller_id})", flush=True)
            if i_am_best_price is True or i_am_best_price is None:
                send_discord_alert(item_name, best, ASSET_ID)
            i_am_best_price = False

        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
