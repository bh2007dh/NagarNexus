"""Train baseline Machine Learning models on the NagarNexus environmental dataset."""
import sys
from pathlib import Path
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.machine_learning.ml_engine import train_and_evaluate_model
from app.schemas.ml import MLTrainRequest
from app.services.seeder import generate_sample_csv_files


def main():
    generate_sample_csv_files()
    env_csv = Path(settings.SAMPLE_DIR) / "sample_environmental_indicators.csv"
    df = pd.read_csv(env_csv)

    models_to_train = [
        MLTrainRequest(
            dataset_id=1,
            model_name="CLI Trained Temperature Regressor",
            algorithm="random_forest_regressor",
            feature_columns=["humidity_pct", "rainfall_mm", "wind_speed_kmh", "pm25"],
            target_column="temperature_c",
        ),
        MLTrainRequest(
            dataset_id=1,
            model_name="CLI Trained K-Means Urban Clusterer",
            algorithm="kmeans",
            feature_columns=["temperature_c", "rainfall_mm", "humidity_pct", "pm25"],
            n_clusters=3,
        ),
        MLTrainRequest(
            dataset_id=1,
            model_name="CLI Trained Isolation Forest Detector",
            algorithm="isolation_forest",
            feature_columns=["temperature_c", "rainfall_mm", "pm25", "no2"],
            contamination=0.05,
        ),
    ]

    for req in models_to_train:
        info = train_and_evaluate_model(df, req)
        print(f"[NagarNexus] Trained {info['model_name']} -> Saved to {info['model_path']}")
        print(f"             Metrics: {info['metrics'].get('task_type')}")


if __name__ == "__main__":
    main()

