import pandas as pd
import joblib
import time

from sklearn.model_selection import train_test_split
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

#pakai param fix
model = Pipeline([
    ("scaler", StandardScaler()),
    ("svm", SVC(
        kernel="rbf",
        C=100,
        gamma=0.25
    ))
])

print("\n=== FINAL MODEL START ===")
start = time.time()

model.fit(X_train, y_train)

end = time.time()

print("\n=== FINAL MODEL DONE ===")
print("Training time: %.2f detik" % (end - start))


scaler = model.named_steps["scaler"]
svm_model = model.named_steps["svm"]

print("\n===== SCALING =====")
print("MEAN :", scaler.mean_)
print("STD  :", scaler.scale_)

print("\n===== SVM INFO =====")
print("Kernel :", svm_model.kernel)
print("C      :", svm_model.C)
print("Gamma  :", svm_model.gamma)
print("Gamma actual :", svm_model._gamma)

y_pred = model.predict(X_test)

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


output_model = "C:/Users/pandy/Desktop/svm_rbf_fix.pkl"

joblib.dump(model, output_model)
