import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle, os

np.random.seed(42)
n = 500

study    = np.random.uniform(0, 10, n)
attend   = np.random.uniform(30, 100, n)
prev     = np.random.uniform(30, 100, n)
sleep    = np.random.uniform(3, 10, n)
assign   = np.random.randint(0, 11, n)

score = (study*4 + attend*0.3 + prev*0.4 + sleep*1.5 + assign*2
         + np.random.normal(0, 5, n))
result = (score > np.percentile(score, 40)).astype(int)

df = pd.DataFrame({
    "study_hours":       study.round(1),
    "attendance_pct":    attend.round(1),
    "previous_score":    prev.round(1),
    "sleep_hours":       sleep.round(1),
    "assignments_done":  assign,
    "result":            result
})
df.to_csv("dataset.csv", index=False)

X = df.drop("result", axis=1)
y = df["result"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
acc = model.score(X_test, y_test)
print(f"Model Accuracy: {acc*100:.1f}%")

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)
with open("scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)
print("model.pkl and scaler.pkl saved!")
