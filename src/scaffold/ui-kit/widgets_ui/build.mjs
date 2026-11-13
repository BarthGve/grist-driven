// Construit chaque widget en un HTML autonome dist/<entrée>.html et affiche sa taille.
// Un build par entrée : vite-plugin-singlefile n'accepte qu'une page à la fois.
import { build } from "vite";
import { readdirSync, statSync } from "node:fs";

// Une entrée par page HTML de src/ ; `node build.mjs exemple` n'en construit qu'une.
const ENTREES = readdirSync("src").filter((f) => f.endsWith(".html")).map((f) => f.slice(0, -5));
const demandees = process.argv.slice(2);
const choisies = demandees.length ? demandees : ENTREES;
for (const entree of choisies) {
  if (!ENTREES.includes(entree)) throw new Error(`entrée inconnue : ${entree} (${ENTREES.join(", ")})`);
  await build({
    logLevel: "warn",
    build: {
      emptyOutDir: entree === choisies[0],
      rollupOptions: { input: `${import.meta.dirname}/src/${entree}.html`, output: { format: "iife", inlineDynamicImports: true } },
    },
  });
  console.log(`${entree} : ${(statSync(`dist/${entree}.html`).size / 1024).toFixed(0)} Ko`);
}
