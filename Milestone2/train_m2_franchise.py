"""
train_m2_franchise.py — Multi-Agent ML Training Pipeline for FranchiseOps AI (Milestone 2)

Trains 3 agents, each comparing 5+ algorithms, plus KMeans outlet tiering:
  Agent 1: Workforce Attrition (Classification, ROC-AUC)
  Agent 2: Revenue Simulation (Regression, R^2) + Outlet Tiering (KMeans)
  Agent 3: Inventory Demand (Regression, R^2)

Datasets are pulled via kagglehub. If Kaggle credentials/network aren't
available, each agent falls back to a synthetic dataset with the same
schema shape, so the notebook never crashes — it just trains on fake data
instead of real data.

Champion models are saved to models/*.joblib and every algorithm's metric
is logged to the ml_models table (via db.py's get_conn()), matching the
schema: agent_name, algorithm, metric_name, metric_value, is_champion, trained_at.
"""

import os
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier,
    RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor,
    AdaBoostRegressor,
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import roc_auc_score, r2_score

from db import get_conn

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)


# --------------------------------------------------------------------------
# DB LOGGING HELPERS
# --------------------------------------------------------------------------
def clear_agent_metrics(agent_name):
    """Wipe old rows for this agent before logging a fresh training run."""
    conn = get_conn()
    conn.execute("DELETE FROM ml_models WHERE agent_name=?", (agent_name,))
    conn.commit()
    conn.close()


def log_metric(agent_name, algorithm, metric_name, metric_value, is_champion=False):
    conn = get_conn()
    conn.execute(
        """INSERT INTO ml_models (agent_name, algorithm, metric_name, metric_value, is_champion)
           VALUES (?,?,?,?,?)""",
        (agent_name, algorithm, metric_name, float(metric_value), int(is_champion)),
    )
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# KAGGLE DOWNLOAD WITH SYNTHETIC FALLBACK
# --------------------------------------------------------------------------
def try_kaggle_download(slug, target_filename):
    """Attempt to download+locate a Kaggle dataset file. Returns a DataFrame or None."""
    try:
        import kagglehub
        path = kagglehub.dataset_download(slug)
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower() == target_filename.lower():
                    return pd.read_csv(os.path.join(root, f))
        # fallback: grab the first csv found if exact name doesn't match
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(".csv"):
                    return pd.read_csv(os.path.join(root, f))
    except Exception as e:
        print(f"[kaggle fallback] Could not load {slug} ({target_filename}): {e}")
    return None


def synthetic_attrition_df(n=1200, seed=42):
    rng = np.random.default_rng(seed)
    age = rng.integers(20, 60, n)
    monthly_income = rng.integers(15000, 150000, n)
    overtime = rng.choice(["Yes", "No"], n, p=[0.3, 0.7])
    job_satisfaction = rng.integers(1, 5, n)
    years_at_company = rng.integers(0, 20, n)
    distance_from_home = rng.integers(1, 30, n)

    risk = (
        (overtime == "Yes").astype(int) * 0.35
        + (job_satisfaction <= 2).astype(int) * 0.25
        + (years_at_company < 2).astype(int) * 0.2
        + (distance_from_home > 20).astype(int) * 0.1
        + rng.normal(0, 0.15, n)
    )
    attrition = (risk > np.percentile(risk, 75)).astype(int)

    return pd.DataFrame({
        "Age": age,
        "MonthlyIncome": monthly_income,
        "OverTime": overtime,
        "JobSatisfaction": job_satisfaction,
        "YearsAtCompany": years_at_company,
        "DistanceFromHome": distance_from_home,
        "Attrition": np.where(attrition == 1, "Yes", "No"),
    })


def synthetic_sales_df(n=1500, seed=7):
    rng = np.random.default_rng(seed)
    cities = ["Mumbai", "Delhi NCR", "Bengaluru", "Hyderabad", "Chennai", "Pune"]
    outlet_id = rng.integers(1, 11, n)
    order_count = rng.integers(5, 200, n)
    discount = rng.uniform(0, 0.4, n)
    unit_price = rng.uniform(100, 5000, n)
    quantity = rng.integers(1, 20, n)

    revenue = (unit_price * quantity * (1 - discount)) + rng.normal(0, 200, n)
    revenue = np.clip(revenue, 0, None)

    return pd.DataFrame({
        "OutletID": outlet_id,
        "City": rng.choice(cities, n),
        "OrderCount": order_count,
        "Discount": discount,
        "UnitPrice": unit_price,
        "Quantity": quantity,
        "Revenue": revenue,
    })


