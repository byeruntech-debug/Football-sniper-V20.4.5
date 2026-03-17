# Referensi Training Liga — Football Sniper V20.4.5

| # | Liga | Fit Seasons | Data Range | Teams | Thr | Comp ID | Update Cara |
|---|------|------------|-----------|-------|-----|---------|-------------|
| 1 | Bundesliga | 2020–2025 | 2012–2025 | 21 | 0.66 | L1 | games.csv baru |
| 2 | EPL | 2015–2025 | 1993–2025 | 34 | 0.65 | GB1 | PremierLeague.csv |
| 3 | Serie_A | 2020–2025 | 2012–2025 | 25 | 0.68 | IT1 | games.csv baru |
| 4 | Eredivisie | 2020–2025 | 2012–2025 | 22 | 0.59 | NL1 | games.csv baru |
| 5 | La_Liga | 2020–2025 | 2012–2025 | 26 | 0.58 | ES1 | games.csv baru |
| 6 | Liga_Portugal | 2021–2025 | 2012–2025 | 26 | 0.68 | PO1 | games.csv baru |
| 7 | Super_Lig | 2020–2025 | 2012–2025 | 23 | 0.65 | TR1 | games.csv baru |
| 8 | Ligue_1 | 2020–2025 | 2012–2025 | 24 | 0.63 | FR1 | games.csv baru |
| 9 | Belgium | 2021–2025 | 2012–2025 | 22 | 0.64 | BE1 | games.csv baru |
| 10 | Scotland | 2021–2025 | 2012–2025 | 14 | 0.68 | SC1 | games.csv baru |
| 11 | Greece | 2021–2025 | 2012–2025 | 19 | 0.68 | GR1 | games.csv baru |
| 12 | J1_League | 2018–2022 ⚠ | 2012–2022 | 28 | 0.55 | — | CARI DATA 2023-2025 |
| 13 | Brazil | 2019–2025 | 2003–2025 | 30 | 0.54 | — | matches-20XX.txt |
| 14 | Venezuela | 2019–2025 | 2002–2025 | 27 | 0.56 | — | futve_20XX_results.csv |
| 15 | Russia | 2021–2025 | 2012–2025 | 22 | 0.55 | RU1 | games.csv baru |
| 16 | Denmark | 2021–2025 | 2012–2025 | 16 | 0.55 | DK1 | games.csv baru |
| 17 | Ukraine | 2021–2025 | 2012–2025 | 26 | 0.58 | UKR1 | games.csv baru |

## Cara Update 14 Liga games.csv
1. Download games.csv terbaru dari Transfermarkt/Kaggle
2. Filter: `competition_id == [comp_id]` dan `competition_type == domestic_league`
3. Fit window: ambil 5 musim terakhir
4. Elo walk-forward dari 2012 (semua data)
5. WF scan: pilih threshold robust (n≥30, acc≥70%)

## Cara Update Liga Khusus
- EPL: update PremierLeague.csv — fit dari 2015
- Brazil: tambah baris baru ke matches-20XX-20XX.txt
- Venezuela: download futve_20XX_results.csv tiap akhir musim
- J1 ⚠: cari source data 2022–2025 sebelum retrain

## Catatan Penting
- Fit window = 5 musim terakhir (bisa diubah di kode)
- Elo selalu walk-forward dari data tertua
- Threshold robust = n≥30 dari WF scan
- Jangan pakai threshold dengan n<30 (overfitting)
- Brazil: 3 tim Atlético berbeda — MG, PR, GO
