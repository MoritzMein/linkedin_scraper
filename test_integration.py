import urllib.request
import json
import urllib.error
import time

# URL des FastAPI Servers
url = "http://127.0.0.1:8000/vernetzt_seit/"

# Liste von Profilen zum Testen (aus test.py übernommen)
profiles = [
    'https://www.linkedin.com/in/ute-schr%C3%B6der/',
    'https://www.linkedin.com/in/katrin-wollert/'
]

print(f"Teste Integration mit Endpoint: {url}")
print("Bitte stelle sicher, dass der Server läuft (uvicorn main:app --reload)\n")

for profile_url in profiles:
    data = {
        "profile_url": profile_url
    }

    # Daten in JSON konvertieren und encodieren
    json_data = json.dumps(data).encode('utf-8')

    # Request erstellen
    req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})

    print(f"--------------------------------------------------")
    print(f"Sende Request für Profil: {profile_url}")

    try:
        start_time = time.time()
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            duration = time.time() - start_time
            print(f"Dauer: {duration:.2f} Sekunden")
            print("Antwort vom Server:")
            
            # Formatiere JSON output schön
            try:
                parsed_json = json.loads(response_data)
                print(json.dumps(parsed_json, indent=4, ensure_ascii=False))
            except:
                print(response_data)
                
    except urllib.error.URLError as e:
        print(f"\nFehler bei der Verbindung: {e}")
        try:
             if e.code == 500:
                print("Server Error (500). Prüfe die Server-Logs auf Fehlermeldungen.")
                # Versuche Fehlerbody zu lesen
                print(e.read().decode('utf-8'))
        except:
            pass
        print("Läuft der Server? Starte ihn mit: uvicorn main:app --reload")

    print(f"--------------------------------------------------\n")
