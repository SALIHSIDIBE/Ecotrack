# PKI OpenVPN — Infrastructure à clés publiques (EasyRSA)

## Vue d'ensemble

L'accès à l'infrastructure ECOTRACK est verrouillé derrière un tunnel **OpenVPN** déployé sur la passerelle Debian (hôte Hetzner). La sécurité repose sur une PKI interne initialisée via **EasyRSA**, délivrant des certificats cryptographiques nominatifs et stricts.

---

## Hiérarchie de confiance

```
CA Racine (RSA 4096 bits — validité 10 ans)
    │
    ├── Certificat Serveur VPN (ECDSA P-256 — validité 2 ans)
    │
    ├── Certificat Client : Abdallah  (ECDSA P-256 — validité 1 an)
    ├── Certificat Client : Boubacar  (ECDSA P-256 — validité 1 an)
    ├── Certificat Client : Wilfried  (ECDSA P-256 — validité 1 an)
    ├── Certificat Client : Terry     (ECDSA P-256 — validité 1 an)
    └── Certificat Client : Salih     (ECDSA P-256 — validité 1 an)
```

---

## Algorithmes et paramètres cryptographiques

| Élément | Algorithme | Taille / Paramètre |
|---|---|---|
| CA racine | RSA | 4096 bits |
| Certificats serveur/clients | ECDSA | Courbe P-256 |
| Chiffrement tunnel | AES-256-GCM | — |
| Auth TLS statique | tls-auth (HMAC) | Clé partagée |
| Hash | SHA-256 | — |

---

## Configuration OpenVPN

```
# Sécurité
tls-version-min 1.2
cipher AES-256-GCM
auth SHA256
tls-auth ta.key 0

# Auth double facteur réseau
# 1. Certificat x509 client (PKI EasyRSA)
# 2. Clé TLS statique partagée (tls-auth)

# Port non-standard (anti-scan)
port XXXX
proto udp

# Réseau assigné après authentification
# → accès restreint à Zone Management (10.10.3.0/24)
```

---

## Politique de sécurité des accès

- **Aucun accès WAN direct** : toutes les interfaces d'administration sont bloquées depuis Internet
- **OpenVPN obligatoire** : prérequis pour atteindre Proxmox, pfSense, Wazuh, Grafana
- **Port non-standard** : évite les scans automatisés ciblant le port par défaut 1194
- **Certificats individuels** : chaque ingénieur a son propre certificat — révocation unitaire possible
- **Durée de vie limitée** : certificats clients valides 1 an pour limiter la fenêtre de compromission

---

## Révocation des certificats (CRL)

En cas de compromission ou de départ d'un membre :

```bash
# Révoquer un certificat
cd /etc/openvpn/easy-rsa
./easyrsa revoke <nom_ingenieur>
./easyrsa gen-crl

# Mettre à jour la CRL sur la passerelle OpenVPN
cp pki/crl.pem /etc/openvpn/server/crl.pem
systemctl restart openvpn
```

La CRL est vérifiée à chaque tentative de connexion. Le certificat révoqué est immédiatement rejeté.

> **En production** : ce mécanisme manuel serait remplacé par un répondeur **OCSP** pour une vérification en temps réel sans latence.

---

## Flux d'accès administrateur

```
Poste admin
    │
    ▼ (certificat x509 + tls-auth)
OpenVPN Gateway (hôte Debian Hetzner)
    │
    ▼ (tunnel chiffré AES-256)
Zone Management (10.10.3.0/24)
    ├── Proxmox VE Web UI
    ├── ECO-SEC / Wazuh (10.10.3.10)
    └── ECO-MON / Grafana (10.10.3.11)
    │
    ▼ (SSH clé Ed25519 uniquement — PermitRootLogin no)
Serveurs de production
```
