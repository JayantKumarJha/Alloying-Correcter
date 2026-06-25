# Alloy Addition Calculator

A Streamlit app for melt-shop floor use: calculates exactly how much of each
alloying element to add — and how much dilution material is needed for
over-limit elements — to hit a target spec, given the current composition
from your test report, the molten bath weight, and melt/addition recovery
rates.

- **Step 1 — Main Ingredients**: list every charge material (Casting, TT,
  Wheels, Ingot, etc.) with its own weight and melting recovery %. Bath weight
  = sum of each material's retained weight.
- **Step 2 — Elements**: enter current % (from your test report) and target %
  for each element. The app auto-detects whether an element needs an
  **addition** (current below target) or **dilution** (current above target)
  — no manual mode switch needed.
- **Step 3 — Dilution material**: if any element is over-limit, name the
  diluting material (e.g. Casting/TT) and its recovery %. The app solves for
  exactly how much to add — driven by whichever over-limit element needs the
  *most* dilution — while simultaneously solving any other elements that still
  need adding, since the diluent's own weight dilutes those too.

All multi-element math (additions, and additions + dilution together) is
solved **simultaneously**, never one element at a time, since every addition
or dilution changes the bath weight and therefore every other element's %.

## Files
- `app.py` — the Streamlit app
- `requirements.txt` — Python dependencies

## Deploy it (free, ~5 minutes, works on phone)

1. **Create a GitHub repo**
   - Go to https://github.com/new, name it e.g. `alloy-calculator`, create it (public or private both work).
   - Upload `app.py` and `requirements.txt` to the repo (use "Add file → Upload files" on github.com, or `git push` if you use git locally).

2. **Deploy on Streamlit Community Cloud**
   - Go to https://share.streamlit.io and sign in with your GitHub account.
   - Click **"New app"**.
   - Pick your repo, branch (`main`), and main file path (`app.py`).
   - Click **Deploy**. First build takes 1-2 minutes.

3. **Use it on your phone**
   - You'll get a URL like `https://your-app-name.streamlit.app`.
   - Open that link in any phone browser — no install needed. Bookmark it or
     add it to your home screen (Share → "Add to Home Screen") for app-like access.

## Updating later
Any time you edit `app.py` in the GitHub repo, Streamlit Cloud automatically
redeploys the live app within a minute or two — no redeploy step needed.

## Notes on the math
- **Additions** for multiple elements (current % below target) are solved as a
  linear system together, so adding one correctly dilutes the others' % too.
- **Over-limit elements** (current % above target) are fixed by dilution, not
  addition. If several are over-limit at once, the app dilutes based on
  whichever needs the *most* dilution (the highest current/target ratio) —
  the others will land at or below their own target automatically, since
  diluting further than the worst case only helps a milder excess.
- The dilution material is assumed to contain ~0% of every tracked element
  (i.e. a clean diluent like primary aluminium or low-alloy scrap). If your
  diluting material actually carries meaningful amounts of a tracked element,
  add it as a Main Ingredient in Step 1 with its known weight instead.
- **Gross mass to weigh & add** already accounts for recovery/burn-off —
  that's the number to actually weigh on the floor.
