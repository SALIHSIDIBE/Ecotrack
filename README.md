# 🌿 ECOTRACK — Plateforme IoT de Gestion des Déchets Urbains

> Infrastructure cybersécurité déployée en production sur Proxmox VE / Hetzner  
> Projet académique RNCP Niveau 7 — INGETIS Paris | Spécialité Cybersécurité & Réseaux

---

## 📌 Présentation

**ECOTRACK** est une plateforme de supervision intelligente des déchets urbains combinant IoT, architecture réseau segmentée et cybersécurité défensive. Le système collecte des données environnementales (température, poids, taux de remplissage, batterie) via des capteurs simulés, les traite en temps réel et les restitue sur un tableau de bord web sécurisé.

L'infrastructure complète est virtualisée sur un **serveur dédié Hetzner** sous **Proxmox VE**, simulant un environnement de production métropolitain réaliste pour une ville de 500 000 habitants.

---

## 🏗️ Architecture — Défense en profondeur (5 zones)

```
Internet
    │
    ▼
┌─────────────────────────────────────┐
│  pfSense (Firewall + IDS/IPS)       │  ← Suricata, Default Deny, NAT/ACL
│  WAN — vmbr0 / 10.0.0.0/24          │
└──────────────────┬──────────────────┘
                   │
    ┌──────────────▼─────────────┐
    │  ZONE DMZ — 10.10.1.0/24   │
    │  HAProxy (VIP 10.10.1.100) │  ← Keepalived HA actif/passif
    │  Nginx + ModSecurity WAF   │  ← OWASP CRS Paranoia Level 2
    │  Squid (forward proxy)     │
    │  etcd (consensus cluster)  │
    └──────────────┬─────────────┘
                   │
    ┌──────────────▼─────────────┐
    │  ZONE APPLICATIVE          │
    │  10.10.2.0/24              │
    │  ECO-APP (site web)        │
    │  ECO-DB (PostgreSQL)       │  ← HA cluster + Redis cache
    └──────────────┬─────────────┘
                   │
    ┌──────────────▼─────────────────┐
    │  ZONE MANAGEMENT               │
    │  10.10.3.0/24                  │
    │  Wazuh SIEM (ECO-SEC)          │  ← Agents sur toutes les VMs
    │  (ECO-MON) Prometheus + Grafana│  ← Métriques temps réel
    │  Elasticsearch / Kibana        │  ← Centralisation des logs
    └────────────────────────────────┘

    ┌────────────────────────────┐
    │  ZONE IoT — 10.10.4.0/24   │
    │  Broker MQTT Mosquitto     │  ← Auth obligatoire
    │  Scripts de simulation     │
    └────────────────────────────┘
```

Accès administration : **OpenVPN uniquement** → certificats PKI nominatifs (x5) → SSH clé Ed25519

---

## 🔐 Stack Sécurité

| Couche | Technologie | Rôle |
|---|---|---|
| Périmètre | pfSense + Suricata IPS | Filtrage stateful, blocage signatures ET Ruleset |
| DMZ | HAProxy + Keepalived | Load balancing HA, VIP VRRP |
| Applicatif web | Nginx + ModSecurity | WAF OWASP CRS, anti-SQLi, anti-XSS |
| Flux sortants | Squid proxy | Contrôle et audit des sorties réseau |
| SIEM / HIDS | Wazuh | Agents FIM, corrélation MITRE ATT&CK, CTI VirusTotal |
| Accès distants | OpenVPN + PKI EasyRSA | 5 certificats nominatifs, TLS auth, port non-standard |
| Durcissement SSH | Fail2ban + Ed25519 | Ban auto après 3 échecs, PermitRootLogin no |
| BDD HA | PostgreSQL + Patroni + etcd | Élection leader, réplication synchrone, mTLS |
| Chiffrement | TLS 1.3 / AES-256 / bcrypt | Transit + repos + secrets |
| Monitoring | Prometheus + Grafana | Scraping Node Exporter, alertes seuils critiques |

---

## 📁 Structure du repo

