---
name: theme
description: Generate and apply CSS themes for Svelte/SvelteKit + Bun projects. Connects
  to THM adapter service (self-hosted tweakcn + neutral protocol + format adapters).
  Use when (1) Starting a new project and need a theme, (2) Importing a tweakcn preset,
  (3) Generating variables.css from a saved theme, (4) Listing available themes or adapters.
  Primary command is /theme. Requires THM service at thm.ism.la or localhost:3110.
---

# Theme: CSS Theme Generation via THM

Generate, import, and apply CSS themes through the THM adapter service.

## What This Skill Does

Bridges the tweakcn visual theme editor and your project's CSS through a neutral JSON protocol.
The THM service translates tweakcn's shadcn-format output into framework-specific CSS.

```
tweakcn (visual editor) → neutral protocol (JSON) → adapter → variables.css
```

## Available Adapters

| Adapter | Output | Use Case |
|---------|--------|----------|
| `svelte-semantic` | `variables.css` with `--bg`, `--surface`, `--text`, faded states, brutalist shadows, spacing scale | Svelte/SvelteKit + Bun stack |
| `vanilla-css` | Plain `:root`/`.dark` custom properties | Any project, no opinions |
| `tailwind-v4` | `@theme inline` block with color/radius mappings | Tailwind CSS v4 projects |

## Commands

### `/theme`

Interactive theme workflow. Lists saved themes, lets user pick or import, runs adapter, writes output.

### `/theme list`

List all saved themes in the THM database.

### `/theme import <preset>`

Import a tweakcn preset by name. Available presets include:
`neo-brutalism`, `modern-minimal`, `violet-bloom`, `t3-chat`, `mocha-mousse`,
`cosmic-night`, `bold-tech`, `elegant-luxury`, `clean-slate`, `ocean-breeze`,
`midnight-bloom`, `northern-lights`, `vintage-paper`, `sunset-horizon`, and more.

### `/theme apply <theme-id> [adapter]`

Transform a saved theme through an adapter and write the output.
Default adapter: `svelte-semantic`.

### `/theme show <theme-id>`

Display the neutral protocol JSON for a saved theme.

## Workflow

### Import and Apply a Theme

```
User: /theme import neo-brutalism
Agent: Imports from tweakcn, translates to protocol, saves to DB.

User: /theme apply neo-brutalism svelte-semantic
Agent: Runs adapter, writes variables.css to the project.
```

### Interactive Mode

```
User: /theme
Agent:
  1. Calls theme_list to show saved themes
  2. Asks user to pick a theme or import a new preset
  3. Asks which adapter to use (defaults to svelte-semantic)
  4. Generates the CSS output
  5. Asks where to write it (default: app/styles/variables.css or src/styles/variables.css)
  6. Writes the file and shows a summary of what changed
```

## Connection

### MCP (preferred)

The THM service exposes MCP tools. If configured as an MCP server in your Claude settings:

| Tool | Description |
|------|-------------|
| `theme_list` | List all saved themes |
| `theme_get` | Fetch a theme by ID |
| `theme_save` | Save a new theme |
| `theme_adapt` | Transform through adapter |
| `theme_import` | Import a tweakcn preset |

### REST Fallback

If MCP is not configured, use the REST API at `thm.ism.la`:

```bash
# List themes
curl https://thm.ism.la/api/themes

# Import a preset
curl -X POST https://thm.ism.la/api/import \
  -H "Content-Type: application/json" \
  -d '{"preset": "neo-brutalism"}'

# Adapt a theme
curl -X POST https://thm.ism.la/api/adapt \
  -H "Content-Type: application/json" \
  -d '{"theme_id": "neo-brutalism", "adapter": "svelte-semantic"}'
```

## Neutral Protocol Schema

The framework-agnostic JSON contract between tweakcn and adapters:

```json
{
  "name": "theme-name",
  "modes": {
    "light": {
      "colors": {
        "primary": "#hex", "primary-foreground": "#hex",
        "secondary": "#hex", "secondary-foreground": "#hex",
        "accent": "#hex", "accent-foreground": "#hex",
        "destructive": "#hex", "destructive-foreground": "#hex",
        "background": "#hex", "surface": "#hex",
        "muted": "#hex", "text": "#hex", "text-muted": "#hex",
        "border": "#hex", "input": "#hex", "ring": "#hex"
      },
      "shadows": {
        "color": "#hex", "opacity": 1.0,
        "blur": 0, "spread": 0,
        "offset-x": 4, "offset-y": 4
      }
    },
    "dark": { "colors": {}, "shadows": {} }
  },
  "typography": {
    "sans": "Font, sans-serif",
    "serif": "Font, serif",
    "mono": "Font, monospace"
  },
  "spacing": { "base": "0.25rem" },
  "radius": "0px"
}
```

## Translation Map (tweakcn → Protocol)

When importing from tweakcn, these shadcn variables are mapped:

| tweakcn | protocol | notes |
|---------|----------|-------|
| `--background` | `colors.background` | |
| `--foreground` | `colors.text` | renamed |
| `--card` | `colors.surface` | renamed |
| `--muted-foreground` | `colors.text-muted` | renamed |
| `--primary` | `colors.primary` | direct |
| `--secondary` | `colors.secondary` | direct |
| `--accent` | `colors.accent` | direct |
| `--destructive` | `colors.destructive` | direct |
| `--border`, `--input`, `--ring` | direct | direct |
| `--popover-*`, `--chart-*`, `--sidebar-*` | dropped | not used |

## Svelte-Semantic Adapter Details

The `svelte-semantic` adapter produces a complete `variables.css` with:

1. **Semantic naming** — `--bg`, `--surface`, `--text` (not `--background`, `--card`, `--foreground`)
2. **Faded states** — `--primary-faded`, `--secondary-faded`, `--accent-faded` (solid hex, calculated from 40% mix with white/surface)
3. **Brutalist shadows** — hard-offset `Npx Npx 0px 0px` (no blur)
4. **Spacing scale** — `--space-1` through `--space-8` from base unit
5. **Both modes** — `:root` and `.dark` blocks
6. **Body reset** — `* { margin:0; padding:0; box-sizing:border-box }` + body styles
