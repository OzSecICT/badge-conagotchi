#!/usr/bin/env python3
"""
stackup-renderer.py — Render a .kicad_pcb file across all solder mask / silkscreen /
                       copper finish combinations and generate an HTML Render Browser.

Usage: python3 stackup-renderer.py [board.kicad_pcb]
       (board path is optional; defaults to ../kicad/OzSec2026-ESP32/OzSec2026-ESP32.kicad_pcb)

Author:  Claude (Anthropic)  —  https://claude.ai
Project: stackup-renderer / KiCad multi-variant 3D render pipeline
"""

import sys
import os
import re
import json
import platform
import subprocess
import tempfile


def detect_kicad():
    """
    Return (kicad_cli, kicad_share) for the current OS.
    Both can be overridden via environment variables:
      KICAD_CLI   — full path to the kicad-cli executable
      KICAD_SHARE — path to the KiCad shared-support folder
                    (parent of 3dmodels/, symbols/, etc.)
    """
    system = platform.system()

    if system == "Darwin":          # macOS
        default_cli   = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
        default_share = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
    elif system == "Windows":
        default_cli   = r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
        default_share = r"C:\Program Files\KiCad\9.0\share\kicad"
    else:                           # Linux / other
        default_cli   = "kicad-cli"          # assumed to be on PATH
        default_share = "/usr/share/kicad"

    kicad_cli   = os.environ.get("KICAD_CLI",   default_cli)
    kicad_share = os.environ.get("KICAD_SHARE", default_share)
    return kicad_cli, kicad_share


def _use_unicode_bars() -> bool:
    """Return True if the terminal supports Unicode block characters."""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.kernel32.GetConsoleOutputCP() == 65001
        except Exception:
            return False
    return True

# --- Render settings ---
RENDER_ARGS_COMMON = [
    "--width", "1024",
    "--height", "768",
    "--perspective",
    "--quality", "high",
    "--pan", "0,1,0",
]

VIEWS = [
    {
        "suffix": "front",
        "rotate": "345,0,15",
    },
    {
        "suffix": "back",
        "rotate": "345,180,15",
    },
]

# --- All stackup variants ---
VARIANTS = [
    {
        "name": "Black_Gold",
        "mask_color": "Black",
        "silk_color": "White",
        "copper_finish": "ENIG",
    },
    {
        "name": "Black_Silver",
        "mask_color": "Black",
        "silk_color": "White",
        "copper_finish": "HAL SnPb",
    },
    {
        "name": "Green_Silver",
        "mask_color": "Green",
        "silk_color": "White",
        "copper_finish": "HAL SnPb",
    },
    {
        "name": "Purple_Silver",
        "mask_color": "Purple",
        "silk_color": "White",
        "copper_finish": "HAL SnPb",
    },
    {
        "name": "Red_Silver",
        "mask_color": "Red",
        "silk_color": "White",
        "copper_finish": "HAL SnPb",
    },
    {
        "name": "Yellow_Silver",
        "mask_color": "Yellow",
        "silk_color": "White",
        "copper_finish": "HAL SnPb",
    },
    {
        "name": "Blue_Silver",
        "mask_color": "Blue",
        "silk_color": "White",
        "copper_finish": "HAL SnPb",
    },
    {
        "name": "White_Silver",
        "mask_color": "White",
        "silk_color": "Black",
        "copper_finish": "HAL SnPb",
    },
    {
        "name": "Green_Gold",
        "mask_color": "Green",
        "silk_color": "White",
        "copper_finish": "ENIG",
    },
    {
        "name": "Purple_Gold",
        "mask_color": "Purple",
        "silk_color": "White",
        "copper_finish": "ENIG",
    },
    {
        "name": "Red_Gold",
        "mask_color": "Red",
        "silk_color": "White",
        "copper_finish": "ENIG",
    },
    {
        "name": "Yellow_Gold",
        "mask_color": "Yellow",
        "silk_color": "White",
        "copper_finish": "ENIG",
    },
    {
        "name": "Blue_Gold",
        "mask_color": "Blue",
        "silk_color": "White",
        "copper_finish": "ENIG",
    },
    {
        "name": "White_Gold",
        "mask_color": "White",
        "silk_color": "Black",
        "copper_finish": "ENIG",
    },
]


