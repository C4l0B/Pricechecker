"""
Roblox Limited Price Monitor
==============================
Lógica simples: compara o menor preço do catálogo com o seu preço.
Se alguém listar abaixo do seu preço → notifica no Discord.
Não depende de seller ID.
"""

import requests
import time
import os
from datetime import datetime

# ============================================================
# ⚙️  CONFIGURAÇÕES (lidas das variáveis de ambiente)
# ============================================================

ASSET_ID        = int(os.environ.get("ASSET_ID", "24112667"))
SEU_PRECO       = int(os.environ.get("SEU_PRECO", "889999"))
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
        return data.get("CollectibleItemId"), data.get("Name", f"Item #{asset_id}")
    except Exception as e:
        print(f"[{now()}] ⚠️  Erro ao buscar detalhes: {e}", flush=True)
        return None, f"Item #{asset_id}"


def get_lowest_price(collectible_id):
    url = f"{MARKETPLACE_API}/v1/item/{collectible_id}/resellers?limit=10"
    try:
        r = requests.get(url, headers=get_auth_headers(), timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None, None
        best = data[0]
        return best.get("price"), best.get("sellerName", "Desconhecido")
    except Exception as e:
        print(f"[{now()}] ⚠️  Erro ao buscar revendedores: {e}", flush=True)
        return None, None


def send_discord_alert(item_name, menor_preco, seller_name, asset_id):
    item_url   = f"https://www.roblox.com/catalog/{asset_id}"
    diferenca  = SEU_PRECO - menor_preco
    embed = {
        "title": "🚨 Você foi superado no preço!",
        "description": (
            f"**{item_name}** — alguém listou mais barato!\n\n"
            f"**Menor preço atual:** {menor_preco:,} R$ — vendido por **{seller_name}**\n"
            f"**Seu preço:** {SEU_PRECO:,} R$\n"
            f"**Diferença:** {diferenca:,} R$\n\n"
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


def send_discord_ok(item_name, menor_preco, asset_id):
    item_url = f"https://www.roblox.com/catalog/{asset_id}"
    embed = {
        "title": "✅ Você é o best price novamente!",
        "description": (
            f"**{item_name}** — menor preço atual: **{menor_preco:,} R$**\n"
            f"Seu preço de **{SEU_PRECO:,} R$** é o menor!\n\n"
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
    print(f"  Usuário:        {SEU_USERNAME}", flush=True)
    print(f"  Seu preço:      {SEU_PRECO:,} R$", flush=True)
    print(f"  Intervalo:      {INTERVALO}s", flush=True)
    print(f"  Cookie:         {'✅ definido' if ROBLOSECURITY else '❌ ausente'}", flush=True)
    print("=" * 55, flush=True)
    print(f"[{now()}] 🚀 Monitoramento iniciado...\n", flush=True)

    i_am_best_price = None  # None = primeira checagem

    while True:
        menor_preco, seller_name = get_lowest_price(collectible_id)

        if menor_preco is None:
            time.sleep(INTERVALO)
            continue

        sou_eu = (menor_preco >= SEU_PRECO)

        if sou_eu:
            print(f"[{now()}] ✅ Você é o best price — menor preço: {menor_preco:,} R$", flush=True)
            if i_am_best_price is False:
                send_discord_ok(item_name, menor_preco, ASSET_ID)
            i_am_best_price = True
        else:
            print(f"[{now()}] 🚨 SUPERADO! Menor preço: {menor_preco:,} R$ por {seller_name}", flush=True)
            # Notifica sempre que o preço mudar ou for a primeira checagem
            if i_am_best_price is True or i_am_best_price is None:
                send_discord_alert(item_name, menor_preco, seller_name, ASSET_ID)
            i_am_best_price = False

        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
