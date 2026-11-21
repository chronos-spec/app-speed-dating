import unittest

from faux_profils import generer
from groupes import Donnees, Groupe, est_valide, former_groupes


def donnees_depuis(data: dict) -> Donnees:
    return Donnees(
        [p["id"] for p in data["profils"] if p["genre"] == "F"],
        [p["id"] for p in data["profils"] if p["genre"] == "H"],
        {k: set(v) for k, v in data["likes"].items()},
        {p["id"]: str(p["segment"]) for p in data["profils"]},
    )


class TestGroupes(unittest.TestCase):
    def test_tout_le_monde_se_like(self):
        femmes = [f"f{i}" for i in range(10)]
        hommes = [f"h{i}" for i in range(10)]
        likes = {f: set(hommes) for f in femmes} | {h: set(femmes) for h in hommes}
        groupes, reste = former_groupes(Donnees(femmes, hommes, likes), essais=2, iterations=50)
        self.assertEqual(len(groupes), 1)
        self.assertEqual(reste, [])

    def test_personne_ne_se_like(self):
        d = Donnees([f"f{i}" for i in range(10)], [f"h{i}" for i in range(10)], {})
        groupes, reste = former_groupes(d, essais=2, iterations=50)
        self.assertEqual(groupes, [])
        self.assertEqual(len(reste), 20)

    def test_groupes_respectent_les_regles(self):
        d = donnees_depuis(generer(n=200, tribus=2, popularite=0, graine=1))
        groupes, reste = former_groupes(d, min_mutuels=5, essais=5, iterations=2000)
        self.assertGreater(len(groupes), 0)
        places = [p for g in groupes for p in g.femmes + g.hommes]
        self.assertEqual(len(places), len(set(places)), "personne n'est dans deux groupes")
        self.assertEqual(len(places) + len(reste), 200)
        for g in groupes:
            self.assertEqual((len(g.femmes), len(g.hommes)), (10, 10))
            self.assertTrue(est_valide(d, g, 5, True))

    def test_validation_detecte_une_paire_sans_like(self):
        likes = {"f1": {"h1"}, "h1": {"f1"}}
        d = Donnees(["f1", "f2"], ["h1"], likes)
        self.assertFalse(est_valide(d, Groupe(["f1", "f2"], ["h1"]), 0, True))
        self.assertTrue(est_valide(d, Groupe(["f1", "f2"], ["h1"]), 0, False))


if __name__ == "__main__":
    unittest.main()
