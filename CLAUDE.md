# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Vue d'ensemble

Site Jekyll statique hébergé sur GitHub Pages (`https://paperjam-redaction.github.io/tasteoflux`) qui publie les recettes de chefs luxembourgeois. Chaque page recette est conçue pour être **embarquée dans des sites tiers** (Paperjam principalement) via iframe — l'autonomie visuelle et le redimensionnement automatique de l'embed sont des contraintes structurantes.

Pas de framework, pas de build front : Liquid + CSS + JS vanilla. Le seul plugin Jekyll est `jekyll-seo-tag` (le reste est limité à ce que GitHub Pages autorise).

## Stack et commandes

- **Ruby** : cf. `.tool-versions`. À noter : Jekyll 3.9 (verrouillé par le gem `github-pages`) ne s'installe plus à partir de Ruby 3.4 à cause du retrait de `csv` du stdlib — si ton Ruby local est plus récent que ce que déclare `.tool-versions`, le dev Jekyll local échouera. Le déploiement réel passe par GitHub Pages côté serveur, donc ce n'est pas bloquant pour publier.
- **Dev local** : `bundle exec jekyll serve` puis `http://localhost:4000/tasteoflux/recettes/<slug>/`
- **Validation des recettes** : `pip install pyyaml jsonschema && python scripts/validate_recipes.py` — à lancer avant de pousser des changements de schéma. La CI exécute la même commande.

Pas de suite de tests, pas de linter. La seule vérification automatique est la validation de schéma des recettes.

## Architecture

### Modèle de contenu

- `_recipes/*.md` — une recette = un fichier Markdown avec un frontmatter YAML riche. Permalink défini dans `_config.yml` : `/recettes/:name/`. Le layout `recipe` est appliqué par défaut à la collection.
- `_layouts/embed.html` — layout **de base**, volontairement minimal. Porte le script inline qui détecte si la page est dans un iframe et envoie sa hauteur au parent via `postMessage`.
- `_layouts/recipe.html` — layout recette (hérite de `embed`). Boucle directement sur la liste plate `page.ingredients`.
- `index.html` — page d'index simple qui liste les recettes.

### Système d'embed (point clé non-trivial)

L'autonomie des pages recette n'est pas accidentelle : elles servent à être **iframées** depuis d'autres sites. Trois pièces coopèrent :

1. **Détection iframe** : script bloquant en `<head>` de `embed.html` qui pose `.pj-is-embedded` sur `<html>` si `window.self !== window.top`. Posé **avant** le rendu pour éviter tout flash.
2. **Height reporter** : même script, observe `document.documentElement` via `ResizeObserver` et envoie `{type: 'tasteoflux:embed-height', height}` à `window.parent`. Permet aux iframes responsives de se redimensionner automatiquement.
3. **Générateur d'embed** : bouton flottant « Intégrer » (HTML dans `recipe.html`, JS dans `assets/js/embed-tool.js`) qui construit deux snippets (iframe simple à hauteur fixe + iframe responsive avec un script `postMessage` côté parent). Le bouton est masqué via CSS quand `.pj-is-embedded` est présent — il n'apparaît jamais dans une page embarquée.

Côté parent (snippet responsive) : l'identification de l'iframe se fait par `contentWindow === e.source` (pas besoin d'ID) ; l'origine est vérifiée via `e.origin`.

### CMS (Sveltia)

- `admin/index.html` charge **Sveltia CMS** (fork de Decap) depuis le CDN.
- `admin/config.yml` définit le schéma des recettes et la connexion GitHub. Les commits CMS vont **directement sur main** (pas d'editorial workflow). Les changements sont donc visibles immédiatement après publication.
- **Le schéma `admin/config.yml` et `scripts/validate_recipes.py` doivent rester synchronisés.** Si tu modifies l'un, mets l'autre à jour.
- **Piège connu** : le navigateur de l'éditeur peut garder l'ancien `config.yml` en cache. Après tout changement de schéma, un hard-refresh (Cmd+Shift+R) du CMS est nécessaire ; sinon l'éditeur publie avec le vieux schéma et corrompt le contenu. Une régression de ce type s'est déjà produite (structure `group/items` réintroduite dans les ingrédients après que `_layouts/recipe.html` ait été migré vers la liste plate).

### Pipeline CI / déploiement

`.github/workflows/jekyll-gh-pages.yml` — trois jobs séquentiels :

| Job | Trigger | Rôle |
|---|---|---|
| `validate` | push main + PR | Lance `scripts/validate_recipes.py` |
| `build` | push main uniquement (`if: github.event_name == 'push'`) | Jekyll build |
| `deploy` | push main uniquement | Deploy GitHub Pages |

Sur une PR : seul `validate` tourne, ce qui bloque le merge en cas de schéma cassé. Sur push main : les trois jobs s'enchaînent. La validation gate donc à la fois le merge **et** le déploiement.

`scripts/validate_recipes.py` utilise un JSON Schema strict (`additionalProperties: False` à tous les niveaux) qui rejette en particulier :
- les ingrédients au format imbriqué `group/items` (ancien schéma, régression connue)
- les champs requis vides (`qty`, `name`, `title`, `body`)
- les champs top-level inconnus dans le frontmatter

## Conventions

- **Tout le contenu utilisateur est en français.** Templates, commentaires, messages de commit, copy : tout en français. Le code (identifiants, variables) reste en anglais sauf les classes CSS qui suivent le préfixe `pj-` historique.
- **Messages de commit en français**, style impératif. Inclure le trailer `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` quand Claude contribue.
- **PRs en français** également, avec sections **Résumé** et **Test plan**.
- Le repo a un bot de review **Kilo Code** qui commente automatiquement les PRs. Adresser les warnings et répondre sur chaque thread via `gh api` avec une mention du commit de fix, puis résoudre le thread via GraphQL (`resolveReviewThread`).

## Pièges à éviter

- Ne pas réintroduire la structure `group/items` dans `ingredients` — c'est aplati partout (template, CMS, validateur). La CI bloquera.
- Ne pas ajouter de champ au frontmatter d'une recette sans mettre à jour à la fois `admin/config.yml` (pour que le CMS l'expose) **et** `scripts/validate_recipes.py` (sinon `additionalProperties: False` rejette).
- Ne pas casser le contrat `postMessage` (`type: 'tasteoflux:embed-height'`) entre `embed.html` et le snippet responsive généré par `embed-tool.js` — les deux doivent rester alignés sinon les embeds existants se figent à leur dernière hauteur connue.
- Ne pas supposer que Jekyll tourne en local. Quand un changement touche du Liquid, soit le tester via un environnement Jekyll fonctionnel (pas garanti), soit le faire valider par la PR (preview GitHub Pages après merge ou via inspection visuelle).
