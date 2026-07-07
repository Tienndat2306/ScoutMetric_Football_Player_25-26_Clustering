import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score
from kneed import KneeLocator
from sklearn.cluster import KMeans

def get_elbow(scaled_data):
    inertia_values = []
    k_values = range(1, 9) 
    
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(scaled_data)
        inertia_values.append(float(kmeans.inertia_))

    kl = KneeLocator(k_values, inertia_values, curve='convex', direction='decreasing')
    optimal_k = kl.elbow if kl.elbow is not None else 3
    
    return list(k_values), inertia_values, optimal_k

def get_silhouette_scores(scaled_data):
    sil_scores = []
    k_values = range(2, min(11, len(scaled_data)))
    # Silhouette yêu cầu tối thiểu k=2 cụm
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled_data)
        score = silhouette_score(scaled_data, labels)
        sil_scores.append(score)
    
    optimal_k = k_values[np.argmax(sil_scores)]
    return sil_scores, optimal_k

def get_db_index(scaled_data):
    db_indices = []
    # DB Index yêu cầu tối thiểu k=2 cụm
    k_values = range(2, min(11, len(scaled_data)))
    
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled_data)
        
        # Tính toán DB Index
        score = davies_bouldin_score(scaled_data, labels)
        db_indices.append(score)
        
    # Tìm k có DB Index nhỏ nhất (argmin)
    optimal_k = k_values[np.argmin(db_indices)]
    
    return db_indices, optimal_k

def get_hybrid_k(scaled_data):
    elbow_k_values, inertia_values, elbow_k = get_elbow(scaled_data)
    max_k = min(10, len(scaled_data) - 1)
    if max_k < 2:
        return {
            "elbow_k_values": elbow_k_values,
            "inertia_values": inertia_values,
            "elbow_k": elbow_k,
            "candidate_k_values": [],
            "silhouette_scores": [],
            "optimal_k": 1
        }

    candidate_start = max(2, elbow_k - 1)
    candidate_end = min(max_k, elbow_k + 2)
    candidate_k_values = list(range(candidate_start, candidate_end + 1))

    silhouette_scores = []
    for k in candidate_k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled_data)
        silhouette_scores.append(float(silhouette_score(scaled_data, labels)))

    optimal_k = (
        candidate_k_values[int(np.argmax(silhouette_scores))]
        if silhouette_scores else elbow_k
    )

    return {
        "elbow_k_values": elbow_k_values,
        "inertia_values": inertia_values,
        "elbow_k": int(elbow_k),
        "candidate_k_values": candidate_k_values,
        "silhouette_scores": silhouette_scores,
        "optimal_k": int(optimal_k)
    }
