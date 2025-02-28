# EyeOnSaur - Intégration Saur pour Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![Quality Scale][quality-scale-shield]][quality-scale]

[releases-shield]: https://img.shields.io/github/release/cekage/eyeonsaur-ha.svg
[releases]: https://github.com/cekage/eyeonsaur-ha/releases
[license-shield]: https://img.shields.io/github/license/github/cekage/eyeonsaur-ha.svg
[license]: LICENSE
[quality-scale-shield]: https://img.shields.io/badge/Quality%20Scale-Bronze-orange
[quality-scale]: https://www.home-assistant.io/integrations/quality_scale/

**⚠️ ATTENTION : Cette intégration n'est *pas* une application officielle de Saur. Elle est développée par un contributeur indépendant, sans affiliation ni approbation de Saur. L'auteur décline toute responsabilité en cas de problème lié à son utilisation. Son utilisation peut être soumise aux [Conditions Générales d'Utilisation de Saur](https://www.saurclient.fr/conditions-generales-dutilisation-du-site). ⚠️**

**EyeOnSaur** est une intégration Home Assistant qui permet de suivre votre consommation d'eau Saur. Elle récupère les données **passées** (donc au mieux, la veille), mises à jour quotidiennement et *non en temps réel*, depuis votre compte Saur via une API non officielle. Les données sont structurées par **contrat**, puis par **compteur**. Chaque compteur expose des **données fixes** (date d'installation, numéro de série) et des **données de relevé** (date du relevé, valeur du relevé).

L'intégration injecte les données directement dans le tableau de bord "Énergie" de Home Assistant pour un suivi quotidien, hebdomadaire, mensuel et un historique de votre consommation. **Le capteur *Panneau Énergie* est *exclusivement* conçu pour être utilisé avec le tableau de bord "Énergie" de Home Assistant. Sa valeur restera toujours "inconnue", les données étant directement injectées dans l'historique du tableau de bord.**

## À propos de Saur

