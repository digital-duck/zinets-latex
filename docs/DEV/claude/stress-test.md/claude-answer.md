# Image identification test: Claude's answers

Image: `oracle-bone-script-1.png` (shown to Claude as an attachment, no caption).

## Turn 1

I can describe it, but I can't name it with confidence.

**What I see**
- It is a thick-lined black glyph, symmetric left to right. The lines are fat and slightly uneven, like brush or cast strokes.
- There are two nested arches, an outer one and an inner one, like a tunnel mouth or a gate, so the middle is a hollow tall archway.
- The arches come down into two vertical legs on each side, and each leg has a short horizontal bar near the lower part, like a rung or a crossbeam.
- At each outer foot there is a flared tip that sweeps up and outward, like a horn, a raised arm, or a pointed foot. These look the same on both sides.

**What it looks like**
This isn't a modern or regular-script form. The thick, rounded strokes and the pictorial symmetry look like an ancient pictograph, probably oracle bone, or a bronze inscription or clan sign. The outline could read as a gate or a dwelling, as a standing figure seen from the front with raised arms, or as an arch with two supports. The nesting of two arches suggests a doorway or a frame, but I am speculating.

**What I can't do**
I can't tell you which character or emblem it is, and I would rather say so than guess. Some features would help me narrow it down: whether the two small bars are meant as hands, belts or rungs, and which script and source it comes from.

If it is one of your oracle bone components with no Unicode code point, the way to use it in zitex is already there. You would give it a `{name}` and an SVG entry in `fonts.yaml`, and it would be drawn in the tree, matrix and equations like any other part.

**Note on fairness.** Listing this directory afterwards showed the image file name, `oracle-bone-script-1.png`. Claude had already guessed "oracle bone" from the strokes in the answer above, but the file name was not available when the answer was written.

## Clue 1

> This is an oracle bone script character, for a composite character, not found in my elemental character set.

## Turn 2

Still not certain. The clue narrows what kind of answer to look for.

**What the clue changes**
- A composite is built from parts that are in your elemental set, so I should be able to read the picture as a few simple pieces, not as one pictograph.
- Reading the image that way, I see three things: a **frame** (the two nested arches), something **inside** it (the open hollow under the inner arch), and a **mirrored pair** on the left and right (the flared tips with a short bar).

**Candidates, in order of how much I trust them (all low)**
1. **A gate with hands on it**, such as 開 or 闢 in oracle form. The arches would be the gate (門), and the mirrored flares with bars would be a pair of hands (又, or 廾 as two hands together) on the leaves or on the bolt. My reservations: I do not remember the oracle forms of these characters exactly, and the inner arch is more than a plain gate has.
2. **A frame with a pair of attendants**, a building or structure with two figures at its sides. I have no specific character for this.
3. **A person-like figure seen from the front**, with the arch as the body. This fits the symmetry but not the second arch.

I would not bet on any of these. The first fits the "frame + mirrored pair" structure best.

**How it would look in zitex, if reading 1 were right**
A three-part level with the mirrored hands as `L` and `R` and the gate as `M` (`L-M-R`, operator ⿲), or the gate as an `Mo` frame with the hands inside. Which of the two depends on how your decomposition treats it.

**What would help most**
- Does the glyph stand for a **thing** (a building, a gate, a vessel) or an **action** (opening, entering, pushing)?
- Is the modern form a **single-frame** character such as 門, 冂, 宀 or 穴?

## Clue 2

> It is not an action, but an image depicting what humans see in nature. What I first learned about it 2 days ago: oracle bone scripts are not written language, but a way to record human experience many thousand years ago.

## Turn 3

**My answer: 虹 (hóng), the rainbow.** I am fairly confident, about two in three, not certain.

**Why it fits**
- "Something humans see in nature" plus "not an action" removes the gate readings from turn 2.
- The **two nested arches** read as a rainbow, and a double one at that, the primary bow with the fainter secondary bow.
- The **flared tips at both feet** read as two heads. As far as I know, the oracle form of 虹 is an arch with a head at each end, because the rainbow was imagined as a two-headed creature (a serpent or dragon) drinking from the earth. The mirrored pair that I took for hands or attendants in turn 2 would be those heads.
- It is a **composite** in the way you describe: the modern 虹 is 虫 + 工, neither of which is the arch.

