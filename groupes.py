"""Formation des groupes de speed dating (10 femmes + 10 hommes) à partir des likes.

Règles (cf. page Vision dans Notion) :
- chaque participant a au moins `min_mutuels` matchs mutuels dans son groupe ;
- dans un groupe, chaque paire femme/homme a au moins un like dans un sens
  (personne ne rencontre quelqu'un qu'il n'a ni liké ni été liké par lui),
  sauf si `exiger_interet=False`.

Usage :
    python groupes.py likes.json [--taille 10] [--min-mutuels 3] [--sortie groupes.json]

Format de likes.json :
    {"profils": [{"id": "f1", "genre": "F"}, ...],
     "likes": {"f1": ["h3", "h7"], "h3": ["f1"], ...}}
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field

POIDS_MUTUEL = 3
POIDS_SIMPLE = 1


@dataclass
class Donnees:
    femmes: list[str]
    hommes: list[str]
    likes: dict[str, set[str]]

    def interet(self, f: str, h: str) -> int:
        """0 = aucun like, 1 = like dans un seul sens, 2 = like mutuel."""
        return (h in self.likes.get(f, set())) + (f in self.likes.get(h, set()))


@dataclass
class Groupe:
    femmes: list[str] = field(default_factory=list)
    hommes: list[str] = field(default_factory=list)


def charger(chemin: str) -> Donnees:
    with open(chemin, encoding="utf-8") as fh:
        brut = json.load(fh)
    femmes = [p["id"] for p in brut["profils"] if p["genre"] == "F"]
    hommes = [p["id"] for p in brut["profils"] if p["genre"] == "H"]
    likes = {k: set(v) for k, v in brut["likes"].items()}
    return Donnees(femmes, hommes, likes)


def _score_paire(d: Donnees, f: str, h: str) -> int:
    i = d.interet(f, h)
    return POIDS_MUTUEL if i == 2 else POIDS_SIMPLE if i == 1 else 0


def score_groupe(d: Donnees, g: Groupe) -> int:
    return sum(_score_paire(d, f, h) for f in g.femmes for h in g.hommes)


def mutuels(d: Donnees, personne: str, autres: list[str]) -> int:
    return sum(d.interet(personne, o) == 2 if personne in d.femmes else d.interet(o, personne) == 2
               for o in autres)


def est_valide(d: Donnees, g: Groupe, min_mutuels: int, exiger_interet: bool) -> bool:
    for f in g.femmes:
        if sum(d.interet(f, h) == 2 for h in g.hommes) < min_mutuels:
            return False
    for h in g.hommes:
        if sum(d.interet(f, h) == 2 for f in g.femmes) < min_mutuels:
            return False
    if exiger_interet:
        return all(d.interet(f, h) > 0 for f in g.femmes for h in g.hommes)
    return True


def _penalite(d: Donnees, g: Groupe, min_mutuels: int, exiger_interet: bool) -> int:
    """Mesure à quel point le groupe viole les règles (0 = valide)."""
    p = 0
    for f in g.femmes:
        p += max(0, min_mutuels - sum(d.interet(f, h) == 2 for h in g.hommes))
    for h in g.hommes:
        p += max(0, min_mutuels - sum(d.interet(f, h) == 2 for f in g.femmes))
    if exiger_interet:
        p += sum(d.interet(f, h) == 0 for f in g.femmes for h in g.hommes)
    return p


def _construire(d: Donnees, femmes: set[str], hommes: set[str], taille: int,
                rng: random.Random) -> Groupe | None:
    """Construit un groupe glouton à partir de la meilleure paire mutuelle disponible."""
    paires = [(f, h) for f in femmes for h in hommes if d.interet(f, h) == 2]
    if not paires:
        return None
    rng.shuffle(paires)

    def degre(p: str, cote: set[str]) -> int:
        return sum((d.interet(p, o) if p in femmes else d.interet(o, p)) == 2 for o in cote)

    f0, h0 = max(paires, key=lambda fh: degre(fh[0], hommes) + degre(fh[1], femmes))
    g = Groupe([f0], [h0])
    while len(g.femmes) < taille or len(g.hommes) < taille:
        # On complète le côté le moins rempli.
        if len(g.femmes) <= len(g.hommes) and len(g.femmes) < taille:
            dispo = [f for f in femmes if f not in g.femmes]
            if not dispo:
                return None
            g.femmes.append(max(dispo, key=lambda f: (sum(_score_paire(d, f, h) for h in g.hommes),
                                                      rng.random())))
        else:
            dispo = [h for h in hommes if h not in g.hommes]
            if not dispo:
                return None
            g.hommes.append(max(dispo, key=lambda h: (sum(_score_paire(d, f, h) for f in g.femmes),
                                                      rng.random())))
    return g


def _ameliorer(d: Donnees, g: Groupe, femmes: set[str], hommes: set[str], min_mutuels: int,
               exiger_interet: bool, iterations: int, rng: random.Random) -> Groupe:
    """Recherche locale : échange un membre avec une personne extérieure si ça améliore."""
    def cout(gr: Groupe) -> tuple[int, int]:
        return (_penalite(d, gr, min_mutuels, exiger_interet), -score_groupe(d, gr))

    meilleur = cout(g)
    for _ in range(iterations):
        cote = rng.choice(["F", "H"])
        membres = g.femmes if cote == "F" else g.hommes
        reserve = [p for p in (femmes if cote == "F" else hommes) if p not in membres]
        if not reserve:
            continue
        i = rng.randrange(len(membres))
        ancien = membres[i]
        membres[i] = rng.choice(reserve)
        nouveau = cout(g)
        if nouveau <= meilleur:
            meilleur = nouveau
        else:
            membres[i] = ancien
        if meilleur[0] == 0 and rng.random() < 0.002:
            break
    return g


def former_groupes(d: Donnees, taille: int = 10, min_mutuels: int = 3, exiger_interet: bool = True,
                   essais: int = 20, iterations: int = 4000, graine: int = 0
                   ) -> tuple[list[Groupe], list[str]]:
    """Forme autant de groupes valides que possible. Renvoie (groupes, personnes non placées)."""
    rng = random.Random(graine)
    femmes, hommes = set(d.femmes), set(d.hommes)
    groupes: list[Groupe] = []
    while len(femmes) >= taille and len(hommes) >= taille:
        trouve = None
        for _ in range(essais):
            g = _construire(d, femmes, hommes, taille, rng)
            if g is None:
                break
            g = _ameliorer(d, g, femmes, hommes, min_mutuels, exiger_interet, iterations, rng)
            if est_valide(d, g, min_mutuels, exiger_interet):
                if trouve is None or score_groupe(d, g) > score_groupe(d, trouve):
                    trouve = g
        if trouve is None:
            break
        groupes.append(trouve)
        femmes -= set(trouve.femmes)
        hommes -= set(trouve.hommes)
    return groupes, sorted(femmes | hommes)


def rapport(d: Donnees, groupes: list[Groupe], non_places: list[str]) -> dict:
    sortie = {"groupes": [], "non_places": non_places}
    for n, g in enumerate(groupes, 1):
        tous = [(p, mutuels(d, p, g.hommes if p in g.femmes else g.femmes))
                for p in g.femmes + g.hommes]
        sortie["groupes"].append({
            "numero": n,
            "femmes": g.femmes,
            "hommes": g.hommes,
            "score": score_groupe(d, g),
            "matchs_mutuels_min": min(m for _, m in tous),
            "matchs_mutuels_moyen": round(sum(m for _, m in tous) / len(tous), 1),
        })
    return sortie


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("likes")
    ap.add_argument("--taille", type=int, default=10)
    ap.add_argument("--min-mutuels", type=int, default=3)
    ap.add_argument("--souple", action="store_true",
                    help="autorise des paires sans aucun like dans le groupe")
    ap.add_argument("--sortie")
    args = ap.parse_args()

    d = charger(args.likes)
    groupes, non_places = former_groupes(d, args.taille, args.min_mutuels, not args.souple)
    r = rapport(d, groupes, non_places)
    texte = json.dumps(r, ensure_ascii=False, indent=2)
    if args.sortie:
        with open(args.sortie, "w", encoding="utf-8") as fh:
            fh.write(texte)
    print(f"{len(groupes)} groupe(s) formé(s), {len(non_places)} personne(s) non placée(s).")
    for g in r["groupes"]:
        print(f"  Groupe {g['numero']} : score {g['score']}, matchs mutuels min {g['matchs_mutuels_min']}, "
              f"moyenne {g['matchs_mutuels_moyen']}")


if __name__ == "__main__":
    main()
