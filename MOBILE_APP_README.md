# DeAI Mobile — quick start (Android)

This repository now includes a phone-friendly web interface called **DeAI Mobile**. It processes one image at a time using the existing Python image engine, without needing terminal menus. It is **not** an offline Android APK.

## Open the app on your Android phone

1. Open **your fork**: https://github.com/BkongSilverback/AI-Image-Detection-Bypass
2. Tap **Code → Codespaces → Create codespace on main**. Make a **new** Codespace for this fork (the old Codespace was for the original author's repository). GitHub may need a few minutes to build the environment.
3. The Codespace should automatically install the CPU dependencies and start DeAI Mobile. If the app doesn't open automatically, look for **PORTS** in Codespaces, find port **8000**, and tap **Open in Browser**. Keep the port's visibility set to **Private**.
4. Once you see **DeAI Mobile**, choose an image, select Light or Medium, press **Process Image**, and then **Save to My Phone**.

Optional: In Android Chrome use the **⋮ menu → Add to Home screen**. It will look like an app, but still needs a running Codespace and internet connection.

## What it does / doesn't do

- One-at-a-time image processing on CPU, JPG/PNG/WebP input, 20 MB / 24 megapixel limit.
- Uses the existing \`scripts/deai.py\` engine in Light or Medium mode.
- Retains a copy of transparent masks when present, but processing can distort fine lines/edges and transparency may be imperfect if the original engine moves pixels.
- Doesn't override your original file; uploads and intermediate files are kept temporarily.
- Does **not** inject false camera metadata, query detector services, promise to evade any AI detectors, or verify authorship.
- Codespaces may have usage limits or costs; the web app stops responding when the Codespace stops.
- Security: keep port **Private**; it accepts uploaded images and has no separate password of its own.
- For an already-running Codespace based on your new fork, the files may need pulling and the app starting. Creating a **new** Codespace after this commit automatically configures everything.

## In case the new Codespace doesn't start automatically

In that new fork Codespace, run \`bash .devcontainer/start_mobile.sh\`, or inspect \`/tmp/deai-mobile.log\`. No special keys required. The auto-install command is \`bash .devcontainer/install_mobile.sh\` if the environment wasn't built successfully.

## Limitations

The original repository's detector-bypass claims have not been independently verified and detector scores are not proof of the origin of any artwork. For authorship records, preserve the original sketches, layers, and creation history.
