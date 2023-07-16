import pandas as pd
import numpy as np
from math import sqrt
import matplotlib.pyplot as plt
import yfinance as yf

# scarico di dati da Yahoo Finance in un dataframe e calcolo delle medie mobili
sp500 = yf.download('^GSPC', start='2000-01-01', end='2020-01-01')
sp500['42d'] = np.round(sp500['Close'].rolling(window=42).mean(), 2)
sp500['252d'] = np.round(sp500['Close'].rolling(window=252).mean(), 2)

# Creo la colonna con la differenza tra le medie mobili
sp500['42-252'] = sp500['42d'] - sp500['252d']

# importo il numero di punti come soglia dello spread tra le medie mobili
# e creo la colonna con lo 'Stance' della strategia
X = 50
sp500['Stance'] = np.where(sp500['42-252'] > X, 1, 0)
sp500['Stance'] = np.where(sp500['42-252'] < X, -1, sp500['Stance'])
sp500['Stance'].value_counts()

# creo le colonne con i rendimenti logaritmici giornalieri dei prezzi e della strategia
sp500['Market Returns'] = np.log(sp500['Close'] / sp500['Close'].shift(1))
sp500['Strategy'] = sp500['Market Returns'] * sp500['Stance'].shift(1)

# importo l'equity iniziare della strategia a 1 (100%) e genero la curva di equity
sp500['Strategy Equity'] = sp500['Strategy'].cumsum() + 1
sp500.dropna(subset=['Strategy Equity'], inplace=True)

# grafico della curva di equity
sp500['Strategy Equity'].plot()

strat = pd.DataFrame([sp500['Strategy Equity'], sp500['Strategy']]).transpose()

# crea le colonne che identificato i giorni con rendimenti positivi, negativi o flat
strat['win'] = (np.where(strat['Strategy'] > 0, 1, 0))
strat['loss'] = (np.where(strat['Strategy'] < 0, 1, 0))
strat['scratch'] = (np.where(strat['Strategy'] == 0, 1, 0))

# crea le colonne con le somme comulative dei rendimenti giornalieri
strat['wincum'] = (np.where(strat['Strategy'] > 0, 1, 0)).cumsum()
strat['losscum'] = (np.where(strat['Strategy'] < 0, 1, 0)).cumsum()
strat['scratchcum'] = (np.where(strat['Strategy'] == 0, 1, 0)).cumsum()

# crea una colonna che somma i rendimenti dei giorni di trading
# usiamo questa colonna per creare le percentuali
strat['days'] = (strat['wincum'] + strat['losscum'] + strat['scratchcum'])
# crea le colonne che mostra la somma dei giorni positivi, negativi e flat con finestra mobile a 252 giorni
strat['rollwin'] = strat['win'].rolling(window=252).sum()
strat['rollloss'] = strat['loss'].rolling(window=252).sum()
strat['rollscratch'] = strat['scratch'].rolling(window=252).sum()

# crea le colonne con i dati del hit ratio e loss ratio
strat['hitratio'] = strat['wincum'] / (strat['wincum'] + strat['losscum'])
strat['lossratio'] = 1 - strat['hitratio']

# crea le colonne con i dati del hit ratio e loss ratio con finestra mobile a 2252 giorni
strat['rollhitratio'] = strat['hitratio'].rolling(window=252).mean()
strat['rolllossratio'] = 1 - strat['rollhitratio']

# crea la colonna che i redimenti a finestra mobile di 12 mesi
strat['roll12mret'] = strat['Strategy'].rolling(window=252).sum()

# crea le colonne con le vincite medie, le perdite medie e i redimenti medi giornalieri
strat['averagewin'] = strat['Strategy'][(strat['Strategy'] > 0)].mean()
strat['averageloss'] = strat['Strategy'][(strat['Strategy'] < 0)].mean()
strat['averagedailyret'] = strat['Strategy'].mean()

# crea le colonne con la deviazione standard e la deviazione standard annualizzate
# con finestra mobile a 1 anno
strat['roll12mstdev'] = strat['Strategy'].rolling(window=252).std()
strat['roll12mannualisedvol'] = strat['roll12mstdev'] * sqrt(252)

strat['roll12mannualisedvol'].plot(grid=True, figsize=(8, 5), title='Rolling 1 Year Annualised Volatility')

strat['rollhitratio'].plot(grid=True, figsize=(8, 5), title='Rolling 1 Year Hit Ratio')

strat['roll12mret'].plot(grid=True, figsize=(8, 5), title='Rolling 1 Year Returns')

strat['Strategy'].plot(grid=True, figsize=(8, 5), title='Daily Returns')

strat['Strategy'].plot(kind='hist', figsize=(8, 5), title='Daily Return Distribution', bins=100)

print("Skew:", round(strat['Strategy'].skew(), 4))
print("Kurtosis:", round(strat['Strategy'].kurt(), 4))

# Crea un nuovo DataFrame per i dati mensili e popolalo con i dati della colonna dei rendimenti
# giornalieri del DataFrame originale e sommati per mese
stratm = pd.DataFrame(strat['Strategy'].resample('M').sum())

