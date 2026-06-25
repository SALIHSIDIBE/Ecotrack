# Architecture Proxmox VE — Ponts virtuels (vmbr)

## Environnement d'hébergement

| Paramètre | Valeur |
|---|---|
| Hébergeur | Hetzner (serveur dédié physique) |
| OS hôte | Debian 12 (Bookworm) |
| Hyperviseur | Proxmox VE |
| Accès admin | OpenVPN → SSH clé Ed25519 uniquement |

---

## Plan des ponts virtuels

```
Serveur physique Hetzner
└── Debian 12 (OS hôte)
    └── Proxmox VE
        ├── vmbr0  ─── WAN (interface physique → Internet Hetzner)
        ├── vmbr1  ─── Access pfSense  (10.0.0.0/24)
        ├── vmbr2  ─── DMZ             (10.10.1.0/24)
        ├── vmbr3  ─── Applicatif      (10.10.2.0/24)
        ├── vmbr4  ─── Management      (10.10.3.0/24)
        └── vmbr5  ─── IoT             (10.10.4.0/24)
```

---

## Machines virtuelles et conteneurs

| ID | Nom | Type | Réseau | IP | Rôle |
|---|---|---|---|---|---|
| 100 | PfSense | VM (qemu) | vmbr0-vmbr5 | 10.0.0.2 | Firewall central |
| 101 | ECO-PROXY | CT (lxc) | vmbr2 | 10.10.1.10 | Reverse proxy principal |
| 102 | ECO-LB-02 | CT (lxc) | vmbr2 | 10.10.1.11 | Reverse proxy secondaire |
| — | VIP Keepalived | Virtuelle | vmbr2 | 10.10.1.100 | IP virtuelle HA |
| 103 | DB-ECO-02 | CT (lxc) | vmbr3 | 10.10.2.31 | PostgreSQL réplica |
| 107 | APP-ECO | CT (lxc) | vmbr3 | 10.10.2.20 | Application web |
| 111 | DB-ECO | CT (lxc) | vmbr3 | 10.10.2.30 | PostgreSQL leader (Patroni) |
| 105 | ECO-SEC | CT (lxc) | vmbr4 | 10.10.3.10 | Wazuh SIEM |
| 108 | ECO-MON | CT (lxc) | vmbr4 | 10.10.3.11 | Prometheus + Grafana |
| 106 | IoT-MQTT | CT (lxc) | vmbr5 | 10.10.4.x | Broker Mosquitto |

---

## Haute disponibilité DMZ

```
Internet
    │
    ▼ (port 80/443)
VIP Keepalived : 10.10.1.100  ← VRRP entre ECO-PROXY et ECO-LB-02
    │
    ├── ECO-PROXY (10.10.1.10)  ← Nœud MASTER
    │       HAProxy + Nginx + ModSecurity + Squid + etcd
    │
    └── ECO-LB-02 (10.10.1.11) ← Nœud BACKUP
            HAProxy + Nginx + ModSecurity + Squid + etcd
```

Bascule automatique en quelques millisecondes si le nœud master tombe.

---

## Cluster PostgreSQL (zone Applicative)

```
ECO-DB  (10.10.2.30) ← Leader PostgreSQL (Patroni)
ECO-DB-02 (10.10.2.31) ← Réplica asynchrone
    │
    └── etcd (dans DMZ) ← Consensus d'élection du leader
        Communication sécurisée par mTLS bidirectionnel
```

---

## Schéma global

```
                        ┌──────────────────┐
                        │  Hetzner / WAN   │
                        └────────┬─────────┘
                                 │ vmbr0
                        ┌────────▼─────────┐
                        │  pfSense (100)   │
                        │  vmbr1-vmbr5     │
                        └──┬───┬───┬───┬───┘
                     vmbr2 │   │vmbr3 │vmbr4  │vmbr5
               ┌───────────┘   └──┬───┘   └──┐    └──────────┐
       ┌───────▼──────┐    ┌──────▼──────┐  ┌▼────────┐  ┌───▼──────┐
       │  DMZ         │    │  APPLICATIF │  │ MGMT    │  │  IoT     │
       │  10.10.1.0   │    │  10.10.2.0  │  │10.10.3.0│  │10.10.4.0 │
       │  ECO-PROXY   │    │  ECO-APP    │  │ECO-SEC  │  │Mosquitto │
       │  ECO-LB-02   │    │  ECO-DB     │  │ECO-MON  │  │Scripts   │
       │  VIP .100    │    │  ECO-DB-02  │  │         │  │          │
       └──────────────┘    └─────────────┘  └─────────┘  └──────────┘
```
