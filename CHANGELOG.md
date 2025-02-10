# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## ## [v1.1.5] - 2024-02-29

### Added
- Feature: L'intégration peut être rechargée sans relancer HomeAssistant
- Feature: Ajout d'un attribut d'information sur le délai de disponibilité des données
- Feature: Mise jour toutes les 12h

### Fixed
- Bug: Correction de la requete SQL pour les données absolues
- Bug: Correction du bug du premier jour du mois courant.
- Bug: Correction des champs de configuration manquants
- Bug: Correction des mois manquants

### Changed
- Chore: ruff ne bloque plus les constantes dans tests/
- Chore: Les attributs du sensor sont en français.
- Chore: Réduction du nombre de requetes API en phase d'initialisation
- Chore: StrongTyping (mypy strict) 
- Chore: Blacklist des mois (HTTP 500 de l'API SAUR)
- Chore: Ajout d'un debouncer sur _async_update_data
- Refactor: Refactorisation de [module impacté] pour une meilleure lisibilité.
- Chore: Roadmap Bronze 99% !

### Dependency Updates
- Bump: Mise à jour de la dépendance `Saur_fr_clientr` vers la version `0.2.7`.

### Deprecated
- Fonctionnalité dépréciée : Aucune

### Removed
- Fonctionnalité supprimée : Aucune