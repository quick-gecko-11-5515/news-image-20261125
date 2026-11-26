[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/quick-gecko-11-5515/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/quick-gecko-11-5515/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

# The World Today — 25 November 2026

This repository is an entry for the make.fun competition **Sum up 25 November's world news in one image** (`news-image-20261125`). It presents Wednesday 25 November 2026's world headlines as a 1024×1024 editorial broadsheet front page (`entry.png`), composed deterministically with Pillow by `compose.py` from original editorial photography in `assets/` with validated typography and gradient scrims. Running `main.py` (Python 3.13, standard library only) copies `entry.png` to `$MAKEFUN_OUTPUT_DIR/entry.png` (defaulting to `/output/entry.png`) with byte-identical output across repeated runs.

## Stories & News Sources

- **Hero — Ukraine Strikes Samara Refineries:** Ukrainian long-range drones struck two Rosneft oil refineries in Russia's Samara region, roughly 800 km from the border, sparking fires, killing one person, and causing power cuts — one day after President Vladimir Putin vowed retaliation for strikes on Russian refineries (international wire coverage, 25 November 2026).
- **World Chess Championship — Geneva (Game 2):** Defending champion D. Gukesh (White) and challenger Javokhir Sindarov drew Game 2 in just 20 moves by threefold repetition after Gukesh surprised with the London System (`3.Bf4`). The match is tied 1–1 ahead of Game 3 on Thursday with Sindarov playing White (FIDE / international sports wires, 25 November 2026).
- **China Launches Shenzhou-24 — Tiangong Space Station:** China launched the crewed Shenzhou-24 mission to the Tiangong space station carrying three astronauts, including the first Pakistani astronaut — the first foreign astronaut to fly aboard China's space programme (CMSA / international press, 25 November 2026).
- **Briefs:** A flood at a gold mine in Bogor, Indonesia, left 9 dead with 17 people still trapped; Ukrainian President Volodymyr Zelensky stated Ukraine needs €115 billion in foreign aid for 2027 (wire dispatches, 25 November 2026).
- **Footer:** North Korea expelled Swiss diplomats and ordered the Swiss embassy in Pyongyang shut within 48 hours (diplomatic wire reports, 25 November 2026).

## Verification

- **Format & Size:** `entry.png` is a 1024×1024 8-bit RGB PNG, `855755` bytes (under 1 MiB / 1,048,576 bytes).
- **SHA-256:** `2be43acaf820baba3de718b1a04ffeb1cc2310e551bb329626213c5e38cf3b34`
- **Reproducibility:** Both `compose.py` and `main.py` (verified across two independent `MAKEFUN_OUTPUT_DIR` temporary directories) produce byte-identical outputs with matching SHA-256 digests.
