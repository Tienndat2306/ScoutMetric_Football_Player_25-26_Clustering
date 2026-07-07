from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
import os
import numpy as np
import pandas as pd
from clustering.optimal_k import get_elbow, get_silhouette_scores, get_db_index, get_hybrid_k
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

class Football_Player_Clustering:
    TOP_5_LEAGUES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]

    def __init__(self, position, league ,criteria):
        self.position = position
        self.league = league
        self.criteria = criteria

        self.data = self.selected_position()

        # Cấu hình các bộ chỉ số theo tiêu chí cho từng vị trí
        # Đây là nơi định nghĩa các công thức gom cụm
        self.criteria_map = {
            "Midfielder": {
                "Style": ["Non-penalty xG", "Expected assists (xA)", "Tackles", "Interceptions", "Recoveries", "Duels won"],
                "Pressing": ["Possession won final 3rd", "Recoveries"],
                "Duel": ["Aerial duels won", "Duels won"]
            },
            "Striker": {
                "Style": ["Non-penalty xG", "Shots", "Touches", "Chances created"]
            },
            "Defender": {
                "Style": ["Tackles", "Blocked shots", "Interceptions", "Clearances", "Aerial duels won", "Touches", "Successful passes", "Accurate long balls"],
                "Duel": ["Aerial duels won", "Duels won"]
            },
            "Fullback":{
                "Style": ["Non-penalty xG", "Expected assists (xA)", "Tackles", "Interceptions", "Recoveries", "Duels won"]
            },
            "Winger":{
                "Pressing": ["Possession won final 3rd", "Recoveries"]
            }
        }

    def selected_position(self):
        # Chuyển đổi tên vị trí thành tên file (ví dụ: Midfielder -> midfielder_stats.csv)
        file_name = f"{self.position.lower()}_stats.csv"
        file_path = os.path.join('data', 'player_stats', file_name)
        
        try:
            return pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file {file_path}")
            return pd.DataFrame()

    def selected_league(self):
        if self.league == "All League":
            return self.data.copy()
        if self.league == "Top 5 League":
            return self.data[self.data['League'].isin(self.TOP_5_LEAGUES)].copy()
        return self.data[self.data['League'] == self.league].copy()

    def get_min_minutes_threshold(self):
        df_league = self.selected_league()
        if df_league.empty or 'Minutes played' not in df_league.columns:
            return None

        minutes_played = pd.to_numeric(df_league['Minutes played'], errors='coerce')
        max_minutes = minutes_played.max()
        if pd.isna(max_minutes) or max_minutes <= 0:
            return None

        return float(max_minutes / 2)
    
    def selected_criteria(self, filtered_df):
        if self.criteria == "Style" and (self.position == "Midfielder" or self.position == "Fullback"):
            filtered_df['Expected Output'] = filtered_df['Non-penalty xG'] + filtered_df['Expected assists (xA)']
            filtered_df['Ball Winning Actions'] = filtered_df['Tackles'] + filtered_df['Interceptions'] + filtered_df['Recoveries'] + filtered_df['Duels won']
            return filtered_df[['Name', 'Expected Output', 'Ball Winning Actions']]
        elif self.criteria == "Style" and self.position == "Striker":
            filtered_df['Finishing'] = filtered_df['Non-penalty xG'] + filtered_df['Shots']
            filtered_df['Build-up'] = filtered_df['Touches'] + filtered_df['Chances created']
            return filtered_df[['Name', 'Finishing', 'Build-up']]
        elif self.criteria == "Style" and self.position == "Defender":
            filtered_df['Defending'] = filtered_df['Tackles'] + filtered_df['Blocked shots'] + filtered_df['Interceptions'] + filtered_df['Duels won']
            filtered_df['Build-up'] = filtered_df['Touches'] + filtered_df['Successful passes'] + filtered_df['Accurate long balls']
            return filtered_df[['Name', 'Defending', 'Build-up']]
        elif self.criteria == "Pressing":
            filtered_df['Possession won final 3rd'] = filtered_df['Possession won final 3rd']
            filtered_df['Recoveries'] = filtered_df['Recoveries']
            return filtered_df[['Name', 'Possession won final 3rd', 'Recoveries']]
        elif self.criteria == "Duel" and (self.position == "Defender" or self.position == "Midfielder"):
            filtered_df['Aerial duels won'] = filtered_df['Aerial duels won']
            filtered_df['Duels won'] = filtered_df['Duels won']
            return filtered_df[['Name', 'Aerial duels won', 'Duels won']]

    def selected_component_columns(self):
        if self.criteria == "Style" and (self.position == "Midfielder" or self.position == "Fullback"):
            return ["Non-penalty xG", "Expected assists (xA)", "Tackles", "Interceptions", "Recoveries", "Duels won"]
        elif self.criteria == "Style" and self.position == "Striker":
            return ["Non-penalty xG", "Shots", "Touches", "Chances created"]
        elif self.criteria == "Style" and self.position == "Defender":
            return ["Tackles", "Blocked shots", "Interceptions", "Duels won", "Touches", "Successful passes", "Accurate long balls"]
        elif self.criteria == "Pressing":
            return ["Possession won final 3rd", "Recoveries"]
        elif self.criteria == "Duel" and (self.position == "Defender" or self.position == "Midfielder"):
            return ["Aerial duels won", "Duels won"]
        return []
    
    def find_best_k(self, scaled_data, method="Silhouette Score", manual_k=None):
        """Kết hợp Elbow và Silhouette để tìm k tốt nhất"""
        if method == "Manual":
            return int(manual_k) if manual_k else 3
        try:
            if method == "Elbow":
                _, _, k_opt = get_elbow(scaled_data)
            elif method == "Davies-Bouldin":
                _, k_opt = get_db_index(scaled_data)
            elif method == "Hybrid":
                k_opt = get_hybrid_k(scaled_data)["optimal_k"]
            else: 
                _, k_opt = get_silhouette_scores(scaled_data)
            return k_opt
        except Exception as e:
            print(f"Lỗi khi tính toán k: {e}")
            return 3 
    
    def prepare_data(self):
        """Phương thức hỗ trợ để chuẩn bị dữ liệu chuẩn hóa dùng chung cho các thuật toán"""
        # 1. Lọc giải đấu
        df_league = self.selected_league()
        if df_league.empty:
            return None, None, None

        min_minutes = self.get_min_minutes_threshold()
        if min_minutes is not None:
            minutes_played = pd.to_numeric(df_league['Minutes played'], errors='coerce')
            df_league = df_league[minutes_played >= min_minutes].copy()

        if df_league.empty:
            return None, None, None

        # 2. Lấy tiêu chí
        features_df = self.selected_criteria(df_league)
        if features_df is None or features_df.empty:
            return None, None, None

        train_data = features_df.drop(columns=['Name']) if 'Name' in features_df.columns else features_df
        
        # 3. Chuẩn hóa dữ liệu
        # scaler = StandardScaler()
        scaler = RobustScaler()
        scaled_data = scaler.fit_transform(train_data)
        
        return df_league, scaled_data, features_df

    def find_best_gmm_k(self, scaled_data, method="BIC", manual_k=None):
        if method == "Manual":
            return int(manual_k) if manual_k else 3

        method = "BIC"

        k_values = list(range(2, min(11, len(scaled_data))))
        if not k_values:
            return 1

        scores = []
        for k in k_values:
            gmm = GaussianMixture(n_components=k, random_state=42)
            labels = gmm.fit_predict(scaled_data)

            if method == "Davies-Bouldin":
                scores.append(davies_bouldin_score(scaled_data, labels))
            elif method == "BIC":
                scores.append(gmm.bic(scaled_data))
            else:
                scores.append(silhouette_score(scaled_data, labels))

        if method in ["Davies-Bouldin", "BIC"]:
            return k_values[scores.index(min(scores))]

        return k_values[scores.index(max(scores))]

    def fit_best_gmm_model(self, scaled_data, method="BIC", manual_k=None):
        covariance_types = ["full", "tied", "diag", "spherical"]
        k_values = (
            [int(manual_k) if manual_k else 3]
            if method == "Manual"
            else list(range(2, min(11, len(scaled_data))))
        )
        if not k_values:
            k_values = [1]

        best = None
        candidates = []
        for k in k_values:
            for covariance_type in covariance_types:
                try:
                    gmm = GaussianMixture(
                        n_components=k,
                        covariance_type=covariance_type,
                        random_state=42
                    )
                    labels = gmm.fit_predict(scaled_data)
                    bic = float(gmm.bic(scaled_data))
                    aic = float(gmm.aic(scaled_data))
                    candidates.append({
                        "k": int(k),
                        "covariance_type": covariance_type,
                        "bic": bic,
                        "aic": aic
                    })
                    if best is None or bic < best["bic"]:
                        best = {
                            "model": gmm,
                            "labels": labels,
                            "k": int(k),
                            "covariance_type": covariance_type,
                            "bic": bic,
                            "aic": aic,
                            "init_params": gmm.init_params
                        }
                except Exception:
                    continue

        if best is None:
            fallback = GaussianMixture(n_components=1, random_state=42)
            labels = fallback.fit_predict(scaled_data)
            best = {
                "model": fallback,
                "labels": labels,
                "k": 1,
                "covariance_type": fallback.covariance_type,
                "bic": float(fallback.bic(scaled_data)),
                "aic": float(fallback.aic(scaled_data)),
                "init_params": fallback.init_params
            }

        best["candidates"] = candidates
        return best

    def get_gmm_evaluation_data(self, scaled_data, method="BIC"):
        method = "BIC"
        k_values = list(range(2, min(11, len(scaled_data))))
        if not k_values:
            return None

        scores = []
        covariance_types = []
        for k in k_values:
            best = None
            for covariance_type in ["full", "tied", "diag", "spherical"]:
                try:
                    gmm = GaussianMixture(
                        n_components=k,
                        covariance_type=covariance_type,
                        random_state=42
                    )
                    labels = gmm.fit_predict(scaled_data)

                    if method == "Davies-Bouldin":
                        score = float(davies_bouldin_score(scaled_data, labels))
                    elif method == "BIC":
                        score = float(gmm.bic(scaled_data))
                    else:
                        score = float(silhouette_score(scaled_data, labels))

                    if best is None or score < best["score"]:
                        best = {"score": score, "covariance_type": covariance_type}
                except Exception:
                    continue

            if best:
                scores.append(best["score"])
                covariance_types.append(best["covariance_type"])

        lower_is_better = method in ["Davies-Bouldin", "BIC"]
        optimal_k = (
            k_values[scores.index(min(scores))]
            if lower_is_better
            else k_values[scores.index(max(scores))]
        )
        metric_name = {
            "Davies-Bouldin": "Davies-Bouldin",
            "BIC": "BIC",
            "Silhouette Score": "Silhouette Score"
        }.get(method, "Silhouette Score")

        return {
            "k_values": k_values,
            "scores": scores,
            "optimal_k": int(optimal_k),
            "metric_name": metric_name,
            "lower_is_better": lower_is_better,
            "covariance_types": covariance_types
        }

    def get_k_evaluation_data(self, gmm_method="Silhouette Score"):
        _, scaled_data, _ = self.prepare_data()
        if scaled_data is None or len(scaled_data) < 3:
            return None

        elbow_k_values = list(range(1, min(9, len(scaled_data) + 1)))
        inertia_values = []
        for k in elbow_k_values:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(scaled_data)
            inertia_values.append(float(kmeans.inertia_))

        _, _, elbow_optimal_k = get_elbow(scaled_data)

        silhouette_k_values = list(range(2, min(11, len(scaled_data))))
        silhouette_values = []
        for k in silhouette_k_values:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(scaled_data)
            silhouette_values.append(float(silhouette_score(scaled_data, labels)))

        silhouette_optimal_k = (
            silhouette_k_values[silhouette_values.index(max(silhouette_values))]
            if silhouette_values else None
        )

        hybrid_data = get_hybrid_k(scaled_data)

        return {
            "elbow": {
                "k_values": elbow_k_values,
                "scores": inertia_values,
                "optimal_k": int(elbow_optimal_k) if elbow_optimal_k else None
            },
            "silhouette": {
                "k_values": silhouette_k_values,
                "scores": silhouette_values,
                "optimal_k": int(silhouette_optimal_k) if silhouette_optimal_k else None
            },
            "hybrid": {
                "elbow_k": hybrid_data["elbow_k"],
                "candidate_k_values": hybrid_data["candidate_k_values"],
                "silhouette_scores": hybrid_data["silhouette_scores"],
                "optimal_k": hybrid_data["optimal_k"],
                "description": "Elbow narrows the feasible K range, then Silhouette selects the best K within that range."
            },
            "gmm": self.get_gmm_evaluation_data(scaled_data, method=gmm_method)
        }

    def _safe_internal_metrics(self, scaled_data, labels, ignore_noise=False):
        metric_data = scaled_data
        metric_labels = np.asarray(labels)

        if ignore_noise:
            non_noise_mask = metric_labels != -1
            metric_data = scaled_data[non_noise_mask]
            metric_labels = metric_labels[non_noise_mask]

        unique_labels = set(metric_labels)
        if len(metric_data) < 3 or len(unique_labels) < 2 or len(unique_labels) >= len(metric_data):
            return {}

        metrics = {}
        try:
            metrics["silhouette"] = float(silhouette_score(metric_data, metric_labels))
        except Exception:
            pass

        try:
            metrics["davies_bouldin"] = float(davies_bouldin_score(metric_data, metric_labels))
        except Exception:
            pass

        try:
            metrics["calinski_harabasz"] = float(calinski_harabasz_score(metric_data, metric_labels))
        except Exception:
            pass

        return metrics

    def _percentile_score(self, value, reference_values, higher_is_better=True):
        valid_values = [
            float(item) for item in reference_values
            if item is not None and np.isfinite(float(item))
        ]
        if value is None or not np.isfinite(float(value)) or not valid_values:
            return None

        value = float(value)
        if higher_is_better:
            percentile = sum(item <= value for item in valid_values) / len(valid_values)
        else:
            percentile = sum(item >= value for item in valid_values) / len(valid_values)

        return round(percentile * 100, 1)

    def _metric_payload(self, key, label, value, reference_values, higher_is_better=True):
        if value is None:
            return None

        return {
            "key": key,
            "label": label,
            "value": float(value),
            "percentile": self._percentile_score(value, reference_values, higher_is_better),
            "higher_is_better": higher_is_better
        }

    def _reference_scores(self, scaled_data, algorithm):
        algorithm = (algorithm or "").lower()
        references = {
            "silhouette": [],
            "davies_bouldin": [],
            "calinski_harabasz": [],
            "inertia": [],
            "bic": [],
            "aic": [],
            "noise_ratio": []
        }

        k_values = list(range(2, min(11, len(scaled_data))))
        if algorithm != "dbscan":
            for k in k_values:
                try:
                    if algorithm == "gmm":
                        for covariance_type in ["full", "tied", "diag", "spherical"]:
                            model = GaussianMixture(
                                n_components=k,
                                covariance_type=covariance_type,
                                random_state=42
                            )
                            labels = model.fit_predict(scaled_data)
                            references["bic"].append(float(model.bic(scaled_data)))
                            references["aic"].append(float(model.aic(scaled_data)))
                            metrics = self._safe_internal_metrics(scaled_data, labels)
                            for metric_key, score in metrics.items():
                                references[metric_key].append(score)
                        continue
                    elif algorithm == "hierarchical":
                        model = AgglomerativeClustering(n_clusters=k, linkage='ward')
                        labels = model.fit_predict(scaled_data)
                    else:
                        model = KMeans(n_clusters=k, random_state=42, n_init=10)
                        labels = model.fit_predict(scaled_data)
                        references["inertia"].append(float(model.inertia_))

                    metrics = self._safe_internal_metrics(scaled_data, labels)
                    for metric_key, score in metrics.items():
                        references[metric_key].append(score)
                except Exception:
                    continue

        if algorithm == "dbscan":
            eps_values = [0.2, 0.3, 0.5, 0.8, 1.0, 1.3, 1.6, 2.0]
            min_samples_values = [3, 5, 8]
            for eps in eps_values:
                for min_samples in min_samples_values:
                    try:
                        labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(scaled_data)
                        noise_ratio = float(np.mean(np.asarray(labels) == -1))
                        references["noise_ratio"].append(noise_ratio)

                        metrics = self._safe_internal_metrics(scaled_data, labels, ignore_noise=True)
                        for metric_key, score in metrics.items():
                            references[metric_key].append(score)
                    except Exception:
                        continue

        return references

    def evaluate_clustering(self, scaled_data, labels, algorithm, fitted_model=None):
        labels = np.asarray(labels)
        unique_labels = set(labels)
        cluster_labels = [label for label in unique_labels if label != -1]
        cluster_sizes = {
            str(int(label)): int(np.sum(labels == label))
            for label in sorted(unique_labels)
        }
        noise_count = int(np.sum(labels == -1))
        noise_ratio = float(noise_count / len(labels)) if len(labels) else 0
        references = self._reference_scores(scaled_data, algorithm)
        metrics = self._safe_internal_metrics(
            scaled_data,
            labels,
            ignore_noise=(algorithm == "DBSCAN")
        )

        metric_items = []
        metric_items.append(self._metric_payload(
            "silhouette",
            "Silhouette Score",
            metrics.get("silhouette"),
            references["silhouette"],
            True
        ))
        metric_items.append(self._metric_payload(
            "davies_bouldin",
            "Davies-Bouldin Index",
            metrics.get("davies_bouldin"),
            references["davies_bouldin"],
            False
        ))
        metric_items.append(self._metric_payload(
            "calinski_harabasz",
            "Calinski-Harabasz Score",
            metrics.get("calinski_harabasz"),
            references["calinski_harabasz"],
            True
        ))

        if algorithm == "K-Means" and fitted_model is not None:
            metric_items.append(self._metric_payload(
                "inertia",
                "Inertia",
                getattr(fitted_model, "inertia_", None),
                references["inertia"],
                False
            ))

        if algorithm == "GMM" and fitted_model is not None:
            metric_items.append(self._metric_payload(
                "bic",
                "BIC",
                fitted_model.bic(scaled_data),
                references["bic"],
                False
            ))
            metric_items.append(self._metric_payload(
                "aic",
                "AIC",
                fitted_model.aic(scaled_data),
                references["aic"],
                False
            ))

        if algorithm == "DBSCAN":
            metric_items.append(self._metric_payload(
                "noise_ratio",
                "Noise Ratio",
                noise_ratio,
                references["noise_ratio"],
                False
            ))

        return {
            "algorithm": algorithm,
            "cluster_count": int(len(cluster_labels)),
            "noise_count": noise_count,
            "noise_ratio": noise_ratio,
            "cluster_sizes": cluster_sizes,
            "metrics": [item for item in metric_items if item is not None]
        }
    
    def attach_selected_features(self, df_league, features_df):
      feature_cols = [col for col in features_df.columns if col != 'Name']

      for col in feature_cols:
          df_league[col] = features_df[col].to_numpy()

      return df_league
    
    def run_kmeans_clustering(self, k_method="Silhouette Score", manual_k=None):
        df_league, scaled_data, features_df = self.prepare_data()
        if df_league is None: return None, None

        optimal_k = self.find_best_k(scaled_data, method=k_method, manual_k=manual_k)
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled_data)

        df_league['Cluster'] = clusters
        df_league = self.attach_selected_features(df_league, features_df)
        df_league.attrs['evaluation'] = self.evaluate_clustering(scaled_data, clusters, "K-Means", kmeans)

        return df_league, optimal_k

    def run_dbscan_clustering(self, eps=0.5, min_samples=5):
        """
        Thực hiện gom cụm bằng DBSCAN.
        """
        df_league, scaled_data, features_df = self.prepare_data()
        if df_league is None: return None, None

        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(scaled_data)

        df_league['Cluster'] = clusters
        
        df_league = self.attach_selected_features(df_league, features_df)

        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        df_league.attrs['evaluation'] = self.evaluate_clustering(scaled_data, clusters, "DBSCAN", dbscan)
        return df_league, n_clusters

    def run_gmm_clustering(self, k_method="BIC", manual_k=None):
        """
        Thực hiện gom cụm bằng Gaussian Mixture Model.
        """
        df_league, scaled_data, features_df = self.prepare_data()
        if df_league is None: return None, None

        best_gmm = self.fit_best_gmm_model(scaled_data, method=k_method, manual_k=manual_k)
        optimal_k = best_gmm["k"]
        gmm = best_gmm["model"]
        clusters = best_gmm["labels"]
        probabilities = gmm.predict_proba(scaled_data)
        confidence = probabilities.max(axis=1)

        df_league['Cluster'] = clusters
        df_league['Cluster_Confidence'] = confidence
        df_league = self.attach_selected_features(df_league, features_df)
        evaluation = self.evaluate_clustering(scaled_data, clusters, "GMM", gmm)
        evaluation["gmm_info"] = {
            "selected_k": int(optimal_k),
            "selected_covariance_type": best_gmm["covariance_type"],
            "bic": best_gmm["bic"],
            "aic": best_gmm["aic"],
            "init_params": best_gmm["init_params"],
            "initialization_method": "kmeans",
            "candidate_count": len(best_gmm.get("candidates", []))
        }
        ambiguous_df = df_league[df_league["Cluster_Confidence"] < 0.65].copy()
        ambiguous_df = ambiguous_df.sort_values("Cluster_Confidence").head(10)
        evaluation["ambiguous_players"] = [
            {
                "Player": row.get("Name"),
                "Team": row.get("Team"),
                "Cluster": int(row.get("Cluster")),
                "Cluster_Confidence": float(row.get("Cluster_Confidence"))
            }
            for _, row in ambiguous_df.iterrows()
        ]
        df_league.attrs['evaluation'] = evaluation

        return df_league, optimal_k
