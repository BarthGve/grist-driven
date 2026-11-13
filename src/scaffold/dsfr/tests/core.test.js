const test = require("node:test");
const assert = require("node:assert");
const { lignesAffichables } = require("../widgets/core.js");

test("trie par titre et écarte les titres vides", () => {
  const l = lignesAffichables([{ id: 2, titre: "b" }, { id: 1, titre: " a " }, { id: 3, titre: "" }]);
  assert.deepStrictEqual(l.map((x) => x.id), [1, 2]);
});
