# Notice: data in this folder

The files here (`zitex.sqlite3`, `zitex-quarantine.csv`, `zitex-quarantine-undecomposed.csv`) are **data derived from the ZiNets decomposition database**. They are not covered by the MIT licence of the zitex code (see the `LICENSE` file in the repository root).

## Attribution

The English glosses, the English meanings, and the pinyin of characters that are not in the elemental set come from **CC-CEDICT**, a community-maintained Chinese-English dictionary:

- CC-CEDICT, https://cc-cedict.org (hosted by MDBG, https://www.mdbg.net/chinese/dictionary?page=cc-cedict)
- Licence: **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**, https://creativecommons.org/licenses/by-sa/4.0/ . If the CEDICT file you hold states another version, that version applies.

### Changes made

The definitions were adapted for use as short labels:

- tone numbers were converted to tone marks (`xie4` became `xiè`);
- each definition was shortened to its first sense for the gloss, and to at most three senses for the meaning;
- cross-references (`CL:臺|台[tai2]`, `used in 舾裝|舾装[xi1 zhuang1]`) and notes such as `(bound form)` were removed.

### What this asks of you

CC BY-SA asks you to keep this attribution when you share the data, to say that changes were made, and to share an adapted version under the same licence. In short: this derived data is shared under **CC BY-SA 4.0**. The same text is stored inside the database file (table `zx_meta`, key `attribution`) and written at the top of every YAML file that `zitex extract` produces, so it travels with the data.

## Not from CC-CEDICT

- The curated one-word meanings of the elemental characters and radicals, the decompositions and the positions come from the ZiNets database, which is the author's own work.
- The CEDICT attribution above is based on the structure of the source tables (`w_cedict_*`, CEDICT-style definitions with `CL:` and `[pinyin]` notes). It has not been checked entry by entry, and other sources in the original database (for example the Shuowen texts or the HSK lists) are not used here.

This notice is not legal advice.
