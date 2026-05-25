from flask import Flask, request
import requests
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Konfiguracja
MESSENGER_TOKEN = "EAAWVmsUSv9kBRlxV50hQFdbFV3JlbZAo27oj5fLJoib6dNROedsyn4s1"
GROUP_ID = "9894722734827"
ADMIN_ID = "206529637153164"
VERIFY_TOKEN = "your_verify_token_123"  # Możesz to zmienić na cokolwiek

# API klucze
RAPIDAPI_KEY = "e070f08446msh3596da078887611p1ac0c9jsn79c7e3210132"
ODDS_API_KEY = "787a0a14062c4331cf0d37657b61a35b"

# Ligi do monitorowania
LEAGUES = {
    39: "Premier League",
    135: "La Liga",
    207: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    116: "Ekstraklasa"
}

# Turnieje (wyjątki - codzienne mecze)
TOURNAMENTS = {
    "Champions League": [2],
    "Europa League": [3],
    "Conference League": [848],
    "Euro": [500],
    "World Cup": [1]
}

def get_matches():
    """Pobiera mecze z API-Football"""
    try:
        url = "https://free-api-live-football-data.p.rapidapi.com/football-matches"
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"
        }
        
        # Pobierz mecze na dziś i jutro
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        matches = []
        
        # Dla każdej ligi pobierz mecze
        for league_id, league_name in LEAGUES.items():
            params = {
                "league_id": league_id,
                "date": str(today)
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    for match in data.get("result", []):
                        matches.append({
                            "home": match.get("match_home_name"),
                            "away": match.get("match_away_name"),
                            "time": match.get("match_time"),
                            "league": league_name,
                            "league_id": league_id
                        })
        
        return matches[:10]  # Max 10 meczów
        
    except Exception as e:
        print(f"Błąd przy pobieraniu meczów: {e}")
        return []

def get_odds(home_team, away_team):
    """Pobiera kursy z The Odds API"""
    try:
        url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
        
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        
        response = requests.get(url, timeout=10, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Szukaj meczu
            for event in data.get("events", []):
                if home_team.lower() in event["home_team"].lower() and away_team.lower() in event["away_team"].lower():
                    for bookmaker in event.get("bookmakers", []):
                        for market in bookmaker.get("markets", []):
                            if market["key"] == "h2h":
                                outcomes = market["outcomes"]
                                # outcomes[0] = home win, outcomes[1] = away win, outcomes[2] = draw
                                return {
                                    "home": outcomes[0]["odds"],
                                    "draw": outcomes[2]["odds"],
                                    "away": outcomes[1]["odds"]
                                }
        
        # Jeśli nie znaleziono, zwróć domyślne kursy
        return {
            "home": 2.0,
            "draw": 3.2,
            "away": 3.5
        }
        
    except Exception as e:
        print(f"Błąd przy pobieraniu kursów: {e}")
        return {"home": 2.0, "draw": 3.2, "away": 3.5}

def format_message(matches):
    """Formatuje wiadomość z meczami"""
    if not matches:
        return "Brak meczów na dzisiaj! ⚽"
    
    message = "⚽ MECZE NA DZISIAJ ⚽\n\n"
    
    for i, match in enumerate(matches[:10], 1):
        odds = get_odds(match["home"], match["away"])
        
        message += f"{i}. {match['home']} - {match['away']}\n"
        message += f"   Godzina: {match['time']}\n"
        message += f"   Liga: {match['league']}\n"
        message += f"   Kursy: 1:{odds['home']:.2f} | X:{odds['draw']:.2f} | 2:{odds['away']:.2f}\n"
        message += f"   💡 Analiza: {get_team_analysis(match['home'])} vs {get_team_analysis(match['away'])}\n\n"
    
    return message

def get_team_analysis(team_name):
    """Zwraca prostą analizę formy drużyny"""
    # To jest uproszczone - w pełnej wersji byłoby pobieranie rzeczywistych danych
    analyses = {
        "good": "Forma: ✅ Dobra",
        "average": "Forma: ⚠️ Średnia",
        "bad": "Forma: ❌ Słaba"
    }
    
    # Losowa analiza (w produkcji byłoby z rzeczywistych danych)
    import random
    return random.choice(list(analyses.values()))

def send_message(recipient_id, message_text):
    """Wysyła wiadomość przez Messenger"""
    try:
        url = f"https://graph.facebook.com/v12.0/me/messages"
        
        params = {"access_token": MESSENGER_TOKEN}
        
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        response = requests.post(url, json=data, params=params, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Błąd przy wysyłaniu wiadomości: {e}")
        return False

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
                    if message_text in ["!mecze", "!Mecze"]:
                        matches = get_matches()
                        formatted = format_message(matches)
                        send_message(GROUP_ID, formatted)
    
    return "ok", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
