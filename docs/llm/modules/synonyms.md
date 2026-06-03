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

Maps canonical tokens (lowercase) to their expansion lists. Two categories.
The lists below are *representative* — the authoritative, complete table lives in
`backend/synonyms.py` (`_EXPANSIONS`). Examples are quoted verbatim from the code:

**Grape synonyms** (canonical → local names / alternate spellings):
- `"pinot noir"` → spätburgunder, blauburgunder, pinot nero
- `"grenache"` → garnacha, cannonau, grenache noir
- `"syrah"` → shiraz, sérine
- `"tempranillo"` → tinto fino, tinta roriz, cencibel, ull de llebre
- `"mourvèdre"` → monastrell, mataro
- `"sangiovese"` → chianti, brunello, morellino, rosso di montalcino
- `"nebbiolo"` → barolo, barbaresco, langhe nebbiolo, ghemme, gattinara
- `"chenin blanc"` → vouvray, savennières, montlouis
- `"vermentino"` → rolle
- `"blaufränkisch"` → blaufrankisch, lemberger, kékfrankos

(Many single-grape keys have empty expansion lists — e.g. `"fiano"`, `"furmint"`,
`"verdejo"` — present so the canonical token is recognised even without aliases.
There is no `"garganega"` entry.)

**Region/appellation expansions** (canonical region → sub-appellations and aliases):
- `"burgundy"` → bourgogne, côte de nuits, côte de beaune, gevrey, chambolle, vosne, nuits-saint-georges, pommard, volnay, meursault, puligny-montrachet, chassagne-montrachet, marsannay, fixin, morey-saint-denis, vougeot, flagey, auxey-duresses, saint-romain, saint-aubin, santenay, maranges, côte chalonnaise, rully, mercurey, givry, montagny, mâconnais, mâcon, viré-clessé, pouilly-fuissé (plus accent-free variants)
- `"champagne"` → grower champagne, grower-producer, champagne producer, aÿ, ay, épernay, reims, côte des bar, vallée de la marne, montagne de reims, blanc de blancs, blanc de noirs, brut nature, brut zéro, extra brut
- `"jura"` → arbois, château-chalon, l'étoile, etoile, côtes du jura, vin jaune, vin de paille, savagnin, ouillé (plus accent-free variants)
- `"rioja"` → rioja alta, rioja alavesa, rioja oriental
- `"swartland"` → swartland winemakers
- `"piedmont"` → piemonte, barolo, barbaresco, barbera d'asti, barbera d'alba, dolcetto, langhe, monferrato, roero, gavi, moscato d'asti
- `"chablis"` → petit chablis, chablis premier cru, chablis grand cru

(Other region keys present in `_EXPANSIONS` include `"loire"`, `"rhône"`, `"alsace"`,
`"beaujolais"`, `"bordeaux"`, `"languedoc"`, `"provence"`, `"southwest france"`,
`"tuscany"`, `"veneto"`, `"sicily"`, `"galicia"`, `"mosel"`, `"wachau"`, `"douro"`,
`"willamette valley"`, `"walker bay"`, and others. Some keys — e.g. `"ribera del duero"`,
`"rheingau"`, `"alentejo"` — carry empty expansion lists.)

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
