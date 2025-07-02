#!/usr/bin/env python3
import requests
import json
import sys
import argparse
import unicodedata
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class JellyseerrEmbyMatcher:
    def __init__(self, jellyseerr_url: str, jellyseerr_api_key: str, 
                 emby_url: str, emby_api_key: str, tmdb_api_key: str = None,
                 radarr_url: str = None, radarr_api_key: str = None,
                 sonarr_url: str = None, sonarr_api_key: str = None):
        self.jellyseerr_url = jellyseerr_url.rstrip('/')
        self.jellyseerr_api_key = jellyseerr_api_key
        self.emby_url = emby_url.rstrip('/')
        self.emby_api_key = emby_api_key
        self.tmdb_api_key = tmdb_api_key
        self.use_api_key_param = False
        
        # Configuration Radarr/Sonarr
        self.radarr_url = radarr_url.rstrip('/') if radarr_url else None
        self.radarr_api_key = radarr_api_key
        self.sonarr_url = sonarr_url.rstrip('/') if sonarr_url else None
        self.sonarr_api_key = sonarr_api_key
        
        self.jellyseerr_headers = {
            'X-Api-Key': self.jellyseerr_api_key,
            'Content-Type': 'application/json'
        }
        
        self.emby_headers = {
            'X-Emby-Token': self.emby_api_key,
            'Content-Type': 'application/json'
        }
        
        # Headers pour Radarr et Sonarr
        if self.radarr_api_key:
            self.radarr_headers = {
                'X-Api-Key': self.radarr_api_key,
                'Content-Type': 'application/json'
            }
        
        if self.sonarr_api_key:
            self.sonarr_headers = {
                'X-Api-Key': self.sonarr_api_key,
                'Content-Type': 'application/json'
            }

    def safe_lower(self, value: str) -> str:
        """Applique .lower() de manière sécurisée"""
        if value is None:
            return ""
        return str(value).lower()

    def safe_strip(self, value: str) -> str:
        """Applique .strip() de manière sécurisée"""
        if value is None:
            return ""
        return str(value).strip()

    def normalize_name(self, name: str) -> str:
        """Normalise un nom en supprimant accents, espaces multiples, etc."""
        if not name:
            return ""
        
        try:
            # Supprimer les accents
            name = unicodedata.normalize('NFD', name)
            name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
            
            # Convertir en minuscules et supprimer espaces multiples
            name = ' '.join(name.lower().split())
            
            return name
        except Exception:
            return str(name).lower().strip()

    def safe_int(self, value, default: int = 0) -> int:
        """Convertit en int de manière sécurisée"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def safe_float(self, value, default: float = 0.0) -> float:
        """Convertit en float de manière sécurisée"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def is_older_than_two_months(self, date_str: str) -> bool:
        """Vérifie si une date est antérieure à 2 mois"""
        if not date_str:
            return False
        
        try:
            request_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            two_months_ago = datetime.now().replace(tzinfo=request_date.tzinfo) - timedelta(days=60)
            return request_date < two_months_ago
        except Exception:
            return False

    def test_emby_connection(self) -> bool:
        """Teste la connexion à l'API Emby"""
        print("🔍 Test de connexion à Emby...")
        
        try:
            response = requests.get(f"{self.emby_url}/System/Info/Public", timeout=10)
            if response.status_code == 200:
                print("✅ Serveur Emby accessible")
            else:
                print(f"⚠️  Serveur Emby répond mais avec code: {response.status_code}")
        except Exception as e:
            print(f"❌ Serveur Emby inaccessible: {e}")
            return False
        
        # Test avec header X-Emby-Token
        try:
            response = requests.get(
                f"{self.emby_url}/System/Info",
                headers=self.emby_headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Authentification Emby réussie avec header X-Emby-Token")
                return True
            elif response.status_code == 401:
                print("⚠️  Header X-Emby-Token non autorisé, test avec paramètre...")
            else:
                print(f"⚠️  Réponse inattendue avec header: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur avec header: {e}")
        
        # Test avec paramètre api_key
        try:
            response = requests.get(
                f"{self.emby_url}/System/Info",
                params={'api_key': self.emby_api_key},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Authentification Emby réussie avec paramètre api_key")
                self.use_api_key_param = True
                self.emby_headers = {'Content-Type': 'application/json'}
                return True
            else:
                print(f"❌ Échec avec paramètre api_key: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur avec paramètre: {e}")
        
        print("❌ Toutes les méthodes d'authentification Emby ont échoué")
        return False

    def test_radarr_connection(self) -> bool:
        """Teste la connexion à l'API Radarr"""
        if not self.radarr_url or not self.radarr_api_key:
            return False
            
        print("🔍 Test de connexion à Radarr...")
        try:
            response = requests.get(
                f"{self.radarr_url}/api/v3/system/status",
                headers=self.radarr_headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Connexion Radarr réussie")
                return True
            else:
                print(f"❌ Échec connexion Radarr: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion Radarr: {e}")
            return False

    def test_sonarr_connection(self) -> bool:
        """Teste la connexion à l'API Sonarr"""
        if not self.sonarr_url or not self.sonarr_api_key:
            return False
            
        print("🔍 Test de connexion à Sonarr...")
        try:
            response = requests.get(
                f"{self.sonarr_url}/api/v3/system/status",
                headers=self.sonarr_headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Connexion Sonarr réussie")
                return True
            else:
                print(f"❌ Échec connexion Sonarr: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion Sonarr: {e}")
            return False

    def make_emby_request(self, endpoint: str, params: Dict = None) -> Optional[requests.Response]:
        """Effectue une requête à l'API Emby avec la méthode d'authentification appropriée"""
        if params is None:
            params = {}
            
        if self.use_api_key_param:
            params['api_key'] = self.emby_api_key
            headers = {'Content-Type': 'application/json'}
        else:
            headers = self.emby_headers
        
        try:
            response = requests.get(
                f"{self.emby_url}{endpoint}",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Erreur lors de la requête Emby {endpoint}: {e}")
            return None

    def get_all_jellyseerr_users(self) -> List[Dict]:
        """Récupère tous les utilisateurs Jellyseerr avec pagination"""
        try:
            all_users = []
            page = 1
            
            while True:
                response = requests.get(
                    f"{self.jellyseerr_url}/api/v1/user",
                    headers=self.jellyseerr_headers,
                    params={'take': 50, 'skip': (page - 1) * 50},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, dict):
                    users = data.get('results', [])
                    all_users.extend(users)
                    
                    if not users or len(users) < 50:
                        break
                        
                elif isinstance(data, list):
                    all_users.extend(data)
                    break
                else:
                    break
                    
                page += 1
                
                if page > 10:
                    break
            
            return all_users
            
        except requests.RequestException as e:
            print(f"❌ Erreur lors de la récupération des utilisateurs Jellyseerr: {e}")
            return []

    def get_all_emby_users(self) -> List[Dict]:
        """Récupère tous les utilisateurs Emby"""
        response = self.make_emby_request('/Users')
        if not response:
            return []
        
        try:
            return response.json()
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Erreur lors du parsing des utilisateurs Emby: {e}")
            return []

    def match_users(self, jellyseerr_users: List[Dict], emby_users: List[Dict]) -> Tuple[List[Tuple[Dict, Dict]], List[Dict]]:
        """Associe les utilisateurs avec plusieurs stratégies de matching"""
        matched_users = []
        unmatched_emby_users = []
        
        jellyseerr_by_username = {}
        jellyseerr_by_display = {}
        jellyseerr_by_normalized = {}
        
        for js_user in jellyseerr_users:
            username = js_user.get('username')
            display_name = js_user.get('displayName')
            
            if username and self.safe_strip(username) and username != 'None':
                jellyseerr_by_username[username] = js_user
                jellyseerr_by_normalized[self.normalize_name(username)] = js_user
            
            if display_name and self.safe_strip(display_name):
                jellyseerr_by_display[display_name] = js_user
                jellyseerr_by_normalized[self.normalize_name(display_name)] = js_user
        
        for emby_user in emby_users:
            emby_name = emby_user.get('Name')
            
            if not emby_name or not self.safe_strip(emby_name):
                unmatched_emby_users.append(emby_user)
                continue
            
            matched_js_user = None
            
            if emby_name in jellyseerr_by_username:
                matched_js_user = jellyseerr_by_username[emby_name]
            elif emby_name in jellyseerr_by_display:
                matched_js_user = jellyseerr_by_display[emby_name]
            elif self.normalize_name(emby_name) in jellyseerr_by_normalized:
                matched_js_user = jellyseerr_by_normalized[self.normalize_name(emby_name)]
            
            if matched_js_user:
                matched_users.append((matched_js_user, emby_user))
            else:
                unmatched_emby_users.append(emby_user)
        
        return matched_users, unmatched_emby_users

    def get_jellyseerr_requests(self, user_id: int) -> List[Dict]:
        """Récupère les demandes de films ET séries d'un utilisateur sur Jellyseerr"""
        try:
            all_requests = []
            page = 1
            
            while True:
                response = requests.get(
                    f"{self.jellyseerr_url}/api/v1/request",
                    headers=self.jellyseerr_headers,
                    params={
                        'take': 50,
                        'skip': (page - 1) * 50,
                        'filter': 'all'
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                requests_data = data.get('results', [])
                
                if not requests_data:
                    break
                
                # Filtrer les demandes de l'utilisateur spécifique (films ET séries)
                user_requests = [
                    req for req in requests_data 
                    if req.get('requestedBy', {}).get('id') == user_id and 
                       req.get('type') in ['movie', 'tv']
                ]
                
                all_requests.extend(user_requests)
                
                if len(requests_data) < 50:
                    break
                    
                page += 1
                
            return all_requests
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération des demandes Jellyseerr: {e}")
            return []

    def get_emby_watched_content(self, user_id: str) -> List[Dict]:
        """Récupère les films ET séries vus par un utilisateur sur Emby"""
        params = {
            'UserId': user_id,
            'Recursive': 'true',
            'IncludeItemTypes': 'Movie,Series',
            'Fields': 'ProviderIds,UserData,Path,CommunityRating,CriticRating',
            'format': 'json'
        }
        
        response = self.make_emby_request('/Items', params)
        if not response:
            return []
        
        try:
            items = response.json().get('Items', [])
            watched_items = []
            
            for item in items:
                if item.get('UserData', {}).get('Played', False):
                    watched_items.append(item)
            
            return watched_items
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Erreur lors du parsing du contenu Emby: {e}")
            return []

    def extract_title_from_request(self, request: Dict) -> str:
        """Extrait le titre du contenu depuis différentes sources dans la demande Jellyseerr"""
        sources = [
            request.get('media', {}).get('title'),
            request.get('title'),
            request.get('media', {}).get('originalTitle')
        ]
        
        for title in sources:
            if title and self.safe_strip(title):
                return self.safe_strip(title)
        
        tmdb_id = request.get('media', {}).get('tmdbId')
        content_type = "Série" if request.get('type') == 'tv' else "Film"
        return f"{content_type} TMDB:{tmdb_id}" if tmdb_id else "Titre inconnu"

    def calculate_average_rating(self, community_rating: float = None, critic_rating: float = None) -> float:
        """Calcule la moyenne entre la note communauté (sur 10) et la note critique (en %)"""
        if not community_rating and not critic_rating:
            return 0.0
        
        # Si une seule note est disponible, on la retourne
        if community_rating and not critic_rating:
            return community_rating
        if critic_rating and not community_rating:
            return critic_rating / 10  # Convertir le % en note sur 10
        
        # Si les deux notes sont disponibles, calculer la moyenne
        critic_rating_on_10 = critic_rating / 10  # Convertir % en note sur 10
        average = (community_rating + critic_rating_on_10) / 2
        return average

    def format_rating(self, community_rating: float = None, critic_rating: float = None) -> str:
        """Formate les notes du contenu avec moyenne"""
        ratings = []
        
        if community_rating and community_rating > 0:
            stars = "⭐" * int(round(community_rating / 2))
            ratings.append(f"👥 {community_rating:.1f}/10 {stars}")
        
        if critic_rating and critic_rating > 0:
            ratings.append(f"🎭 {critic_rating:.0f}%")
        
        # Calculer et afficher la moyenne
        average = self.calculate_average_rating(community_rating, critic_rating)
        if average > 0:
            avg_stars = "⭐" * int(round(average / 2))
            ratings.append(f"📊 {average:.1f}/10 {avg_stars}")
        
        if not ratings:
            return "📊 Pas de note"
        
        return " | ".join(ratings)

    def get_content_type_emoji(self, request_type: str) -> str:
        """Retourne l'emoji correspondant au type de contenu"""
        if request_type == 'tv':
            return "📺"
        elif request_type == 'movie':
            return "🎬"
        else:
            return "❓"

    def match_content(self, jellyseerr_requests: List[Dict], emby_watched: List[Dict]) -> List[Dict]:
        """Compare les demandes Jellyseerr avec le contenu vu sur Emby"""
        matches = []
        
        for request in jellyseerr_requests:
            media = request.get('media', {})
            
            tmdb_id = media.get('tmdbId')
            imdb_id = media.get('imdbId')
            title = self.extract_title_from_request(request)
            year = (media.get('releaseDate', ''))[:4] if media.get('releaseDate') else None
            content_type = request.get('type', 'unknown')
            
            for watched_item in emby_watched:
                provider_ids = watched_item.get('ProviderIds', {})
                emby_title = watched_item.get('Name', '')
                emby_year = str(watched_item.get('ProductionYear', '')) if watched_item.get('ProductionYear') else None
                emby_type = watched_item.get('Type', '')
                
                # Vérifier que le type correspond (Movie/Series)
                type_match = False
                if content_type == 'movie' and emby_type == 'Movie':
                    type_match = True
                elif content_type == 'tv' and emby_type == 'Series':
                    type_match = True
                
                if not type_match:
                    continue
                
                match_found = False
                match_type = "inconnu"
                
                if tmdb_id and provider_ids.get('Tmdb') == str(tmdb_id):
                    match_found = True
                    match_type = "TMDB ID"
                elif imdb_id and provider_ids.get('Imdb') == imdb_id:
                    match_found = True
                    match_type = "IMDB ID"
                elif (self.safe_lower(title) == self.safe_lower(emby_title) and 
                      year and emby_year and year == emby_year):
                    match_found = True
                    match_type = "Titre + Année"
                elif self.safe_lower(title) == self.safe_lower(emby_title):
                    match_found = True
                    match_type = "Titre uniquement"
                
                if match_found:
                    user_data = watched_item.get('UserData', {})
                    
                    # Utiliser le titre Emby qui est le vrai nom du contenu
                    display_title = emby_title if emby_title else title
                    
                    match_data = {
                        'title': display_title,
                        'year': year,
                        'content_type': content_type,
                        'tmdb_id': tmdb_id,
                        'imdb_id': imdb_id,
                        'request_date': request.get('createdAt'),
                        'request_status': self.safe_int(request.get('status')),
                        'emby_title': emby_title,
                        'emby_year': emby_year,
                        'emby_id': watched_item.get('Id'),
                        'watch_date': user_data.get('LastPlayedDate'),
                        'play_count': self.safe_int(user_data.get('PlayCount')),
                        'community_rating': self.safe_float(watched_item.get('CommunityRating')),
                        'critic_rating': self.safe_float(watched_item.get('CriticRating')),
                        'match_type': match_type
                    }
                    
                    matches.append(match_data)
                    break
        
        return matches

    def format_date(self, date_str: str) -> str:
        """Formate une date ISO en format lisible compact"""
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%d/%m/%y')
        except Exception:
            return date_str[:10] if len(str(date_str)) >= 10 else str(date_str)

    def get_status_emoji(self, status: int) -> str:
        """Retourne l'emoji correspondant au statut de la demande"""
        status_map = {
            1: "⏳",
            2: "✅", 
            3: "🚫",
            4: "⬇️",
            5: "✅"
        }
        return status_map.get(self.safe_int(status), "❓")

    def get_radarr_movie_by_tmdb(self, tmdb_id: int) -> Optional[Dict]:
        """Récupère un film dans Radarr par son ID TMDB"""
        if not self.radarr_url or not self.radarr_api_key:
            return None
            
        try:
            response = requests.get(
                f"{self.radarr_url}/api/v3/movie",
                headers=self.radarr_headers,
                timeout=30
            )
            response.raise_for_status()
            movies = response.json()
            
            for movie in movies:
                if movie.get('tmdbId') == tmdb_id:
                    return movie
            return None
        except Exception as e:
            print(f"Erreur lors de la recherche du film TMDB {tmdb_id}: {e}")
            return None

    def get_sonarr_series_by_tmdb(self, tmdb_id: int) -> Optional[Dict]:
        """Récupère une série dans Sonarr par son ID TMDB"""
        if not self.sonarr_url or not self.sonarr_api_key:
            return None
            
        try:
            response = requests.get(
                f"{self.sonarr_url}/api/v3/series",
                headers=self.sonarr_headers,
                timeout=30
            )
            response.raise_for_status()
            series = response.json()
            
            for serie in series:
                if serie.get('tmdbId') == tmdb_id:
                    return serie
            return None
        except Exception as e:
            print(f"Erreur lors de la recherche de la série TMDB {tmdb_id}: {e}")
            return None

    def delete_radarr_movie(self, movie_id: int, delete_files: bool = True, add_exclusion: bool = False) -> bool:
        """Supprime un film de Radarr"""
        if not self.radarr_url or not self.radarr_api_key:
            return False
            
        try:
            params = {
                'deleteFiles': str(delete_files).lower(),
                'addImportExclusion': str(add_exclusion).lower()
            }
            
            response = requests.delete(
                f"{self.radarr_url}/api/v3/movie/{movie_id}",
                headers=self.radarr_headers,
                params=params,
                timeout=30
            )
            
            if response.status_code in [200, 204]:
                return True
            else:
                print(f"Erreur suppression film Radarr {movie_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Erreur lors de la suppression du film {movie_id}: {e}")
            return False

    def delete_sonarr_series(self, series_id: int, delete_files: bool = True, add_exclusion: bool = False) -> bool:
        """Supprime une série de Sonarr"""
        if not self.sonarr_url or not self.sonarr_api_key:
            return False
            
        try:
            params = {
                'deleteFiles': str(delete_files).lower(),
                'addImportExclusion': str(add_exclusion).lower()
            }
            
            response = requests.delete(
                f"{self.sonarr_url}/api/v3/series/{series_id}",
                headers=self.sonarr_headers,
                params=params,
                timeout=30
            )
            
            if response.status_code in [200, 204]:
                return True
            else:
                print(f"Erreur suppression série Sonarr {series_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Erreur lors de la suppression de la série {series_id}: {e}")
            return False

    def delete_content_from_arr(self, content: Dict, delete_files: bool = True, add_exclusion: bool = False) -> bool:
        """Supprime le contenu de Radarr ou Sonarr selon le type"""
        tmdb_id = content.get('tmdb_id')
        content_type = content.get('content_type')
        title = content.get('title', 'Titre inconnu')
        
        if not tmdb_id:
            print(f"⚠️  Pas d'ID TMDB pour {title}")
            return False
        
        if content_type == 'movie' and self.radarr_url:
            # Rechercher le film dans Radarr
            movie = self.get_radarr_movie_by_tmdb(tmdb_id)
            if movie:
                movie_id = movie.get('id')
                print(f"🎬 Suppression du film '{title}' de Radarr...")
                success = self.delete_radarr_movie(movie_id, delete_files, add_exclusion)
                if success:
                    print(f"✅ Film '{title}' supprimé de Radarr")
                else:
                    print(f"❌ Échec suppression film '{title}' de Radarr")
                return success
            else:
                print(f"⚠️  Film '{title}' non trouvé dans Radarr")
                return False
                
        elif content_type == 'tv' and self.sonarr_url:
            # Rechercher la série dans Sonarr
            series = self.get_sonarr_series_by_tmdb(tmdb_id)
            if series:
                series_id = series.get('id')
                print(f"📺 Suppression de la série '{title}' de Sonarr...")
                success = self.delete_sonarr_series(series_id, delete_files, add_exclusion)
                if success:
                    print(f"✅ Série '{title}' supprimée de Sonarr")
                else:
                    print(f"❌ Échec suppression série '{title}' de Sonarr")
                return success
            else:
                print(f"⚠️  Série '{title}' non trouvée dans Sonarr")
                return False
        else:
            print(f"⚠️  Type de contenu non supporté ou service non configuré: {content_type}")
            return False

    def generate_user_report(self, delete_files: bool = True, add_exclusion: bool = False, dry_run: bool = True) -> None:
        """Génère un rapport filtré avec option de suppression"""
        print("🗑️  Mode suppression activé" if not dry_run else "👁️  Mode simulation (dry-run)")
        print("🎬📺 Films et Séries mal notés et anciens (< 6.5/10 et > 2 mois)")
        print("=" * 70)
        
        if not self.test_emby_connection():
            return
        
        # Tests de connexion pour Radarr/Sonarr
        radarr_available = self.test_radarr_connection()
        sonarr_available = self.test_sonarr_connection()
        
        if not dry_run and not radarr_available and not sonarr_available:
            print("❌ Aucun service Radarr/Sonarr disponible pour la suppression")
            return
        
        print("\n👥 Récupération des utilisateurs...")
        
        jellyseerr_users = self.get_all_jellyseerr_users()
        emby_users = self.get_all_emby_users()
        
        print(f"   📋 Jellyseerr: {len(jellyseerr_users)} | 🎭 Emby: {len(emby_users)}")
        print()
        
        # Associer les utilisateurs
        matched_users, _ = self.match_users(jellyseerr_users, emby_users)
        
        if len(matched_users) == 0:
            print("\n❌ Aucun utilisateur associé trouvé")
            return
        
        print("🔄 Analyse en cours...\n")
        
        # Collecter tout le contenu avec leurs notes
        all_content = []
        
        for js_user, emby_user in matched_users:
            display_name = js_user.get('displayName')
            username = js_user.get('username')
            
            if display_name and self.safe_strip(display_name):
                user_display_name = display_name
            elif username and self.safe_strip(username) and username != 'None':
                user_display_name = username
            else:
                user_display_name = f"Utilisateur ID {js_user.get('id', 'inconnu')}"
            
            js_user_id = js_user.get('id')
            emby_user_id = emby_user.get('Id')
            
            # Récupérer les données
            jellyseerr_requests = self.get_jellyseerr_requests(js_user_id)
            emby_watched = self.get_emby_watched_content(emby_user_id)
            matches = self.match_content(jellyseerr_requests, emby_watched)
            
            # Ajouter l'utilisateur à chaque contenu
            for match in matches:
                match['user'] = user_display_name
                # Calculer la note moyenne pour le tri
                match['average_rating'] = self.calculate_average_rating(
                    match.get('community_rating'),
                    match.get('critic_rating')
                )
                all_content.append(match)
        
        if not all_content:
            print("ℹ️  Aucun contenu trouvé")
            return
        
        # **FILTRAGE** : note moyenne < 6.5 ET demande > 2 mois
        filtered_content = []
        for content in all_content:
            average_rating = content.get('average_rating', 0)
            request_date = content.get('request_date')
            
            # Appliquer les filtres
            if (average_rating < 6.5 and average_rating > 0 and  # Note < 6.5 (mais pas 0)
                self.is_older_than_two_months(request_date)):  # Demande > 2 mois
                filtered_content.append(content)
        
        if not filtered_content:
            print("ℹ️  Aucun contenu ne correspond aux critères (note < 6.5 et demande > 2 mois)")
            return
        
        # Trier le contenu filtré par note moyenne croissante (les plus mauvais en premier)
        filtered_content.sort(key=lambda x: x.get('average_rating', 0))
        
        print("📉 **Contenu mal noté et ancien :**\n")
        
        for i, content in enumerate(filtered_content, 1):
            title = content.get('title', 'Titre inconnu')
            year = f" ({content.get('year')})" if content.get('year') else ""
            user = content.get('user', 'Utilisateur inconnu')
            request_date = self.format_date(content.get('request_date'))
            watch_date = self.format_date(content.get('watch_date'))
            play_count = content.get('play_count', 0)
            status = self.get_status_emoji(content.get('request_status'))
            content_type_emoji = self.get_content_type_emoji(content.get('content_type'))
            rating = self.format_rating(
                content.get('community_rating'),
                content.get('critic_rating')
            )
            
            print(f"{i:2d}. {content_type_emoji} **{title}**{year} | {rating}")
            print(f"    👤 {user} | 📅 {request_date} → 🎬 {watch_date} ({play_count}x) {status}")
            print()
        
        # Statistiques
        movies_count = len([c for c in filtered_content if c.get('content_type') == 'movie'])
        series_count = len([c for c in filtered_content if c.get('content_type') == 'tv'])
        
        print(f"📊 **{len(filtered_content)}** contenus mal notés et anciens | 🎬 {movies_count} films | 📺 {series_count} séries")
        
        # Option de suppression
        if filtered_content and not dry_run:
            print("\n🗑️  **Options de suppression :**")
            response = input("Voulez-vous supprimer ce contenu de Radarr/Sonarr ? (o/N): ").lower()
            
            if response in ['o', 'oui', 'y', 'yes']:
                deleted_count = 0
                failed_count = 0
                
                print("\n🔄 Suppression en cours...")
                
                for content in filtered_content:
                    success = self.delete_content_from_arr(content, delete_files, add_exclusion)
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                
                print(f"\n📊 **Résultats :** ✅ {deleted_count} supprimés | ❌ {failed_count} échecs")
            else:
                print("❌ Suppression annulée")

def main():
    # Configuration - MODIFIEZ CES VALEURS
    JELLYSEERR_URL = "JELLYSEERR_URL"
    JELLYSEERR_API_KEY = "JELLYSEERR_API_KEY"
    EMBY_URL = "EMBY_URL"
    EMBY_API_KEY = "EMBY_API_KEY"
    
    # Configuration Radarr et Sonarr - À MODIFIER selon votre installation
    RADARR_URL = "RADARR_URL"
    RADARR_API_KEY = "RADARR_API_KEY"  # À remplacer
    SONARR_URL = "SONARR_URL"
    SONARR_API_KEY = "SONARR_API_KEY"  # À remplacer
    
    matcher = JellyseerrEmbyMatcher(
        JELLYSEERR_URL, JELLYSEERR_API_KEY,
        EMBY_URL, EMBY_API_KEY,
        radarr_url=RADARR_URL, radarr_api_key=RADARR_API_KEY,
        sonarr_url=SONARR_URL, sonarr_api_key=SONARR_API_KEY
    )
    
    try:
        # Mode simulation par défaut (dry_run=True)
        # Changez dry_run=False pour vraiment supprimer
        matcher.generate_user_report(
            delete_files=True,      # Supprimer les fichiers du disque
            add_exclusion=False,    # NE PAS ajouter à l'exclusion
            dry_run=False           # Mode simulation
        )
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Script interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
