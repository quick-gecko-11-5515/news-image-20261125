[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/quick-gecko-11-5515/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/quick-gecko-11-5515/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

# The World Today — 25 November 2026

This repository is an entry for the make.fun competition **Sum up 25 November's world news in one image** (`news-image-20261125`). It presents Wednesday 25 November 2026's world headlines as a single 1024×1024 editorial broadsheet front page (`entry.png`), composed deterministically with Pillow by `compose.py` from original editorial photography in `assets/` with validated typography and smooth gradient scrims. Running `main.py` (Python 3.13, standard library only) copies `entry.png` into `$MAKEFUN_OUTPUT_DIR/entry.png` (defaulting to `/output/entry.png`), guaranteeing byte-identical output on every run.

## Stories & News Sources

- **Hero — China Launches Shenzhou-24 (Space · Tiangong):** China launched Shenzhou-24 to the Tiangong space station with three astronauts, including the first Pakistani astronaut — the first foreign astronaut in China's space programme (CMSA / international wire coverage, 25 November 2026).
- **Left Panel — World Chess Championship Game 2 (Geneva):** Defending champion D. Gukesh (White) and challenger Javokhir Sindarov drew Game 2 in just 20 moves by threefold repetition after Gukesh surprised with the London System (`3.Bf4`). The match is tied 1–1 ahead of Game 3 on Thursday with Sindarov playing White (FIDE / international sports wires, 25 November 2026).
- **Right Panel — Ukraine Strikes Samara Refineries (Samara · Oil War):** Ukrainian drones hit two Rosneft refineries in Russia's Samara region, about 800 km from the border, causing fires, one fatality, and power cuts — one day after President Putin vowed retaliation for refinery strikes (international wire coverage, 25 November 2026).
- **Briefs:** A gold mine flood in Bogor, Indonesia, left 9 dead with 17 still trapped; President Zelensky said Ukraine needs €115 billion in foreign aid for 2027 (wire dispatches, 25 November 2026).
- **Footer:** North Korea expelled Swiss diplomats and ordered the Swiss embassy shut within 48 hours (diplomatic wire reports, 25 November 2026).

## Verification

- **Format & Size:** `entry.png` is a 1024×1024 8-bit RGB PNG, `736601` bytes (under 1 MiB / 1,048,576 bytes).
- **SHA-256:** `d3d02200415422ed9cc568ea9d3cc03841a3719a230c16d85be2f131ee6ed4fb`
- **Reproducibility:** Both `compose.py` and `main.py` (verified across two independent `MAKEFUN_OUTPUT_DIR` temporary directories) produce byte-identical output with matching SHA-256 digests.
