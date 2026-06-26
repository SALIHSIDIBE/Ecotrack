import paho.mqtt.client as mqtt
import json
import random
import time

# Added version compatibility for modern paho-mqtt
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.connect("10.10.4.12", 1883, 60)
client.loop_start()  # Starts background networking

POUBELLES = {
    "ECO-BAT-0001": "Zone Commerciale Sud",
    "ECO-BAT-0002": "Zone Résidentielle Nord",
    "ECO-BAT-0003": "Zone Résidentielle Est",
    "ECO-BAT-0004": "Zone Résidentielle Ouest",
    "ECO-BAT-0005": "Parc Municipal",
    "ECO-BAT-0006": "Quartier Gare",
    "ECO-BAT-0007": "Centre Ville",
    "ECO-BAT-0008": "Quartier Gare"
}

while True:
    print("\n=== STARTING NEW TRANSMISSION CYCLE ===")
    
    for poubelle, secteur in POUBELLES.items():
        data = {
            "poubelle_id": poubelle,
            "secteur": secteur,
            "remplissage": random.randint(40, 100),
            "temperature": round(random.uniform(18, 40), 2),
            "poids": round(random.uniform(20, 150), 2),
            "humidite": round(random.uniform(30, 90), 2),
            "batterie": random.randint(60, 100)
        }

        # Send to MQTT
        client.publish("ville/dechets", json.dumps(data))
        
        # This will now print ALL 8 individual data packets to your console
        print(data)
        
        # Tiny break to keep the network happy
        time.sleep(0.1)

    print("=== Cycle terminé, waiting 60 seconds ===\n")
    time.sleep(60)