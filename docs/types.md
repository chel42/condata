# Types de colonnes

CONDATA n’invente pas de type. Il affiche uniquement des types de données **connus**, lus depuis le dtype pandas (et un test date sur du texte).

| Type affiché | Valeur JSON | Quand |
| --- | --- | --- |
| Entier | `integer` | dtype entier (`int64`, `Int64`, …) |
| Réel | `float` | dtype flottant (`float64`, …) |
| Date/heure | `datetime` | dtype datetime, ou texte dont ≥ 80 % des valeurs d’échantillon se parse en date |
| Texte | `text` | `string` / `object` qui n’est pas une date |
| Booléen | `boolean` | dtype booléen |
| Inconnu | `unknown` | tout le reste (rare) |

Il n’y a **pas** de type « catégoriel ». Un identifiant, un commentaire ou une ville sont du **texte**. Une vraie catégorie métier reste du texte : CONDATA ne décide pas à ta place si c’est une feature catégorielle ML.

## Ce que CONDATA ne fait pas

- Il ne convertit pas un réel en entier même si les valeurs sont `1.0`, `2.0` (pandas a lu un flottant, souvent à cause de cellules vides).
- Il ne convertit pas du texte `"1"`, `"2"` en entier. Si une colonne mélange chiffres et mots, c’est signalé en `mixed_types`, le type reste **texte**.
- Il ne relit pas les booléens écrits `"oui"` / `"True"` : c’est du texte.

## Usage dans le rapport

- Statistiques, outliers et corrélations : **entiers + réels**
- Fréquences (valeur dominante) : **texte + booléens**
- Incohérence de casse / espaces : colonnes **texte** uniquement
