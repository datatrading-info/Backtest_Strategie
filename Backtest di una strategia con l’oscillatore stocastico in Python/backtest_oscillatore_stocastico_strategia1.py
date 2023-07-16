import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')

# Download dei dati storici di Apple in un dataframe Pandas
df = yf.download("AAPL", start="2010-01-01", end="2020-01-01")
# Stampa le prime 5 righe del dataframe per controllare il formato
print(df.head())

# Calcolo dei minimi a finestra mobile dei 14 periodi precedenti
df['L14'] = df['Low'].rolling(window=14).min()
# Calcolo dei massimi a finestra mobile dei 14 periodi precedenti
df['H14'] = df['High'].rolling(window=14).max()
# Calcolo della linea %K
df['%K'] = 100*((df['Close'] - df['L14']) / (df['H14'] - df['L14']) )
# Calcolo della linea %D
df['%D'] = df['%K'].rolling(window=3).mean()

fig, axes = plt.subplots(nrows=2, ncols=1,figsize=(20,10))
df['Adj Close'].plot(ax=axes[0]); axes[0].set_title('Close')
df[['%K','%D']].plot(ax=axes[1]); axes[1].set_title('Oscillator')
plt.show()

# Crea i segnali d'entrata SHORT quando la linea %K attraversa al
# ribasso la linea %D e il valore è sopra gli 80
df['Sell Entry'] = ((df['%K'] < df['%D']) & (df['%K'].shift(1) > df['%D'].shift(1))) & (df['%D'] > 80)
# Crea i segnali d'uscita SHORT quando la linea %K attraversa al rialzo la linea %D
df['Sell Exit'] = ((df['%K'] > df['%D']) & (df['%K'].shift(1) < df['%D'].shift(1)))

# Crea le posizione SHORT (-1 per lo short e 0 per il flat) tramite i valori booleani
df['Short'] = np.nan
df.loc[df['Sell Entry'],'Short'] = -1
df.loc[df['Sell Exit'],'Short'] = 0

# Posizione flat per il giorno 1
df['Short'][0] = 0
# Riempimento in avanti delle posizioni per rappresentare il mantenimento delle posizioni a mercato
df['Short'] = df['Short'].fillna(method='pad')

# Crea i segnali d'entra LONG quando la linea %K attraversa al rialzo la linea %D e il valore è minore di 20
df['Buy Entry'] = ((df['%K'] > df['%D']) & (df['%K'].shift(1) < df['%D'].shift(1))) & (df['%D'] < 20)
# Crea i segnali d'uscita LONG quanto la linea %K attraversa al ribasso la linea %D
df['Buy Exit'] = ((df['%K'] < df['%D']) & (df['%K'].shift(1) > df['%D'].shift(1)))

# Crea le posizione LONG (1 per il long e 0 per il flat) tramite i valori booleani
df['Long'] = np.nan
df.loc[df['Buy Entry'],'Long'] = 1
df.loc[df['Buy Exit'],'Long'] = 0
# Posizione flat per il giorno 1
df['Long'][0] = 0
# Riempimento in avanti delle posizioni per rappresentare il mantenimento delle posizioni a mercato
df['Long'] = df['Long'].fillna(method='pad')

# Unisce le posizione long e short per ottenere le posizioni della strategia
# (1 per il long, -1 per lo short e 0 per il flat)
df['Position'] = df['Long'] + df['Short']

df['Position'].plot(figsize=(20,10))
plt.show()

# Calcola i rendimenti giornalieri di Apple
df['Market Returns'] = df['Close'].pct_change()
# Calcola i rendimenti della strategia moltiplicando i rendimenti di Apple per le posizioni del giorno precedente
df['Strategy Returns'] = df['Market Returns'] * df['Position'].shift(1)
# Grafico dei rendimenti
df[['Strategy Returns','Market Returns']].cumsum().plot()
plt.show()