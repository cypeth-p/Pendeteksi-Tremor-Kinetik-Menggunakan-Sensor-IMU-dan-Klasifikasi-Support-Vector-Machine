import pandas as pd
import joblib
import time

from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

#jgn lupa ganti csv yg mau dipake
file_name = "C:/Users/pandy/Desktop/featext/4feature600.csv"

data = pd.read_csv(file_name)

X = data[["MAV", "RMS", "WL", "DASDV"]]
y = data["Label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("svm", SVC())
])

#param gridsearchnya
param_grid = [
    {
        "svm__kernel": ["rbf", "linear", "poly"],
        "svm__C": [0.1, 1, 10, 100],
        "svm__gamma": ["scale", "auto"],
	"svm__degree": [1, 2, 3, 4]
    }
]

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=cv,
    scoring="f1",
    n_jobs=-1,
    verbose=3
)

print("\n=== GRID SEARCH START ===")
start = time.time()

grid.fit(X_train, y_train)

end = time.time()

print("\n=== GRID SEARCH DONE ===")
print("Training time: %.2f detik" % (end - start))

best_model = grid.best_estimator_

print("\n===== BEST PARAMETER =====")
print(grid.best_params_)

print("\nBest CV F1 Score: %.4f" % grid.best_score_)

scaler = best_model.named_steps["scaler"]

print("\n===== SCALING =====")
print("MEAN :", scaler.mean_)
print("STD  :", scaler.scale_)

svm_model = best_model.named_steps["svm"]

print("\n===== SVM INFO =====")
print("Kernel :", svm_model.kernel)
print("C      :", svm_model.C)

if svm_model.kernel in ["rbf", "poly", "sigmoid"]:
    print("Gamma setting :", svm_model.gamma)
    print("Gamma actual  :", svm_model._gamma)
else:
    print("Gamma : Tidak dipakai untuk linear")

if svm_model.kernel == "poly":
    print("Degree :", svm_model.degree)
    print("Coef0  :", svm_model.coef0)

y_pred = best_model.predict(X_test)

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred)
rec = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print("\n===== TEST PERFORMANCE =====")
print("Accuracy  : %.2f%%" % (acc * 100))
print("Precision : %.2f%%" % (prec * 100))
print("Recall    : %.2f%%" % (rec * 100))
print("F1 Score  : %.2f%%" % (f1 * 100))

print("\n===== CONFUSION MATRIX =====")
print(confusion_matrix(y_test, y_pred))

print("\n===== CLASSIFICATION REPORT =====")
print(classification_report(y_test, y_pred))
