# factory-ed site

Source for https://factorydashed.com. GitHub Pages serves the `docs/` folder.

## Build

```bash
python3 build.py
```

## Add an app

1. Add its entry to `apps.json`: name, colors, features, themes.
2. Put its images in `docs/assets/<slug>/` and `docs/assets/<slug>/themes/`, with its icon as `icon.svg`.
3. Run the build.

It gets a home row, a logo stripe, a menu entry, its own page and a privacy page.

## Store links and video

Set `play`, `appStore` or `video` on the app in `apps.json`, then build. Empty values show "Coming to Google Play", "App Store later" and the default-theme screenshot.

Only use screenshots and video with sample data.
