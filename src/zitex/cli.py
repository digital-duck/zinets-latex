"""Command line: ``zitex render|check|shape|fonts|patterns|setup|db-build|extract|install-sty`` (or ``python -m zitex ...``)."""
from __future__ import annotations

import csv
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from itertools import product
from pathlib import Path

import click

from .build import build as build_snippets, scan_tex, write_snippet
from .fonts import FontConfig, coverage_report
from . import zxdb, yamlio
from .ops import op_for_pattern
from .render import STYLES, render_with
from .sources import ENV_DB, DB_RELATIVE, SqliteSource, find_default_database, is_sqlite, open_source
from .tree import ParseError, to_shape
from .validate import validate_entry

FILE = click.Path(exists=True, dir_okay=False)
DEFAULT_LEXICON = "lexicon.yaml"      # used by `render` when -x is not given and the file exists in the current folder


def _open(data: str, depth: int | None = None):
    """The data adapter for a decomposition YAML or a SQLite database."""
    try:
        src = open_source(data, depth)
        src.entries()                                    # read it now, so that errors surface here
    except (ParseError, ValueError, sqlite3.Error, OSError) as ex:
        click.echo(f"{data}: error: {ex}", err=True)
        sys.exit(2)
    if isinstance(src, SqliteSource) and src.from_raw:
        click.echo(f"{data}: reading the raw working tables (nothing is written). "
                   "`zitex db-build` saves a clean zx_* copy.", err=True)
    return src


def _load(data: str, depth: int | None = None):
    return _open(data, depth).entries()


DEFAULT_CHARS = "chars.yaml"


def input_option(f=None, *, many: bool = False, required: bool = False, help: str | None = None):
    """-i / --input, the one way every command is told what to read.

    With many=True the value is a comma-separated list (a.yaml,b.yaml), like -c; split it with _inputs().
    """
    def deco(fn):
        return click.option("-i", "--input", "input_", type=str if many else FILE, multiple=many, required=required,
                            help=help or f"the decomposition YAML or SQLite database (default: ./{DEFAULT_CHARS})")(fn)
    return deco(f) if f is not None else deco


def _inputs(values: tuple[str, ...]) -> list[str]:
    """A comma-separated list of files (repeating -i adds to it), each of which must exist."""
    paths = list(dict.fromkeys(p.strip() for v in values for p in v.split(",") if p.strip()))
    for p in paths:
        if not Path(p).is_file():
            raise click.UsageError(f"input {p!r} is not a file")
    return paths


def _input_or_default(value: str | None) -> str:
    """The --input given, or ./chars.yaml. There is no other default: a command that reads every character
    must not guess at a large database."""
    if value:
        return value
    if not Path(DEFAULT_CHARS).is_file():
        raise click.UsageError(f"no input: there is no {DEFAULT_CHARS} in this folder. Pass --input PATH.")
    return DEFAULT_CHARS


def depth_option(f):
    return click.option("--depth", type=click.IntRange(min=1), default=None,
                        help="database only: expand components down to this many levels (default: all)")(f)


def _csv(_ctx, _param, value):
    return [x for x in value.split(",") if x] if value else None


def math_options(f):
    f = click.option("--collapse", is_flag=True, help="math: 3 x 口 instead of 口 + 口 + 口")(f)
    f = click.option("--arrow", type=click.Choice(["=", "reaction", "role"]), default="=", show_default=True,
                     help="math: equals sign, plain arrow, or arrow labelled with the phonetic role")(f)
    f = click.option("--result", type=click.Choice(["below", "paren"]), default="below", show_default=True,
                     help="math: gloss of the result below it (like the pieces) or in brackets after it")(f)
    f = click.option("--show-pos", is_flag=True, help="math: subscript each piece with its position")(f)
    return f


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, subcommand_metavar="COMMAND [ARGS]")
@click.version_option(package_name="zitex")
def main() -> None:
    """zitex: Chinese character decomposition trees rendered through XeLaTeX."""


