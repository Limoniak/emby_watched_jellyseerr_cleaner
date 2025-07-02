# emby_watched_jellyseerr_cleaner

[![python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)  [![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Présentation

**emby_watched_jellyseerr_cleaner** est un utilitaire Python destiné aux administrateurs de médiathèques auto-hébergées. Il croise les demandes Jellyseerr avec l’historique de visionnage Emby afin d’identifier les films et séries mal notés qui n’ont plus d’intérêt pour vos utilisateurs. Il peut ensuite – en simulation ou en mode actif – supprimer ces contenus via Radarr/Sonarr pour libérer de l’espace disque.

## Fonctionnalités principales

* Association automatique des comptes Jellyseerr ↔︎ Emby (nom, alias, normalisation).
* Analyse conjointe des demandes Jellyseerr et du statut « vu » Emby.
* Calcul d’une note moyenne (communauté + critique) et filtrage configurable (< 6.5/10 et demande > 60 jours par défaut).
* Génération d’un rapport détaillé en console avec emojis et statistiques.
* Suppression optionnelle des titres correspondants dans Radarr/Sonarr (fichiers + import-exclusion).
* Mode _dry-run_ sécurisé pour valider le résultat avant toute action destructive.

## Prérequis

* Python ≥ 3.9 
* Un accès API fonctionnel aux services suivants :
  * Jellyseerr ≥ 1.6
  * Emby Server ≥ 4.9
  * (optionnel) Radarr / Sonarr avec API v3 activée
* Bibliothèques Python : `requests`, `python-dotenv` (installées automatiquement via `pip`).

## Installation

```bash
# 1. Cloner le dépôt
$ git clone https://github.com/Limoniak/emby_watched_jellyseerr_cleaner.git
$ cd emby_watched_jellyseerr_cleaner

# 2. Créer un environnement virtuel (recommandé)
$ python -m venv venv && source venv/bin/activate

# 3. Installer les dépendances
$ pip install -r requirements.txt
```

## Configuration

Toutes les URLs et clés API sont désormais chargées depuis un fichier **.env** afin d’éviter toute fuite d’information sensible dans le dépôt Git.

1. Copiez le modèle :
   ```bash
   cp .env.example .env
   ```
2. Éditez **.env** et renseignez vos valeurs :
   ```ini
   JELLYSEERR_URL=https://jellyseerr.example.com
   JELLYSEERR_API_KEY=xxxxxxxxxxxxxxxxx
   EMBY_URL=https://emby.example.com
   EMBY_API_KEY=xxxxxxxxxxxxxxxxx
   RADARR_URL=https://radarr.example.com        # optionnel
   RADARR_API_KEY=xxxxxxxxxxxxxxxxx             # optionnel
   SONARR_URL=https://sonarr.example.com        # optionnel
   SONARR_API_KEY=xxxxxxxxxxxxxxxxx             # optionnel
   ```

⚠️ Le fichier **.env** est ignoré par Git grâce à l’entrée correspondante dans `.gitignore`.

## Utilisation rapide

```bash
# Simulation (aucune suppression réelle)
$ python3 pruner.py --dry-run

# Suppression effective après confirmation
$ python3 pruner.py --no-dry-run
```

Arguments courants :

| Option                | Valeur par défaut | Description                                                |
|-----------------------|-------------------|------------------------------------------------------------|
| `--dry-run / --no-dry-run` | `--dry-run`       | Exécute le script en mode lecture seule.                   |
| `--min-rating`        | `6.5`             | Seuil de note moyenne sous lequel un titre est considéré comme « mal noté ». |
| `--older-than`        | `60`              | Âge minimum de la demande (en jours) avant d’être éligible. |
| `--delete-files`      | activé            | Supprimer également les fichiers multimédia sur disk.      |
| `--add-exclusion`     | désactivé         | Ajoute une exclusion d’import dans Radarr/Sonarr après suppression. |

## Exemple de sortie

```
👁️  Mode simulation (dry-run)
🎬📺 Films et Séries mal notés et anciens (< 6.5/10 et > 2 mois)
====================================================================
 1. 🎬 **The Bad Movie** (2022) | 📊 4.8/10 ⭐⭐
    👤 Alice | 📅 13/04/24 → 🎬 18/04/24 (1x) ✅
...
📊 3 contenus mal notés et anciens | 🎬 2 films | 📺 1 série
```

## Contribution

Les demandes de fusion sont les bienvenues ! Merci de :

1. Créer une issue pour décrire le bug ou la fonctionnalité souhaitée.
2. Travailler dans une branche dédiée.
3. Lancer `flake8` et `pytest` avant tout commit.


## Remerciements

* [Jellyseerr](https://github.com/fallenbagel/jellyseerr) et sa communauté.
* [Emby](https://emby.media) pour son API riche.[5]
* Les projets **Radarr** et **Sonarr** pour l’automatisation média.[20]
* Le paquet `python-dotenv` pour la gestion sécurisée des variables d’environnement.[28]
