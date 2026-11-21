"""Génère de faux profils et de faux likes pour tester la formation des groupes.

Modèle simple : chaque personne s'inscrit dans un segment (âge, quartier, soirée)
et a une popularité. Elle like 40 profils de l'autre genre de son segment,
avec une préférence pour les profils populaires.

Usage :
    python faux_profils.py --n 200 --segments 4 --sortie likes.json
"""
from __future__ import annotations

import argparse
import json
import random


def generer(n: int = 200, nb_likes: int = 40, tribus: int = 4, fidelite: float = 1.0,
            popularite: float = 1.0, graine: int = 0) -> dict:
    """n profils, moitié femmes moitié hommes.

    fidelite   : probabilité qu'un like reste dans le segment (1 = toujours).
    popularite : 0 = tous les profils ont le même attrait ; plus haut = likes concentrés.
    """
    rng = random.Random(graine)
    profils = []
    for i in range(n):
        genre = "F" if i % 2 == 0 else "H"
        profils.append({
            "id": f"{genre.lower()}{i // 2 + 1}",
            "genre": genre,
            "segment": rng.randrange(tribus),
            "attrait": rng.lognormvariate(0, popularite) if popularite > 0 else 1.0,
        })

    likes: dict[str, list[str]] = {}
    for p in profils:
        autres = [o for o in profils if o["genre"] != p["genre"]]
        meme = [o for o in autres if o["segment"] == p["segment"]]
        ailleurs = [o for o in autres if o["segment"] != p["segment"]]
        choisis: set[str] = set()
        while len(choisis) < min(nb_likes, len(autres)):
            vivier = meme if (meme and rng.random() < fidelite) else (ailleurs or meme)
            o = rng.choices(vivier, weights=[x["attrait"] for x in vivier])[0]
            choisis.add(o["id"])
        likes[p["id"]] = sorted(choisis)

    return {"profils": [{"id": p["id"], "genre": p["genre"], "segment": p["segment"]} for p in profils],
            "likes": likes}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--likes", type=int, default=40)
    ap.add_argument("--segments", dest="tribus", type=int, default=4)
    ap.add_argument("--fidelite", type=float, default=1.0)
    ap.add_argument("--popularite", type=float, default=1.0)
    ap.add_argument("--graine", type=int, default=0)
    ap.add_argument("--sortie", default="likes.json")
    a = ap.parse_args()
    data = generer(a.n, a.likes, a.tribus, a.fidelite, a.popularite, a.graine)
    with open(a.sortie, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"{a.n} profils écrits dans {a.sortie}")


if __name__ == "__main__":
    main()
