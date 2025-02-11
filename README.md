# EyeOnSaur - Intégration non officielle pour le suivi de consommation d'eau Saur

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![Quality Scale][quality-scale-shield]][quality-scale]

[quality-scale-shield]: https://img.shields.io/badge/Quality%20Scale-Bronze-orange
[quality-scale]: https://www.home-assistant.io/integrations/quality_scale/

[commits-shield]: https://img.shields.io/github/commit-activity/w/cekage/eyeonsaur-ha.svg
[commits]: https://github.com/cekage/eyeonsaur-ha/commits/master
[license-shield]: https://img.shields.io/github/license/cekage/eyeonsaur-ha.svg
[releases-shield]: https://img.shields.io/github/release/cekage/eyeonsaur-ha.svg
[releases]: https://github.com/cekage/eyeonsaur-ha/releases

**⚠️ Cette intégration n'est pas une application officielle de Saur. Elle a été développée par un contributeur indépendant et n'est pas affiliée à Saur ni approuvée par eux. L'utilisation de cette intégration peut être soumise aux conditions d'utilisation de Saur. ⚠️**

**EyeOnSaur** est une intégration personnalisée pour Home Assistant qui vous permet de suivre votre consommation d'eau remontée par les compteurs connectés SAUR. Elle récupère les données de consommation depuis votre compte Saur (via une API non officielle) et les affiche dans des capteurs Home Assistant, vous offrant ainsi un suivi détaillé de votre consommation quotidienne, hebdomadaire et mensuelle, ainsi qu'un historique.

