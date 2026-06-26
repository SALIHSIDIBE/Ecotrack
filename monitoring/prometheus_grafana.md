# Monitoring — Prometheus + Grafana

## Architecture d'observabilité

```
Toutes les VMs / Conteneurs
    │ Node Exporter (port 9100)
    │ expose métriques HTTP
    ▼
ECO-MON (10.10.3.11) — Prometheus
    │ scraping toutes les 15s
    │ stockage TSDB
    ▼
Grafana
    │ dashboards temps réel
    └── Alertmanager → notifications
```

---

## Node Exporter — Métriques collectées

Déployé sur **chaque machine virtuelle et conteneur** de l'infrastructure :

| Métrique | Description |
|---|---|
| `node_cpu_seconds_total` | Utilisation CPU par cœur |
| `node_memory_MemAvailable_bytes` | RAM disponible |
| `node_disk_io_time_seconds_total` | I/O disque |
| `node_network_receive_bytes_total` | Trafic réseau entrant |
| `node_network_transmit_bytes_total` | Trafic réseau sortant |
| `node_filesystem_avail_bytes` | Espace disque disponible |

---

## Configuration Prometheus (extrait)

```yaml
# prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'ecotrack'
    static_configs:
      - targets:
          - '10.10.1.10:9100'   # ECO-PROXY
          - '10.10.1.11:9100'   # ECO-LB-02
          - '10.10.2.20:9100'   # ECO-APP
          - '10.10.2.30:9100'   # ECO-DB
          - '10.10.2.31:9100'   # ECO-DB-02
          - '10.10.3.10:9100'   # ECO-SEC
          - '10.10.3.11:9100'   # ECO-MON (auto)
          - '10.10.4.10:9100'   # IoT-MQTT
```

---

## Règles d'alerting (alert_rules.yml)

```yaml
groups:
  - name: ecotrack_alerts
    rules:

      # CPU critique
      - alert: CPUElevé
        expr: 100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU > 85% sur {{ $labels.instance }}"

      # RAM critique
      - alert: RAMCritique
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "RAM < 10% disponible sur {{ $labels.instance }}"

      # Disque critique
      - alert: DisqueCritique
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100 < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disque < 15% disponible sur {{ $labels.instance }}"

      # Instance down
      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} inaccessible"
```

---

## Dashboards Grafana

| Dashboard | Contenu |
|---|---|
| Infrastructure Overview | CPU, RAM, disque, réseau — toutes VMs |
| ECOTRACK IoT | Taux de remplissage conteneurs, flux MQTT |
| PostgreSQL | Connexions actives, latence requêtes, réplication |
| HAProxy | Connexions, taux d'erreur, backends actifs |
| Wazuh Alerts | Événements sécurité corrélés (via Elasticsearch) |

---

## Objectifs de disponibilité

| Indicateur | Objectif | Description |
|---|---|---|
| Disponibilité | 99,5% | < 44h d'indisponibilité/an |
| RTO | < 4 heures | Durée max d'interruption acceptable |
| RPO | < 1 heure | Perte de données maximale acceptable |
| Latence API | < 2 secondes | Ingestion messages IoT |

---

## Commandes utiles

```bash
# Vérifier les targets Prometheus
curl http://10.10.3.11:9090/api/v1/targets

# Vérifier les alertes actives
curl http://10.10.3.11:9090/api/v1/alerts

# Accéder à Grafana (via VPN)
http://10.10.3.11:3000
# Login par défaut changé lors du déploiement

# Vérifier Node Exporter sur une VM
curl http://10.10.2.20:9100/metrics | grep node_cpu
```
