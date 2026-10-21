# Feature Scaling: When It Matters and When It Doesn't

Feature scaling is one of the first preprocessing steps people learn, and one of the most misunderstood. Some models break without it; others do not care at all. Knowing the difference saves time and avoids silent bugs.

![Two features on very different scales](https://example.com/images/feature-scaling/different-scales.png)

## Why scale features at all?

Many algorithms compare samples using distances or gradients. If one feature is measured in thousands (income) and another in units (number of children), the large one dominates every distance and every gradient step. The model ends up "seeing" mostly one feature.

## Models that need scaling

- **Distance-based models** such as k-nearest neighbours, k-means and SVMs with an RBF kernel: distances are meaningless when features live on different scales.
- **Gradient-based models** such as linear and logistic regression trained with gradient descent, and neural networks: unscaled features create elongated loss surfaces, so training is slow and unstable.
- **Regularised linear models** (ridge, lasso): the penalty treats all coefficients equally, so a feature's scale changes how strongly it is penalised.
- **PCA**: it finds directions of maximum variance, and the feature with the largest scale wins by default.

![Gradient descent with and without scaling](https://example.com/images/feature-scaling/gradient-descent.png)

## Models that don't need it

Tree-based models (decision trees, random forests, gradient boosting such as XGBoost or LightGBM) split on one feature at a time using thresholds. Multiplying a feature by 1,000 moves the threshold, but the split, and therefore the model, stays the same.

## Standardisation vs. normalisation

| Method | Formula | Use it when |
|---|---|---|
| Standardisation | (x - mean) / std | Default choice; works well with outliers that are not extreme. |
| Min-max normalisation | (x - min) / (max - min) | You need a fixed range such as [0, 1], e.g. for image pixels. |
| Robust scaling | (x - median) / IQR | The feature has strong outliers. |

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

model = make_pipeline(StandardScaler(), LogisticRegression())
model.fit(X_train, y_train)
```

## The most common bug: data leakage

Fitting the scaler on the whole dataset before splitting leaks information from the test set into training: the mean and standard deviation already "know" the test data. Always fit the scaler on the training set only, which is exactly what a scikit-learn `Pipeline` does for you, including inside cross-validation.

![Fit the scaler inside the pipeline](https://example.com/images/feature-scaling/pipeline.png)

## Key takeaways

1. Scale features for distance-based, gradient-based and regularised models, and before PCA.
2. Don't bother for tree-based models.
3. Use standardisation by default and robust scaling when there are outliers.
4. Put the scaler inside a pipeline so it is only ever fitted on training data.

Read the full post: https://example.com/blog/feature-scaling
