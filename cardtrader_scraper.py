import requests
import sys

# INSERISCI QUI IL TUO NUOVO TOKEN (Non condividerlo mai!)
AUTH_TOKEN = "INSERISCI QUI IL TUO TOKEN CARDTRADER(PROFILO -> IMPOSTAZIONI -> APIs -> COPIA NEGLI APPUNTI)"

HEADERS = {
    "Authorization" : f"Bearer {AUTH_TOKEN}" # CORRETTO: Aggiunta la 'h'
}

BASE_URL = "https://api.cardtrader.com/api/v2"

def main():
    # Chiediamo input (ricordiamo all'utente di usare l'inglese)
    target_expansion = str(input("Inserisci l'espansione che stai cercando (in INGLESE, es: 'Paldean Fates'): ")).strip()
    target_pokemon = str(input("Inserisci il Pokemon che stai cercando (es: 'Umbreon ex'): ")).strip()
    target_lang = str(input("Inserisci La lingua della carta(es. it, en, jp...): ")).strip()
    target_condition = str(input("Inserisci le condizioni(es. near mint, slightly played, moderately played, played, poor): ")).strip()

    print(f"\nCerco l'espansione '{target_expansion}'...")

    expansion_response = requests.get(f"{BASE_URL}/expansions", headers=HEADERS)

    if expansion_response.status_code != 200:
        print(f"Errore nel recupero dell'espansione. Codice: {expansion_response.status_code}. Controlla il tuo token.")
        sys.exit(1)

    expansions = expansion_response.json()
    
    # Cerca l'ID dell'espansione confrontando i nomi in minuscolo
    expansion_id = next((exp["id"] for exp in expansions if exp["name"].lower() == target_expansion.lower()), None)
    
    if not expansion_id:
        print(f"Errore: L'espansione '{target_expansion}' non è stata trovata. Sicuro sia il nome in inglese corretto?")
        sys.exit(1)

    print(f"Espansione trovata! ID : {expansion_id}")
    print("Recupero i blueprint dell'espansione per filtrare le carte richieste...")

    blueprints_response = requests.get(f"{BASE_URL}/blueprints/export?expansion_id={expansion_id}", headers=HEADERS)
    blueprints = blueprints_response.json()

    target_blueprints = {}

    for bp in blueprints:
        name = bp.get("name", "").lower()
        version = bp.get("version", "")
        
        # CORRETTO: Verifichiamo direttamente se il nome inserito è contenuto nel nome della carta
        is_target_pokemon = target_pokemon.lower() in name

        if is_target_pokemon:
            bp_id_str = str(bp["id"])
            full_name = f"{bp.get('name')} {version}".strip()
            target_blueprints[bp_id_str] = full_name
    
    if not target_blueprints:
        print(f"Nessuna carta di '{target_pokemon}' trovata in questa espansione.")
        return
    
    print(f"Trovate {len(target_blueprints)} versioni/carte. Recupero i prezzi sul marketplace...\n")

    market_response = requests.get(
        f"{BASE_URL}/marketplace/products", headers=HEADERS,
        params={"expansion_id": expansion_id}
    )

    market_data = market_response.json()

    print("-" * 80)
    print(f"{'CARTA':<45} | PREZZO MIN (EN + NM + CT ZERO)")
    print("-" * 80)

    for bp_id, card_name in target_blueprints.items():
        products_list = market_data.get(bp_id, [])
        valid_products = []

        for product in products_list:
            props = product.get("properties_hash", {})

            is_language = False
            is_condition = False
            is_ct_zero = product.get("user", {}).get("can_sell_via_hub", False)

            for key, value in props.items():
                # CORRETTO: Aggiunte le parentesi a lower() -> lower()
                if "language" in key.lower() and str(value).lower() == target_lang:
                    is_language = True
                if "condition" in key.lower() and str(value).lower() == target_condition:
                    is_condition = True
            
            # CORRETTO: Questo blocco va FUORI dal ciclo for che analizza le properties
            if is_language and is_condition and is_ct_zero:
                valid_products.append(product)

        if not valid_products:
            print(f"{card_name:<45} | N/A (Nessuna copia adatta trovata)")
            continue

        cheapest_product = min(valid_products, key=lambda p: p["price"]["cents"])

        price_cents = cheapest_product["price"]["cents"]
        currency = cheapest_product["price"]["currency"]
        formatted_price = f"{price_cents / 100:.2f} {currency}"

        print(f"{card_name:<45} | {formatted_price}")
        
if __name__ == "__main__":
    if AUTH_TOKEN == "INSERISCI_IL_TUO_NUOVO_TOKEN_QUI":
        print("ATTENZIONE: Ricordati di inserire il tuo AUTH_TOKEN aggiornato nello script!")
        sys.exit(1)
        
    main()