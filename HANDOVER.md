# Tai Lieu Ban Giao Du An: Football Player Clustering (ScoutMetric Pro)

## 1. Tong Quan & Cong Nghe Su Dung

Du an la mot he thong phan tich va phan cum cau thu bong da, ten giao dien la **ScoutMetric Pro**. Muc dich chinh la lay du lieu thong ke cau thu tu FotMob, chuan hoa du lieu theo vi tri thi dau, sau do cho phep nguoi dung chon vi tri, giai dau, tieu chi va thuat toan de phan nhom cau thu theo phong cach/hieu suat.

Cong nghe chinh:

| Nhom | Cong nghe / thu vien | Ghi chu |
|---|---|---|
| Backend web | Flask | Dung Blueprint, route API JSON va render template |
| Data processing | pandas, numpy | Doc/ghi CSV, xu ly bang du lieu, tinh feature |
| Machine Learning | scikit-learn | KMeans, DBSCAN, AgglomerativeClustering, GaussianMixture, RobustScaler, metrics |
| Chon so cum K | kneed | `KneeLocator` cho Elbow method |
| Crawling | Selenium, BeautifulSoup4, webdriver-manager | Crawl FotMob: doi, cau thu, thong ke per 90 |
| Visualization backend/test | matplotlib, scipy | Chu yeu dung trong script test/visualization offline |
| Frontend | Jinja2 templates, vanilla JavaScript, Tailwind CDN, Chart.js, Material Symbols | Dashboard web tuong tac |
| Database | Khong co DBMS | Du lieu luu bang CSV trong `data/` |

Luu y: `requirements.txt` va `README.md` dang rong, nen khong co phien ban dependency chinh thuc de ban giao.

## 2. Cau Truc Thu Muc