def synthetic_inventory_df(n=1500, seed=99):
    rng = np.random.default_rng(seed)
    stock_level = rng.integers(0, 500, n)
    lead_time = rng.integers(1, 15, n)
    temperature = rng.uniform(15, 42, n)
    is_rainy = rng.choice([0, 1], n, p=[0.7, 0.3])
    promo_flag = rng.choice([0, 1], n, p=[0.85, 0.15])

    demand = (
        50
        + (500 - stock_level) * 0.05
        - lead_time * 1.5
        + (temperature > 35).astype(int) * 10
        + is_rainy * 15
        + promo_flag * 30
        + rng.normal(0, 8, n)
    )
    demand = np.clip(demand, 0, None)

    return pd.DataFrame({
        "StockLevel": stock_level,
        "LeadTimeDays": lead_time,
        "TemperatureC": temperature,
        "IsRainy": is_rainy,
        "PromoFlag": promo_flag,
        "DemandUnits": demand,
    })


# --------------------------------------------------------------------------
# GENERIC PREPROCESSING
# --------------------------------------------------------------------------
def preprocess(df, target_col):
    """Encode categoricals, drop nulls, split X/y."""
    df = df.copy()
    df = df.dropna(subset=[target_col])

    for col in df.columns:
        if col == target_col:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna("Unknown")
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    y = df[target_col]
    X = df.drop(columns=[target_col])
    # keep only numeric feature columns
    X = X.select_dtypes(include=[np.number])
    return X, y


