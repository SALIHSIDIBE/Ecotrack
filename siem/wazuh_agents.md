# Wazuh SIEM — Déploiement agents et règles MITRE ATT&CK

## Architecture agent-manager

```
Toutes les VMs / Conteneurs
    │ (agent Wazuh léger)
    │ chiffré port 1514/1515
    ▼
ECO-SEC (10.10.3.10) — Wazuh Manager
    │
    ├── Elasticsearch (indexation des alertes)
    ├── Kibana (visualisation)
    └── API VirusTotal (enrichissement CTI)
```

---

## Machines couvertes par les agents

| Machine | IP | Fonctions surveillées |
|---|---|---|
| ECO-PROXY | 10.10.1.10 | Logs Nginx, ModSecurity, HAProxy |
| ECO-LB-02 | 10.10.1.11 | Logs Nginx, HAProxy, Keepalived |
| ECO-APP | 10.10.2.20 | Logs applicatifs, accès API |
| ECO-DB | 10.10.2.30 | Logs PostgreSQL, Patroni |
| ECO-DB-02 | 10.10.2.31 | Logs réplication PostgreSQL |
| ECO-SEC | 10.10.3.10 | Auto-surveillance Wazuh manager |
| ECO-MON | 10.10.3.11 | Logs Prometheus, Grafana |
| IoT-MQTT | 10.10.4.x | Logs Mosquitto, scripts ingestion |

---

## Fonctionnalités déployées

### File Integrity Monitoring (FIM)
Surveillance en temps réel de l'intégrité des fichiers critiques :

```xml
<!-- ossec.conf — extrait FIM -->
<syscheck>
  <frequency>300</frequency>
  <directories check_all="yes">/etc/ssh/sshd_config</directories>
  <directories check_all="yes">/etc/nginx/</directories>
  <directories check_all="yes">/etc/postgresql/</directories>
  <directories check_all="yes">/etc/openvpn/</directories>
  <directories check_all="yes">/usr/bin,/usr/sbin</directories>
</syscheck>
```

Toute modification non autorisée déclenche une alerte immédiate dans Kibana.

### Détection d'anomalies SSH
```xml
<!-- Règle custom : détection force brute SSH -->
<rule id="100001" level="10">
  <if_matched_sid>5710</if_matched_sid>
  <same_source_ip />
  <description>Brute force SSH détecté</description>
  <mitre>
    <id>T1110</id>  <!-- Brute Force -->
  </mitre>
</rule>
```

### Enrichissement CTI (VirusTotal)
En cas de détection d'un fichier suspect ou d'un IOC :
- Wazuh interroge automatiquement l'**API VirusTotal**
- Qualification de la menace (hash, IP, URL malveillants)
- Résultat indexé dans Elasticsearch et visible dans Kibana

---

## Règles MITRE ATT&CK couvertes

| Technique MITRE | ID | Détection Wazuh |
|---|---|---|
| Brute Force | T1110 | Échecs auth SSH répétés |
| Valid Accounts | T1078 | Connexions hors horaires |
| File and Directory Discovery | T1083 | Accès fichiers sensibles |
| Modify Authentication Process | T1556 | Modification sshd_config |
| Data Exfiltration | T1041 | Flux sortants anormaux |
| Rootkit | T1014 | Scan rootcheck Wazuh |

---

## Alertes et seuils configurés

| Événement | Seuil | Action |
|---|---|---|
| Échecs SSH | 3 tentatives / 10 min | Alerte niveau 10 + Fail2ban ban 24h |
| Modification fichier critique | Immédiat | Alerte niveau 12 |
| CPU > 85% pendant 5 min | Seuil Grafana | Alerte équipe |
| Taux erreur API > 2% | Seuil Prometheus | Alerte équipe |
| IOC détecté VirusTotal | Immédiat | Alerte critique niveau 15 |

---

## Commandes utiles

```bash
# Vérifier le statut des agents sur le manager
/var/ossec/bin/agent_control -l

# Voir les alertes en temps réel
tail -f /var/ossec/logs/alerts/alerts.log

# Vérifier la connexion agent → manager
/var/ossec/bin/agent_control -i <agent_id>

# Forcer un scan FIM immédiat
/var/ossec/bin/agent_control -r -u <agent_id>
```
