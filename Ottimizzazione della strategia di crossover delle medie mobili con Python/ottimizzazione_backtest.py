import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')


def ma_strat(sp500, short_ma, long_ma):
    # Legge i dati da Yahoo Finance per il ticker
    sp500['short_ma'] = np.round(sp500['Close'].rolling(window=short_ma).mean(), 2)
    sp500['long_ma'] = np.round(sp500['Close'].rolling(window=long_ma).mean(), 2)

    # Crea la colonna con lo spread di differenza della media mobile
    sp500['short_ma-long_ma'] = sp500['short_ma'] - sp500['long_ma']

    # Imposta il numero desidarto della soglia per la differenza dello spread
    # e crea la colonna 'Stance'
    X = 50
    sp500['Stance'] = np.where(sp500['short_ma-long_ma'] > X, 1, 0)
    sp500['Stance'] = np.where(sp500['short_ma-long_ma'] < -X, -1, sp500['Stance'])
    sp500['Stance'].value_counts()

    # Crea le colonne per i rendimenti logaritmici giornalieri del ticker e i
    # rendimenti logaritmici giornalieri della strategia
    sp500['Market Returns'] = np.log(sp500['Close'] / sp500['Close'].shift(1))
    sp500['Strategy'] = sp500['Market Returns'] * sp500['Stance'].shift(1)

    # Imposta l'equity iniziale della strategia a 1 e genera la curva equity
    sp500['Strategy Equity'] = sp500['Strategy'].cumsum() + 1

    sharpe = annualised_sharpe(sp500['Strategy'])

    return (sp500['Strategy'].cumsum()[-1], sharpe)


# Funzione per calcolare lo Sharpe Ratio - l'elemento Risk free rate è escluso per semplicità
def annualised_sharpe(returns, N=252):
    return np.sqrt(N) * (returns.mean() / returns.std())


short_ma = np.linspace(10, 60, 25, dtype=int)
long_ma = np.linspace(220, 270, 25, dtype=int)

results_pnl = np.zeros((len(short_ma), len(long_ma)))
results_sharpe = np.zeros((len(short_ma), len(long_ma)))

sp500 = yf.download('^GSPC', start='2000-01-01', end='2020-01-01')

for i, shortma in enumerate(short_ma):
    for j, longma in enumerate(long_ma):
        pnl, sharpe = ma_strat(sp500,shortma,longma)
        results_pnl[i,j] = pnl
        results_sharpe[i,j] = sharpe

plt.pcolor(short_ma,long_ma,results_pnl)
plt.colorbar()
plt.show()

plt.pcolor(short_ma,long_ma,results_sharpe)
plt.colorbar()
plt.show()
print("")