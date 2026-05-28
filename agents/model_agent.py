class ModelImprovementAgent:

    def suggest(self, df, result):

        suggestions = []

        best_model = result.get("best_model", {})
        score = float(best_model.get("score", 0))

        # Dataset quality checks
        missing = int(df.isnull().sum().sum())

        if missing > 0:
            suggestions.append(
                f"Dataset still contains {missing} missing values."
            )

        duplicates = int(df.duplicated().sum())

        if duplicates > 0:
            suggestions.append(
                f"Dataset contains {duplicates} duplicate rows."
            )

        # Accuracy recommendations
        if score < 0.60:

            suggestions.extend([
                "Model accuracy is low.",
                "Add more training data.",
                "Perform feature engineering.",
                "Remove noisy columns.",
                "Try normalization and scaling."
            ])

        elif score < 0.80:

            suggestions.extend([
                "Accuracy is moderate.",
                "Use feature selection.",
                "Tune hyperparameters.",
                "Try ensemble algorithms."
            ])

        else:

            suggestions.extend([
                "Model performance is good.",
                "Validate using cross-validation.",
                "Monitor for overfitting."
            ])

        suggestions.append(
            "Consider XGBoost, CatBoost, or LightGBM for better performance."
        )

        return suggestions