@main.command(short_help="Check decomposition YAML files and report problems as warnings (warnings never fail the run).")
@input_option(many=True, help=f"one or more files, separated by commas: a.yaml,b.yaml (default: ./{DEFAULT_CHARS})")
@depth_option
def check(input_: tuple[str, ...], depth) -> None:
    """Validate decomposition files (YAML or SQLite). Warnings never fail the run."""
    for path in _inputs(input_) or [_input_or_default(None)]:
        entries = _load(path, depth)
        warns = [w for e in entries for w in validate_entry(e)]
        for w in warns:
            click.echo(f"{path}: {w}")
        click.echo(f"{path}: {len(entries)} entries, {len(warns)} warnings")


@main.command(short_help="Print the compact shape string of every entry in a decomposition YAML file.")
@input_option
@depth_option
def shape(input_, depth) -> None:
    """Print the compact shape string of every entry."""
    for e in _load(_input_or_default(input_), depth):
        click.echo(f"{e.char}\t{to_shape(e.tree)}")



@main.command(short_help="Report which font or image draws each component, and which components have no glyph.")
@input_option
@click.option("--fonts", "fonts_file", type=FILE, help="fonts.yaml (default: Noto Serif CJK SC, no fallbacks)")
@click.option("--strict", is_flag=True, help="exit 1 if any component has no glyph")
@depth_option
def fonts(input_, fonts_file, strict, depth) -> None:
    """Report which font (or image) draws each component, and which have no glyph."""
    cfg = FontConfig.load(fonts_file) if fonts_file else FontConfig()
    rep = coverage_report(_load(_input_or_default(input_), depth), cfg)
    if not rep.inspected:
        click.echo(f"note: cannot read font {cfg.primary!r}; assuming it covers everything", err=True)
    click.echo(f"primary: {cfg.primary}   fallbacks: {', '.join(cfg.fallbacks) or '-'}")
    for ch, r, users in rep.rows:
        if r.kind != "plain":
            how = {"font": f"font {r.value}", "svg": f"svg {r.value}", "alias": f"alias {r.value}",
                   "missing": "MISSING"}[r.kind]
            click.echo(f"  {ch}\t{how}\t(used in {' '.join(users)})")
    plain = sum(1 for _, r, _ in rep.rows if r.kind == "plain")
    click.echo(f"{len(rep.rows)} components: {plain} in the primary font, {len(rep.rows) - plain - len(rep.missing)} "
               f"via fallback, {len(rep.missing)} missing")
    if strict and rep.missing:
        sys.exit(1)


@main.command(short_help="Render characters from a decomposition YAML file or SQLite database to LaTeX snippets and PDF figures.")
@input_option
@click.option("-c", "--char", "--chars", "char_args", multiple=True, metavar="CHARS",
              help="characters to render, separated by commas or spaces, e.g. 叕,作 (default: every character in the input)")
@click.option("-s", "--style", "--styles", default=None, metavar="STYLE[,STYLE]",
              help=f"{', '.join(sorted(STYLES))} (default: all; tree for a single file)")
@click.option("-l", "--lang", "langs", multiple=True, help="gloss language, repeatable (default: en)")
@click.option("-x", "--lexicon", "lexicons", multiple=True, type=FILE, help="lexicon YAML (pinyin, glosses), repeatable (default: ./lexicon.yaml, if it exists)")
@click.option("--fonts", "fonts_file", type=FILE, help="fonts.yaml: primary font, fallbacks, per-component overrides")
@click.option("--reading", default=None, help="named reading of the roles (default: the entry's first)")
@click.option("-o", "--out", default=None, type=click.Path(),
              help="a directory (default: zitex-out/), a file or stem for one output, or - for stdout")
@click.option("--emit", type=click.Choice(["tex", "pdf", "both"]), default=None,
              help="tex = snippet, pdf = compiled figure (default: both; tex with --scan; from the -o suffix)")