**What I cannot explain**
The two short horizontal bars near the feet. They may be mouths, or the water being drunk, or just the shape of the carving. I do not know.

**In zitex**
The modern form is `⿰虫工`. Note that 虫 (#142) and 工 (#48) are both Kangxi radicals, so the radical rule gives the peers pattern `L-R`. If your DB has `L-M` here, with 工 as the sound part, that is a case where the rule and your decision differ, and `W8` would not flag it (it only fires when a radical is `M` and the other part is not a radical).

**Turn count:** 3 (the first answer, then turns 2 and 3, with 2 clues).

## Result of test 1

虹 (rainbow), identified in turn 3 after 2 clues. Confirmed correct by the author. (The author reports Gemini also got it right from the "nature" hint.)

## Test 2: why are 虫 and 工 in 虹?

**Short answer.** 虫 is the meaning part and 工 is the sound part. It is a phono-semantic compound (形声字). I am answering from memory and have not checked a source.

**虫, the meaning**
- In the oldest writing 虫 is not "insect". It is a picture of a **snake** (read *huǐ*, the old form of 虺). Insects are the later, separate character 蟲 (*chóng*).
- The rainbow was imagined as a **serpent or dragon** arching across the sky, which is why the oracle form (the image in test 1) has a head at each end. When the character was later rebuilt as a compound, the snake was kept as the meaning part.
- The Shuowen dictionary (Han dynasty) glosses 虹 as 螮蝀 (an old name for the rainbow), says it is 狀似蟲 ("shaped like a worm or snake"), and analyzes it as 从虫，工聲 ("from 虫, with 工 as the sound"). That wording is from memory.

**工, the sound**
- 工 (*gōng*) and 虹 (*hóng*) are close in sound, so 工 supplies the pronunciation. This is the standard analysis.
- Some people also see 工 as a picture, an arch or bridge shape, which would fit a rainbow. I treat that as a folk or secondary reading, not the main one.

**What happened to the picture**
The oracle form is a **pictograph** of the rainbow with its two heads. Later script replaced it with a **compound**: a snake for the meaning plus 工 for the sound. This is a common path in Chinese writing, from a drawing to a meaning + sound pair, and the loss of the picture is the price of being easier to write and to extend.

**For zitex**
- `role: {虫: semantic, 工: phonetic}`.
- Both 虫 and 工 are Kangxi radicals, so the radical rule gives the peers pattern `L-R`. The sound part carrying the weight suggests `L-M` in your DB, with 工 as `M`. This is the same kind of case as 虹 in the note under turn 3.
- It is also a good example for the living-fossil paper: the same concept, the rainbow, shown as a two-headed serpent first and as 虫 + 工 later.

## Author's response to test 2

The author disagrees with my analysis in test 2 and says that there is **no settled answer**. Their interpretation is consistent with their ZiNets work, and the glyph gave them two insights:

1. Ancient people's knowledge of the world was limited.
2. Before there was language, humans already tried to record and document their world knowledge.

Consequence for the data: the entry for 虹 in `tests/data/chars.yaml` has **no `role` set**, so it does not assume 虫 is semantic and 工 is phonetic. My etymology above is the dictionary view from memory, and it stays labelled as such.

## Test 3: `trap-dog.png`

**Answer: 器 (qì), in an early form.** One turn, but not a fair test, for two reasons I should state: you described 器 earlier in this session as four 口 (pits) around a 犬 (a trap for a wild dog), and the file name is `trap-dog.png`. Without those I would have been guessing between several characters made of repeated 口.

**What the image shows**
- Four 口-like shapes, each a rounded cup or pit with raised rims and a small hollow inside, at the upper left, upper right, lower left and lower right.
- A tall central figure running most of the height of the glyph: a vertical body with diagonal strokes branching out near the top and a long tail curving to the right at the bottom. That is how I read 犬 (the dog).

**In the Zi-Matrix**
Four corners and a center is the pattern `LU-RU-M-LD-RD`, written `⁙口口犬口口`, which is how your DB decomposes 器.

**A difference from what zitex draws**
In this form the dog is **tall and central**, with a pit at each corner beside it. The zitex matrix for 器 stacks three rows (two 口 on top, 犬 in the middle, two 口 below), which is how the modern form is laid out. The glyph here would fit a different layout: a left column (LU over LD), a full-height center column (M), and a right column (RU over RD). The layout is not part of the data and could be an option later.
