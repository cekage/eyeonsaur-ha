# EyeOnSaur - Intégration non officielle pour le suivi de consommation d'eau Saur

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

**⚠️ Cette intégration n'est pas une application officielle de Saur. Elle a été développée par un contributeur indépendant et n'est pas affiliée à Saur ni approuvée par eux. L'utilisation de cette intégration peut être soumise aux conditions d'utilisation de Saur. ⚠️**

**EyeOnSaur** est une intégration personnalisée pour Home Assistant qui vous permet de suivre votre consommation d'eau remontée par les compteurs connectés SAUR. Elle récupère les données de consommation depuis votre compte Saur (via une API non officielle) et les affiche dans des capteurs Home Assistant, vous offrant ainsi un suivi détaillé de votre consommation quotidienne, hebdomadaire et mensuelle, ainsi qu'un historique.

## À propos de Saur

Saur est une entreprise française spécialisée dans la gestion déléguée des services de l'eau et de l'assainissement pour les collectivités locales et les industriels.

## Fonctionnalités

*   **Récupération automatique des données de consommation :** Récupère les données de consommation d'eau (journalière, hebdomadaire, mensuelle) depuis votre compte Saur.
*   **Capteurs Home Assistant :** Crée des capteurs pour le suivi de la consommation :
    *   Consommation journalière
    *   Consommation hebdomadaire
    *   Consommation mensuelle
    *   Historique de consommation
*   **Informations supplémentaires :**
    *   Relevé physique du compteur (si disponible sur votre compte en ligne)
    *   Date d'installation du compteur
*   **Configuration facile :** Installation simple manuellement, et configuration via l'interface utilisateur de Home Assistant.

## Prérequis

*   Un compte Home Assistant.
*   Un compte Saur avec un accès aux données de consommation d'eau (compteur connecté).
*   Avoir activé l'accès aux données de consommation via le site ou l'application Saur.

## Installation

### Via HACS (Home Assistant Community Store)

L'installation via HACS n'est pas encore possible, mais est prévue prochainement. L'intégration `EyeOnSaur` est en cours d'amélioration pour satisfaire les critères de qualité de HACS. Vous pourrez bientôt l'installer facilement via HACS.

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

Une fois l'intégration EyeOnSaur installée et configurée, elle créera automatiquement des capteurs dans Home Assistant pour suivre votre consommation d'eau. Voici comment visualiser vos données :

1. **Ajout de l'intégration :**
    *   Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
    *   Cliquez sur le bouton "+ Ajouter une intégration" en bas à droite.
    *   Recherchez "EyeOnSaur" et sélectionnez l'intégration.
    *   Saisissez votre adresse email et votre mot de passe Saur.
    *   Cochez la case "Je comprends et j'accepte que cette intégration ne soit pas officielle" pour confirmer que vous avez compris les implications de l'utilisation d'une intégration non officielle.
    *   Cliquez sur "Soumettre".

2. **Ajout des capteurs à la carte Énergie :**
    *   Allez dans Paramètres -> Tableaux de bord -> Énergie.
    *   Cliquez sur "Ajouter une consommation".
    *   Dans la liste déroulante "Consommation d'eau", sélectionnez le capteur "Compteur d'eau" créé par l'intégration EyeOnSaur (par exemple, `sensor.compteur_d_eau`).
    *   Configurez les autres options si nécessaire (par exemple, le coût de l'eau si vous souhaitez un suivi monétaire, **cette option sera disponible dans une future version**).
    *   Cliquez sur "Enregistrer".

3. **Visualisation de l'historique :**
    *   L'intégration mettra à jour les données de consommation **toutes les 24 heures**.
    *   Vous pouvez visualiser l'historique de votre consommation d'eau en ajoutant une carte "Historique" à votre tableau de bord et en sélectionnant le capteur "Compteur d'eau".

    Voici un exemple de ce que vous pourrez voir :

    ![Historique de consommation d'eau](https://raw.githubusercontent.com/cekage/eyeonsaur-ha/main/images/historique_fictive.png)

**Remarques :**

*   Les données de consommation sont récupérées quotidiennement.
*   L'historique de consommation affiché dépend de la disponibilité des données sur votre compte Saur.

## Dépendance

Cette intégration utilise la librairie Python non officielle [saur_client](https://github.com/cekage/Saur_fr_client) pour communiquer avec l'API de Saur.

## Désinstallation

1. Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
2. Trouvez l'intégration "EyeOnSaur" et cliquez sur les trois points verticaux.
3. Sélectionnez "Supprimer".
4. Redémarrez Home Assistant.
5. (Facultatif) Si vous avez installé l'intégration manuellement, supprimez le dossier `eyeonsaur` de votre dossier `custom_components`.

## Dépannage

Si vous rencontrez des problèmes avec l'intégration, veuillez consulter la section "Dépannage" du [guide de l'utilisateur](Lien vers le guide si existant) ou ouvrir une issue sur le [dépôt GitHub](https://github.com/cekage/eyeonsaur-ha/issues).

## Contributions

Les contributions sont les bienvenues ! Si vous souhaitez contribuer à l'amélioration de cette intégration, veuillez consulter les [directives de contribution](Lien vers les directives si existantes).

## Licence

Ce projet est sous licence [MIT](LICENSE).

---
<!-- Badges -->
[commits-shield]: https://img.shields.io/github/commit-activity/w/cekage/eyeonsaur-ha.svg
[commits]: https://github.com/cekage/eyeonsaur-ha/commits/master
[license-shield]: https://img.shields.io/github/license/cekage/eyeonsaur-ha.svg
[releases-shield]: https://img.shields.io/github/release/cekage/eyeonsaur-ha.svg
[releases]: https://github.com/cekage/eyeonsaur-ha/releases