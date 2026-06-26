import json
import paho.mqtt.client as mqtt
import psycopg2

conn = psycopg2.connect(
    host="10.10.2.30",
    database="smartwaste",
    user="postgres",
    password="motdepasse"
)

cur = conn.cursor()

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        cur.execute("""
            UPDATE capteurs 
            SET 
                secteur = %s,
                remplissage = %s,
                temperature = %s,
                poids = %s,
                humidite = %s,
                batterie = %s,
                date_mesure = NOW()
            WHERE poubelle_id = %s
        """,
        (
            data["secteur"],
            data["remplissage"],
            data["temperature"],
            data["poids"],
            data["humidite"],
            data["batterie"],
            data["poubelle_id"]
        ))

        conn.commit()
        print(f" [✓] Mise a jour des data en temps reel pour: {data['poubelle_id']} ({data['secteur']})")
        
    except Exception as e:
        print(f" [X] Erreur de traitement: {e}")
        conn.rollback()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_message = on_message

client.connect("10.10.4.11", 1883)

client.subscribe("ville/dechets")

print("En ecoute des messages MQTT et mise a jour de notre DB...")
client.loop_forever()