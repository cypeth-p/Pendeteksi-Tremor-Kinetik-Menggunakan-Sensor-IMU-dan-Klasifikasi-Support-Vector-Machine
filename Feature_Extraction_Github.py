import pandas as pd
import numpy as np

data = pd.read_csv("datasets_complete.csv")

print("Kolom dataset:", data.columns)

ax = data["aX"]
ay = data["aY"]
az = data["aZ"]

label_col = data["Label"]

mag = np.sqrt(ax**2 + ay**2 + az**2)

#window param (fix 600)
window_size = 600
step = 50

features = []

def MAV(x):
    return np.mean(np.abs(x))

def RMS(x):
    return np.sqrt(np.mean(np.square(x)))

def WL(x):
    return np.sum(np.abs(np.diff(x)))

def DASDV(x):
    diff = np.diff(x)
    return np.sqrt(np.mean(np.square(diff)))

for i in range(0, len(mag) - window_size + 1, step):

    window = mag.iloc[i:i + window_size]

    mav = MAV(window)
    rms = RMS(window)
    wl = WL(window)
    dasdv = DASDV(window)

    label = label_col.iloc[i:i + window_size].mode()[0]

    features.append([mav, rms, wl, dasdv, label])

df = pd.DataFrame(
    features,
    columns=["MAV", "RMS", "WL", "DASDV", "Label"]
)

df.to_csv("C:/Users/pandy/Desktop/featext/4feature600.csv", index=False)

print("Total data:", len(df))
print(df.head())