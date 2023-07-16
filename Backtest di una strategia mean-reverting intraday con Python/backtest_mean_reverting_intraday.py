import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yfinance as yf
from math import sqrt

# Assicurara che il file NYSE.txt sia nella stessa cartella dello script
stocks = pd.read_csv('NYSE.txt',delimiter="\t")
# Creao una lista vuota per i ticker azionari
stocks_list = []
# Iterazione tramite il dataframe pandas e aggiunta dei ticker nella lista
for symbol in stocks['Symbol']:
    stocks_list.append(symbol)

print(len(stocks_list))

# Crea una lista vuota
frames = []

for stock in stocks_list:
    try:
        # Download dei dati delle azioni in DataFrame
        df = yf.download(stock, start='2000-01-01', end='2020-01-01')
        # Crea la deviazione standard mobile a 90 giorni
        df['Stdev'] = df['Close'].rolling(window=90).std()
        # Crea la media mobile a 20 giorni
        df['Moving Average'] = df['Close'].rolling(window=20).mean()
        # Verifica se il gap tra il minimo del giorno precedente e l'apertura
        # odierna è maggiore della deviazione standard a 90 giorni
        df['Criteria1'] = (df['Open'] - df['Low'].shift(1)) < -df['Stdev']
        # Verifica se il prezzo di apertura è maggiore della media mobile a 20 giorni
        df['Criteria2'] = df['Open'] > df['Moving Average']
        # Segnale BUY se entrambi i criteri sono veri
        df['BUY'] = df['Criteria1'] & df['Criteria2']
        # Calcola i rendimenti giornalieri percentuali delle azioni
        df['Pct Change'] = (df['Close'] - df['Open']) / df['Open']
        # Redimenti della strategia usando i rendimenti giornalieri delle
        # azioni quando abbiamo un segnale BUY
        df['Rets'] = df['Pct Change'][df['BUY'] == True]
        # Aggiungere il rendimento della strategia alla lista
        frames.append(df['Rets'])
    except:
        pass

# Concate i singoli dataframe della nostra lista lungo l'asse delle colonne
masterFrame = pd.concat(frames,axis=1)
# Crea la somma dei rendimenti giornalieri delle singole strategie
masterFrame['Total'] = masterFrame.sum(axis=1)
# Conteggia il numero di titoli che sono tradate ogni giorno
masterFrame['Count'] = masterFrame.count(axis=1) - 1
# Divide il rendimenti giornalieri "totali" per il numero di titoli che sono
# tradati ogni giorno per ottenere i rendimenti equamente pesati.
masterFrame['Return'] = masterFrame['Total'] / masterFrame['Count']

masterFrame['Return'].dropna().cumsum().plot()
plt.show()

SharpeRatio = (masterFrame['Return'].mean() *252) / (masterFrame['Return'].std() * (sqrt(252)))
print(SharpeRatio)

Annual_Return = (masterFrame['Return'].dropna().cumsum()[-1]+1)**(365.0/252) - 1
print(Annual_Return)