# agyswap Release Checklist

Every release **must** update ALL of the following files. No exceptions.

---

## Step 1 — Bump Version in Code & Metadata

- [ ] `agyswap.py` → `VERSION = "x.y.z"` (line ~56)
- [ ] `bin/agyswap` → run `cp agyswap.py bin/agyswap`
- [ ] `pyproject.toml` → `version = "x.y.z"`

## Step 2 — Update Documentation

- [ ] `README.md` → Update feature list and command reference for new features
- [ ] `CHANGELOG.md` → Add new `## [x.y.z] — YYYY-MM-DD` section at top
- [ ] `docs/index.html` (GitHub Pages) → version badge, feature tiles, command cards
- [ ] `assets/architecture.svg` → update `agyswap Engine Core (vX.Y.Z)` text
- [ ] `docs/assets/architecture.svg` → **same as above — both files are independent copies, update both!**

> ⚠️ Quick command to update both SVGs at once:
> ```bash
> sed -i '' 's/Engine Core (vOLD)/Engine Core (vNEW)/g' assets/architecture.svg docs/assets/architecture.svg
> ```

## Step 3 — Commit & Tag

```bash
cp agyswap.py bin/agyswap
git add -A
git commit -m "chore(release): bump version to vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## Step 4 — GitHub Release

- [ ] Create GitHub Release for tag `vX.Y.Z` with release notes
- [ ] Copy release notes from `CHANGELOG.md`

## Step 5 — Homebrew Formula (after GitHub release exists)

```bash
# Get sha256 of the released tarball
curl -sL https://github.com/g1mn/agyswap/archive/refs/tags/vX.Y.Z.tar.gz | shasum -a 256

# Then update Formula/agyswap.rb:
#   url "https://github.com/g1mn/agyswap/archive/refs/tags/vX.Y.Z.tar.gz"
#   sha256 "<new-hash>"
```

- [ ] `Formula/agyswap.rb` → update `url` and `sha256`
- [ ] `git add Formula/agyswap.rb && git commit -m "chore(formula): bump Homebrew formula to vX.Y.Z" && git push`
- [ ] Also update `g1mn/homebrew-tap` repo with the same sha256

---

## Complete File Checklist (9 files total)

| # | File | What to change |
|---|---|---|
| 1 | `agyswap.py` | `VERSION = "x.y.z"` |
| 2 | `bin/agyswap` | `cp agyswap.py bin/agyswap` |
| 3 | `pyproject.toml` | `version = "x.y.z"` |
| 4 | `README.md` | Feature list, command reference |
| 5 | `CHANGELOG.md` | New version section at top |
| 6 | `docs/index.html` | Version badge, tiles, command cards |
| 7 | `assets/architecture.svg` | `Engine Core (vX.Y.Z)` text |
| 8 | `docs/assets/architecture.svg` | `Engine Core (vX.Y.Z)` text (independent copy!) |
| 9 | `Formula/agyswap.rb` | `url` + `sha256` (after GitHub release) |

## Notes

- `bin/agyswap` is always a mirror of `agyswap.py` — never edit separately.
- `assets/architecture.svg` and `docs/assets/architecture.svg` are **two independent files** — update both every time.
- GitHub Pages (`https://g1mn.github.io/agyswap/`) auto-deploys from `docs/` folder on push to `main` (2–3 min).
- Formula sha256 must be computed **after** the GitHub release tar.gz is published.
