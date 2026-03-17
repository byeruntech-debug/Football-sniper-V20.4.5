# Football Sniper — Changelog

## V20.4.5
- Fix Ukraine threshold: auto-select ambil thr=0.50 salah → manual fix thr=0.58 (n=51, acc=72.5%)
- Ukraine status: WATCHLIST → ACTIVE
 (2026-03-17)
- Ukraine (Premier Liga) ditambahkan dari games.csv
  - 2,502 matches | 14 seasons (2012-2025)
  - thr=0.5 | acc=60.9% | n=92 | 🟡 WATCHLIST
  - Teams: 26 | H2H: +265 pairs

## V20.4.4 (2026-03-17)
- Russia + Denmark ditambahkan dari games.csv (Transfermarkt 2012–2025)
  - Russia: thr=0.6 | acc=92.3% | n=39
  - Denmark: thr=0.57 | acc=87.9% | n=33
- Total liga: 16 aktif + 0 watchlist

## V20.4.3 (2026-03-17)
- Fix DC optimizer EPL: L-BFGS-B(maxiter=3000) + Nelder-Mead polish
  - ok=False → ok=True
  - HFA: 0.1331 → 0.1331
  - Rho: -0.0040 → -0.0040
  - LL improvement: 0.0000

## V20.4.2 (2026-03-17)
- EV analysis Brazil: thr=0.72 | ROI=+3.1% | n=40 | src=AvgCH odds

## V20.4.1 (2026-03-17)
- Bugfix Brazil: name mapping Atlético ambigu diperbaiki
  - 'Atltico' sebelumnya di-map ke satu nama saja
  - Fix: /MG → Atlético-MG | /PR → Athletico-PR | /GO → Atlético-GO
  - Impact: 30→30 teams, DC retrain ulang
  - Data 2024-2025: 3 tim Atlético aktif di Série A

## V20.4.0 (2026-03-17)
- Retrain 4 liga dari games.csv (Transfermarkt, 78,414 matches, 2012–2025)
  - Liga_Portugal: thr 0.59→0.68 | 21→26 teams | HFA=0.206
  - Belgium      : thr 0.65→0.64 | 21→22 teams | HFA=0.210
  - Scotland     : thr 0.66→0.68 | 13→14 teams | HFA=0.287
  - Greece       : thr 0.65→0.68 | 19→19 teams | HFA=0.230
- Semua 4 liga data 2012–2025 (paling fresh sejauh ini)
- H2H: +751 pasang baru (total mencapai 3810 pasang)

## V20.3.9 (2026-03-17)
- Brazil (Série A) update dengan data 2024–2025
  - Source: matches-2003-2025.txt (9,165 matches total)
  - Ditambah: 760 matches baru (2024: 380, 2025: 380)
  - DC fitting: 2019–2025 (2,660 matches), 30 tim
  - HFA Brazil: 0.348 (tertinggi semua liga — home advantage sangat kuat)
  - Threshold: 0.57 → 0.57 (tidak berubah, sudah robust)
  - Teams: 29 → 30 (Mirassol, tim baru promosi 2024)
  - Name mapping: 8 tim (Atlético, Grêmio, São Paulo, dll)
  - H2H: +43 pasang baru (total 3,059)

## V20.3.8 (2026-03-17)
- EPL retrain dengan PremierLeague.csv (12,160 matches, 1993–2025)
  - DC fitting: 2015-2025 (10 musim, 3,800 matches)
  - Elo walk-forward: dari 2000-2001
  - Threshold: 0.68 → 0.73
  - Draw warning: 0.243 → 0.206
  - Teams: 34 tim aktif di EPL

- Injury Warning System V20.6
  - Upgrade dari V20.5: tambah injury_type severity lookup
  - Data: player_injuries.csv (143,195 records, Transfermarkt)
  - 232 injury types terkategorisasi
  - Severity: CRITICAL/MAJOR/MODERATE/MINOR berdasarkan avg days missed
  - Backward compatible dengan format input V20.5

