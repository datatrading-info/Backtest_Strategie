import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')

sp500 = yf.download('^GSPC', start='2000-01-01', end='2020-01-01')

print(sp500.head())

sp500['Close'].plot(grid=True,figsize=(8,5))

sp500['42d'] = np.round(sp500['Close'].rolling(window=42).mean(),2)
sp500['252d'] = np.round(sp500['Close'].rolling(window=252).mean(),2)

sp500[['Close','42d','252d']].plot(grid=True,figsize=(8,5))

sp500['42-252'] = sp500['42d'] - sp500['252d']

X = 50
sp500['Stance'] = np.where(sp500['42-252'] > X, 1, 0)
sp500['Stance'] = np.where(sp500['42-252'] < -X, -1, sp500['Stance'])
print(sp500['Stance'].value_counts())

sp500['Stance'].plot(lw=1.5,ylim=[-1.1,1.1])

sp500['Market Returns'] = np.log(sp500['Close'] / sp500['Close'].shift(1))
sp500['Strategy'] = sp500['Market Returns'] * sp500['Stance'].shift(1)

sp500[['Market Returns','Strategy']].cumsum().plot(grid=True,figsize=(8,5))

