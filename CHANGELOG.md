# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.1.9] - 2024-02-27

### Added
- ✨ Ajout du sensor **Date Installation**
- ✨ Ajout du sensor **Date Contrat**
- ✨ Ajout du sensor **Date Relevé physique**
- ✨ Ajout du sensor **Valeur Relevé physique**
- ✨ Ajout du sensor **Numéro de série**
- ⚡ Ajout du sensor **Valeur pour Panneau Énergie**
- 🔄 Gère tous les **compteurs actifs**
- 📦 Regroupement des **compteurs actifs par contrats**

### Fixed
- 🛠️ Rétablissement du **dernier relevé** dans les attributs du sensor
- 🔧 Correction du **double _authenticate()**

### Changed
- 📜 `manifest.json` utilise maintenant **PyPi**
- 🔨 Refonte totale de la **base de données**
- ⚙️ Utilisation du **DEBUG** de `configuration.yaml`
- ✅ Couverture de **test**

### Dependency Updates
- ⬆️ Mise à jour de la dépendance `Saur_fr_clientr` vers la version **0.3.2** de **PyPi**

### Deprecated
- 🚫 Fonctionnalité dépréciée : **Aucune**

### Removed
- 🗑️ Fonctionnalité supprimée : **Aucune**