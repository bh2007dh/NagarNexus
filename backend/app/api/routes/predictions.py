from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.routes.datasets import get_authorized_dataset
from app.core.database import get_db
from app.core.security import get_current_user
from app.data_processing.profiler import load_dataframe
from app.machine_learning.ml_engine import (
    SUPPORTED_ALGORITHMS,
    train_and_evaluate_model,
    predict_with_saved_model,
)
from app.models.prediction import MLModel, Prediction
from app.models.user import User
from app.schemas.ml import MLTrainRequest, MLPredictRequest, PredictiveRunRequest
from app.utils.activity import log_activity, sanitize_json

router = APIRouter(tags=["Machine Learning & Predictive Analytics"])


def serialize_ml_model(m: MLModel) -> dict:
    return sanitize_json({
        "id": m.id,
        "user_id": m.user_id,
        "dataset_id": m.dataset_id,
        "model_name": m.model_name,
        "model_type": m.model_type,
        "algorithm": m.algorithm,
        "model_version": m.model_version,
        "feature_columns": m.feature_columns,
        "target_column": m.target_column,
        "metrics_json": m.metrics_json,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    })


def get_authorized_model(db: Session, model_id: int, current_user: User) -> MLModel:
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ML Model not found.")
    if not model.is_public and model.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this private ML model.",
        )
    return model


@router.get("/api/ml/algorithms")
def list_ml_algorithms():
    return {"algorithms": SUPPORTED_ALGORITHMS}


@router.post("/api/ml/train", status_code=status.HTTP_201_CREATED)
def train_ml_model_endpoint(
    payload: MLTrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, payload.dataset_id, current_user)
    target_path = (
        ds.processed_file_path
        if ds.processed_file_path and Path(ds.processed_file_path).exists()
        else ds.file_path
    )
    df = load_dataframe(target_path)

    trained_info = train_and_evaluate_model(df, payload)

    model_rec = MLModel(
        user_id=current_user.id,
        dataset_id=ds.id,
        model_name=trained_info["model_name"],
        model_type=trained_info["model_type"],
        algorithm=trained_info["algorithm"],
        model_version=trained_info["model_version"],
        feature_columns=trained_info["feature_columns"],
        target_column=trained_info["target_column"],
        metrics_json=trained_info["metrics"],
        model_path=trained_info["model_path"],
        is_public=0,
    )
    db.add(model_rec)
    db.commit()
    db.refresh(model_rec)

    log_activity(
        db,
        current_user.id,
        "ML_TRAIN",
        f"Trained {model_rec.algorithm} model '{model_rec.model_name}' (v{model_rec.model_version}) on '{ds.name}'",
    )
    return serialize_ml_model(model_rec)


@router.get("/api/ml/models")
def list_ml_models(
    dataset_id: int | None = Query(None),
    model_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MLModel).filter(
        or_(MLModel.user_id == current_user.id, MLModel.is_public == 1)
    )
    if dataset_id:
        query = query.filter(MLModel.dataset_id == dataset_id)
    if model_type:
        query = query.filter(MLModel.model_type == model_type)

    models = query.order_by(MLModel.created_at.desc()).all()
    return {"models": [serialize_ml_model(m) for m in models]}


@router.get("/api/ml/models/{model_id}")
def get_ml_model_details(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = get_authorized_model(db, model_id, current_user)
    return serialize_ml_model(model)


@router.post("/api/ml/models/{model_id}/predict")
def predict_from_ml_model(
    model_id: int,
    payload: MLPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = get_authorized_model(db, model_id, current_user)
    pred_out = predict_with_saved_model(model.model_path, payload.features)

    pred_rec = Prediction(
        model_id=model.id,
        user_id=current_user.id,
        category=payload.category or model.target_column or "environmental",
        location_id=payload.location_id,
        input_json=pred_out["resolved_features"],
        predicted_value=pred_out["predicted_value"],
        numeric_prediction=pred_out.get("numeric_prediction"),
        actual_value=payload.actual_value,
        confidence_metadata=pred_out["confidence_metadata"],
    )
    db.add(pred_rec)
    db.commit()
    db.refresh(pred_rec)

    log_activity(
        db,
        current_user.id,
        "ML_PREDICT",
        f"Generated prediction ({pred_rec.predicted_value}) using model '{model.model_name}'",
    )

    return sanitize_json({
        "prediction_id": pred_rec.id,
        "model_id": model.id,
        "model_name": model.model_name,
        "model_version": model.model_version,
        "algorithm": model.algorithm,
        "target_column": model.target_column,
        "input_features": pred_out["resolved_features"],
        "predicted_value": pred_rec.predicted_value,
        "numeric_prediction": pred_rec.numeric_prediction,
        "actual_value": pred_rec.actual_value,
        "evaluation_metrics": model.metrics_json,
        "confidence_metadata": pred_out["confidence_metadata"],
        "created_at": pred_rec.created_at.isoformat() if pred_rec.created_at else None,
    })


# --- PREDICTIVE ANALYTICS ROUTES ---

@router.post("/api/predictions/run")
def run_predictive_analytics(
    payload: PredictiveRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = get_authorized_model(db, payload.model_id, current_user)
    pred_out = predict_with_saved_model(
        model.model_path,
        payload.features,
        horizon_steps=payload.horizon_steps,
    )

    pred_rec = Prediction(
        model_id=model.id,
        user_id=current_user.id,
        category=payload.category,
        location_id=payload.location_id,
        input_json=pred_out["resolved_features"],
        predicted_value=pred_out["predicted_value"],
        numeric_prediction=pred_out.get("numeric_prediction"),
        actual_value=payload.actual_value,
        confidence_metadata=pred_out["confidence_metadata"],
    )
    db.add(pred_rec)
    db.commit()
    db.refresh(pred_rec)

    log_activity(
        db,
        current_user.id,
        "PREDICTION_RUN",
        f"Ran {payload.category} forecast ({pred_rec.predicted_value}) with model '{model.model_name}'",
    )

    return sanitize_json({
        "prediction_id": pred_rec.id,
        "category": payload.category,
        "model_id": model.id,
        "model_name": model.model_name,
        "model_version": model.model_version,
        "input_features": pred_out["resolved_features"],
        "predicted_value": pred_rec.predicted_value,
        "numeric_prediction": pred_rec.numeric_prediction,
        "actual_value": pred_rec.actual_value,
        "evaluation_metrics": model.metrics_json,
        "confidence_metadata": pred_out["confidence_metadata"],
        "created_at": pred_rec.created_at.isoformat() if pred_rec.created_at else None,
    })


@router.get("/api/predictions/history")
def get_prediction_history(
    category: str | None = Query(None),
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Prediction).filter(
        or_(Prediction.user_id == current_user.id, Prediction.user_id.is_(None))
    )
    if category and category != "all":
        query = query.filter(Prediction.category == category)

    preds = query.order_by(Prediction.created_at.desc()).limit(limit).all()
    history_items = []
    for p in preds:
        m = db.query(MLModel).filter(MLModel.id == p.model_id).first()
        history_items.append({
            "id": p.id,
            "model_id": p.model_id,
            "model_name": m.model_name if m else f"Model #{p.model_id}",
            "model_version": m.model_version if m else "1.0.0",
            "category": p.category,
            "input_features": p.input_json,
            "predicted_value": p.predicted_value,
            "numeric_prediction": p.numeric_prediction,
            "actual_value": p.actual_value,
            "confidence_metadata": p.confidence_metadata,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return sanitize_json({"predictions": history_items})

