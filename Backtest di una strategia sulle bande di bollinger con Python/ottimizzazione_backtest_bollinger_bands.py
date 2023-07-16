
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')

# Download data del Dat dal 2015 in un dataframe Pandas
df = yf.download("^GDAXI", start="2015-01-01", end="2020-01-01")
print(df.head())


def bollinger_strat(df, window, std):
    # Calcolo della media mobile e deviazione standard
    rolling_mean = df['Adj Close'].rolling(window).mean()
    rolling_std = df['Adj Close'].rolling(window).std()

    df['Bollinger High'] = rolling_mean + (rolling_std * std)
    df['Bollinger Low'] = rolling_mean - (rolling_std * std)

    df['Short'] = None
    df['Long'] = None
    df['Position'] = None

    for row in range(len(df)):

        if (df['Adj Close'].iloc[row] > df['Bollinger High'].iloc[row]) and (
                df['Adj Close'].iloc[row - 1] < df['Bollinger High'].iloc[row - 1]):
            df['Position'].iloc[row] = -1

        if (df['Adj Close'].iloc[row] < df['Bollinger Low'].iloc[row]) and (
                df['Adj Close'].iloc[row - 1] > df['Bollinger Low'].iloc[row - 1]):
            df['Position'].iloc[row] = 1

    df['Position'].fillna(method='ffill', inplace=True)

    df['Market Return'] = np.log(df['Adj Close'] / df['Adj Close'].shift(1))
    df['Strategy Return'] = df['Market Return'] * df['Position'].shift(1)

    df['Strategy Return'].cumsum().plot()

bollinger_strat(df,50,2)
plt.show()
print("")

# Imposta i vettori per "periodo di giorni" e "numero di deviazione standard".
# Ad esempio il primo crea un vettore di 20 valori interi equidistanti che vanno da 10 a 100
# Il secondo crea un vettore di 10 numeri in virgola mobile equidistanti da 1 a 3
windows = np.linspace(10,100,20,dtype=int)
stds = np.linspace(1,3,10)

# Ciclo su entrambi i vettore e esecuzione del backtest per ogni combinazione di valori
for window in windows:
    for std in stds:
        bollinger_strat(df,window,std)

plt.show()
print("")