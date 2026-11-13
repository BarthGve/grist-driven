// Cœur pur du widget : testé par node:test, recopié dans les pages par `python -m grist_kit inliner`.
function normaliser(texte) {
  return String(texte || "").trim();
}

function lignesAffichables(records) {
  return records
    .map((r) => ({ id: r.id, titre: normaliser(r.titre), statut: normaliser(r.statut) }))
    .filter((l) => l.titre !== "")
    .sort((a, b) => a.titre.localeCompare(b.titre, "fr"));
}

if (typeof module !== "undefined") module.exports = { normaliser, lignesAffichables };
