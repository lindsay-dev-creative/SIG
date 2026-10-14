# Shopify Prestige build rules

Rules for Claude when turning a Figma design into a working Shopify page on the Prestige theme. Follow every rule unless Lindsay says otherwise.

## Tools

- **Shopify Dev MCP**: docs lookup and Liquid validation. Must run with `LIQUID=true` and `LIQUID_VALIDATION_MODE=full`.
- **Figma MCP**: read frames, variables, and screenshots.
- **Shopify CLI**: `shopify theme dev` for preview, `shopify theme check` for linting, `shopify theme push` to upload.
- Work in the client theme repo, for example `Desktop/CLIENTS/SIG/signaturesociety-theme`.

Dev MCP config:

```json
{
  "mcpServers": {
    "shopify-dev-mcp": {
      "command": "npx",
      "args": ["-y", "@shopify/dev-mcp@latest"],
      "env": { "LIQUID": "true", "LIQUID_VALIDATION_MODE": "full" }
    }
  }
}
```

## Design sizes

- Lindsay designs two sizes in Figma: **1920 (desktop)** and **360 (mobile)**.
- There is no tablet frame. Claude builds the **768 tablet view** in Shopify. See "Tablet rules".

## Workflow

1. **Confirm a backup.** Work only on an unpublished duplicate of the live theme. Never touch the published theme.
2. **Learn first.** Call `learn_shopify_api` before writing any Liquid. Use `search_docs_chunks` for any object, filter, or tag you are unsure of. Do not guess.
3. **Read the design.** For each frame, call `get_design_context`, `get_variable_defs`, and `get_screenshot`.
4. **Map to Prestige first.** For each section, check if a Prestige section, block, or theme setting already does it. Report the mapping to Lindsay before building anything custom.
5. **Build.** Follow "Prestige rules" and "Type rules".
6. **Build tablet.** Follow "Tablet rules".
7. **Validate.** Run `validate_theme` after every new or changed file. Fix every error.
8. **Lint.** Run `shopify theme check` before pushing. Fix errors. Report any warnings left.
9. **Preview.** Run `shopify theme dev`. Compare to the Figma screenshots at 360 and 1920. Review 768 by eye.
10. **Push.** Push to the unpublished duplicate only. Lindsay publishes after client sign-off.

## Prestige rules

Do:
- Use Prestige sections, blocks, and theme settings before writing code.
- Name custom files with the client code prefix: `sections/sig-hero.liquid`, `snippets/sig-card.liquid`.
- Put all custom CSS in one file: `assets/[code]-custom.css`.
- Read the theme's base CSS for existing variables, class names, and breakpoints. Reuse them.
- Give every editable text, image, and link a `{% schema %}` setting.
- Use Prestige theme blocks for repeatable pieces.
- Log every custom file and any core edit in `CHANGES.md` at the repo root.

Do not:
- Edit core Prestige files. If there is no other way, ask Lindsay first and log the exact edit in `CHANGES.md`.
- Hardcode copy, links, or images in Liquid.
- Guess Prestige class names or CSS variables.
- Use `!important` to override the theme.
- Add fonts or scripts the design does not need.

Why: Prestige updates replace core files. Prefixed custom files survive updates.

## Liquid checks

| Check | Catches | When |
|---|---|---|
| `validate_theme` | Bad syntax, unknown objects and filters, broken schema JSON, missing snippets | After every file change |
| `shopify theme check` | Performance issues, missing alt text, deprecated tags, unused variables, missing translations | Before every push |
| Theme editor test | Settings that don't save, blocks that break when empty or reordered | Before sign-off |

Common errors to catch:
- Missing `{% endif %}`, `{% endfor %}`, or `{% endschema %}`.
- `{% include %}` used. Use `{% render %}`.
- Images not using `image_url` and `image_tag` with widths and alt text.
- No blank check on settings, for example `{% if section.settings.heading != blank %}`.
- Schema JSON with trailing commas or duplicate setting IDs.
- Hardcoded text that belongs in a setting or `locales/en.default.json`.

## Type rules

- Every `font-size` uses a `--step` token. No fixed px or raw rem font sizes.
- Use rem, never px, so browser zoom works.
- Never change the root font size on `html`.
- Line height is unitless: `1.15` for headings, `1.7` for body.
- Map the steps onto Prestige's existing heading variables so theme and custom sections match.
- For client work, replace the base size and ratios with the client's brand values and recompute the scale.

LDC default scale. Fluid from 360 to 1920. Base 15px. Ratio 1.125 at 360, 1.25 at 1920.

```css
:root {
  --step--1: clamp(0.75rem, 0.853rem - 0.085vw, 0.833rem);
  --step-0:  0.9375rem;
  --step-1:  clamp(1.055rem, 1.028rem + 0.120vw, 1.172rem);
  --step-2:  clamp(1.187rem, 1.122rem + 0.285vw, 1.465rem);
  --step-3:  clamp(1.335rem, 1.220rem + 0.509vw, 1.831rem);
  --step-4:  clamp(1.502rem, 1.320rem + 0.807vw, 2.289rem);
  --step-5:  clamp(1.689rem, 1.419rem + 1.202vw, 2.861rem);
  --step-6:  clamp(1.901rem, 1.514rem + 1.719vw, 3.576rem);
}
```

| Token | Use | 360 | 768 | 1920 |
|---|---|---|---|---|
| `--step-6` | Hero headline | 30px | 37px | 57px |
| `--step-5` | H1 | 27px | 32px | 46px |
| `--step-4` | H2 | 24px | 27px | 37px |
| `--step-3` | H3 | 21px | 23px | 29px |
| `--step-2` | H4, large intro | 19px | 20px | 23px |
| `--step-1` | Lead paragraph | 17px | 17px | 19px |
| `--step-0` | Body | 15px | 15px | 15px |
| `--step--1` | Captions, small print | 13px | 13px | 12px |

To recompute for a client: for each step `n`, min = base × mobileRatio^n, max = base × desktopRatio^n. Slope = (max − min) / (1920 − 360). Intercept = min − slope × 360. Write as `clamp(min, intercept + slope×100vw, max)` in rem (divide px by 16).

## Tablet rules

- Type and spacing scale on their own through the fluid tokens.
- Layout follows the closest Figma frame. Grids drop columns, for example 4 on desktop, 2 on tablet, 1 on mobile.
- Side-by-side blocks stay side by side if each column still reads well. If not, stack them like mobile.
- Navigation follows mobile unless the desktop menu fits at 768.
- Images keep their crop and focal point. No new art direction without asking.
- Use Prestige's existing breakpoints in the code. Do not add new media queries. 768 is the check width, not a new breakpoint.
- After building, list every tablet judgment call so Lindsay can approve or change it.

## Done checklist

- [ ] Work done on the unpublished duplicate theme
- [ ] Prestige settings used wherever possible
- [ ] Custom files prefixed and logged in `CHANGES.md`
- [ ] `validate_theme` returns no errors
- [ ] `shopify theme check` returns no errors
- [ ] All font sizes use `--step` tokens
- [ ] Page matches Figma at 360 and 1920
- [ ] Tablet view at 768 reviewed, judgment calls listed
- [ ] Every section editable in the theme editor, including empty states
- [ ] Images have alt text and load at the right sizes
- [ ] Client signed off before publishing
