"""
Predictive Intelligence Layer: Probabilistic Direction & Regime Forecaster.
"""
from pathlib import Path
from typing import Tuple, Optional, List
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss

from src.config import MODELS_DIR


class MarketPredictor:
    """
    Gradient-boosted decision engine that estimates directional probability P(Up)
    and confidence calibrated across market features.
    """

    def __init__(self, ticker: str, feature_cols: List[str], model_seed: int = 42):
        self.ticker = ticker
        self.feature_cols = feature_cols
        self.model_seed = model_seed
        self.model: Optional[lgb.Booster] = None
        self.metrics: dict = {}

    def train(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        num_boost_round: int = 250,
        learning_rate: float = 0.03,
        max_depth: int = 5,
        num_leaves: int = 24,
        model_seed: Optional[int] = None,
    ) -> dict:
        """
        Trains LightGBM classifier with early stopping on validation split.
        """
        seed_to_use = model_seed if model_seed is not None else self.model_seed
        X_train = train_df[self.feature_cols].values
        y_train = train_df["target_direction"].values

        train_data = lgb.Dataset(X_train, label=y_train)

        params = {
            "objective": "binary",
            "metric": ["binary_logloss", "auc"],
            "boosting_type": "gbdt",
            "learning_rate": learning_rate,
            "max_depth": max_depth,
            "num_leaves": num_leaves,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 1,
            "verbosity": -1,
            "seed": seed_to_use,
        }

        valid_sets = [train_data]
        valid_names = ["train"]

        if val_df is not None:
            X_val = val_df[self.feature_cols].values
            y_val = val_df["target_direction"].values
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            valid_sets.append(val_data)
            valid_names.append("valid")

        callbacks = [lgb.early_stopping(stopping_rounds=30, verbose=False)] if val_df is not None else []

        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=num_boost_round,
            valid_sets=valid_sets,
            valid_names=valid_names,
            callbacks=callbacks,
        )

        # Compute validation performance
        if val_df is not None:
            X_val = val_df[self.feature_cols].values
            y_val = val_df["target_direction"].values
            preds_val = self.model.predict(X_val)
            auc = roc_auc_score(y_val, preds_val) if len(np.unique(y_val)) > 1 else 0.5
            acc = accuracy_score(y_val, (preds_val > 0.5).astype(int))
            brier = brier_score_loss(y_val, preds_val)
            self.metrics = {"val_auc": float(auc), "val_acc": float(acc), "val_brier": float(brier)}
            print(f"[{self.ticker} Predictor] Validation AUC: {auc:.4f} | Accuracy: {acc:.4f} | Brier: {brier:.4f}")
        else:
            self.metrics = {"train_status": "fitted_without_val"}

        return self.metrics

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """
        Returns array of calibrated probabilities P(Price Up).
        """
        if self.model is None:
            raise ValueError("Predictor model has not been trained yet.")
        X = df[self.feature_cols].values
        return self.model.predict(X)

    def get_feature_importances(self) -> pd.DataFrame:
        """
        Returns DataFrame of features sorted by importance gain.
        """
        if self.model is None:
            raise ValueError("Model is not trained.")
        gains = self.model.feature_importance(importance_type="gain")
        importance_df = pd.DataFrame({
            "feature": self.feature_cols,
            "importance": gains,
        }).sort_values("importance", ascending=False).reset_index(drop=True)
        return importance_df

    def save(self, model_path: Optional[Path] = None) -> Path:
        if model_path is None:
            model_path = MODELS_DIR / f"{self.ticker}_lgb.txt"
        self.model.save_model(str(model_path))
        return model_path

    def load(self, model_path: Optional[Path] = None):
        if model_path is None:
            model_path = MODELS_DIR / f"{self.ticker}_lgb.txt"
        self.model = lgb.Booster(model_file=str(model_path))


if __name__ == "__main__":
    from src.data_loader import fetch_and_cache_ticker
    from src.feature_pipeline import prepare_feature_dataset

    df = fetch_and_cache_ticker("SPY")
    proc_df, feats = prepare_feature_dataset(df, "SPY", save_processed=False)
    
    # Train / Test split by time (80% train, 20% val)
    split_idx = int(len(proc_df) * 0.8)
    train_df = proc_df.iloc[:split_idx]
    val_df = proc_df.iloc[split_idx:]

    predictor = MarketPredictor("SPY", feats)
    predictor.train(train_df, val_df)
    
    importances = predictor.get_feature_importances()
    print("\nTop 5 Most Important Features:")
    print(importances.head(5))