@click.option("--font", default=None, help="CJK font for PDF output (default: primary of --fonts, else Noto Serif CJK SC)")
@click.option("--scan", "scan_file", type=FILE, help="render only what this .tex file asks for with its \\zi, \\zimath, \\zitree, \\zimatrix and \\ziformula commands")
@depth_option
@math_options
def render_cmd(input_, char_args, style, langs, lexicons, fonts_file, reading, out, emit, font, scan_file, depth,
               collapse, arrow, show_pos, result) -> None:
    """Render the characters of a decomposition YAML, or of a SQLite database, to LaTeX snippets and PDF figures.

    The input is --input, or ./chars.yaml when it is not given. With no other options, every character is rendered in every style, as <char>-<style>.tex and .pdf,
    into ./zitex-out/ (the folder zitex.sty reads). Choose what to render with --char, and where
    the output goes with -o:

    \b
      zitex render                                  everything in ./chars.yaml, into zitex-out/
      zitex render -i data/chars.yaml               the same, from another file
      zitex render -c 叕,作 -o figs/                 two characters, every style, into figs/
      zitex render -c 森 -s math -o sen              sen.tex and sen.pdf (one output: a file stem)
      zitex render -c 森 -s math -o sen.tex          the snippet only (.pdf: the figure only)
      zitex render -c 森 -s math -o -                print the snippet
      zitex render --scan main.tex                   only what main.tex asks for with its \\zi commands

    A name without a suffix is a file stem when one character and one style are named (-s), and a
    directory otherwise.
    """
    data = _input_or_default(input_)
    source = _open(data, depth)
    entries = source.entries()
    by_char = {x.char: x for x in entries}
    lexicons = lexicons or ((DEFAULT_LEXICON,) if Path(DEFAULT_LEXICON).is_file() else ())   # -x replaces the default
    lex = source.lexicon(lexicons)
    fonts = FontConfig.load(fonts_file) if fonts_file else None
    langs_list = list(dict.fromkeys(langs)) or ["en"]
    math_opts = {"collapse": collapse, "arrow": arrow, "show_pos": show_pos, "result": result}

    styles = [s.strip() for s in style.split(",") if s.strip()] if style else None
    bad = [s for s in styles or [] if s not in STYLES]
    if bad:
        raise click.BadParameter(f"unknown style(s) {bad}; choose from {sorted(STYLES)}", param_hint="--style")

    to_stdout = out == "-"
    file_suffix = bool(out) and not to_stdout and Path(out).suffix.lower() in (".tex", ".pdf")
    explicit_dir = bool(out) and not to_stdout and (Path(out).is_dir() or out.endswith(("/", os.sep)))
    if emit in ("pdf", "both") and to_stdout:
        raise click.UsageError("-o - prints a snippet: it cannot be combined with --emit pdf or both")

    # ---- what to render ----
    if scan_file:
        if char_args or style or reading:
            raise click.UsageError("--scan renders what the document asks for: do not combine it with --char, --style or --reading")
        if to_stdout or file_suffix:
            raise click.UsageError("--scan writes several files: -o must be a directory")
        jobs = {(c, s, l or langs_list[0], rd) for c, s, l, rd in scan_tex(scan_file)}
        if not jobs:
            click.echo(f"{scan_file}: no \\zi calls found")
            return
        found, single = [], False
    else:
        wanted = list(dict.fromkeys(c for tok in char_args for c in re.split(r"[,，、\s]+", tok) if c))
        wanted = wanted or [x.char for x in entries]
        missing = [c for c in wanted if c not in by_char]
        found = [by_char[c] for c in wanted if c in by_char]
        if missing:
            click.echo(f"not in {data}: {' '.join(missing)}", err=True)
        if not found:
            sys.exit(1)
        jobs = None
        # one output goes to a file, several to a directory
        n_styles = len(styles) if styles else None
        if to_stdout or file_suffix:
            single = True
        elif out and not explicit_dir:
            single = len(found) == 1 and n_styles == 1          # a bare name is a stem only for one named style
        else:
            single = False
        styles = styles or (["tree"] if single else list(STYLES))
        if single and (len(found) > 1 or len(styles) > 1):
            raise click.UsageError("several outputs need a directory: use -o DIR (or no -o), or name one character and one style")
        if single and len(langs_list) > 1 and styles[0] in ("math", "formula"):
            raise click.UsageError("one output has one language: give a single -l")
    user_emit = emit
    emit = emit or ("tex" if scan_file else "both")

    # ---- one output: stdout or a file ----
    if single:
        e, st, lang = found[0], styles[0], langs_list[0]
        kw: dict = {}
        if st in ("math", "formula"):
            kw.update(lang=lang, lex=lex)
        if st == "math":
            kw.update(math_opts)
        snippet, resolver = render_with(e, st, fonts, reading=reading, **kw)
        if resolver and resolver.missing:
            click.echo(f"no glyph for: {' '.join(sorted(resolver.missing))} (drawn as a boxed label; see `zitex fonts`)", err=True)
        if to_stdout:
            click.echo(snippet)
            return
        path = Path(out)
        suffix = path.suffix.lower()
        stem = path.with_suffix("") if suffix in (".tex", ".pdf") else path
        how = user_emit or {".tex": "tex", ".pdf": "pdf"}.get(suffix, "both")   # an explicit --emit wins over the suffix
        try:
            tex, pdf, ok = write_snippet(snippet, resolver, fonts, stem, how, font)
        except RuntimeError as ex:               # e.g. xelatex or inkscape is not installed
            click.echo(f"error: {ex}", err=True)
            sys.exit(1)
        for p in (tex, pdf):
            if p:
                click.echo(f"wrote {p}")
        if not ok:
            click.echo(f"failed to compile {stem}.pdf", err=True)
            sys.exit(1)
        return

    # ---- several outputs: a directory ----
    outdir = Path(out) if out else Path("zitex-out")
    n = len(jobs) if jobs is not None else len(found) * len(styles)
    if emit != "tex" and n > 10:
        click.echo(f"rendering {n} snippets and compiling their PDFs into {outdir}/ (this takes a while)", err=True)
    try:
        res = build_snippets(entries, outdir, jobs, chars=[x.char for x in found], styles=styles, langs=langs_list,
                             emit=emit, lex=lex, font=font, fonts=fonts, reading=reading, math_opts=math_opts)
    except RuntimeError as ex:
        click.echo(f"error: {ex}", err=True)
        sys.exit(1)
    files = res.tex + res.pdf
    if len(files) <= 10:
        for p in files:
            click.echo(f"wrote {p}")
    click.echo(f"{outdir}: {len(res.tex)} .tex, {len(res.pdf)} .pdf")
    if res.missing:
        click.echo(f"not in {data}: {' '.join(res.missing)}", err=True)
    if res.glyph_missing:
        click.echo(f"no glyph for: {' '.join(res.glyph_missing)} (drawn as a boxed label; see `zitex fonts`)", err=True)
    if res.failed:
        click.echo(f"failed to compile: {' '.join(str(p) for p in res.failed)}", err=True)
        sys.exit(1)


