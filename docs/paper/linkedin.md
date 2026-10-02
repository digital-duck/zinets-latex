# LinkedIn post (draft)

Attach: `linkedin-assets/器-ancient-glyph.png` (the ancient form) and `linkedin-assets/器-matrix.png` (1200 x 1200, the zitex matrix of 器). Say where the ancient glyph image comes from (its source and licence are not recorded in the repo). Optional comparison figures (ancient forms next to zitex matrices; the glyph images are public domain, from Wikimedia Commons): `figures/qi-figure-1-mouths.png` and `figures/qi-figure-2-weapon.png`. LinkedIn takes up to 20 images in a post, but one or two is plenty. If you make the illustration, see `linkedin-assets/scene-prompt.md`, and label it "AI-generated, imagined scene" in the caption.

---

Why does the Chinese character for "container" have a dog in it?

器 (qì) means vessel, tool, utensil. Look closely: four mouths (口) around a dog (犬).

The traditional answer, from a dictionary about 1,900 years old (说文解字), is that the dog is there to guard the vessels. That never convinced me. Why would a dog guard pots? And why is one dog in the middle, surrounded by four mouths?

Look at the ancient form: a lone dog, hemmed in on all sides. My reading is that it shows a wild animal trapped and crying out, with the clamour of mouths around it, and not a storeroom. It is a hypothesis, not a settled fact, and testing ideas like this is why I started taking more than 6,000 Chinese characters apart, to see what they are made of and how the pieces are arranged. (My paper: https://arxiv.org/abs/2502.19428)

Then a second problem showed up. How do you *show* a character's pieces in a document? Drawing it by hand is slow, and it goes stale the moment your analysis changes.

So I turned to an old friend, LaTeX, the tool scientists use to typeset equations. I built zitex, a free, open-source extension that writes a character as a little chemical-style equation, a box diagram or a tree, straight from the data:

日 + 寺 → 時
(sun + temple → time)

It is for learning and for fun: teachers making worksheets, students exploring why characters look the way they do, anyone who has wondered what is hiding inside a character.

It began as a chat with Google Gemini, and Claude Code from Anthropic helped build, test and write it up. The character decompositions, the design and the checking of results are mine.

Try it: https://github.com/digital-duck/zinets-latex

What character would you like to see taken apart?

#ChineseCharacters #LaTeX #OpenSource #LearningChinese #Python #ZiNets