# --------------------------------------------------------------------------
# AGENT 1: WORKFORCE ATTRITION (Classification, ROC-AUC)
# --------------------------------------------------------------------------
def train_agent1():
    agent_name = "Workforce Attrition"
    print(f"\n=== Training {agent_name} ===")

    df1 = try_kaggle_download(
        "pavansubhasht/ibm-hr-analyticsattrition-dataset",
        "WA_Fn-UseC_-HR-Employee-Attrition.csv",
    )
    df2 = try_kaggle_download("rhuebner/human-resources-data-set", "HRDataset_v14.csv")

    frames = [d for d in (df1, df2) if d is not None]
    if not frames:
        print("Using fully synthetic attrition data (no Kaggle source available).")
        df = synthetic_attrition_df()
    else:
        # normalize target column name across whichever dataset(s) loaded
        for d in frames:
            if "Attrition" not in d.columns:
                if "Termd" in d.columns:
                    d["Attrition"] = np.where(d["Termd"] == 1, "Yes", "No")
                    d.drop(columns=["Termd"], inplace=True)  # avoid leaking the label
                elif "EmploymentStatus" in d.columns:
                    d["Attrition"] = np.where(
                        d["EmploymentStatus"].astype(str).str.contains("Term", case=False, na=False),
                        "Yes", "No",
                    )
                    d.drop(columns=["EmploymentStatus"], inplace=True)  # avoid leaking the label
        frames = [d for d in frames if "Attrition" in d.columns]

        # Also drop any other obviously leaky columns if present (dates/reasons tied to termination)
        leak_cols = ["TermReason", "TerminationDate", "DateofTermination", "termreason", "TermDate"]
        for d in frames:
            for lc in leak_cols:
                if lc in d.columns:
                    d.drop(columns=[lc], inplace=True)
        df = pd.concat(frames, ignore_index=True, sort=False) if frames else synthetic_attrition_df()

    df["Attrition"] = LabelEncoder().fit_transform(df["Attrition"].astype(str))  # Yes/No -> 1/0
    X, y = preprocess(df, "Attrition")

    if X.shape[1] == 0 or y.nunique() < 2:
        print("Fell back to synthetic data due to unusable columns/target.")
        df = synthetic_attrition_df()
        df["Attrition"] = LabelEncoder().fit_transform(df["Attrition"])
        X, y = preprocess(df, "Attrition")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    algorithms = {
        "LogisticRegression": LogisticRegression(max_iter=2000),
        "RandomForestClassifier": RandomForestClassifier(n_estimators=200, random_state=42),
        "GradientBoostingClassifier": GradientBoostingClassifier(random_state=42),
        "SVC": SVC(kernel="rbf", probability=True, random_state=42),
        "DecisionTreeClassifier": DecisionTreeClassifier(random_state=42),
        "AdaBoostClassifier": AdaBoostClassifier(random_state=42),
        "KNeighborsClassifier": KNeighborsClassifier(),
    }

    clear_agent_metrics(agent_name)
    results = {}
    for name, model in algorithms.items():
        model.fit(X_train_s, y_train)
        proba = model.predict_proba(X_test_s)[:, 1]
        score = roc_auc_score(y_test, proba)
        results[name] = (model, score)
        print(f"  {name}: ROC-AUC = {score:.4f}")

    champion_name = max(results, key=lambda k: results[k][1])
    champion_model, champion_score = results[champion_name]

    for name, (_, score) in results.items():
        log_metric(agent_name, name, "ROC-AUC", score, is_champion=(name == champion_name))

    joblib.dump(champion_model, os.path.join(MODELS_DIR, "agent1_attrition_champion.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "agent1_scaler.joblib"))
    print(f"  Champion: {champion_name} (ROC-AUC={champion_score:.4f}) saved.")
    return champion_name, champion_score


# --------------------------------------------------------------------------
# AGENT 2: REVENUE SIMULATION (Regression, R^2) + OUTLET TIERING (KMeans)
# --------------------------------------------------------------------------
def train_agent2():
    agent_name = "Revenue Simulation"
    print(f"\n=== Training {agent_name} ===")

    df1 = try_kaggle_download("vivek465/superstore-dataset-final", "Sample - Superstore.csv")
    df2 = try_kaggle_download("kyanyoga/sample-store-data", "store_data.csv")

    frames = [d for d in (df1, df2) if d is not None]
    if not frames:
        print("Using fully synthetic sales data (no Kaggle source available).")
        df = synthetic_sales_df()
    else:
        df = frames[0]
        # try to standardize a "Revenue" / "Sales" target column
        if "Revenue" not in df.columns:
            for candidate in ("Sales", "sales", "Total", "Amount"):
                if candidate in df.columns:
                    df["Revenue"] = df[candidate]
                    break
        if "Revenue" not in df.columns:
            df = synthetic_sales_df()

    X, y = preprocess(df, "Revenue")
    if X.shape[1] == 0:
        df = synthetic_sales_df()
        X, y = preprocess(df, "Revenue")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    algorithms = {
        "RandomForestRegressor": RandomForestRegressor(n_estimators=200, random_state=42),
        "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42),
        "ExtraTreesRegressor": ExtraTreesRegressor(n_estimators=200, random_state=42),
        "Ridge": Ridge(),
        "DecisionTreeRegressor": DecisionTreeRegressor(random_state=42),
        "AdaBoostRegressor": AdaBoostRegressor(random_state=42),
        "KNeighborsRegressor": KNeighborsRegressor(),
    }

    clear_agent_metrics(agent_name)
    results = {}
    for name, model in algorithms.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        score = r2_score(y_test, preds)
        results[name] = (model, score)
        print(f"  {name}: R^2 = {score:.4f}")

    champion_name = max(results, key=lambda k: results[k][1])
    champion_model, champion_score = results[champion_name]

    for name, (_, score) in results.items():
        log_metric(agent_name, name, "R2", score, is_champion=(name == champion_name))

    joblib.dump(champion_model, os.path.join(MODELS_DIR, "agent2_revenue_champion.joblib"))
    print(f"  Champion: {champion_name} (R^2={champion_score:.4f}) saved.")

    # ---- Outlet Tiering (KMeans on 10 seeded outlets) ----
    train_outlet_tiering(df)

    return champion_name, champion_score


def train_outlet_tiering(sales_df):
    print("  -- Outlet Tiering (KMeans) --")
    if "OutletID" not in sales_df.columns:
        sales_df = synthetic_sales_df()  # guarantees OutletID exists

    grouped = sales_df.groupby("OutletID").agg(
        avg_daily_revenue=("Revenue", "mean") if "Revenue" in sales_df.columns else ("OutletID", "count"),
        order_count=("OutletID", "count"),
    ).reset_index()

    # ensure exactly 10 seeded outlets exist (pad if fewer from real data)
    if grouped.shape[0] < 10:
        pad_needed = 10 - grouped.shape[0]
        synth = synthetic_sales_df(n=200)
        pad = synth.groupby("OutletID").agg(
            avg_daily_revenue=("Revenue", "mean"), order_count=("OutletID", "count")
        ).reset_index().head(pad_needed)
        grouped = pd.concat([grouped, pad], ignore_index=True)

    grouped = grouped.head(10).reset_index(drop=True)
    grouped["OutletID"] = range(1, len(grouped) + 1)

    features = grouped[["avg_daily_revenue", "order_count"]]
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features_scaled)
    grouped["cluster"] = clusters

    # rank clusters by mean revenue to assign meaningful tier labels
    cluster_rank = grouped.groupby("cluster")["avg_daily_revenue"].mean().sort_values(ascending=False)
    tier_labels = ["Excellent", "Good", "Needs Attention", "Critical"]
    cluster_to_tier = {cl: tier_labels[i] for i, cl in enumerate(cluster_rank.index)}
    grouped["tier"] = grouped["cluster"].map(cluster_to_tier)

    joblib.dump(kmeans, os.path.join(MODELS_DIR, "kmeans_outlets.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "outlet_scaler.joblib"))
    grouped.to_csv(os.path.join(MODELS_DIR, "outlet_tiers.csv"), index=False)

    log_metric("Outlet Tiering", "KMeans", "n_clusters", 4, is_champion=True)
    print(f"  Outlet tiers saved: {dict(grouped[['OutletID','tier']].values)}")


# --------------------------------------------------------------------------
# AGENT 3: INVENTORY DEMAND (Regression, R^2)
# --------------------------------------------------------------------------
def train_agent3():
    agent_name = "Inventory Demand"
    print(f"\n=== Training {agent_name} ===")

    df1 = try_kaggle_download("pratyushraj1/retail-inventory-management-dataset", "inventory.csv")
    df2 = try_kaggle_download("shashwatwork/web-store-item-demand-forecasting-dataset", "train.csv")

    frames = [d for d in (df1, df2) if d is not None]
    if not frames:
        print("Using fully synthetic inventory data (no Kaggle source available).")
        df = synthetic_inventory_df()
    else:
        df = frames[0]
        if "DemandUnits" not in df.columns:
            for candidate in ("Demand", "sales", "Sales", "units_sold", "Units"):
                if candidate in df.columns:
                    df["DemandUnits"] = df[candidate]
                    break
        if "DemandUnits" not in df.columns:
            df = synthetic_inventory_df()

    X, y = preprocess(df, "DemandUnits")
    if X.shape[1] == 0:
        df = synthetic_inventory_df()
        X, y = preprocess(df, "DemandUnits")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    algorithms = {
        "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=200, random_state=42),
        "ExtraTreesRegressor": ExtraTreesRegressor(n_estimators=200, random_state=42),
        "Ridge": Ridge(),
        "DecisionTreeRegressor": DecisionTreeRegressor(random_state=42),
        "AdaBoostRegressor": AdaBoostRegressor(random_state=42),
        "KNeighborsRegressor": KNeighborsRegressor(),
    }

    clear_agent_metrics(agent_name)
    results = {}
    for name, model in algorithms.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        score = r2_score(y_test, preds)
        results[name] = (model, score)
        print(f"  {name}: R^2 = {score:.4f}")

    champion_name = max(results, key=lambda k: results[k][1])
    champion_model, champion_score = results[champion_name]

    for name, (_, score) in results.items():
        log_metric(agent_name, name, "R2", score, is_champion=(name == champion_name))

    joblib.dump(champion_model, os.path.join(MODELS_DIR, "agent3_inventory_champion.joblib"))
    print(f"  Champion: {champion_name} (R^2={champion_score:.4f}) saved.")
    return champion_name, champion_score


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------
def run_all():
    from db import init_db
    init_db()  # safe no-op if tables already exist

    a1 = train_agent1()
    a2 = train_agent2()
    a3 = train_agent3()

    print("\n=== Training complete ===")
    print(f"Agent 1 champion: {a1[0]} (ROC-AUC={a1[1]:.4f})")
    print(f"Agent 2 champion: {a2[0]} (R^2={a2[1]:.4f})")
    print(f"Agent 3 champion: {a3[0]} (R^2={a3[1]:.4f})")
    print(f"All models saved to ./{MODELS_DIR}/")


if __name__ == "__main__":
    run_all()
