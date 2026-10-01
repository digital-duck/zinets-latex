"""Command line: ``zitex build|render|check|ids`` (or ``python -m zitex ...``)."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from .build import build as build_snippets, scan_tex
from .fonts import FontConfig, coverage_report
from .lexicon import load_lexicon
from .loader import load_yaml
from .render import STYLES, render
from .tree import ParseError, to_ids
from .validate import validate_entry

FILE = click.Path(exists=True, dir_okay=False)


def _load(data: str):
    try:
        return load_yaml(data)
    except (ParseError, ValueError) as ex:
        click.echo(f"{data}: error: {ex}", err=True)
        sys.exit(2)


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


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="zitex")
def main() -> None:
    """zitex: Chinese character decomposition trees rendered through XeLaTeX."""


@main.command()
@click.argument("files", nargs=-1, required=True, type=FILE)
def check(files: tuple[str, ...]) -> None:
    """Validate YAML decomposition files. Warnings never fail the run."""
    for path in files:
        entries = _load(path)
        warns = [w for e in entries for w in validate_entry(e)]
        for w in warns:
            click.echo(f"{path}: {w}")
        click.echo(f"{path}: {len(entries)} entries, {len(warns)} warnings")


@main.command()
@click.argument("file", type=FILE)
def ids(file: str) -> None:
    """Print the compact ids form of every entry."""
    for e in _load(file):
        click.echo(f"{e.char}\t{to_ids(e.tree)}")


@main.command()
@click.argument("data", type=FILE)
@click.option("-o", "--out", default="zitex-out", show_default=True, help="output directory")
@click.option("--emit", type=click.Choice(["tex", "pdf", "both"]), default="tex", show_default=True)
@click.option("-s", "--styles", callback=_csv, help=f"comma list of {','.join(STYLES)} (default: all)")
@click.option("-c", "--chars", callback=_csv, help="comma list of characters, e.g. 藻,時 (default: all)")
@click.option("--scan", "scan_file", type=FILE, help="build only what this .tex file asks for via \\zi...{}")
@click.option("-l", "--lang", "langs", multiple=True, help="gloss language, repeatable (default: en)")
@click.option("-x", "--lexicon", "lexicons", multiple=True, type=FILE, help="lexicon YAML (pinyin, glosses), repeatable")
@click.option("--font", default=None, help="CJK font for PDF output (default: primary of --fonts, else Noto Serif CJK SC)")
@click.option("--fonts", "fonts_file", type=FILE, help="fonts.yaml: primary font, fallbacks, per-component overrides")
@math_options
def build(data, out, emit, styles, chars, scan_file, langs, lexicons, font, fonts_file, collapse, arrow, show_pos, result) -> None:
    """Write snippets (.tex) and/or figures (.pdf) for characters in DATA."""
    entries = _load(data)
    lex = load_lexicon(entries, *lexicons)
    bad = [s for s in (styles or []) if s not in STYLES]
    if bad:
        raise click.BadParameter(f"unknown style(s) {bad}; choose from {sorted(STYLES)}", param_hint="--styles")
    default_lang = (langs or ("en",))[0]
    jobs = None
    if scan_file:
        jobs = {(c, s, l or default_lang) for c, s, l in scan_tex(scan_file)}
        if not jobs:
            click.echo(f"{scan_file}: no \\zi calls found")
    res = build_snippets(entries, out, jobs, chars=chars, styles=styles, langs=list(langs) or ["en"], emit=emit,
                         lex=lex, font=font, fonts=FontConfig.load(fonts_file) if fonts_file else None, math_opts={"collapse": collapse, "arrow": arrow, "show_pos": show_pos, "result": result})
    click.echo(f"{out}: {len(res.tex)} .tex, {len(res.pdf)} .pdf")
    if res.missing:
        click.echo(f"not in {data}: {' '.join(res.missing)}", err=True)
    if res.glyph_missing:
        click.echo(f"no glyph for: {' '.join(res.glyph_missing)} (drawn as a boxed label; see `zitex fonts`)", err=True)
    if res.failed:
        click.echo(f"failed to compile: {' '.join(str(p) for p in res.failed)}", err=True)
        sys.exit(1)


@main.command()
@click.argument("data", type=FILE)
@click.option("--fonts", "fonts_file", type=FILE, help="fonts.yaml (default: Noto Serif CJK SC, no fallbacks)")
@click.option("--strict", is_flag=True, help="exit 1 if any component has no glyph")
def fonts(data, fonts_file, strict) -> None:
    """Report which font (or image) draws each component, and which have no glyph."""
    cfg = FontConfig.load(fonts_file) if fonts_file else FontConfig()
    rep = coverage_report(_load(data), cfg)
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


@main.command()
@click.argument("char")
@click.option("-f", "--data", required=True, type=FILE, help="decomposition YAML")
@click.option("-s", "--style", type=click.Choice(sorted(STYLES)), default="tree", show_default=True)
@click.option("-l", "--lang", default="en", show_default=True)
@click.option("-x", "--lexicon", "lexicons", multiple=True, type=FILE)
@click.option("--fonts", "fonts_file", type=FILE, help="fonts.yaml")
@math_options
def render_cmd(char, data, style, lang, lexicons, fonts_file, collapse, arrow, show_pos, result) -> None:
    """Print the LaTeX snippet for one character to stdout (no files)."""
    entries = _load(data)
    e = next((x for x in entries if x.char == char), None)
    if e is None:
        click.echo(f"{char}: not in {data}", err=True)
        sys.exit(1)
    kw: dict = {}
    if style in ("math", "formula"):
        kw.update(lang=lang, lex=load_lexicon(entries, *lexicons))
    if style == "math":
        kw.update(collapse=collapse, arrow=arrow, show_pos=show_pos, result=result)
    click.echo(render(e, style, fonts=FontConfig.load(fonts_file) if fonts_file else None, **kw))


main.add_command(render_cmd, name="render")

if __name__ == "__main__":
    main()