## V20.3.7 (2026-03-17)
- Brasil (Serie A) ditambahkan sebagai liga ke-13 ✅ ACTIVE
  - Data: jogos_brasileirao_af.csv (8,405 matches, 2003–2023)
  - DC fitting: 2,280 matches (2018–2023), 29 tim
  - WF Accuracy: 73.9% (88 picks, threshold=0.57)
  - Draw warning: 0.229 | HFA=0.299 (tertinggi semua liga)
  - Top teams: Palmeiras, Atlético-MG, Internacional, Grêmio, Flamengo

- Venezuela (Liga FUTVE) ditambahkan sebagai liga ke-14 ✅ ACTIVE
  - Data: futve_consolidate + 2024 + 2025 (7,017 matches, 2002–2025)
  - DC fitting: 2,312 matches (2019–2025), 27 tim
  - WF Accuracy: 75.4% (130 picks, threshold=0.56)
  - Draw warning: 0.267 | Data terfresh (sampai Desember 2025)
  - Top teams: Carabobo, La Guaira, Dep. Táchira, Puerto Cabello

- H2H: +669 pasang baru (total 2,755 pasang)
- Total liga aktif: 14 | Total tim: 324

## V20.3.6 (2026-03-17)
- J1 League (Japan) ditambahkan sebagai liga ke-12 ✅ ACTIVE
- Data: results.csv (3,213 matches, 2012–2022), 28 tim
- Fitting DC: 1,371 matches (5 musim terakhir 2018–2022)
- Elo: walk-forward dari 2012, 28 tim terkalibrasi
- WF Accuracy J1: 76.1% (71 picks, threshold=0.55)
- Draw warning J1: 0.272
- H2H: +337 pasang baru (total 1,939 → 2,276 pasang)
- Sumber data: Statsbomb J1 League (results.csv + event data)

## V20.3.5 (2026-03-17)
- Greece ditambahkan sebagai liga ke-11 (79.2% WF, n=24, dom=21%)
- Data dari games.csv (78,414 laga, 2012-2025) — lebih lengkap dari football-data.co.uk
- Draw warning dikoreksi 0.162 → 0.221
- EPL diagnosis: max conf 2024-25 = 0.617, threshold 0.68 tidak pernah tercapai
- PremierLeague.csv: 12,160 laga + B365 odds 1993-2025 tersimpan

## V20.3.4 (2026-03-17)
- Brazil ditambahkan sebagai watchlist (75% WF, n=12, 2 musim data)
- Segunda (Serie B Spain) DITOLAK — outlier 1 tim
- Ligue 2 DITOLAK — Lorient outlier 57% picks
- Germany2 DITOLAK — n=2, 50%

## V20.3.3 (2026-03-17)
- Belgium Pro League ditambahkan: 78.6% WF (28 picks, 1236 laga)
- Scotland Premiership ditambahkan: 79.2% WF (53 picks, 912 laga)
- Greece DITOLAK: 68.3% < 70% (dari football-data.co.uk, data kurang)
- 10 liga aktif
- Streamlit UI + GitHub Pages static HTML deployed

## V20.3.2 (2026-03-17)
- Ligue 1 ditambahkan sebagai liga ke-8
- DC fitting: 1,372 laga (4 musim 2021-2025)
- WF accuracy Ligue 1: 82.9% (35 picks)
- Draw warning: 0.270

## V20.3.1 (2026-03-15)
- Threshold optimization: Eredivisie 0.56→0.59, Serie A 0.66→0.68
- Draw warning 8 liga diperbarui (90% avg_miss_dprob)
- calculate_kelly() passive shadow mode
- EV filter wajib EPL/La Liga
- Bootstrap CI: [75.3%, 86.1%], p=4.27e-19

## V20.3 (2026-03-15)
- Walk-forward accuracy: 81.4% (194 SNIPER picks)
- DC 55% + Elo 45% ensemble
- 7 liga aktif: EPL, Bundesliga, Serie A, La Liga, Eredivisie, Liga PT, Super Lig
- Time leakage V20 dicabut (87.5% → 72.5% cold WF → 81.4% warm WF)
