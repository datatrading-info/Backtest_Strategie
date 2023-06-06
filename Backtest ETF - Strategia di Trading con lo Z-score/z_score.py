from datetime import datetime
import pandas as pd
import numpy as np
from numpy import log, polyfit, sqrt, std, subtract
import statsmodels.tsa.stattools as ts
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')


meanSpread = df1.spread.rolling(window=halflife).mean()
stdSpread = df1.spread.rolling(window=halflife).std()

#############################################################

df1['zScore'] = (df1.spread - meanSpread) / stdSpread

df1['zScore'].plot()

entryZscore = 2
exitZscore = 0

# calcolo num units long
df1['long entry'] = ((df1.zScore < - entryZscore) & (df1.zScore.shift(1) > - entryZscore))
df1['long exit'] = ((df1.zScore > - exitZscore) & (df1.zScore.shift(1) < - exitZscore))
df1['num units long'] = np.nan
df1.loc[df1['long entry'], 'num units long'] = 1
df1.loc[df1['long exit'], 'num units long'] = 0
df1['num units long'][0] = 0
df1['num units long'] = df1['num units long'].fillna(method='pad')
# calcolo num units short
df1['short entry'] = ((df1.zScore > entryZscore) & (df1.zScore.shift(1) < entryZscore))
df1['short exit'] = ((df1.zScore < exitZscore) & (df1.zScore.shift(1) > exitZscore))
df1.loc[df1['short entry'], 'num units short'] = -1
df1.loc[df1['short exit'], 'num units short'] = 0
df1['num units short'][0] = 0
df1['num units short'] = df1['num units short'].fillna(method='pad')

df1['numUnits'] = df1['num units long'] + df1['num units short']
df1['spread pct ch'] = (df1['spread'] - df1['spread'].shift(1)) / ((df1['x'] * abs(df1['hr'])) + df1['y'])
df1['port rets'] = df1['spread pct ch'] * df1['numUnits'].shift(1)

df1['cum rets'] = df1['port rets'].cumsum()
df1['cum rets'] = df1['cum rets'] + 1

plt.plot(df1['cum rets'])
plt.xlabel("EWC")
plt.ylabel("EWA")
plt.show()

sharpe = ((df1['port rets'].mean() / df1['port rets'].std()) * sqrt(252))

start_val = 1
end_val = df1['cum rets'].iat[-1]

start_date = df1.iloc[0].name
end_date = df1.iloc[-1].name
days = (end_date - start_date).days

CAGR = round(((float(end_val) / float(start_val)) ** (252.0 / days)) - 1, 4)

print("CAGR = {}%".format(CAGR * 100))
print("Sharpe Ratio = {}".format(round(sharpe, 2)))

print("")