```text
Football_Player_Clustering/
|-- app.py
|-- requirements.txt
|-- README.md
|-- HANDOVER.md
|-- app/
|   |-- __init__.py
|   |-- routes.py
|   |-- templates/
|   |   |-- base.html
|   |   |-- index.html
|   |   |-- chart.html
|   |   |-- code.html
|   |   `-- DESIGN.md
|   `-- static/
|       |-- js/main.js
|       `-- css/style.css
|-- clustering/
|   |-- football_player_clustering.py
|   `-- optimal_k.py
|-- crawler/
|   |-- fotmob_crawl.py
|   |-- get_teams.py
|   |-- get_players.py
|   |-- get_stats.py
|   `-- crawl_by_position.py
|-- data_preprocessing/
|   |-- clean_invalid_players.py
|   `-- process_percentage_value.py
|-- data/
|   |-- player_stats/
|   |-- player_stats_clean/
|   |-- player_stats_test/
|   `-- <league folders>/*_player_ids.csv
|-- backup_data/
`-- test/
    |-- test_kmeans.py
    |-- test_dbscan.py
    `-- test_hierarchical.py
```

Chuc nang thu muc lon:

| Thu muc | Vai tro |
|---|---|
| `app/` | Flask app, route API, template dashboard va static frontend |
| `clustering/` | Logic chon du lieu, tao feature, scale du lieu va chay thuat toan clustering |
| `crawler/` | Script Selenium crawl du lieu FotMob theo league/team/player |
| `data_preprocessing/` | Script lam sach CSV va chuan hoa cot phan tram |
| `data/` | Nguon du lieu CSV chinh: danh sach doi, player IDs, thong ke cau thu theo vi tri |
| `backup_data/` | Ban sao du lieu thong ke theo vi tri |
| `test/` | Script kiem thu/thu nghiem truc quan, chua phai pytest test chuan |

## 3. Ban Do Chuc Nang File

| File | Chuc nang chinh | Ham/class quan trong |
|---|---|---|
| `app.py` | Entry point chay Flask server o port 5000 | `create_app()` |
| `app/__init__.py` | Factory tao Flask app, dang ky Blueprint | `create_app()` |
| `app/routes.py` | API chinh cho frontend: params, criteria, preview data, clustering, K evaluation | `get_params`, `get_criteria_options`, `load_raw_data`, `cluster`, `k_evaluation`, `index` |
| `clustering/football_player_clustering.py` | Loi nghiep vu clustering cau thu | `Football_Player_Clustering`, `prepare_data`, `selected_position`, `selected_league`, `selected_criteria`, `run_kmeans_clustering`, `run_dbscan_clustering`, `run_hierarchical_clustering`, `run_gmm_clustering` |
| `clustering/optimal_k.py` | Tinh K toi uu bang Elbow, Silhouette, Davies-Bouldin | `get_elbow`, `get_silhouette_scores`, `get_db_index` |
| `app/static/js/main.js` | Dieu khien UI, goi API, render Chart.js scatter/line/radar/heatmap | `init`, `loadPreviewData`, `runClustering`, `renderChart`, `renderMetricChart`, `renderClusterSummary`, `renderClusterRadarChart`, `renderClusterHeatmap` |
| `app/templates/base.html` | Layout HTML nen, import Tailwind CDN, Chart.js, Google fonts/icons | Jinja blocks: `title`, `content`, `extra_css`, `extra_js` |
| `app/templates/index.html` | Trang dashboard chinh: form chon tham so va include chart | Jinja extends/includes |
| `app/templates/chart.html` | Layout vung bieu do scatter, Elbow/Silhouette, summary, radar, heatmap | Canvas IDs cho Chart.js |
| `app/templates/code.html` | Mockup HTML tinh, hien chua duoc route su dung | Khong co logic runtime |
| `crawler/fotmob_crawl.py` | Script tong hop crawl league/team roi luu player IDs | main script, goi `get_team_ids_from_leagues`, `get_player_ids_from_team` |
| `crawler/get_teams.py` | Crawl danh sach doi tu trang league FotMob | `get_team_ids_from_leagues` |
| `crawler/get_players.py` | Crawl danh sach cau thu trong squad cua mot doi | `get_player_ids_from_team` |
| `crawler/get_stats.py` | Crawl thong ke Per 90 cua mot cau thu | `get_player_stats_per90` |
| `crawler/crawl_by_position.py` | Crawl stats roi phan loai vao CSV theo nhom vi tri | `POSITION_SCHEMAS`, `crawl_and_save_by_position` |
| `data_preprocessing/process_percentage_value.py` | Chuan hoa cac cot `%` thanh so thap phan | `process_percentage_columns` |
| `data_preprocessing/clean_invalid_players.py` | Verify lai league thuc te tren FotMob va xuat du lieu sach | `verify_league`, `clean_invalid_players` |
| `test/test_*.py` | Script thu nghiem thuat toan va ve bieu do bang matplotlib | `run_system_test`, `run_dbscan_test`, `run_hierarchical_test` |

## 4. Luong Hoat Dong Chinh

Luong chay web:

```text
app.py
  -> app.create_app()
  -> dang ky Blueprint app.routes.main
  -> GET /
  -> render app/templates/index.html
  -> base.html load app/static/js/main.js
  -> JS goi /api/get_params
  -> JS goi /get_criteria_options/<position>
  -> JS goi /api/load_raw_data hoac /api/cluster
  -> routes.py tao Football_Player_Clustering
  -> selected_position doc data/player_stats/<position>_stats.csv
  -> selected_league loc league
  -> prepare_data loc Minutes played >= 50% max minutes cua league
  -> selected_criteria tao feature 2 truc
  -> RobustScaler chuan hoa du lieu
  -> KMeans / DBSCAN / GMM chay clustering
  -> routes.py tra JSON
  -> main.js render Chart.js scatter, line chart, radar, heatmap
```

Luong crawl du lieu offline:

```text
crawler/fotmob_crawl.py
  -> get_teams.py crawl team IDs theo league
  -> get_players.py crawl player IDs theo team
  -> luu data/<league>/<team>_player_ids.csv

crawler/crawl_by_position.py
  -> doc player IDs theo league
  -> get_stats.py crawl stats Per 90 tung player
  -> map vi tri sang goalkeeper/defender/fullback/midfielder/winger/striker
  -> luu data/player_stats/<position>_stats.csv

data_preprocessing/
  -> clean_invalid_players.py loc player khong thuoc Top 5 league
  -> process_percentage_value.py chuan hoa cot phan tram
```

## 5. Danh Gia Hien Trang & Next Steps

Da tuong doi hoan thien:

- Web dashboard Flask co the render giao dien va goi API phan cum.
- Logic clustering chinh da co KMeans, DBSCAN, GMM; Hierarchical co trong class nhung chua expose ra UI/API.
- Du lieu CSV chinh trong `data/player_stats/` da co cho 6 nhom vi tri.
- Frontend da render scatter chart, Elbow/Silhouette chart, cluster summary, radar chart, heatmap.
- Pipeline crawl FotMob da co cac script rieng cho league, team, player va stats.

Con dang do hoac rui ro:

- `requirements.txt` rong, khong the tai lap moi truong.
- `README.md` rong, chua co huong dan setup/chay/crawl/test.
- `pytest` khong duoc cai trong moi truong hien tai; cac file `test/` la script demo co `plt.show()`, chua phai test tu dong co assertion.
- Text/comment tieng Viet trong nhieu file dang bi loi encoding hien thi.
- `LEAGUE_MAP` frontend co `"Top 5 League"` nhung khong co `"All League"`, trong khi backend ho tro `"All League"`.
- `CRITERIA_MAP` khai bao nhieu tieu chi nhu `Finishing`, `Build-up`, `Defending` nhung backend route criteria thuc te chi tra `Style`/`Pressing` tuy vi tri.
- `style.css` ton tai nhung `base.html` khong include.
- `code.html` la mockup tinh, co ve khong tham gia runtime.
- API `/api/cluster` khong expose Hierarchical du class da co `run_hierarchical_clustering`.
- DBSCAN dang hard-code `eps=0.5`, `min_samples=5`, frontend chua cho chinh tham so.

Next steps de xuat:

1. Hoan thien reproducibility: dien `requirements.txt` hoac `pyproject.toml`, them README setup/run/crawl/test, chuan hoa encoding UTF-8.
2. Chuan hoa domain config: gom `POSITION_MAP`, `LEAGUE_MAP`, `CRITERIA_MAP`, feature formulas vao mot module cau hinh dung chung cho frontend/API/clustering.
3. Bien test demo thanh test tu dong: them pytest fixtures voi CSV nho, assertion cho `prepare_data`, chon K, KMeans/DBSCAN/GMM, route API.
4. Cai thien API clustering: expose Hierarchical neu can, them validation input, validate `manual_k`, tra loi ro khi criteria khong hop le.
5. Tach pipeline du lieu: phan biet raw/clean/test/backup bang config path, them command/script chuan cho crawl, clean, normalize, tranh ghi de CSV ngoai y muon.