[Saur](https://www.saur.com/fr) est une entreprise française spécialisée dans la gestion déléguée des services de l'eau et de l'assainissement pour les collectivités locales et les industriels.

## Fonctionnalités

*   **Intégration au tableau de bord Énergie :** Injecte les données de consommation d'eau (données de la veille, non temps réel) directement dans l'historique utilisé par le tableau de bord "Énergie" de Home Assistant pour un suivi quotidien, hebdomadaire, mensuel et un historique. *Le compteur d'eau doit être ajouté au tableau de bord Énergie par l'utilisateur.*
*   **Capteur "Panneau Énergie" :** Crée un capteur *Panneau Énergie* qui est *exclusivement* utilisé par le tableau de bord "Énergie". Sa valeur restera toujours "inconnue".
*   **Informations du compteur :** Expose des informations fixes liées au compteur (date d'installation, numéro de série) et des informations de relevé (date du relevé, valeur du relevé).
*   **Configuration via l'interface utilisateur :** Configuration simple via l'interface web de Home Assistant.

**Consultez le [CHANGELOG.md](CHANGELOG.md) pour découvrir les améliorations et corrections apportées à chaque version !**

## Prérequis

*   Un serveur Home Assistant installé et fonctionnel.
*   Un compteur Saur connecté et remontant activement des données à Saur :
    ![Un compteur SAUR connecté](https://github.com/cekage/eyeonsaur-ha/blob/main/images/compteur.png?raw=true)
*   Les données de consommation d'eau doivent être visibles et actives dans votre [Espace Client Saur](https://mon-espace.saurclient.fr/fr/ma-consommation). *Vérifiez que vous pouvez consulter vos données de consommation sur le site web de Saur.*

## Installation

### Via HACS (Home Assistant Community Store)

HACS est la méthode recommandée pour installer EyeOnSaur, car elle simplifie l'installation et les mises à jour.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cekage&repository=eyeonsaur-ha&category=integration)

Pour installer EyeOnSaur via HACS :

1.  Cliquez sur le badge ci-dessus pour ajouter ce dépôt personnalisé à HACS.
2.  Installez l'intégration "EyeOnSaur" depuis HACS.

### Manuellement

1.  Si le dossier `custom_components` n'existe pas dans votre dossier de configuration Home Assistant (par exemple, `/config/`), créez-le.
2.  Copiez le dossier `custom_components/eyeonsaur` de ce dépôt dans votre dossier de configuration Home Assistant (par exemple, `/config/custom_components/eyeonsaur`).
3.  Redémarrez Home Assistant *après* avoir copié le dossier.

## Configuration

1. Redémarrez Home Assistant.
2. Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
3. Cliquez sur le bouton "+ Ajouter une intégration".
4. Recherchez "EyeOnSaur" et sélectionnez-le.
5. Suivez les instructions pour configurer l'intégration en saisissant votre adresse email et votre mot de passe Saur. Vous devrez également accepter que cette intégration n'est pas officielle.
6. **(Optionnel)** Après la configuration initiale, vous pourrez modifier les options de l'intégration (par exemple, le prix du m3, l'heure du relevé dans l'historique). *Ces options ne sont pas encore actives et seront disponibles dans une future version, après stabilisation de l'intégration.*

## Utilisation

Une fois l'intégration EyeOnSaur installée et configurée, elle injecte directement les données de votre consommation d'eau dans l'historique du compteur, qui est utilisé par le tableau de bord "Énergie" de Home Assistant.  Il est ensuite nécessaire d'ajouter le compteur au tableau de bord Énergie. Voici comment procéder :

1.  **Ajout du compteur d'eau au tableau de bord Énergie :**
    *   Allez dans Paramètres -> Tableaux de bord -> Énergie.
    *   Cliquez sur "Ajouter une consommation".
    *   Dans la liste déroulante "Consommation d'eau", sélectionnez le capteur `sensor.compteur_NumeroDeSerieDuCompteur_panneau_energie` créé par l'intégration EyeOnSaur. *L'interface affichera un message d'erreur : "⚠️ Entité indisponible L'état de ces entités configurées n'est actuellement pas disponible : sensor.compteur_NumeroDeSerieDuCompteur_panneau_energie (unknown)". Ce comportement est normal.*
    *   Cliquez sur "Enregistrer".

2.  **Visualisation de votre consommation :**
    *   Vos données de consommation d'eau seront automatiquement affichées dans le tableau de bord "Énergie", avec un suivi quotidien, hebdomadaire, mensuel et un historique.

Exemple de ce que vous pourrez voir dans le tableau de bord Énergie :

![Tableau de bord Énergie avec la consommation d'eau EyeOnSaur](https://github.com/cekage/eyeonsaur-ha/blob/main/images/hsitorique_fictive.png?raw=true)

**Remarques Importantes :**

*   **Données différées :** Les données de consommation sont fournies avec un délai (généralement la veille) et ne sont pas en temps réel.
*   **Utilisation du tableau de bord Énergie :** L'intégration est conçue pour fonctionner *exclusivement* avec le tableau de bord Énergie de Home Assistant.
*   **Injection d'historique :** L'intégration injecte les données directement dans l'historique du tableau de bord Énergie. *Cette méthode peut présenter des limitations.*

## Dépendance

Cette intégration utilise la librairie Python non officielle [saur_client](https://github.com/cekage/Saur_fr_client) (non maintenue par Saur) pour communiquer avec l'API de Saur.

## Désinstallation

1. Si vous avez installé l'intégration via HACS, désinstallez-la de préférence via HACS.
2. Dans Home Assistant, allez dans Paramètres -> Appareils et services -> Intégrations.
3. Trouvez l'intégration "EyeOnSaur" et cliquez sur les trois points verticaux.
4. Sélectionnez "Supprimer".
5. Redémarrez Home Assistant (pour que les changements soient pris en compte).
6. Supprimez le dossier `eyeonsaur` du dossier `custom_components` de votre configuration Home Assistant.
7. **Supprimez le fichier `consommation_saur_EntryUID.db`** (où EntryUID est une chaîne de caractères aléatoire) qui se trouve dans votre dossier de configuration Home Assistant (pour supprimer les données persistantes liées à l'intégration). *Le nom complet du fichier commence par `consommation_saur_` et se termine par `.db`.*

## Dépannage

Si vous rencontrez des problèmes avec l'intégration, veuillez ouvrir une issue sur le [dépôt GitHub](https://github.com/cekage/eyeonsaur-ha/issues).

## Contributions

Les contributions sont les bienvenues ! Si vous souhaitez contribuer à l'amélioration de cette intégration, n'hésitez pas à ouvrir une issue ou à proposer une pull request sur le dépôt GitHub.

## Licence

Ce projet est sous licence [MIT](LICENSE). La licence MIT permet l'utilisation, la modification et la distribution du code, même à des fins commerciales, sous réserve de certaines conditions (voir le fichier LICENSE pour plus de détails).

## Échelle de Qualité

Cette intégration a atteint le niveau de qualité Bronze, ce qui signifie qu'elle remplit les critères suivants (liste non exhaustive) :

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

Pour plus d'informations, consultez la [documentation sur la Quality Scale](https://www.home-assistant.io/integrations/quality_scale/).