@main.command("db-build", short_help="Copy what zitex needs from the ZiNets database into small zx_ tables, leaving the original untouched.")
@input_option(required=True, help="the ZiNets working database to read (never changed). No default: it is not part of a checkout")
@click.option("-o", "--out", type=click.Path(dir_okay=False), default=None,
              help="the SQLite file to write (default: zitex.sqlite3 next to the input)")
@click.option("--in-place", is_flag=True,
              help="add the zx_ tables to the input itself, after making a dated backup copy (default: a separate file)")
@click.option("--report", "report_file", type=click.Path(dir_okay=False), default=None,
              help="also write the rows that could not be converted, as a CSV file")
def db_build(input_, out, in_place, report_file) -> None:
    """Re-create the data zitex needs as four small tables (zx_meta, zx_char, zx_part, zx_quarantine).

    The input is the ZiNets working database (t_zi_part, t_zi, t_ele_zi, t_part). It is opened read only and
    never changed, and the tables are written to a separate file, so a mistake here cannot damage it. Rows that
    cannot be converted safely are not guessed at: they go to zx_quarantine, and to --report. After the build,
    the command checks that the input is byte for byte what it was.
    """
    src = Path(input_)
    if not is_sqlite(src) or not zxdb.has_raw(src):
        click.echo(f"{src}: not a ZiNets working database (no t_zi_part and t_zi tables)", err=True)
        sys.exit(2)
    if in_place and out and Path(out).resolve() != src.resolve():
        click.echo("--in-place adds the tables to the input itself: do not combine it with a different -o file", err=True)
        sys.exit(2)
    dest = src if in_place else (Path(out) if out else src.with_name("zitex.sqlite3"))
    same = dest.resolve() == src.resolve()
    if same and not in_place:
        click.echo(f"{dest} is the source database itself. Choose another file with -o, or pass --in-place to add "
                   "the zx_ tables to it (a backup copy is made first).", err=True)
        sys.exit(2)
    before = zxdb.sha256_of(src)
    zx = zxdb.build_from_raw(src)
    try:
        zxdb.write_zx(zx, dest, in_place=in_place or same)
    except ValueError as ex:
        click.echo(f"error: {ex}", err=True)
        sys.exit(2)
    click.echo(f"wrote {dest}: {len(zx.chars)} characters, {sum(len(v) for v in zx.parts.values())} parts, "
               f"{len(zx.quarantine)} rows left out")
    if zx.meta.get("revisions_reapplied", "0") != "0":
        click.echo(f"re-applied {zx.meta['revisions_reapplied']} revision(s) made by hand (kept in zx_revision)")
    reasons = Counter(r for _, r, _ in zx.quarantine)
    for reason, n in reasons.most_common():
        click.echo(f"  {n:5d}  {reason}")
    undecomposed = Counter(p for lst in zx.parts.values() for _, p in lst
                           if p in zx.chars and not zx.chars[p].has_parts and not zx.chars[p].is_elemental)
    click.echo(f"  {len(undecomposed):5d}  components are neither elemental nor decomposed (they stay leaves in every tree)")
    elem_decomposed = [(zi, " ".join(f"{pos}={part}" for pos, part in zx.parts[zi])) for zi, c in sorted(zx.chars.items())
                       if c.is_elemental and c.has_parts]
    click.echo(f"  {len(elem_decomposed):5d}  elemental characters still have a decomposition (most of them should be primitives)")
    if report_file:
        with open(report_file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["zi", "reason", "cells"])
            w.writerows(zx.quarantine)
        click.echo(f"wrote {report_file}")
        other = Path(report_file).with_name(Path(report_file).stem + "-undecomposed.csv")
        with open(other, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["zi", "used_as_a_part_n_times"])
            w.writerows(undecomposed.most_common())
        click.echo(f"wrote {other}")
        third = Path(report_file).with_name(Path(report_file).stem + "-elemental-decomposed.csv")
        with open(third, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["zi", "decomposition"])
            w.writerows(elem_decomposed)
        click.echo(f"wrote {third}")
    if not (in_place or same):
        after = zxdb.sha256_of(src)
        if after == before:
            click.echo(f"source unchanged: {src} (sha256 {before[:12]})")
        else:
            click.echo(f"warning: {src} changed while it was being read (sha256 {before[:12]} -> {after[:12]}). "
                       "Something else wrote to it; this command only reads it.", err=True)