**Important : L'intégration EyeOnSaur n'offre pas de données de consommation en temps réel.** Les données sont mises à jour quotidiennement, généralement avec les informations de la veille. **Le capteur principal de cette intégration est conçu pour être utilisé avec le tableau de bord "Énergie" de Home Assistant pour un suivi de la consommation sur le long terme.**  Les informations les plus récentes disponibles (relevé physique, date d'installation) sont accessibles dans les attributs du capteur.

## À propos de Saur

Saur est une entreprise française spécialisée dans la gestion déléguée des services de l'eau et de l'assainissement pour les collectivités locales et les industriels.

## Fonctionnalités

*   **Récupération automatique des données de consommation :** Récupère les données de consommation d'eau (journalière, hebdomadaire, mensuelle) depuis votre compte Saur. **Notez que ces données ne sont pas en temps réel et sont généralement mises à jour quotidiennement avec les informations de la veille.**
*   **Capteurs Home Assistant :** Crée un capteur pour le suivi de la consommation :
    *   **Capteur principal pour la carte Énergie :** Conçu spécifiquement pour fonctionner avec le tableau de bord Énergie de Home Assistant.
    *   Consommation journalière (données de la veille, disponibles dans les attributs)
    *   Consommation hebdomadaire (données mises à jour quotidiennement, disponibles dans les attributs)
    *   Consommation mensuelle (données mises à jour quotidiennement, disponibles dans les attributs)
    *   Historique de consommation (suivi sur le long terme)
*   **Informations supplémentaires (disponibles dans les attributs du capteur) :**
    *   Relevé physique du compteur (si disponible sur votre compte en ligne)
    *   Date d'installation du compteur
*   **Configuration facile :** Installation simple manuellement, et configuration via l'interface utilisateur de Home Assistant.

**Pour le détail des changements entre les versions, veuillez consulter le fichier [CHANGELOG.md](CHANGELOG.md).**

## Prérequis

*   Un compte Home Assistant.
*   Un compte Saur avec un accès aux données de consommation d'eau (compteur connecté).
*   Avoir activé l'accès aux données de consommation via le site ou l'application Saur.

## Installation

### Via HACS (Home Assistant Community Store)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cekage&repository=eyeonsaur-ha&category=integration)

L'intégration `EyeOnSaur` est disponible via HACS. Cliquez sur le badge ci-dessus pour ajouter ce dépôt personnalisé à HACS, puis installez l'intégration "EyeOnSaur" depuis HACS.

L'intégration `EyeOnSaur` est en cours d'amélioration pour satisfaire les critères de qualité de HACS et être disponible directement dans le catalogue prochainement.

### Manuellement

1. Copiez le dossier `custom_components/eyeonsaur` de ce dépôt dans votre dossier de configuration Home Assistant (par exemple, `/config/custom_components/eyeonsaur`).
2. Redémarrez Home Assistant.

## Configuration

1. Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
2. Cliquez sur le bouton "+ Ajouter une intégration".
3. Recherchez "EyeOnSaur" et sélectionnez-le.
4. Suivez les instructions pour configurer l'intégration en saisissant vos identifiants Saur.
5. **(Optionnel)** Après la configuration initiale, vous pourrez modifier les options de l'intégration (par exemple le prix du m3, l'heure du relevé dans l'historique). Ces options seront disponibles ultérieurement, après stabilisation de l'intégration.

## Utilisation

Une fois l'intégration EyeOnSaur installée et configurée, elle créera automatiquement un capteur dans Home Assistant pour suivre votre consommation d'eau. **Ce capteur est principalement destiné à être utilisé dans le tableau de bord "Énergie" de Home Assistant.** Voici comment visualiser vos données :

1. **Ajout de l'intégration :**
    *   Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
    *   Cliquez sur le bouton "+ Ajouter une intégration" en bas à droite.
    *   Recherchez "EyeOnSaur" et sélectionnez l'intégration.
    *   Saisissez votre adresse email et votre mot de passe Saur.
    *   Cochez la case "Je comprends et j'accepte que cette intégration ne soit pas officielle" pour confirmer que vous avez compris les implications de l'utilisation d'une intégration non officielle.
    *   Cliquez sur "Soumettre".

2. **Ajout du capteur à la carte Énergie :**
    *   Allez dans Paramètres -> Tableaux de bord -> Énergie.
    *   Cliquez sur "Ajouter une consommation".
    *   Dans la liste déroulante "Consommation d'eau", sélectionnez le capteur "Compteur d'eau" créé par l'intégration EyeOnSaur (par exemple, `sensor.compteur_d_eau`).
    *   Configurez les autres options si nécessaire (par exemple, le coût de l'eau si vous souhaitez un suivi monétaire, **cette option sera disponible dans une future version**).
    *   Cliquez sur "Enregistrer".

3. **Visualisation de l'historique :**
    *   L'intégration mettra à jour les données de consommation **toutes les 24 heures**.
    *   Vous pouvez visualiser l'historique de votre consommation d'eau en ajoutant une carte "Historique" à votre tableau de bord et en sélectionnant le capteur "Compteur d'eau".

    Voici un exemple de ce que vous pourrez voir :

    ![Historique de consommation d'eau](https://github.com/cekage/eyeonsaur-ha/blob/main/images/hsitorique_fictive.png?raw=true)

**Remarques Importantes :**

*   **Données non temps réel :** Les données de consommation ne sont pas fournies en temps réel par SAUR et sont mises à jour quotidiennement par l'intégration, généralement avec les données de la veille.
*   **Capteur pour la carte Énergie :** Le capteur principal est conçu pour fonctionner de manière optimale avec la carte Énergie de Home Assistant pour un suivi de la consommation sur le long terme.
*   **Attributs du capteur :**  Les attributs du capteur fournissent des informations complémentaires telles que le dernier relevé physique et la date d'installation.
*   **Injection de données historiques :** L'intégration inclut une fonctionnalité d'injection de données historiques dans le recorder de Home Assistant pour assurer un suivi de la consommation le plus complet possible. **Cependant, Home Assistant n'est pas nativement conçu pour l'injection de données à posteriori, et cette fonctionnalité peut présenter des limitations.**

## Dépendance

Cette intégration utilise la librairie Python non officielle [saur_client](https://github.com/cekage/Saur_fr_client) pour communiquer avec l'API de Saur.

## Désinstallation

1. Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
2. Trouvez l'intégration "EyeOnSaur" et cliquez sur les trois points verticaux.
3. Sélectionnez "Supprimer".
4. Redémarrez Home Assistant.
5. Supprimez le dossier `eyeonsaur` du dossier `custom_components` de votre configuration Home Assistant.
6. **Supprimez le fichier `consommation_saur.db`** qui se trouve dans votre dossier de configuration Home Assistant.

## Dépannage

Si vous rencontrez des problèmes avec l'intégration, veuillez consulter la section "Dépannage" du [guide de l'utilisateur](Lien vers le guide si existant) ou ouvrir une issue sur le [dépôt GitHub](https://github.com/cekage/eyeonsaur-ha/issues).

## Contributions

Les contributions sont les bienvenues ! Si vous souhaitez contribuer à l'amélioration de cette intégration, veuillez consulter les [directives de contribution](Lien vers les directives si existantes).

## Licence

Ce projet est sous licence [MIT](LICENSE).

## Quality Scale

This integration has achieved the Bronze quality scale. This means that it meets the following criteria:

*   Appropriate polling
*   Brands
*   Common modules
*   Config flow
*   Config flow test coverage
*   Dependency transparency
*   High-level description
*   Installation instructions
*   Removal instructions
*   Entity unique ID
*   Has entity name
*   Runtime data
*   Test before configure
*   Test before setup
*   Unique config entry

---
<!-- Badges -->