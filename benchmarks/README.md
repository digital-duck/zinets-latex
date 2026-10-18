# Benchmarks

`handout.py` measures one thing: how much work a correction to the data costs. It builds a handout of N equations
(`\zimath{X}`) for characters that contain one component, edits one line of `lexicon.yaml` (the gloss of that
component), and rebuilds. It prints the time of each step and how many snippet files changed.

    python benchmarks/handout.py -n 40 -p 口

The time is for `zitex render --scan` and for one XeLaTeX run, on the machine that runs it. The count of changed
snippets is the number of equations that carry the edited gloss: that is the number of places a hand-written set of
figures would need the same edit (it assumes each figure holds the gloss as literal text). The benchmark says nothing
about the time to write the data in the first place, which stays with the author.