```
ECOTRACK/
│
├── README.md
│
├── docs/
│   ├── BLOC1_cadrage_conception.pdf       # Étude de faisabilité, veille, architecture
│   └── BLOC2_deploiement_securite.pdf     # Implémentation, STRIDE, OWASP, PKI
│
├── scripts/
│   ├── capteur_simulation.py              # Script 1 : Publisher MQTT (IoT simulator)
│   └── mqtt_vers_db.py                    # Script 2 : Subscriber MQTT → PostgreSQL
│    
│
├── infrastructure/
│   ├── pfsense/
│   │   └── regles_filtrage.md             # Matrice des flux inter-zones
│   ├── proxmox/
│   │   └── architecture_vmbr.md           # Plan des ponts virtuels vmbr0-vmbr5
│   └── openvpn/
│       └── PKI_easyrsa.md                 # Hiérarchie CA, certificats, révocation CRL
│
├── waf/
│   └── modsecurity_config.md              # Config Nginx + ModSecurity OWASP CRS
│
├── siem/
│   └── wazuh_deployment.md                # Agents, règles MITRE ATT&CK, FIM
│
└── monitoring/
    └── prometheus_grafana.md              # Stack observabilité, alertes
```

---

## 🚀 Scripts d'automatisation

### Script 1 — Simulateur IoT (`capteur_simulation.py`)
Génère des données environnementales aléatoires (température, poids, batterie, taux de remplissage 0-100%) et les publie sur le broker MQTT Mosquitto via authentification obligatoire.

```bash
python3 scripts/capteur_simulation.py
```

### Script 2 — Ingestion MQTT → PostgreSQL (`mqtt_vers_db.py`)
S'abonne en continu aux topics Mosquitto et insère chaque mesure reçue dans le cluster PostgreSQL en temps réel.

```bash
python3 scripts/mqtt_vers_db.py
```

```

```

---

## 🛡️ Modélisation des menaces (STRIDE)

| Menace | CVSS | Contre-mesure |
|---|---|---|
| Spoofing SSH / VPN | 8.1 Élevé | Fail2ban, Ed25519, certificats OpenVPN nominatifs |
| Injection SQL API | 9.8 Critique | WAF ModSecurity OWASP CRS + requêtes préparées |
| DoS sur DMZ | 7.5 Élevé | Suricata IPS + rate-limiting HAProxy + Keepalived HA |
| Élévation via etcd | 8.8 Élevé | mTLS Patroni/etcd, écoute locale uniquement |
| Tampering IoT | 6.5 Moyen | Isolation vmbr5, auth MQTT, filtrage pfSense |
| Répudiation admin | 5.3 Moyen | Agents Wazuh FIM, logs centralisés Elasticsearch |

---

## 📊 Conformité & Référentiels

- ✅ **ANSSI** — Guide d'hygiène informatique (segmentation, hardening SSH, journalisation)
- ✅ **OWASP Top 10** — Couverture complète A01→A10 via ModSecurity CRS
- ✅ **RGPD** — Privacy by Design, minimisation des données, traçabilité des accès
- ✅ **NIS2** — Architecture de défense en profondeur, détection et réponse centralisées
- ✅ **ISO/IEC 27001** — Base organisationnelle pour une future certification

---

## ⚙️ Stack technique complet

```
Virtualisation  : Proxmox VE sur Debian 12 (Hetzner dedicated server)
Réseau          : pfSense + ponts virtuels vmbr0 à vmbr5
IDS/IPS         : Suricata (mode inline IPS, Emerging Threats ruleset)
WAF             : Nginx + ModSecurity + OWASP CRS (Paranoia)
Load Balancer   : HAProxy + Keepalived (VRRP, VIP 10.10.1.100)
SIEM / HIDS     : Wazuh (agents + manager + Elasticsearch + Kibana)
Monitoring      : Prometheus + Node Exporter + Grafana
Base de données : PostgreSQL 15 + Patroni + etcd + Redis
IoT Broker      : Mosquitto MQTT (auth obligatoire)
VPN             : OpenVPN + PKI EasyRSA (5 certificats nominatifs)
Chiffrement     : TLS 1.3, AES-256-CBC (pgcrypto), bcrypt (work factor 12)
Audit           : Fail2ban, FIM Wazuh, logs centralisés, VirusTotal CTI
```

---

## 👥 Équipe

Projet réalisé en équipe de 5 ingénieurs en cybersécurité — INGETIS Paris (2025-2026)  
Abdallah · Boubacar · Wilfried · Terry · Sâlih SIDIBE

---

## 📄 Mastère 1

Usage académique — INGETIS / RNCP38823 EASRSI Niveau 7
