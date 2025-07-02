# Emby Watched Jellyseerr Cleaner

Un script Python pour analyser et nettoyer automatiquement votre bibliothèque multimédia en comparant les demandes Jellyseerr avec le contenu regardé sur Emby.

## 🎯 Fonctionnalités

- **Analyse intelligente** : Compare les demandes Jellyseerr avec le contenu regardé sur Emby
- **Filtrage avancé** : Identifie le contenu mal noté (< 6.5/10) et ancien (> 2 mois)
- **Nettoyage automatique** : Supprime le contenu indésirable de Radarr et Sonarr
- **Rapports détaillés** : Génère des statistiques complètes avec émojis
- **Mode simulation** : Testez avant de supprimer avec le mode dry-run
- **Support multi-services** : Jellyseerr, Emby, Radarr, Sonarr

## 📋 Prérequis

- Python 3.7+
- Accès aux APIs de vos services
- Modules Python requis :
  ```bash
  pip install requests unicodedata
  ```

## ⚙️ Configuration

1. **Ouvrez le fichier `emby_watched_jellyseerr_cleaner.py`**

2. **Modifiez la section configuration dans la fonction `main()` :**

```python
def main():
    # Configuration - MODIFIEZ CES VALEURS
    JELLYSEERR_URL = "http://VOTRE_IP:5055"
    JELLYSEERR_API_KEY = "VOTRE_CLE_API_JELLYSEERR"
    EMBY_URL = "http://VOTRE_IP:8096"
    EMBY_API_KEY = "VOTRE_CLE_API_EMBY"
    
    # Configuration Radarr et Sonarr (optionnel)
    RADARR_URL = "http://VOTRE_IP:7878"
    RADARR_API_KEY = "VOTRE_CLE_API_RADARR"
    SONARR_URL = "http://VOTRE_IP:8989"
    SONARR_API_KEY = "VOTRE_CLE_API_SONARR"
```

### 🔑 Obtenir les clés API

#### Jellyseerr
1. Connexion → Paramètres → API
2. Copiez la clé API

#### Emby
1. Tableau de bord → Avancé → Clés API
2. Créez une nouvelle clé API

#### Radarr/Sonarr
1. Paramètres → Général → API Key
2. Copiez la clé API

## 🚀 Utilisation

### Mode Simulation (Recommandé)
```bash
python emby_watched_jellyseerr_cleaner.py
```

Le script fonctionne en mode simulation par défaut. Il affiche ce qui serait supprimé sans rien supprimer.

### Mode Suppression Réelle
Modifiez dans le script la ligne :
```python
dry_run=True  # Changez en False pour vraiment supprimer
```

## 📊 Critères de Filtrage

Le script identifie le contenu à nettoyer selon ces critères :

- **Note moyenne < 6.5/10** (combinaison note communauté + note critique)
- **Demande ancienne > 2 mois**
- **Contenu regardé** (confirmé dans Emby)

## 🔍 Correspondance Intelligente

Le script utilise plusieurs méthodes pour associer le contenu :

1. **ID TMDB** (priorité haute)
2. **ID IMDB** (priorité haute)
3. **Titre + Année** (priorité moyenne)
4. **Titre uniquement** (priorité faible)

## 📈 Exemple de Sortie

```
🎬📺 Films et Séries mal notés et anciens (< 6.5/10 et > 2 mois)
======================================================================

📉 **Contenu mal noté et ancien :**

 1. 🎬 **Film Example** (2022) | 👥 4.2/10 ⭐⭐ | 📊 4.2/10 ⭐⭐
    👤 Jean Dupont | 📅 15/03/24 → 🎬 20/03/24 (1x) ✅

 2. 📺 **Série Example** (2023) | 👥 5.8/10 ⭐⭐⭐ | 🎭 45% | 📊 5.65/10 ⭐⭐⭐
    👤 Marie Martin | 📅 10/02/24 → 🎬 12/02/24 (3x) ✅

📊 **2** contenus mal notés et anciens | 🎬 1 films | 📺 1 séries
```

## ⚠️ Sécurité

- **Testez toujours en mode simulation** avant la suppression réelle
- **Sauvegardez vos données** avant utilisation
- Le script peut supprimer définitivement vos fichiers media

## 🛠️ Paramètres Avancés

### Options de Suppression
```python
matcher.generate_user_report(
    delete_files=True,      # Supprimer les fichiers du disque
    add_exclusion=False,    # Ajouter à la liste d'exclusion
    dry_run=True           # Mode simulation
)
```

### Personnalisation des Seuils
Modifiez dans la méthode `generate_user_report()` :
```python
# Changer le seuil de note (actuellement 6.5)
if (average_rating < 6.5 and average_rating > 0 and

# Changer la durée d'ancienneté (actuellement 2 mois)
self.is_older_than_two_months(request_date)):
```

## 🐛 Dépannage

### Erreurs de Connexion
- Vérifiez que tous vos services sont accessibles
- Contrôlez les URLs et ports
- Validez les clés API

### Aucun Contenu Trouvé
- Vérifiez que les utilisateurs existent dans les deux services
- Assurez-vous que le contenu a été regardé sur Emby
- Contrôlez les critères de filtrage

### Problèmes de Correspondance
- Le script utilise plusieurs méthodes de matching
- Vérifiez les métadonnées TMDB/IMDB
- Les titres doivent correspondre entre services

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou soumettre une Pull Request.

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## ⚡ Statut des Émojis

| Emoji | Signification |
|-------|---------------|
| ⏳ | En attente |
| ✅ | Approuvé/Terminé |
| 🚫 | Refusé |
| ⬇️ | En téléchargement |
| ❓ | Statut inconnu |
| 🎬 | Film |
| 📺 | Série TV |
| ⭐ | Note (1-5 étoiles) |
| 👥 | Note communauté |
| 🎭 | Note critique |
| 📊 | Note moyenne |

---

**⚠️ Attention :** Ce script peut supprimer définitivement vos fichiers media. Utilisez toujours le mode simulation avant une suppression réelle et assurez-vous d'avoir des sauvegardes.
