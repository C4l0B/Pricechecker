"""
Roblox Limited Item Price Monitor
==================================
Monitora se você continua sendo o menor preço (best price) de um item limitado
no catálogo do Roblox e notifica via webhook no Discord se alguém vender mais barato.

Como usar:
1. pip install requests
2. Preencha as configurações abaixo
3. python roblox_price_monitor.py
"""

import requests
import time
import json
from datetime import datetime

# ============================================================
# ⚙️  CONFIGURAÇÕES — preencha aqui
# ============================================================

ASSET_ID = 0                          # ID do item no Roblox (aparece na URL do catálogo)
SEU_USERNAME = "SeuUsernameAqui"      # Seu username do Roblox
SEU_PRECO = 0                         # O preço que você listou o item (em Robux)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/SEU_WEBHOOK_AQUI"

# Intervalo de verificação em segundos (padrão: 60 segundos)
INTERVALO_SEGUNDOS = 60

# ============================================================
# 🔧  Lógica do bot — não precisa alterar abaixo
# ============================================================

ROBLOX_API_BASE = "https://economy.roblox.com"
CATALOG_API_BASE = "https://catalog.roblox.com"


def get_resellers(asset_id: int) -> list[dict] | None:
    """Busca a lista de revendedores do item."""
    url = f"{ROBLOX_API_BASE}/v1/assets/{asset_id}/resellers?limit=10&cursor="
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("data", [])
    except requests.RequestException as e:
        print(f"[{now()}] ⚠️  Erro ao buscar revendedores: {e}")
        return None


def get_item_name(asset_id: int) -> str:
    """Busca o nome do item no catálogo."""
    url = f"{CATALOG_API_BASE}/v1/catalog/items/details"
    payload = {"items": [{"itemType": "Asset", "id": asset_id}]}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", [])
        if items:
            return items[0].get("name", f"Item #{asset_id}")
    except Exception:
        pass
    return f"Item #{asset_id}"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def send_discord_alert(item_name: str, best_seller: dict, seu_preco: int, asset_id: int):
    """Envia uma notificação rica no Discord."""
    best_price = best_seller["price"]
    best_seller_name = best_seller.get("seller", {}).get("name", "Desconhecido")
    diferenca = seu_preco - best_price

    item_url = f"https://www.roblox.com/catalog/{asset_id}"
    thumbnail_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=150x150&format=Png&isCircular=false"

    embed = {
        "title": "🚨 Você perdeu o Best Price!",
        "description": (
            f"Alguém listou **{item_name}** mais barato que você!\n\n"
            f"**Menor preço atual:** R$ {best_price:,} (por **{best_seller_name}**)\n"
            f"**Seu preço:** R$ {seu_preco:,}\n"
            f"**Diferença:** R$ {diferenca:,} a menos\n\n"
            f"[🔗 Ver no catálogo]({item_url})"
        ),
        "color": 0xFF4444,
        "footer": {"text": f"Roblox Price Monitor • {now()}"},
        "thumbnail": {"url": thumbnail_url},
    }

    payload = {
        "username": "Roblox Price Monitor",
        "avatar_url": "https://images.rbxcdn.com/8c6db9a5f82a3e16b04b8baa39bb9498",
        "embeds": [embed],
    }

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code == 204:
            print(f"[{now()}] ✅ Alerta enviado ao Discord!")
        else:
            print(f"[{now()}] ⚠️  Discord retornou status {r.status_code}: {r.text}")
    except requests.RequestException as e:
        print(f"[{now()}] ❌ Falha ao enviar alerta: {e}")


def send_discord_ok(item_name: str, asset_id: int, seu_preco: int):
    """Envia notificação quando você volta a ser o best price."""
    item_url = f"https://www.roblox.com/catalog/{asset_id}"
    embed = {
        "title": "✅ Você voltou a ser o Best Price!",
        "description": (
            f"**{item_name}** — seu preço de **R$ {seu_preco:,}** é novamente o menor!\n\n"
            f"[🔗 Ver no catálogo]({item_url})"
        ),
        "color": 0x44FF88,
        "footer": {"text": f"Roblox Price Monitor • {now()}"},
    }
    payload = {"username": "Roblox Price Monitor", "embeds": [embed]}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    except Exception:
        pass


def validate_config():
    """Valida as configurações antes de iniciar."""
    errors = []
    if ASSET_ID == 0:
        errors.append("ASSET_ID não foi definido.")
    if SEU_USERNAME == "SeuUsernameAqui":
        errors.append("SEU_USERNAME não foi preenchido.")
    if SEU_PRECO == 0:
        errors.append("SEU_PRECO não foi definido.")
    if "SEU_WEBHOOK_AQUI" in DISCORD_WEBHOOK_URL:
        errors.append("DISCORD_WEBHOOK_URL não foi configurado.")
    if errors:
        print("❌ Erros de configuração:")
        for e in errors:
            print(f"   • {e}")
        print("\nEdite as variáveis na seção CONFIGURAÇÕES e tente novamente.")
        exit(1)


def main():
    validate_config()

    print("=" * 55)
    print("  🎮 Roblox Limited Price Monitor")
    print("=" * 55)

    item_name = get_item_name(ASSET_ID)
    print(f"  Item:      {item_name}")
    print(f"  Asset ID:  {ASSET_ID}")
    print(f"  Usuário:   {SEU_USERNAME}")
    print(f"  Seu preço: R$ {SEU_PRECO:,}")
    print(f"  Intervalo: {INTERVALO_SEGUNDOS}s")
    print("=" * 55)
    print(f"[{now()}] 🚀 Monitoramento iniciado...\n")

    was_best_price = True  # Assume que começa como best price

    while True:
        resellers = get_resellers(ASSET_ID)

        if resellers is None:
            # Erro na API, tenta novamente no próximo ciclo
            time.sleep(INTERVALO_SEGUNDOS)
            continue

        if not resellers:
            print(f"[{now()}] ℹ️  Nenhum revendedor encontrado (item pode estar fora de venda).")
            time.sleep(INTERVALO_SEGUNDOS)
            continue

        # O primeiro da lista é sempre o menor preço
        best = resellers[0]
        best_price = best["price"]
        best_seller_name = best.get("seller", {}).get("name", "?")

        is_best_price = best_price >= SEU_PRECO

        if is_best_price:
            status = "✅ Você é o best price"
            if not was_best_price:
                # Voltou a ser best price — notifica o Discord
                send_discord_ok(item_name, ASSET_ID, SEU_PRECO)
        else:
            status = f"🚨 SUPERADO! Menor: R${best_price:,} por {best_seller_name}"
            if was_best_price:
                # Acabou de perder o best price — notifica imediatamente
                send_discord_alert(item_name, best, SEU_PRECO, ASSET_ID)

        print(f"[{now()}] {status}")
        was_best_price = is_best_price

        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
