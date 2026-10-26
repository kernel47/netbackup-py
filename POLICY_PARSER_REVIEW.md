# Proposition de correction : policies et SLP

Vérification du 26 octobre 2026. Cible principale : NetBackup 11.1 ; prise en charge de plusieurs versions. Audit initial suivi de la correction. Voir README.md et documentation.md pour le comportement livré. La section « Correction proposée » décrit le plan initial ; les copies restent des dictionnaires API complets plutôt que des modèles fermés, afin de préserver aussi les extensions inconnues.

## Références officielles examinées

Les fichiers YAML ont été téléchargés depuis SORT puis analysés avec PyYAML. Les fichiers de travail sont dans `/tmp`, hors du projet.

- [Getting Started 11.1 : versionnement et changements de pagination](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/getting-started/).
- [Policies 11.1 : OpenAPI](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/config_policies/config_policies.yaml).
- [SLP 11.1 : OpenAPI configuration](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/config/config.yaml).
- [Rétention SLP 11.1 : schéma retentionPeriod](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/hostproperties/hostproperties.yaml).
- [Règle de rétention lorsque le stockage est une SLP](https://origin-www.veritas.com/support/en_US/doc/18716246-170847606-0/v41780533-170847606).
- [Priorité du stockage du schedule sur celui de la policy](https://origin-www.veritas.com/support/en_US/doc/18716246-163344127-0/v41780478-163344127).

## Versions vérifiées

La version publiée du contrat ne garantit pas que tous les contrats plus anciens restent acceptés : la documentation autorise leur dépréciation après la fin de vie de leur release d'origine.

| Release NetBackup | Version publiée dans les YAML examinés | Comportement du module |
| --- | --- | --- |
| 10.0 | 7.0 | 7.0 |
| 10.1 | 8.0 | 8.0 |
| 10.1.1 | 9.0 | 8.0 : patch perdu par le découpage major/minor |
| 10.2 | 9.0 | 9.0 |
| 10.3 | 10.0 | 10.0 |
| 10.4 | 11.0 | 11.0 |
| 10.5 | 12.0 | 7.0 : release absente, repli silencieux |
| 11.0 | 13.0 | 13.0 |
| 11.1 | 14.0 | global 14.0 ; policies forcées en 12.0 |
| 11.2 | 14.0 | global 14.0 ; policies forcées en 12.0 |

Sources 10.0 à 10.4 : `https://sort.veritas.com/public/documents/nbu/<release>/windowsandunix/productguides/html/config/config.yaml` ; schémas policies référencés dans ces fichiers. Sources 10.5, 11.0, 11.1 et 11.2 : `https://sort.veritas.com/public/documents/nbu/<release>/windowsandunix/productguides/html/config_policies/config_policies.yaml`.

Le contrat policies 14.0 est publié pour 11.1 et 11.2. Rien dans les documents examinés ne justifie de forcer 12.0 pour ces deux releases. Cela ne prouve pas que 12.0 est refusé par un serveur : il peut s'agir d'un ancien contrat encore accepté.

En API 14.0, `GET /config/policies/` conserve `page[offset]` et `page[limit]` mais retourne une pagination anticipée avec `hasNext`. Les liens `links.next.href` restent décrits. Il ne faut pas basculer arbitrairement cet endpoint en pagination cursor.

## Défauts et limites confirmés

1. `parse_policy_summary()` lit `storage` au niveau `attributes`, mais recherche `storageIsSLP` uniquement dans `policyAttributes`. Le schéma officiel de liste expose les deux au niveau `attributes`. Reproduction : stockage `gold-slp`, marqueur retourné `None`, nom SLP `None`.
2. `_first_copy()` accède à `copies[0]` sans vérifier que la liste contient une entrée. `copies=[]` provoque une `IndexError`.
3. `Schedule.backup_copies` contient un seul dictionnaire simplifié. Le schéma décrit jusqu'à quatre copies, une priorité et une stratégie d'échec par copie. Les copies supplémentaires, `priority` et `failStrategy` ne sont pas exposés dans les champs structurés.
4. Le parser ne remplit pas les attributs de schedule `acceleratorForcedRescan`, `mediaMultiplexing`, `retriesAllowedAfterRunDay`, `snapshotOnly` et `syntheticBackup`, présents notamment dans le schéma Standard 11.1.
5. Les clients sont réduits à `hostName`. Les détails OS/hardware et les identifiants d'instance/base de données propres aux workloads ne sont accessibles que dans `raw`.
6. L'enrichissement remplace `storage` par une destination SLP tout en conservant `storage_is_slp=True`. Cas reproduit : `storage='disk-a'`, `storage_is_slp=True`, `slp='gold-slp'`.
7. Une seule opération est utilisée pour résumer une SLP : BACKUP si présente, sinon la première. Ce choix ne représente pas un lifecycle avec snapshots, duplications et réplications, ni ses différentes règles de rétention.
8. `versionNumber` de la SLP n'est pas exposé. Le GET SLP retourne par défaut sa dernière définition ; ce numéro est distinct de la version NetBackup et du contrat API. Cette définition ne suffit pas à déduire la rétention historique des images déjà créées.
9. Les erreurs SLP dérivant de `NetBackupError` sont absorbées. L'appelant ne peut pas distinguer une résolution réussie d'une SLP inaccessible.
10. `_policy_body()` accepte le premier dictionnaire dont le nom commence par `policy`, y compris `policyAttributes`. Une réponse plate peut donc perdre ses clients et schedules. C'est un défaut de robustesse du fallback annoncé par le code ; les schémas officiels de détail examinés utilisent des enveloppes propres au type de policy. Ce défaut ne prouve pas qu'un serveur produit normalement le format plat.

`raw` conserve les réponses d'origine : la perte concerne les champs structurés et la facilité d'utilisation, pas l'intégralité du JSON stocké.

## Correction proposée

### 1. Préserver la configuration et rendre la résolution explicite

```python
policy = client.policies.get(name)  # un GET policy, aucune résolution SLP
policy = client.policies.get(name, resolve_slp=True)
```

- `policy.storage` et les stockages déclarés des copies restent les valeurs de configuration.
- Exposer les définitions résolues dans `policy.slps: dict[str, SLP]`, indexées par nom.
- Conserver toutes les opérations avec leur type, leur index, leur source, leur stockage, leur rétention et leur type de rétention.
- Ajouter `SLP.version_number`, `flag_values`, `data_classification`, `duplication_priority` et les principaux attributs d'opération manquants.
- En mode résolution, propager les erreurs par défaut. Un éventuel mode partiel explicite doit exposer les échecs par nom de SLP.
- Utiliser le même cache pendant une collecte de plusieurs policies, pour éviter de relire une SLP commune à chaque policy. Ne pas réutiliser indéfiniment un cache entre collectes.
- Pour une vue des valeurs effectives, ajouter des champs distincts indiquant l'origine de la valeur et les opérations concernées. Ne pas inventer une rétention unique au niveau policy.

### 2. Modèles structurés sans perte des valeurs utiles

Introduire `BackupCopies(copies: list[BackupCopy], priority: int | None)` et `BackupCopy(storage, retention_level, retention_period, volume_pool, media_owner, fail_strategy)`.

Conserver `retention_period` sous une forme structurée `{value, unit}`. Fournir éventuellement une propriété de présentation, sans remplacer les données. Le schéma SLP précise que `value=-1` ou `unit=INFINITE` indiquent l'infini ; `value=0` signifie expiration immédiate. Un niveau de rétention numérique, y compris zéro, ne doit pas être perdu ou converti arbitrairement en durée.

Ajouter `client_details` tout en gardant `clients: list[str]` pour les usages actuels. Ajouter `policy_attributes` et les attributs de schedule manquants. Conserver `raw` pour les champs propres aux différents workloads et les extensions futures.

### 3. Parser et héritage

- Reconnaître les enveloppes `policyStandard`, `policyVMware`, `policyOracle`, `policyGeneric`, etc., en vérifiant le contenu, et exclure explicitement `policyAttributes` des candidats.
- Corriger le résumé en lisant `attributes.storageIsSLP` avec un fallback cohérent vers `policyAttributes`.
- Traiter l'absence de copies et la liste vide sans exception ; conserver chaque copie et son ordre.
- Séparer stockage déclaré du schedule et stockage hérité. Calculer ensemble le nom de stockage et son statut SLP, en tenant compte des conventions du contrat et du workload ; ne pas mélanger un nom hérité avec un booléen d'override sans établir leur relation.
- Ne pas supprimer les valeurs explicites `False` et `0` lors de la normalisation des objets de configuration.
- Accepter les champs inconnus sans erreur tout en les conservant dans `raw`, conformément aux recommandations de compatibilité de NetBackup.

### 4. Versionnement

- Corriger la table, en tenant compte de `10.1.1` avant `10.1`, et ajouter `10.5`.
- Pour 11.1, utiliser par défaut les contrats policies et configuration 14.0 examinés. Retirer le pin implicite 12.0 ; garder une surcharge explicite par service pour un contrat ancien validé par l'utilisateur.
- Faire utiliser la même sélection de version au service SLP et à la résolution SLP des policies.
- Sur une release inconnue, demander une version API explicite ou lever une erreur claire. Ne pas revenir silencieusement en 7.0.
- Réparer l'extraction des liens de pagination avec `urllib.parse.urlsplit` et `parse_qs` pour gérer les noms et valeurs encodés. Si `hasNext=True` et aucun lien/suivant n'est fourni, le contrat policies à offset permet un calcul de la prochaine position à partir des métadonnées validées. Ne pas interpréter `count` comme un total sans définition contractuelle.

## Compatibilité et validation prévues

Le changement du type de `backup_copies`, la suppression des mutations de `storage`/`retention` et la résolution désactivée par défaut modifient le comportement public. Les publier dans une version avec une note de migration et mettre à jour README, documentation et exemples. Ne pas maintenir deux significations silencieuses pour les mêmes champs.

Tests nécessaires :

- Mapping des versions, notamment 10.1.1, 10.5, 11.1 et 11.2 ; surcharge explicite prioritaire ; release inconnue.
- Fixtures issues des formes officielles Standard, VMware, Oracle et Generic ; schémas 7.0, 12.0, 13.0 et 14.0, puis couverture des contrats intermédiaires.
- Résumé avec marqueur SLP à plat ; copies absentes/vides/multiples ; priorité, stratégie d'échec, booléens faux et niveau zéro.
- Rétentions structurées, infinies et conditionnelles ; SLP avec plusieurs opérations et numéro de version.
- GET sans résolution : un seul appel. Résolution explicite : aucune mutation des valeurs déclarées, déduplication des lectures SLP et propagation des erreurs.
- Pagination policies 14.0 avec `hasNext`, lien encodé et plusieurs pages ; anciens contrats avec `meta.pagination.next`.

Les tests actuels utilisent des réponses simulées et certains imposent précisément les simplifications problématiques. Leur réussite ne certifie pas la conformité au schéma officiel. Les cas limites signalés ont été reproduits localement ; aucune connexion à un serveur NetBackup réel n'a été effectuée.
