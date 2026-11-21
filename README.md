# App speed dating

On like, on ne discute pas, on se rencontre : un speed dating de 10 femmes et 10 hommes qui se sont choisis.
La vision et la roadmap sont dans Notion (QG – App speed dating).

## Phase 2 – test manuel

Python 3.10+, sans dépendance.

```bash
# 1. Générer 200 faux profils (ou exporter les vrais likes au même format)
python faux_profils.py --n 200 --tribus 4 --sortie likes.json

# 2. Former les groupes
python groupes.py likes.json --min-mutuels 3 --sortie groupes.json

# Variante : autoriser des paires sans aucun like dans un groupe
python groupes.py likes.json --souple

# Tests
python -m unittest -v
```

### Règles appliquées
- Groupes de 10 femmes + 10 hommes, chaque personne dans un seul groupe.
- Chaque participant a au moins `--min-mutuels` matchs mutuels dans son groupe (3 par défaut).
- Mode strict (par défaut) : chaque paire femme/homme du groupe a au moins un like dans un sens.

### Algorithme
Glouton puis recherche locale : on part de la paire mutuelle la mieux connectée, on complète
le groupe avec les profils qui ont le plus de likes avec l'autre côté (mutuel = 3 points,
simple = 1), puis on échange des membres avec l'extérieur tant que ça réduit les violations
des règles et augmente le score. On recommence tant qu'on trouve un groupe valide.

### Premiers résultats (200 faux profils, 20 likes chacun)
| Cas | Strict | Souple |
|---|---|---|
| Une seule tribu (tout le monde like au hasard dans tout le vivier) | 0 % placés | 0–10 % |
| 4 tribus (âge/quartier/style) | 20–40 % | 40–70 % |
| 8 tribus | 40–50 % | 40–80 % |

Le blocage vient surtout de la règle stricte (100 paires avec au moins un like) : avec seulement 20
likes par personne, peu de groupes la satisfont. Les leviers : regrouper les inscrits par tribu
(âge, quartier), autoriser plus de likes, ou passer en mode souple.