@main.command(short_help="Prepare a self-contained working folder: zitex.sty, fonts.yaml, fallback.yaml and glyphs/.")
@click.option("-o", "--out", default=".", show_default=True, type=click.Path(file_okay=False), help="the folder to fill")
@click.option("--force", is_flag=True, help="overwrite files that already exist")
def setup(out, force) -> None:
    """Prepare a working folder: zitex.sty, fonts.yaml, fallback.yaml and glyphs/demo.svg.

    zitex.sty is copied into the folder, so xelatex finds it next to main.tex and the folder is self-contained
    (nothing is installed in your home folder; `zitex install-sty` does that, if you want it). It is brought up
    to date when it differs from this version of zitex. fonts.yaml names the primary CJK font and the fallback
    fonts, chosen from the fonts installed on this computer (the primary is the first of the usual CJK fonts
    found, and each fallback adds characters the others lack). fallback.yaml and glyphs/ are samples for trying
    the fallback. Files you may have edited are kept unless --force. The next steps are `zitex extract` and xelatex:

    \b
      zitex setup -o work/
      zitex extract -c 器,藻,佛 -o work/
      cd work && xelatex main.tex
    """
    from .fonts import detect_fonts
    from .workspace import write_setup
    choice = detect_fonts()
    res = write_setup(Path(out), choice, force)
    for p in res.written:
        click.echo(f"wrote {p}" + (" (updated: it differed from this version of zitex)" if p.name == "zitex.sty" and res.sty == "updated" else ""))
    if res.sty == "up to date":
        click.echo(f"zitex.sty in {out} is up to date")
    for p in res.kept:
        click.echo(f"kept {p} (it exists; --force overwrites)")
    if choice.primary:
        extra = ", ".join(f"{f} (+{n:,})" for f, n in choice.fallbacks) or "none needed"
        click.echo(f"primary font: {choice.primary}; fallbacks: {extra}")
    else:
        click.echo("no CJK font from the usual list was found: fonts.yaml names Noto Serif CJK SC, which you need to install "
                   "(fc-list :lang=zh shows what you have)", err=True)
    click.echo(f"next: zitex extract -c 器,藻,佛 -o {out}")