# Costruisce la curva equity mensile
stratm['Strategy Equity'] = stratm['Strategy'].cumsum() + 1

# Crea un indice numerico per i mesi (es. Gen = 1, Feb = 2 etc)
stratm['month'] = stratm.index.month

print(stratm.head(15))

print("\n1) Rendimento annualizzato")
days = (strat.index[-1] - strat.index[0]).days
cagr = ((((strat['Strategy Equity'][-1]) / strat['Strategy Equity'][1])) ** (365.0 / days)) - 1
print('CAGR =', str(round(cagr, 4) * 100) + "%")

print("\n2) Rendimenti ultimi 12 mesi")
stratm['last12mret'] = stratm['Strategy'].rolling(window=12, center=False).sum()
last12mret = stratm['last12mret'][-1]
print('last 12 month return =', str(round(last12mret * 100, 2)) + "%")

print("\n3) Volatilità")
voldaily = (strat['Strategy'].std()) * sqrt(252)
volmonthly = (stratm['Strategy'].std()) * sqrt(12)
print('Annualised volatility using daily data =', str(round(voldaily, 4) * 100) + "%")
print('Annualised volatility using monthly data =', str(round(volmonthly, 4) * 100) + "%")

print("\n4) Sharpe Ratio")
dailysharpe = cagr / voldaily
monthlysharpe = cagr / volmonthly
print('daily Sharpe =', round(dailysharpe, 2))
print('monthly Sharpe =', round(monthlysharpe, 2))

print("\n5) Maxdrawdown")
# Funzione per calcolare il drawdown massimo
def max_drawdown(X):
    mdd = 0
    peak = X[0]
    for x in X:
        if x > peak:
            peak = x
        dd = (peak - x) / peak
        if dd > mdd:
            mdd = dd
    return mdd
mdd_daily = max_drawdown(strat['Strategy Equity'])
mdd_monthly = max_drawdown(stratm['Strategy Equity'])
print('max drawdown daily data =', str(round(mdd_daily, 4) * 100) + "%")
print('max drawdown monthly data =', str(round(mdd_monthly, 4) * 100) + "%")

print("\n6) Calmar Ratio")
calmar = cagr / mdd_daily
print('Calmar ratio =', round(calmar, 2))

print("\n7) Volatilitè / Drawdown Massimo")
vol_dd = volmonthly / mdd_daily
print('Volatility / Max Drawdown =', round(vol_dd, 2))

print("\n8) Migliore performance mensile")
bestmonth = max(stratm['Strategy'])
print('Best month =', str(round(bestmonth, 2)) + "%")

print("\n9) Peggior performance mensile")
worstmonth = min(stratm['Strategy'])
print('Worst month =', str(round(worstmonth, 2) * 100) + "%")

print("\n10) % di mesi redditizi e % mesi non redditizi")
positive_months = len(stratm['Strategy'][stratm['Strategy'] > 0])
negative_months = len(stratm['Strategy'][stratm['Strategy'] < 0])
flatmonths = len(stratm['Strategy'][stratm['Strategy'] == 0])
perc_positive_months = positive_months / (positive_months + negative_months + flatmonths)
perc_negative_months = negative_months / (positive_months + negative_months + flatmonths)
print('% of Profitable Months =', str(round(perc_positive_months, 2) * 100) + "%")
print('% of Non-profitable Months =', str(round(perc_negative_months, 2) * 100) + "%")

print("\n11) Numero di mesi redditizi/Numero di mesi non redditizi")
prof_unprof_months = positive_months / negative_months
print('Number of Profitable Months/Number of Non Profitable Months', round(prof_unprof_months, 2))

print("\n12) Profitto mensile medio")
av_monthly_pos = (stratm['Strategy'][stratm['Strategy'] > 0]).mean()
print('Average Monthly Profit =', str(round(av_monthly_pos, 4) * 100) + "%")

print("\n13) Perdita mensile media")
av_monthly_neg = (stratm['Strategy'][stratm['Strategy'] < 0]).mean()
print('Average Monthly Loss =', str(round(av_monthly_neg * 100, 2)) + "%")

print("\n14) Profitto mensile medio/Perdita mensile media")
pos_neg_month = abs(av_monthly_pos / av_monthly_neg)
print('Average Monthly Profit/Average Monthly Loss', round(pos_neg_month, 4))

monthly_table = stratm[['Strategy','month']].pivot_table(stratm[['Strategy','month']], index=stratm.index,
                                                         columns='month', aggfunc=np.sum).resample('A')
monthly_table = monthly_table.aggregate('sum')

# Elimina l'indice della colonna di livello superiore che corrispone a "Strategy"
monthly_table.columns = monthly_table.columns.droplevel()

# Sostituisce le date nell'indice con l'anno corrispondente
monthly_table.index = monthly_table.index.year

# Sostituisce l'intero nell'intestazione delle colonne con il formato MMM
monthly_table.columns = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic']

monthly_table.to_csv("mesi.csv")