def apply_stackup(content: str, variant: dict) -> str:
    """Patch the stackup block in a .kicad_pcb file string."""

    mask = variant["mask_color"]
    silk = variant["silk_color"]
    finish = variant["copper_finish"]

    content = re.sub(
        r'(layer "(?:F|B)\.Mask"[^)]*?\(type "[^"]*"\)[^)]*?)\(color "[^"]*"\)',
        rf'\1(color "{mask}")',
        content,
        flags=re.DOTALL,
    )

    content = re.sub(
        r'(layer "(?:F|B)\.SilkS"[^)]*?\(type "[^"]*"\)[^)]*?)\(color "[^"]*"\)',
        rf'\1(color "{silk}")',
        content,
        flags=re.DOTALL,
    )

    content = re.sub(
        r'\(copper_finish "[^"]*"\)',
        f'(copper_finish "{finish}")',
        content,
    )

    return content


def render_view(tmp_path: str, output_png: str, rotate: str, kicad_cli: str) -> bool:
    """Run kicad-cli to render a single view. Returns True on success."""
    cmd = [
        kicad_cli, "pcb", "render",
        "--output", output_png,
        "--rotate", rotate,
        *RENDER_ARGS_COMMON,
        tmp_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    stdout: {result.stdout.strip()}")
        print(f"    stderr: {result.stderr.strip()}")
        return False
    return True


def friendly_name(variant: dict) -> str:
    """Return a human-readable label for a variant."""
    finish_label = "ENIG (Gold)" if variant["copper_finish"] == "ENIG" else "HASL (Silver)"
    return f"{variant['mask_color']} mask / {variant['silk_color']} silk / {finish_label}"


def generate_index(output_dir: str, board_base: str, variants: list, views: list):
    """Write _index.htm into output_dir."""

    js_variants = []
    for v in variants:
        name = v["name"]
        images = {view["suffix"]: f"{board_base}_{name}_{view['suffix']}.png" for view in views}
        js_variants.append({
            "name": name,
            "label": friendly_name(v),
            "images": images,
        })

    js_data = json.dumps(js_variants, indent=2)

    thumb_items = []
    for v in js_variants:
        name = v["name"]
        label = v["label"]
        front_img = v["images"].get("front", "")
        display_name = name.replace("_", " ")
        thumb_items.append(
            f'      <div class="thumb-card" data-name="{name}" onclick="selectVariant(\'{name}\')" title="{label}">'
            f'<div class="thumb-img-wrap"><img src="{front_img}" alt="{label}" loading="lazy"></div>'
            f'<div class="thumb-label">{display_name}</div></div>'
        )
    thumbs_html = "\n".join(thumb_items)

    options_html = "\n".join(
        f'          <option value="{v["name"]}">{v["label"]}</option>'
        for v in js_variants
    )

    view_tabs_html = "\n".join(
        f'        <button class="view-tab" data-view="{view["suffix"]}" onclick="selectView(this)">'
        f'{view["suffix"].capitalize()}</button>'
        for view in views
    )

    first_view = views[0]["suffix"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Render Browser — {board_base}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=JetBrains+Mono:wght@400;600&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:       #0a0c0f;
      --surface:  #111418;
      --border:   #1e2329;
      --accent:   #00e5a0;
      --text:     #e8eaed;
      --muted:    #6b7280;
      --card-bg:  #13181f;
      --radius:   8px;
    }}

    html, body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
      min-height: 100vh;
    }}

    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      background: repeating-linear-gradient(
        0deg,
        transparent, transparent 2px,
        rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px
      );
      pointer-events: none;
      z-index: 999;
    }}

    /* ── Header ── */
    header {{
      padding: 1.75rem 2rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: baseline;
      gap: 1rem;
      flex-wrap: wrap;
    }}
    .header-title {{
      display: flex;
      align-items: baseline;
      gap: 0.75rem;
    }}
    .header-title h1 {{
      font-family: 'Courier Prime', 'Courier New', monospace;
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: 0.01em;
      color: var(--text);
    }}
    .header-title .sep {{
      color: var(--accent);
      font-family: 'Courier Prime', monospace;
      font-size: 1.35rem;
    }}
    .header-title .board-name {{
      font-family: 'Courier Prime', 'Courier New', monospace;
      font-size: 1.35rem;
      font-weight: 400;
      color: var(--muted);
    }}
    .pill {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      color: var(--muted);
      background: var(--border);
      padding: 0.2rem 0.65rem;
      border-radius: 999px;
    }}

    /* ── Layout ── */
    .layout {{
      display: grid;
      grid-template-columns: 1fr;
    }}

    @media (min-width: 860px) {{
      .layout {{
        grid-template-columns: 1fr 1fr;
        height: calc(100vh - 69px);
      }}
      .detail, .overview {{
        overflow-y: auto;
        height: 100%;
      }}
      .detail {{ border-right: 1px solid var(--border); }}
    }}

    /* ── Detail panel ── */
    .detail {{
      padding: 1.75rem;
      border-bottom: 1px solid var(--border);
    }}
    @media (min-width: 860px) {{ .detail {{ border-bottom: none; }} }}

    .controls {{
      display: flex;
      gap: 0.6rem;
      align-items: center;
      margin-bottom: 1.25rem;
      flex-wrap: wrap;
    }}
    .select-wrap {{
      position: relative;
      flex: 1;
      min-width: 200px;
    }}
    .select-wrap::after {{
      content: '▾';
      position: absolute;
      right: 0.9rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--accent);
      pointer-events: none;
    }}
    select {{
      width: 100%;
      appearance: none;
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      padding: 0.6rem 2.2rem 0.6rem 0.9rem;
      border-radius: var(--radius);
      cursor: pointer;
      transition: border-color 0.15s;
    }}
    select:focus {{ outline: none; border-color: var(--accent); }}

    .view-tabs {{ display: flex; gap: 0.35rem; }}
    .view-tab {{
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--muted);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      padding: 0.5rem 1rem;
      border-radius: var(--radius);
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      transition: all 0.15s;
    }}
    .view-tab:hover {{ border-color: var(--accent); color: var(--accent); }}
    .view-tab.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #000;
      font-weight: 700;
    }}

    .img-frame {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 260px;
    }}
    .img-frame img {{
      width: 100%;
      height: auto;
      max-height: 460px;
      object-fit: contain;
      display: block;
      transition: opacity 0.18s;
    }}
    .img-frame img.fade {{ opacity: 0; }}

    .meta {{
      margin-top: 0.9rem;
      display: flex;
      gap: 1.25rem;
      flex-wrap: wrap;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      color: var(--muted);
    }}
    .meta span b {{ color: var(--text); font-weight: 600; }}

    /* ── Overview ── */
    .overview {{ padding: 1.75rem; }}
    .overview h2 {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 1rem;
    }}
    .thumb-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
      gap: 0.65rem;
    }}
    .thumb-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      cursor: pointer;
      transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s;
    }}
    .thumb-card:hover {{
      border-color: var(--accent);
      transform: translateY(-2px);
    }}
    .thumb-card.active {{
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--accent);
    }}
    .thumb-img-wrap {{
      aspect-ratio: 4/3;
      overflow: hidden;
      background: #0d1117;
    }}
    .thumb-img-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.2s;
    }}
    .thumb-card:hover .thumb-img-wrap img {{ transform: scale(1.05); }}
    .thumb-label {{
      padding: 0.4rem 0.55rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.62rem;
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
  </style>
</head>
<body>

<header>
  <div class="header-title">
    <h1>Render Browser</h1>
    <span class="sep">/</span>
    <span class="board-name">{board_base}</span>
  </div>
  <span class="pill">{len(variants)} variants &middot; {len(views)} views each</span>
</header>

<div class="layout">

  <section class="detail">
    <div class="controls">
      <div class="select-wrap">
        <select id="variantSelect" onchange="selectVariant(this.value)">
{options_html}
        </select>
      </div>
      <div class="view-tabs">
{view_tabs_html}
      </div>
    </div>
    <div class="img-frame">
      <img id="detailImg" src="" alt="PCB render">
    </div>
    <div class="meta" id="detailMeta"></div>
  </section>

  <section class="overview">
    <h2>All variants — front view</h2>
    <div class="thumb-grid">
{thumbs_html}
    </div>
  </section>

</div>

<script>
  const VARIANTS = {js_data};

  let currentName = VARIANTS[0].name;
  let currentView = '{first_view}';

  function byName(n) {{ return VARIANTS.find(v => v.name === n); }}

  function selectVariant(name) {{
    currentName = name;
    document.getElementById('variantSelect').value = name;
    updateDetail();
    updateThumbActive();
  }}

  function selectView(btn) {{
    document.querySelectorAll('.view-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentView = btn.dataset.view;
    updateDetail();
  }}

  function updateDetail() {{
    const v   = byName(currentName);
    const img = document.getElementById('detailImg');
    img.classList.add('fade');
    setTimeout(() => {{
      img.src = v.images[currentView] || '';
      img.alt = v.label + ' — ' + currentView;
      img.onload = () => img.classList.remove('fade');
    }}, 80);

    const parts = v.label.split(' / ');
    document.getElementById('detailMeta').innerHTML =
      parts.map(p => {{
        const words = p.trim().split(' ');
        const key   = words[0];
        const val   = words.slice(1).join(' ');
        return `<span><b>${{key}}</b> ${{val}}</span>`;
      }}).join('');
  }}

  function updateThumbActive() {{
    document.querySelectorAll('.thumb-card').forEach(card => {{
      card.classList.toggle('active', card.dataset.name === currentName);
    }});
  }}

  document.querySelector('.view-tab').classList.add('active');
  selectVariant(VARIANTS[0].name);
</script>

</body>
</html>
"""

    index_path = os.path.join(output_dir, "_index.htm")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    return index_path


def print_banner():
    """Print the startup ASCII art banner."""
    b = [
        "",
        "  " + "─" * 79,
        "",
        "   ███████╗████████╗ █████╗  ██████╗██╗  ██╗██╗   ██╗██████╗",
        "   ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝██║   ██║██╔══██╗",
        "   ███████╗   ██║   ███████║██║     █████╔╝ ██║   ██║██████╔╝",
        "   ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ ██║   ██║██╔═══╝",
        "   ███████║   ██║   ██║  ██║╚██████╗██║  ██╗╚██████╔╝██║",
        "   ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝",
        "",
        "   ██████╗ ███████╗███╗   ██╗██████╗ ███████╗██████╗ ███████╗██████╗",
        "   ██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔════╝██╔══██╗██╔════╝██╔══██╗",
        "   ██████╔╝█████╗  ██╔██╗ ██║██║  ██║█████╗  ██████╔╝█████╗  ██████╔╝",
        "   ██╔══██╗██╔══╝  ██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗██╔══╝  ██╔══██╗",
        "   ██║  ██║███████╗██║ ╚████║██████╔╝███████╗██║  ██║███████╗██║  ██║",
        "   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝",
        "",
        "   ── KiCad multi-variant 3D render pipeline ── authored by Claude · Anthropic ──",
        "",
        "  " + "─" * 79,
        "",
    ]
    print("\n".join(b))


def main():
    print_banner()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    DEFAULT_BOARD = os.path.join(
        script_dir, "..", "kicad", "OzSec2026-ESP32", "OzSec2026-ESP32.kicad_pcb"
    )

    board_path = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_BOARD

    if not os.path.isfile(board_path):
        print(f"Error: file not found: {board_path}")
        print(f"  (resolved to: {os.path.abspath(board_path)})")
        sys.exit(1)

    board_dir  = os.path.dirname(os.path.abspath(board_path))
    board_base = os.path.splitext(os.path.basename(board_path))[0]
    output_dir = script_dir
    os.makedirs(output_dir, exist_ok=True)

    # --- Platform detection ---
    kicad_cli, kicad_share = detect_kicad()
    unicode_bars = _use_unicode_bars()

    # --- KiCad 9 environment variables ---
    os.environ.setdefault("KICAD9_3DMODEL_DIR",   os.path.join(kicad_share, "3dmodels"))
    os.environ.setdefault("KICAD9_SYMBOL_DIR",    os.path.join(kicad_share, "symbols"))
    os.environ.setdefault("KICAD9_FOOTPRINT_DIR", os.path.join(kicad_share, "footprints"))
    os.environ.setdefault("KICAD9_TEMPLATE_DIR",  os.path.join(kicad_share, "templates"))

    # KIPRJMOD — resolves ${KIPRJMOD} references inside the .kicad_pcb file
    # Custom 3D models expected at KIPRJMOD/3dmodels/
    os.environ["KIPRJMOD"] = board_dir

    with open(board_path, "r", encoding="utf-8") as f:
        original = f.read()

    total = len(VARIANTS) * len(VIEWS)
    print(f"Platform:           {platform.system()}")
    print(f"kicad-cli:          {kicad_cli}")
    print(f"Board:              {os.path.abspath(board_path)}")
    print(f"Output dir:         {output_dir}")
    print(f"KICAD9_3DMODEL_DIR: {os.environ['KICAD9_3DMODEL_DIR']}")
    print(f"KIPRJMOD:           {board_dir}")
    print(f"Variants:           {len(VARIANTS)}  x  Views: {len(VIEWS)}  =  {total} renders\n")

    failed = []
    counter = 0
    bar_width = 30
    FILL = "█" if unicode_bars else "="
    EMPTY = "░" if unicode_bars else "-"

    def render_status(counter, total, label, state):
        """Overwrite the current console line with a progress bar + status."""
        pct       = counter / total
        filled    = int(bar_width * pct)
        bar       = FILL * filled + EMPTY * (bar_width - filled)
        pct_str   = f"{int(pct * 100):3d}%"
        line      = f"\r[{bar}] {pct_str}  {counter:>{len(str(total))}}/{total}  {label:<32}  {state}"
        try:
            term_w = os.get_terminal_size().columns
        except OSError:
            term_w = 120
        print(line[:term_w], end="", flush=True)

    for variant in VARIANTS:
        name    = variant["name"]
        patched = apply_stackup(original, variant)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".kicad_pcb",
            dir=board_dir,
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(patched)
            tmp_path = tmp.name

        try:
            for view in VIEWS:
                counter += 1
                suffix     = view["suffix"]
                output_png = os.path.join(output_dir, f"{board_base}_{name}_{suffix}.png")
                label      = f"{name} [{suffix}]"

                render_status(counter, total, label, "rendering...")

                if render_view(tmp_path, output_png, view["rotate"], kicad_cli):
                    render_status(counter, total, label, "done ✓      ")
                else:
                    render_status(counter, total, label, "FAILED ✗    ")
                    failed.append(label)
        finally:
            os.unlink(tmp_path)

    # Move to next line after the progress bar
    print()

    if failed:
        print(f"\n⚠  {len(failed)} render(s) failed:")
        for f in failed:
            print(f"   • {f}")
    else:
        print(f"\nAll {total} renders saved to: {output_dir}")

    print("Generating _index.htm ... ", end="", flush=True)
    index_path = generate_index(output_dir, board_base, VARIANTS, VIEWS)
    print(f"done → {index_path}")

    # Prompt to open the index
    try:
        answer = input("\nOpen _index.htm in browser? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    if answer == "y":
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(index_path)}")


if __name__ == "__main__":
    main()