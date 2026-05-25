import os
from flask import Flask, request

app = Flask(__name__)

# Konfiguracja
MESSENGER_TOKEN = "EAAWVmsUSv9kBRlxV50hQFdbFV3JlbZAo27oj5fLJoib6dNROedsyn4s1"
GROUP_ID = "9894722734827"
ADMIN_ID = "206529637153164"
VERIFY_TOKEN = "football_bot_verify_123"

@app.route('/webhook', methods=['GET'])
def verify():
    """Webhook verification z Messengera"""
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args["hub.challenge"]
    return "OK", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Odbiera wiadomości z Messengera"""
    data = request.get_json()
    
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]
                
                # Sprawdź czy to admin
                if sender_id != ADMIN_ID:
                    continue
                
                # Sprawdź czy to wiadomość
                if messaging_event.get("message"):
                    message_text = messaging_event["message"].get("text", "").lower()
                    
                    # Sprawdź komendę
                    if "!mecze" in message_text or "!mecze" in message_text.lower():
                        send_message(GROUP_ID, "⚽ MECZE NA DZISIAJ ⚽\n\n1. Arsenal - Manchester City\n   Godzina: 20:45\n   Kursy: 1:2.80 | X:3.20 | 2:2.50\n   Forma: Arsenal w dobrej kondycji\n\n2. Liverpool - Chelsea\n   Godzina: 18:00\n   Kursy: 1:1.85 | X:3.50 | 2:4.20\n   Forma: Liverpool dominuje\n\n3. Manchester United - Tottenham\n   Godzina: 17:30\n   Kursy: 1:2.10 | X:3.40 | 2:3.30\n   Forma: Wyrównane szanse")
    
    return "ok", 200

def send_message(recipient_id, message_text):
    """Wysyła wiadomość przez Messenger"""
    import requests
    try:
        url = "https://graph.facebook.com/v12.0/me/messages"
        params = {"access_token": MESSENGER_TOKEN}
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        response = requests.post(url, json=data, params=params, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Błąd: {e}")
        return False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
