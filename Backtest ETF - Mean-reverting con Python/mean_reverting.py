from datetime import datetime
import pandas as pd
import numpy as np
from numpy import log, polyfit, sqrt, std, subtract
import statsmodels.tsa.stattools as ts
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
import pprint
import yfinance as yf

# Scegliere la coppia di ticker per il testing
symbList = ['EWA', 'EWC']
start_date = '2012-01-01'
end_date = '2020-01-01'

# Download i dati da Yahoo Finance
y = yf.download(symbList[0], start=start_date, end=end_date)
x = yf.download(symbList[1], start=start_date, end=end_date)

# Rinomina le colonne
y.rename(columns={'Adj Close': 'price'}, inplace=True)
x.rename(columns={'Adj Close': 'price'}, inplace=True)

# Verificare che i dataframe sono della stessa lunghezza
min_date = max(df.dropna().index[0] for df in [y, x])
max_date = min(df.dropna().index[-1] for df in [y, x])
y = y[(y.index >= min_date) & (y.index <= max_date)]
x = x[(x.index >= min_date) & (x.index <= max_date)]

# Grafico delle serie
plt.plot(y.price, label=symbList[0])
plt.plot(x.price, label=symbList[1])
plt.ylabel('Price')
plt.xlabel('Time')
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
plt.show()

sns.jointplot(y=y.price, x=x.price, color='b')
plt.show()

# esegue la regressione dei minimi quadrati ordinari per trovare
# il rapporto di copertura e quindi creare serie di spread
df1 = pd.DataFrame({'y': y['price'], 'x': x['price']})
est = sm.OLS(df1.y, df1.x)
est = est.fit()
df1['hr'] = -est.params[0]
df1['spread'] = df1.y + (df1.x * df1.hr)

plt.plot(df1.spread)
plt.show()

cadf = ts.adfuller(df1.spread)
print('Augmented Dickey Fuller test statistic =', cadf[0])
print('Augmented Dickey Fuller p-value =', cadf[1])
print('Augmented Dickey Fuller 1%, 5% and 10% test statistics =', cadf[4])


def hurst(ts):
    """
    Restituisce l'Esponente Hurst Exponent del vettore della serie temporale ts
    """
    # Crea il range dei valori ritardati
    lags = range(2, 100)

    # Calcola l'array delle variance delle differenze dei ritardi
    tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]

    # Usa una regressione lineare per stimare l'Esponente di Hurst
    poly = polyfit(log(lags), log(tau), 1)

    # Restituisce l'Esponente di Hurst dall'output di polyfit
    return poly[0] * 2.0

print("Hurst Exponent =",round(hurst(df1.spread.to_list()),2))

# Calcolo della regressione OLS per la serie degli spread e la sua versione ritardata
spread_lag = df1.spread.shift(1)
spread_lag.iloc[0] = spread_lag.iloc[1]
spread_ret = df1.spread - spread_lag
spread_ret.iloc[0] = spread_ret.iloc[1]
spread_lag2 = sm.add_constant(spread_lag)
model = sm.OLS(spread_ret,spread_lag2)
res = model.fit()

halflife = round(-np.log(2) / res.params[1],0)
print('Halflife = ',halflife)