@main.command(short_help="Extract characters from a database into a folder: chars.yaml, lexicon.yaml, main.tex and its snippets.")
@input_option(help=f"the SQLite database (default: {DB_RELATIVE} in this folder or a parent folder, or ${ENV_DB})")
@click.option("-o", "--out", default=".", show_default=True, type=click.Path(file_okay=False),
              help="the folder to fill (run `zitex setup` on it first to get fonts.yaml)")
@click.option("-c", "--char", "char_args", multiple=True, metavar="CHARS",
              help="only these characters, separated by commas or spaces (default: all)")
@click.option("--annotation", type=click.Choice(["minimal", "demo"]), default="minimal", show_default=True,
              help="the main.tex to write: minimal (every style for every character) or demo (an annotated paper "
                   "that explains the syntax and the features of zitex, for these characters)")
@depth_option
def extract(input_, out, char_args, annotation, depth) -> None:
    """Extract characters from a database into a working folder, ready for xelatex.

    The database is --input, and db/zitex.sqlite3 (found in this folder or a parent, or named by $ZITEX_DB) when
    that is not given. The folder gets chars.yaml (the decompositions) and lexicon.yaml (pinyin and glosses), which
    load like hand-written files, and main.tex, a document showing every extracted character. The snippets main.tex
    uses are rendered into zitex-out/ with the fonts.yaml in the folder, if there is one. Then:

    \b
      zitex setup -o work/
      zitex extract -c 器,藻,佛 -o work/
      cd work && xelatex main.tex

    Name the characters with -c (commas or spaces; they are written in that order). At most 60 are extracted, a
    document of that size being as much as main.tex should hold: with more, the first 60 are kept and a warning
    says so. With --annotation demo, main.tex is an annotated paper that explains the syntax and the features of
    zitex using your first characters. Running it again on the same folder overwrites chars.yaml, lexicon.yaml,
    main.tex and the snippets, so keep a document you wrote yourself in another folder. The YAML is generated: read
    it for a review, or fix the database and extract again.
    """
    from .fonts import DEFAULT_PRIMARY
    from .lexicon import load_lexicon
    from .loader import load_yaml
    from .workspace import MAX_CHARS, make_main_tex, sty_state
    source = input_
    if source is None:
        found_db = find_default_database()
        if found_db is None:
            raise click.UsageError(f"no database: pass --input PATH. Looked for {DB_RELATIVE} in this folder and its parents, "
                                   f"in the zitex checkout, and in ${ENV_DB}.")
        source = str(found_db)
        click.echo(f"using the database {found_db}", err=True)
    src = _open(source, depth)
    if not isinstance(src, SqliteSource):
        click.echo(f"{source}: already a decomposition YAML, nothing to extract", err=True)
        sys.exit(2)
    dicts = src.entry_dicts()
    wanted = list(dict.fromkeys(c for tok in char_args for c in re.split(r"[,，、\s]+", tok) if c))
    if wanted:
        by_char = {d["char"]: d for d in dicts}
        if [c for c in wanted if c not in by_char]:
            click.echo(f"not in {source}: {' '.join(c for c in wanted if c not in by_char)}", err=True)
        dicts = [by_char[c] for c in wanted if c in by_char]            # in the order they were named
    if not dicts:
        sys.exit(1)
    if len(dicts) > MAX_CHARS:
        click.echo(f"warning: {len(dicts)} characters found: keeping the first {MAX_CHARS}. Name the ones you want with -c.", err=True)
        dicts = dicts[:MAX_CHARS]
    outdir = Path(out)
    chars_f, lex_f, main_f = outdir / "chars.yaml", outdir / "lexicon.yaml", outdir / "main.tex"
    used: set[str] = set()

    def collect(n: dict) -> None:
        if "c" in n:
            used.add(n["c"])
        for p in n.get("parts", []):
            collect(p)

    for d in dicts:
        collect(d["tree"])
        used.add(d["char"])                      # the extracted characters need a gloss too, not only their parts
    lex = {ch: v for ch, v in src.lexicon_dict().items() if ch in used}
    from . import __version__
    stamp = (f"# Generated by zitex {__version__} from {Path(source).name} on {time.strftime('%Y-%m-%d')}.\n"
             f"# Do not edit by hand if you plan to extract again: fix the database, or work on a copy of this file.\n"
             + "".join(f"# {line}\n" for line in _wrap(src.report.meta.get("attribution") or zxdb.ATTRIBUTION, 100)).rstrip("\n"))
    outdir.mkdir(parents=True, exist_ok=True)
    chars_f.write_text(yamlio.dump_entries(dicts, stamp), encoding="utf-8")
    lex_f.write_text(yamlio.dump_lexicon(lex, stamp), encoding="utf-8")
    click.echo(f"wrote {chars_f}: {len(dicts)} characters")
    click.echo(f"wrote {lex_f}: {len(lex)} characters")
    fonts_f = outdir / "fonts.yaml"
    fonts = FontConfig.load(fonts_f) if fonts_f.exists() else None
    if not fonts:
        click.echo(f"no {fonts_f}: using the default font setup (`zitex setup -o {out}` creates one)", err=True)
    state = sty_state(outdir)
    if state == "stale":
        click.echo(f"warning: {outdir / 'zitex.sty'} differs from this version of zitex: run `zitex setup -o {out}` to update it", err=True)
    elif state == "absent" and shutil.which("kpsewhich") and not subprocess.run(
            ["kpsewhich", "zitex.sty"], capture_output=True, text=True).stdout.strip():
        click.echo(f"TeX will not find zitex.sty: run `zitex setup -o {out}` (puts it in the folder), or `zitex install-sty`",
                   err=True)
    main_f.write_text(make_main_tex(dicts, fonts.primary if fonts else DEFAULT_PRIMARY, annotation), encoding="utf-8")
    click.echo(f"wrote {main_f}")
    # render the snippets main.tex asks for, from the files just written: the same path a later `render` takes
    entries = load_yaml(chars_f)
    jobs = {(c, s, l or "en", rd) for c, s, l, rd in scan_tex(main_f)}
    try:
        res = build_snippets(entries, outdir / "zitex-out", jobs, emit="tex", lex=load_lexicon(entries, lex_f), fonts=fonts)
    except RuntimeError as ex:
        click.echo(f"error: {ex}", err=True)
        sys.exit(1)
    click.echo(f"wrote {outdir / 'zitex-out'}: {len(res.tex)} snippets")
    if res.glyph_missing:
        click.echo(f"no glyph for: {' '.join(res.glyph_missing)} (drawn as a boxed label; see `zitex fonts`)", err=True)
    click.echo(f"next: cd {out} && xelatex main.tex")


