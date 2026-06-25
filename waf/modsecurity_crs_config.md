# WAF ModSecurity — Configuration Nginx + OWASP Core Rule Set

## Architecture du flux WAF

```
Internet
    │
    ▼ ports 80/443
HAProxy (VIP 10.10.1.100)       ← Terminaison TCP, load balancing
    │
    ▼ port 81 (interne)
Nginx + ModSecurity WAF          ← Inspection et filtrage HTTP/HTTPS
    │
    ▼ port 3000
ECO-APP (10.10.2.20)            ← Application web ECOTRACK
    │
    ▼ port 5432
PostgreSQL cluster               ← Base de données (jamais exposée directement)
```

---

## Configuration ModSecurity

### Mode de déploiement
```nginx
# /etc/nginx/modsecurity/modsecurity.conf

SecRuleEngine On                  # Mode prévention active (après phase détection)
SecRequestBodyAccess On
SecResponseBodyAccess On
SecAuditEngine RelevantOnly
SecAuditLog /var/log/modsecurity/audit.log
```

> **Déploiement progressif** : d'abord `SecRuleEngine DetectionOnly` pour identifier les faux positifs, puis basculé en `On` (prévention active).

### Niveau de paranoïa OWASP CRS
```
Paranoia Level : 2
```
- **Niveau 1** : règles de base, peu de faux positifs
- **Niveau 2** : règles avancées activées — détection plus agressive des tentatives de contournement

---

## Couverture OWASP Top 10

| Ref | Vulnérabilité | Mesure ModSecurity |
|---|---|---|
| A01 | Broken Access Control | Filtrage pfSense + RBAC PostgreSQL + JWT vérification |
| A02 | Cryptographic Failures | TLS 1.3 forcé, TLS 1.0/1.1/1.2 désactivés |
| A03 | Injection (SQL, XSS) | CRS rules SQLi + XSS, Paranoia Level 2 |
| A04 | Insecure Design | Segmentation 5 zones, moindre privilège structurel |
| A05 | Security Misconfiguration | Hardening ANSSI + FIM Wazuh sur configs |
| A06 | Vulnerable Components | Squid proxy contrôle apt, inventaire CVE Wazuh |
| A07 | Auth Failures | Fail2ban (3 tentatives → ban 24h) + certificats OpenVPN |
| A08 | Software Integrity | GPG Debian via Squid + FIM Wazuh binaires |
| A09 | Logging Failures | SOC Wazuh + Elasticsearch + Grafana alertes |
| A10 | SSRF | Règles CRS SSRF + filtrage sortie strict pfSense |

---

## Test de validation WAF

### Test injection XSS
```bash
curl -i "https://10.10.1.100/?q=<script>alert(1)</script>"
```
**Résultat attendu :**
```
HTTP/1.1 403 Forbidden
# ModSecurity intercepte et bloque — log dans /var/log/modsecurity/audit.log
```

### Test injection SQL
```bash
curl -i "https://10.10.1.100/api/sensors?id=1' OR '1'='1"
```
**Résultat attendu :**
```
HTTP/1.1 403 Forbidden
```

---

## Configuration Nginx (extrait)

```nginx
server {
    listen 81;
    server_name ecotrack.local;

    # ModSecurity
    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsecurity/main.conf;

    # Headers sécurité
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # TLS 1.3 uniquement
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://10.10.2.20:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## Logs et supervision

Les alertes ModSecurity sont transmises au **SIEM Wazuh** via Filebeat pour corrélation et historique.

```bash
# Consulter les alertes WAF en temps réel
tail -f /var/log/modsecurity/audit.log

# Vérifier les règles CRS chargées
nginx -t && nginx -s reload
```
