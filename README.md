# extensions-snapshot

Builds my in-progress extension changes from a branch of my fork of
[keiyoushi/extensions-source](https://github.com/keiyoushi/extensions-source) and publishes
them as an installable extension repo on GitHub Pages, so I can test them on real devices
(iOS via [Tachimanga](https://tachimanga.app/), Android via Mihon) before they're merged
upstream.

My fork stays a clean mirror of upstream — all the pipeline lives here.

## Repo URL (add this in your app)

```
https://quentinvdr.github.io/extensions-snapshot/index.min.json
```

- **Tachimanga (iOS):** Settings → Extensions → repo icon → Add repository → paste the URL.
- **Mihon (Android):** Settings → Browse → Extension repos → add the URL.

Keep the official Keiyoushi repo added alongside it.

## How to publish a branch

1. Push your work to a branch on your fork.
2. Here: **Actions → Publish snapshot → Run workflow**, enter the branch name (and fork if
   different from the default).
3. When it finishes, refresh extensions in the app and install/update.

## How it works

- Checks out the fork at the chosen branch and diffs it against `upstream/main` to find the
  extensions you changed (reuses the fork's own `generate-build-matrices.py`).
- Builds + signs those extensions, then generates `index.min.json` + `apk/` + `icon/`
  (reuses the fork's `create-repo.py`).
- [`scripts/merge-snapshot.py`](scripts/merge-snapshot.py) merges them into the published
  `gh-pages` repo and **drops any extension that upstream has already caught up to** — so once
  your PR merges and Keiyoushi publishes, the app falls back to the official build
  automatically.

## Signing (recommended, optional)

Without a key, builds use a debug signature — works, but each rebuild changes the signer and
forces an uninstall/reinstall on the device. To get smooth in-place updates, create one
keystore and add these repo **Actions secrets**:

| Secret | Value |
| --- | --- |
| `SIGNING_KEY` | base64 of your `.jks` keystore |
| `ALIAS` | key alias |
| `KEY_STORE_PASSWORD` | keystore password |
| `KEY_PASSWORD` | key password |

```bash
keytool -genkey -v -keystore snapshot.jks -alias snapshot \
  -keyalg RSA -keysize 2048 -validity 9000
base64 -w0 snapshot.jks   # paste output into the SIGNING_KEY secret
```
