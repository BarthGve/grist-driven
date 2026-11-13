import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Badge } from "@gouvfr-lasuite/ui-components";

declare const grist: any; // fourni par grist-plugin-api.js

type Ligne = { id: number; titre?: string; statut?: string };

function Exemple() {
  const [lignes, setLignes] = useState<Ligne[]>([]);
  useEffect(() => {
    grist.ready({ requiredAccess: "read table" });
    grist.onRecords((records: Ligne[]) => setLignes(records ?? []));
  }, []);
  if (!lignes.length) return <p>Aucune ligne à afficher.</p>;
  return (
    <ul>
      {lignes.map((l) => (
        <li key={l.id}>{l.titre} <Badge>{l.statut}</Badge></li>
      ))}
    </ul>
  );
}

createRoot(document.getElementById("racine")!).render(<Exemple />);
