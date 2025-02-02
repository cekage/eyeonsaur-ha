# EyeOnSaur - Intégration non officielle pour le suivi de consommation d'eau Saur

**⚠️ Cette intégration n'est pas une application officielle de Saur. Elle a été développée par un contributeur indépendant et n'est pas affiliée à Saur ni approuvée par eux. L'utilisation de cette intégration peut être soumise aux conditions d'utilisation de Saur. ⚠️**

L'intégration EyeOnSaur permet de récupérer les données de consommation d'eau à partir de votre compte Saur et de les afficher dans Home Assistant.
Vous pouvez ainsi suivre votre consommation d'eau quotidienne, hebdomadaire et mensuelle, et visualiser l'historique de votre consommation.

## À propos de Saur

Saur est une entreprise française spécialisée dans la gestion déléguée des services de l'eau et de l'assainissement pour les collectivités locales et les industriels.

## Fonctionnalités

*   Récupération des données de consommation d'eau depuis votre compte Saur.
*   Affichage de la consommation quotidienne, hebdomadaire et mensuelle dans Home Assistant.
*   Historique de la consommation d'eau.
*   Relevé physique du compteur (si disponible).
*   Date d'installation du compteur.

## Prérequis

*   Avoir un compte Home Assistant.
*   Avoir un compte Saur avec un accès aux données de consommation d'eau.
*   Activer l'accès aux données de consommation via le site ou l'application Saur.

## Installation

1. **Via HACS (Home Assistant Community Store):**

    *   Assurez-vous d'avoir HACS installé.
    *   Dans Home Assistant, allez dans HACS -> Intégrations.
    *   Cliquez sur le bouton "Explorer et télécharger des dépôts".
    *   Recherchez "EyeOnSaur" et cliquez sur "Télécharger".
    *   Redémarrez Home Assistant.

2. **Manuellement:**

    *   Copiez le dossier `custom_components/eyeonsaur` de ce dépôt dans votre dossier de configuration Home Assistant (par exemple, `/config/custom_components/eyeonsaur`).
    *   Redémarrez Home Assistant.

3. **Configuration:**
    *   Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
    *   Cliquez sur le bouton "+ Ajouter une intégration".
    *   Recherchez "EyeOnSaur" et sélectionnez-le.
    *   Suivez les instructions pour configurer l'intégration en saisissant vos identifiants Saur.

## Désinstallation

1. Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
2. Trouvez l'intégration "EyeOnSaur" et cliquez sur les trois points verticaux.
3. Sélectionnez "Supprimer".
4. Redémarrez Home Assistant.
5. (Facultatif) Si vous avez installé l'intégration manuellement, supprimez le dossier `eyeonsaur` de votre dossier `custom_components`.

## Dépannage

Si vous rencontrez des problèmes avec l'intégration, veuillez consulter la section "Dépannage" du [guide de l'utilisateur](Lien vers le guide si existant) ou ouvrir une issue sur le [dépôt GitHub](https://github.com/cekage/Saur_fr_client/issues).

## Contributions

Les contributions sont les bienvenues ! Si vous souhaitez contribuer à l'amélioration de cette intégration, veuillez consulter les [directives de contribution](Lien vers les directives si existantes).

## Licence

Ce projet est sous licence [MIT](LICENCE).