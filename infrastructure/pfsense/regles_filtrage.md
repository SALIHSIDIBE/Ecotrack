# Règles de filtrage pfSense — Matrice des flux inter-zones

## Politique par défaut : **Default Deny (Block All)**
Tout trafic non explicitement autorisé est rejeté silencieusement. Journalisation active sur tous les paquets bloqués.

---

## Interfaces réseau

| Interface | Pont virtuel | Réseau | Rôle |
|---|---|---|---|
| WAN | vmbr0 | Internet (Hetzner) | Point d'entrée public |
| Access pfSense | vmbr1 | 10.0.0.0/24 | Liaison hôte Debian ↔ pfSense |
| DMZ | vmbr2 | 10.10.1.0/24 | Zone tampon exposée |
| Applicatif | vmbr3 | 10.10.2.0/24 | Services métier |
| Management | vmbr4 | 10.10.3.0/24 | Administration / SOC |
| IoT | vmbr5 | 10.10.4.0/24 | Capteurs terrain |

---

## Règles de filtrage

### Règle 1 — WAN → Zone DMZ
```
Action   : PASS
Proto    : TCP
Source   : any (Internet)
Dest     : 10.10.1.100 (VIP Keepalived)
Ports    : 80 (HTTP), 443 (HTTPS)
Log      : Oui
```

### Règle 2 — Zone DMZ → Zone Applicative
```
Action   : PASS
Proto    : TCP
Source   : ECO-PROXY (10.10.1.10), ECO-LB-02 (10.10.1.11)
Dest     : ECO-APP (10.10.2.20) port 3000
           ECO-DB  (10.10.2.30) port 5432
Log      : Oui
```

### Règle 3 — Zone Applicative → Zone DMZ (flux sortants via Squid)
```
Action   : PASS
Proto    : TCP
Source   : 10.10.2.0/24
Dest     : Squid (10.10.1.x) port 3128
Usage    : apt-get, mises à jour système contrôlées
Log      : Oui
```

### Règle 4 — Zone Management → Toutes zones
```
Action   : PASS
Proto    : TCP/UDP
Source   : 10.10.3.0/24
Dest     : Toutes zones
Ports    : 1514/1515 (Wazuh agents), 9100 (Node Exporter Prometheus)
Sens inv : BLOQUÉ (aucun flux production → Management autorisé)
Log      : Oui
```

### Règle 5 — Zone IoT → Zone Applicative
```
Action   : PASS
Proto    : TCP
Source   : Script d'ingestion (10.10.4.x)
Dest     : ECO-DB (10.10.2.30) port 5432 uniquement
Autres   : BLOQUÉ (aucune route vers DMZ, Management, WAN)
Log      : Oui
```

### Règle 6 — Tunnel OpenVPN → Zone Management
```
Action   : PASS
Proto    : UDP
Source   : Clients VPN authentifiés (PKI nominative)
Dest     : 10.10.3.0/24 (Proxmox VE, ECO-SEC, ECO-MON)
Log      : Oui
```

### Règle par défaut
```
Action   : BLOCK
Source   : any
Dest     : any
Log      : Oui (alimentation règles détection SIEM)
```

---

## IDS/IPS Suricata (intégré pfSense)

- **Mode** : IPS inline (Netmap) sur interface WAN
- **Rulesets actifs** :
  - Emerging Threats Open (ET) — trafic C2, scanners
  - Règles anti-DoS — SYN Flood, HTTP Flood
  - Règles applicatives — SQLi, XSS au niveau réseau
- **Output** : Alertes transmises via Syslog chiffré → Wazuh SIEM
