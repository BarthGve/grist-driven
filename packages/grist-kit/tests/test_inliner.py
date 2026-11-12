from grist_kit.inliner import MARQUEURS, inliner, inliner_tout

PAGE = "<script>\n/* === CORE BEGIN === */\nancien\n/* === CORE END === */\n</script>\n"


def _page(tmp_path, nom="p.html", texte=PAGE):
    p = tmp_path / nom
    p.write_text(texte, encoding="utf-8")
    return p


def test_recopie_le_core_entre_marqueurs(tmp_path):
    p = _page(tmp_path)
    assert inliner(p, "nouveau()", check=False) is True
    assert p.read_text(encoding="utf-8") == PAGE.replace("ancien", "nouveau()")
    assert inliner(p, "nouveau()", check=True) is True


def test_check_ne_modifie_rien_et_renvoie_faux_si_ecart(tmp_path):
    p = _page(tmp_path)
    assert inliner(p, "nouveau()", check=True) is False
    assert p.read_text(encoding="utf-8") == PAGE


def test_marqueurs_absents_renvoie_faux(tmp_path):
    p = _page(tmp_path, texte="<html></html>")
    assert inliner(p, "x", check=False) is False
    assert p.read_text(encoding="utf-8") == "<html></html>"


def test_core_avec_antislashs_intact(tmp_path):
    core = r"const re = /\d+\n/; s = 'a\\b'; // \g<0> \1"
    p = _page(tmp_path)
    assert inliner(p, core, check=False) is True
    assert core in p.read_text(encoding="utf-8")
    assert inliner(p, core, check=True) is True


def test_inliner_tout_lit_le_core_et_traite_chaque_page(tmp_path):
    core = tmp_path / "core.js"
    core.write_text("  neuf()\n", encoding="utf-8")
    pages = [_page(tmp_path, "a.html"), _page(tmp_path, "b.html")]
    assert inliner_tout(core, pages, check=True) is False
    assert inliner_tout(core, pages, check=False) is True
    assert all("neuf()" in p.read_text(encoding="utf-8") for p in pages)
    assert inliner_tout(core, pages, check=True) is True


def test_inliner_tout_un_echec_rend_faux(tmp_path):
    core = tmp_path / "core.js"
    core.write_text("x", encoding="utf-8")
    pages = [_page(tmp_path, "a.html"), _page(tmp_path, "b.html", "rien")]
    assert inliner_tout(core, pages, check=False) is False
    assert MARQUEURS.search(pages[0].read_text(encoding="utf-8"))
