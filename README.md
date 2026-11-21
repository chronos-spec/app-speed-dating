# App speed dating

On like, on ne discute pas, on se rencontre : un speed dating de 10 femmes et 10 hommes qui se sont choisis.
La vision et la roadmap sont dans Notion (QG – App speed dating).

## Phase 2 – test manuel

Python 3.10+, sans dépendance.

```bash
# 1. Générer 200 faux profils (ou exporter les vrais likes au même format)
python faux_profils.py --n 240 --segments 4 --sortie likes.json   # 40 likes, segments

# 2. Former les groupes
python groupes.py likes.json --sortie groupes.json

# Variante : autoriser des paires sans aucun like dans un groupe
python groupes.py likes.json --souple

# Tests
python -m unittest -v
```

### Règles appliquées
- Groupes de 10 femmes + 10 hommes, chaque personne dans un seul groupe, à l'intérieur de son segment (champ `segment` du profil).
- Chaque participant a au moins `--min-mutuels` matchs mutuels dans son groupe (5 par défaut).
- Mode strict (par défaut) : chaque paire femme/homme du groupe a au moins un like dans un sens.

### Algorithme
Glouton puis recherche locale : on part de la paire mutuelle la mieux connectée, on complète
le groupe avec les profils qui ont le plus de likes avec l'autre côté (mutuel = 3 points,
simple = 1), puis on échange des membres avec l'extérieur tant que ça réduit les violations
des règles et augmente le score. On recommence tant qu'on trouve un groupe valide.

### Résultats (version 2 : 5 matchs mutuels, segments, 40 likes, mode strict)
Les likes se font uniquement à l'intérieur d'un segment (tranche d'âge + quartier, ou soirée choisie à l'avance).

| Taille du segment | Profils plutôt homogènes | Quelques profils très populaires |
|---|---|---|
| 60 inscrits | 100 % placés | 100 % placés |
| 100 inscrits | 80 % placés | 60 % placés |

À retenir : des segments de 50 à 80 inscrits par soirée, avec 40 likes, permettent de placer presque tout le monde
avec au moins 5 matchs mutuels chacun. Les non-placés sont prioritaires sur la soirée suivante.

Version 1 (20 likes, sans segments, 3 matchs) : 0 à 50 % de placés seulement.
