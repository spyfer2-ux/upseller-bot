import os
import json
import time
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "spyfer2-ux/upseller-bot"
COMMANDS_FILE = "commands.json"
STATUS_FILE = "status.json"
GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_file(filename):
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{filename}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        import base64
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    return None, None

def update_file(filename, content, sha, message="update"):
    import base64
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{filename}"
    body = json.dumps(content, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(body.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded, "sha": sha}
    r = requests.put(url, headers=HEADERS, json=payload)
    return r.status_code in [200, 201]

def send_message(text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json().get("result", [])
    except:
        return []

def handle_iniciar():
    cmd, sha = get_file(COMMANDS_FILE)
    if cmd:
        cmd["command"] = "iniciar"
        cmd["timestamp"] = datetime.now().isoformat()
        update_file(COMMANDS_FILE, cmd, sha, "comando: iniciar")
    send_message("▶️ *Comando INICIAR enviado!*\n\nO Claude vai começar a processar os produtos em breve.")

def handle_pausar():
    cmd, sha = get_file(COMMANDS_FILE)
    if cmd:
        cmd["command"] = "pausar"
        cmd["timestamp"] = datetime.now().isoformat()
        update_file(COMMANDS_FILE, cmd, sha, "comando: pausar")
    send_message("⏸️ *Comando PAUSAR enviado!*")

def handle_parar():
    cmd, sha = get_file(COMMANDS_FILE)
    if cmd:
        cmd["command"] = "parar"
        cmd["timestamp"] = datetime.now().isoformat()
        update_file(COMMANDS_FILE, cmd, sha, "comando: parar")
    send_message("🛑 *Comando PARAR enviado!*")

def handle_status():
    status, _ = get_file(STATUS_FILE)
    if status:
        state_emoji = {"idle": "💤", "running": "⚙️", "paused": "⏸️", "stopped": "🛑"}.get(status.get("state","idle"),"❓")
        msg = f"""📊 *STATUS DO PROCESSO*

{state_emoji} Estado: *{status.get('state','idle').upper()}*
✅ Publicados: *{status.get('processed',0)}*
⏭️ Pulados: *{status.get('skipped',0)}*
❌ Erros: *{status.get('failed',0)}*
📋 Na fila: *{status.get('total_in_list',0)}*
🔄 Produto atual: *{status.get('current_product','-')}*
🕐 Última atualização: *{status.get('last_update','-')}*"""
        send_message(msg)
    else:
        send_message("❌ Não foi possível ler o status.")

def handle_lista():
    status, _ = get_file(STATUS_FILE)
    if status and status.get("log"):
        logs = status["log"][-10:]
        msg = "📋 *ÚLTIMAS 10 AÇÕES:*\n\n" + "\n".join(f"• {e}" for e in logs)
        send_message(msg)
    else:
        send_message("📋 Nenhuma ação registrada ainda.")

def handle_atualizar():
    cmd, sha = get_file(COMMANDS_FILE)
    if cmd:
        cmd["command"] = "atualizar"
        cmd["timestamp"] = datetime.now().isoformat()
        update_file(COMMANDS_FILE, cmd, sha, "comando: atualizar")
    send_message("🔄 *Comando ATUALIZAR enviado!*")

def handle_ajuda():
    msg = """🤖 *UPSELLER BOT — COMANDOS*

▶️ /iniciar — Inicia o processo de publicação
⏸️ /pausar — Pausa após o produto atual
🛑 /parar — Para o processo
🔄 /atualizar — Busca novos produtos
📊 /status — Ver estatísticas
📋 /lista — Ver últimas 10 ações
❓ /ajuda — Ver esta mensagem"""
    send_message(msg)

def main():
    print("🤖 UpSeller Bot iniciado!")
    send_message("🤖 *UpSeller Bot online!*\n\nDigite /ajuda para ver os comandos.")
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            text = msg.get("text", "").strip().lower()
            chat_id = str(msg.get("chat", {}).get("id", ""))
            if chat_id != str(CHAT_ID):
                continue
            if text in ["/iniciar", "/start"]:
                handle_iniciar()
            elif text == "/pausar":
                handle_pausar()
            elif text == "/parar":
                handle_parar()
            elif text == "/status":
                handle_status()
            elif text == "/lista":
                handle_lista()
            elif text == "/atualizar":
                handle_atualizar()
            elif text in ["/ajuda", "/help"]:
                handle_ajuda()
        time.sleep(1)

if __name__ == "__main__":
    main()
