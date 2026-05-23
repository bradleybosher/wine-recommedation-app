# synonyms.py

## Responsibility

Synonym and appellation expansion for grape varieties and wine regions. Enables the retrieval pre-filter to match wine-list entries that use local synonyms, sub-appellations, or alternative spellings for terms stored in the taste profile.

## Dependencies

Pure Python — no imports beyond stdlib `unicodedata` (via callers).

## Public Interface

```python
def expand_term(term: str) -> list[str]
  Return a list containing the canonical term plus all known synonyms/sub-appellations.
  Returns [term] if no expansion is defined (safe default).

def expand_terms(terms: list[str]) -> list[str]
  Expand all terms in the list. Returns a flat deduplicated list.
```

## Data Structures

### `_EXPANSIONS: dict[str, list[str]]`

Maps canonical tokens (lowercase) to their expansion lists. Two categories:

**Grape synonyms** (canonical → local names / alternate spellings):
- `"pinot noir"` → Spätburgunder, Pinot Nero, Blauburgunder
- `"grenache"` → Garnacha, Cannonau
- `"syrah"` → Shiraz
- `"tempranillo"` → Tinto Fino, Tinta del País, Tinta Roriz, Aragonez, Ull de Llebre
- `"mourvèdre"` → Monastrell, Mataro
- `"sangiovese"` → Brunello, Prugnolo Gentile, Morellino
- `"nebbiolo"` → Spanna, Picotener, Chiavennasca
- `"garganega"` → Soave (regional alias)
- `"vermentino"` → Rolle
- `"chenin blanc"` → Steen

**Region/appellation expansions** (canonical region → sub-appellations and aliases):
- `"burgundy"` → Bourgogne, Côte de Nuits, Côte de Beaune, Gevrey-Chambertin, Vosne-Romanée, Nuits-Saint-Georges, Chambolle-Musigny, Morey-Saint-Denis, Pommard, Volnay, Meursault, Puligny-Montrachet, Chassagne-Montrachet, Marsannay, Fixin, Aloxe-Corton, Savigny-lès-Beaune, Saint-Aubin, Santenay, Maranges, Hautes Côtes de Nuits, Hautes Côtes de Beaune, Côte Chalonnaise, Mâconnais, Givry, Mercurey, Rully, Montagny
- `"champagne"` → Reims, Épernay, Côte des Blancs, Montagne de Reims, Vallée de la Marne, Aube, Grower Champagne
- `"loire"` → Muscadet, Sancerre, Pouilly-Fumé, Vouvray, Chinon, Bourgueil, Saint-Nicolas-de-Bourgueil, Anjou, Savennières, Coteaux du Layon, Touraine, Montlouis, Crémant de Loire
- `"rhône"` → Châteauneuf-du-Pape, Gigondas, Vacqueyras, Vinsobres, Cairanne, Lirac, Tavel, Crozes-Hermitage, Hermitage, Saint-Joseph, Cornas, Condrieu, Côte-Rôtie, Côtes du Rhône
- `"alsace"` → Alsatian, Bas-Rhin, Haut-Rhin, Grand Cru Alsace
- `"bordeaux"` → Médoc, Pauillac, Saint-Estèphe, Saint-Julien, Margaux, Pessac-Léognan, Graves, Pomerol, Saint-Émilion, Fronsac, Entre-Deux-Mers
- `"chablis"` → Petit Chablis, Chablis Premier Cru, Chablis Grand Cru, Kimmeridgian
- `"jura"` → Arbois, Côtes du Jura, Château-Chalon, L'Étoile, Vin Jaune, Savagnin
- `"piedmont"` → Piemonte, Barolo, Barbaresco, Barbera d'Asti, Barbera d'Alba, Dolcetto, Gavi, Roero, Langhe
- `"tuscany"` → Toscana, Chianti, Chianti Classico, Brunello di Montalcino, Vino Nobile di Montepulciano, Morellino di Scansano, Bolgheri, Super Tuscan, Maremma
- `"rioja"` → Rioja Alta, Rioja Alavesa, Rioja Oriental, Tempranillo (Rioja)
- `"swartland"` → Swartland Independent Producers, Swartland Revolution
- `"priorat"` → Priorat, Priorato

### `_ALIAS_TO_CANONICAL: dict[str, str]`

Reverse index — maps each expansion term back to its canonical key. Built at module load from `_EXPANSIONS`. Used for lookup only (not currently exposed publicly).

## Integration Point

Called in `retrieval.rank_wine_list()` for region and grape term expansion before line scoring:

```python
from synonyms import expand_terms

region_terms = [_normalize(t) for t in expand_terms(list(profile.preferred_regions or [])) if t]
grape_terms = [_normalize(t) for t in expand_terms(list(profile.preferred_grapes or [])) if t]
```

## Patterns & Gotchas

- **Expansion only for regions and grapes**: producer terms and style descriptors are matched as-is. Producers are proper names (exact match is appropriate); style descriptors are sensory phrases unlikely to appear verbatim in list entries.
- **Additive**: `expand_term` always includes the canonical term itself plus expansions. A term with no entry in `_EXPANSIONS` is returned as a single-element list (`[term]`) — safe default.
- **No API calls**: pure keyword expansion, runs synchronously at retrieval time.
- **Growing table**: add new entries to `_EXPANSIONS` as more profiles are observed. No code changes required — just add to the dict.
