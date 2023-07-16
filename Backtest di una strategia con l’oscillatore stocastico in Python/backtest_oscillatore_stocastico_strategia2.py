import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')

df = yf.download("AAPL", start="2010-01-01", end="2020-01-01")
df['L14'] = df['Low'].rolling(window=14).min()
df['H14'] = df['High'].rolling(window=14).max()
df['%K'] = 100*((df['Close'] - df['L14']) / (df['H14'] - df['L14']) )
df['%D'] = df['%K'].rolling(window=3).mean()
# Sengali
df['Sell Entry'] = ((df['%K'] < df['%D']) & (df['%K'].shift(1) > df['%D'].shift(1))) & (df['%D'] > 80)
df['Buy Entry'] = ((df['%K'] > df['%D']) & (df['%K'].shift(1) < df['%D'].shift(1))) & (df['%D'] < 20)
# Posizione
df['Position'] = np.nan
# posizione -1 per i segnali short
df.loc[df['Sell Entry'],'Position'] = -1
# posizione 1 per i segnali long
df.loc[df['Buy Entry'],'Position'] = 1
# posizione iniziale flat
df['Position'].iloc[0] = 0
# Riempimento in avanti per simulare il mantenimento delle posizioni
df['Position'] = df['Position'].fillna(method='ffill')
# Rendimenti giornalieri di Apple
df['Market Returns'] = df['Close'].pct_change()
# Calcola i rendimenti della strategia moltiplicando i rendimenti di Apple per le posizioni del giorno precedente
df['Strategy Returns'] = df['Market Returns'] * df['Position'].shift(1)
# Grafico dei rendimenti
df[['Strategy Returns','Market Returns']].cumsum().plot(figsize=(20,10))
plt.show()