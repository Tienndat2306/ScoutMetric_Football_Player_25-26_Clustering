from flask import Blueprint, render_template, request, jsonify
from clustering.football_player_clustering import Football_Player_Clustering
import pandas as pd

main = Blueprint('main', __name__)

POSITION_MAP = ["Midfielder", "Striker", "Defender", "Fullback", "Winger"]
LEAGUE_MAP = [
    "All League",
    "Top 5 League",
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Liga Portugal"
]
CRITERIA_MAP = ["Style", "Pressing", "Duel"]
ALGORITHM_MAP = ["K-Means", "DBSCAN", "GMM"]
OPTIMAL_K_MAP = ["Manual", "Elbow", "Silhouette Score", "Davies-Bouldin", "Hybrid"]

@main.route('/api/get_params')
def get_params():
    positions = POSITION_MAP
    leagues = LEAGUE_MAP
    criteria = CRITERIA_MAP
    algorithms = ALGORITHM_MAP
    k_methods = OPTIMAL_K_MAP

    return jsonify({
        "positions": positions,
        "leagues": leagues,
        "criteria": criteria,
        "algorithms": algorithms,
        "k_methods": k_methods
    })

@main.route('/get_criteria_options/<position>')
def get_criteria_options(position):
    criteria_map = {
        "Midfielder": ["Style", "Pressing", "Duel"],
        "Striker": ["Style"],
        "Defender": ["Style", "Duel"],
        "Fullback": ["Style"],
        "Winger": ["Pressing"]
    }
    
    normalized_position = next(
        (key for key in criteria_map if key.lower() == position.lower()),
        position
    )
    options = criteria_map.get(normalized_position, [])
    return jsonify(options)

@main.route('/api/load_raw_data', methods=['POST'])
def load_raw_data():
    try:
        params = request.get_json()
        
        model = Football_Player_Clustering(
            position=params.get('position'),
            league=params.get('league'),
            criteria=params.get('criteria')
        )
        
        df_league, scaled_data, features_df = model.prepare_data()
        
        if features_df is not None and not features_df.empty:
            result = features_df.rename(columns={'Name': 'Player'}).to_dict(orient='records')
            
            return jsonify({
                "status": "success",
                "data": result,
                "description": f"{params.get('position')} data in {params.get('league')} based on {params.get('criteria')}"
            })
        
        return jsonify({"status": "error", "message": "No matching data found"}), 404

    except Exception as e:
        print(f"Backend error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@main.route('/api/cluster', methods=['POST'])
def cluster():
    try:
        params = request.get_json() or {}
        algorithm = params.get('algorithm')
        k_method = params.get('k_method') or "Silhouette Score"
        manual_k = params.get('k')

        model = Football_Player_Clustering(
            position=params.get('position'),
            league=params.get('league'),
            criteria=params.get('criteria')
        )

        if algorithm == "K-Means":
            result_df, cluster_count = model.run_kmeans_clustering(
                k_method=k_method,
                manual_k=manual_k
            )
        elif algorithm == "DBSCAN":
            result_df, cluster_count = model.run_dbscan_clustering()
        elif algorithm == "GMM":
            gmm_k_method = "Manual" if k_method == "Manual" else "BIC"
            result_df, cluster_count = model.run_gmm_clustering(
                k_method=gmm_k_method,
                manual_k=manual_k
            )
        else:
            return jsonify({
                "status": "error",
                "message": f"Unsupported algorithm: {algorithm}"
            }), 400

        if result_df is None or result_df.empty:
            return jsonify({
                "status": "error",
                "message": "No matching data found for clustering"
            }), 404

        feature_cols = [
            col for col in model.selected_criteria(model.selected_league()).columns
            if col != 'Name'
        ]
        numeric_stat_cols = [
            col for col in result_df.columns
            if col not in ['id', 'Name', 'Team', 'League', 'Primary Position', 'Cluster', 'Cluster_Confidence']
            and pd.api.types.is_numeric_dtype(result_df[col])
        ]
        metric_cols = list(dict.fromkeys(feature_cols + numeric_stat_cols))
        optional_cols = ['Cluster_Confidence']
        response_cols = ['Name', 'Team', 'League', 'Primary Position', 'Cluster'] + metric_cols + optional_cols
        response_cols = [col for col in response_cols if col in result_df.columns]
        result = result_df[response_cols].rename(columns={'Name': 'Player'}).to_dict(orient='records')
        component_cols = [
            col for col in model.selected_component_columns()
            if col in result_df.columns
        ]
        cluster_components = []
        for cluster_id, cluster_df in result_df.groupby('Cluster'):
            averages = {}
            for col in component_cols:
                numeric_col = pd.to_numeric(cluster_df[col], errors='coerce')
                averages[col] = float(numeric_col.mean()) if not numeric_col.empty else 0

            cluster_components.append({
                "cluster": int(cluster_id),
                "count": int(len(cluster_df)),
                "averages": averages
            })

        return jsonify({
            "status": "success",
            "data": result,
            "selected_features": feature_cols,
            "component_features": component_cols,
            "cluster_components": cluster_components,
            "evaluation": result_df.attrs.get('evaluation'),
            "cluster_count": int(cluster_count),
            "min_minutes_threshold": model.get_min_minutes_threshold(),
            "description": f"{algorithm} for {params.get('position')} in {params.get('league')} based on {params.get('criteria')}"
        })

    except Exception as e:
        print(f"Backend cluster error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@main.route('/api/k_evaluation', methods=['POST'])
def k_evaluation():
    try:
        params = request.get_json() or {}
        model = Football_Player_Clustering(
            position=params.get('position'),
            league=params.get('league'),
            criteria=params.get('criteria')
        )

        k_method = params.get('k_method') or "Silhouette Score"
        gmm_method = "Manual" if k_method == "Manual" else "BIC"
        chart_data = model.get_k_evaluation_data(gmm_method=gmm_method)
        if not chart_data:
            return jsonify({
                "status": "error",
                "message": "Not enough data to calculate Elbow and Silhouette Score"
            }), 404

        return jsonify({
            "status": "success",
            "data": chart_data,
            "description": f"K evaluation for {params.get('position')} in {params.get('league')} based on {params.get('criteria')}"
        })

    except Exception as e:
        print(f"Backend k evaluation error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/compare')
def compare():
    return render_template('compare.html')
