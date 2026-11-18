/**
 * ESLint config for the wet_run web tier.
 *
 * tsc already enforces `strict` + `noUnusedLocals`/`noUnusedParameters`, so the
 * rules here deliberately avoid duplicating type-level checks and focus on
 * runtime-safety and consistency. `npm run lint` (eslint src --ext ts) has been
 * unrunnable since the tier was created because this file was missing.
 */
module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  plugins: ["@typescript-eslint"],
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  rules: {
    // tsc owns unused-symbol detection; avoid double-reporting with a
    // slightly different notion of "used".
    "no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": "off",
    // `any` appears in data-boundary shims; keep it visible but non-blocking.
    "@typescript-eslint/no-explicit-any": "warn",
    // Allow intentionally-unused params prefixed with _ (interface conformance).
    "@typescript-eslint/no-empty-function": "off",
    // `while (true)` with an internal break is the idiomatic line-drawing loop
    // shape in grid.ts and dungeon_crawler.ts (Bresenham).
    "no-constant-condition": ["error", { checkLoops: false }],
  },
  ignorePatterns: ["dist", "node_modules", "e2e", "*.cjs", "*.mjs"],
};