@main.command(short_help="Count how often each compositional pattern, such as L-M or U-D, occurs in a decomposition file or database.")
@input_option
@click.option("--all-levels", is_flag=True, help="count every level of every tree, not only the first level of each character")
@depth_option
def patterns(input_, all_levels, depth) -> None:
    """Print how often each pattern occurs, most frequent first: the table behind Figure 5 of the paper."""
    counts: Counter = Counter()

    def walk(n, first):
        if n.is_leaf:
            return
        counts[n.pattern] += 1
        if all_levels:
            for p in n.parts:
                walk(p, False)

    for e in _load(_input_or_default(input_), depth):
        walk(e.tree, True)
    total = sum(counts.values())
    click.echo(f"{'pattern':<18}{'count':>7}{'share':>8}  operator")
    for pat, n in counts.most_common():
        click.echo(f"{pat:<18}{n:>7}{100 * n / total:>7.1f}%  {op_for_pattern(pat.split('-'))}")
    click.echo(f"{len(counts)} patterns, {total} {'levels' if all_levels else 'characters'}")


def _wrap(text: str, width: int) -> list[str]:
    import textwrap
    return textwrap.wrap(text, width)


def _texmfhome() -> Path:
    """Your personal TeX tree: what kpsewhich reports for TEXMFHOME, else ~/texmf."""
    if shutil.which("kpsewhich"):
        r = subprocess.run(["kpsewhich", "-var-value=TEXMFHOME"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip().split(os.pathsep)[0]).expanduser()
    return Path.home() / "texmf"


@main.command("install-sty", short_help="Install zitex.sty into your personal TeX folder, so that plain xelatex finds it.")
@click.option("--dir", "target", type=click.Path(file_okay=False), default=None,
              help="install into this TeX tree instead (default: your TEXMFHOME, usually ~/texmf)")
def install_sty(target) -> None:
    """Copy zitex.sty into a TeX tree, so a document with \\usepackage{zitex} compiles with plain xelatex.

    The file goes to <tree>/tex/latex/zitex/zitex.sty. Run this again after upgrading zitex to update it.
    Without it, point XeLaTeX at the file for each run with TEXINPUTS=<folder of zitex.sty>:
    """
    src = Path(__file__).with_name("zitex.sty")
    if not src.is_file():
        click.echo(f"error: {src} is missing from the installation", err=True)
        sys.exit(1)
    tree = Path(target).expanduser() if target else _texmfhome()
    dest = tree / "tex" / "latex" / "zitex" / "zitex.sty"
    if dest.is_file() and dest.read_bytes() == src.read_bytes():
        click.echo(f"already up to date: {dest}")
    else:
        verb = "updated" if dest.is_file() else "installed"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        click.echo(f"{verb} {dest}")
    if shutil.which("mktexlsr"):
        subprocess.run(["mktexlsr", str(tree)], capture_output=True)      # refresh the file database if there is one
    if shutil.which("kpsewhich"):
        found = subprocess.run(["kpsewhich", "zitex.sty"], capture_output=True, text=True).stdout.strip()
        if found:
            click.echo(f"TeX finds it at {found}")
        else:
            click.echo(f"TeX does not search {tree}. Add it to TEXMFHOME, or use TEXINPUTS={dest.parent}: when you run xelatex.",
                       err=True)


main.add_command(render_cmd, name="render")

if __name__ == "__main__":
    main()
