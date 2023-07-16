
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')

# Download data del Dax dal 2015 in un dataframe Pandas
df = yf.download("^GDAXI", start="2015-01-01", end="2020-01-01")
print(df.head())

# Imposta il numero di giorni e la deviazione standard da usare per
# il calcolo delle bande delle bollinger
window = 21
no_of_std = 2

# Calcolo della media mobile e deviazione standard
rolling_mean = df['Adj Close'].rolling(window).mean()
rolling_std = df['Adj Close'].rolling(window).std()

# Calcolo della banda superiore e inferiore di bollinger
df['Rolling Mean'] = rolling_mean
df['Bollinger High'] = rolling_mean + (rolling_std * no_of_std)
df['Bollinger Low'] = rolling_mean - (rolling_std * no_of_std)

df[['Adj Close', 'Bollinger High', 'Bollinger Low']].plot()
plt.show()

# Creo una colonna per memorizzare i segnali/posizioni
df['Position'] = None

# Impostazione la posizione a -1 (short( quando il prezzo raggiunge la banda
# superiore e a +1 (buy) quando si raggiungere la banda inferiore
for row in range(len(df)):

    if (df['Adj Close'].iloc[row] > df['Bollinger High'].iloc[row]) and (
            df['Adj Close'].iloc[row - 1] < df['Bollinger High'].iloc[row - 1]):
        df['Position'].iloc[row] = -1

    if (df['Adj Close'].iloc[row] < df['Bollinger Low'].iloc[row]) and (
            df['Adj Close'].iloc[row - 1] > df['Bollinger Low'].iloc[row - 1]):
        df['Position'].iloc[row] = 1

# Riempimento in avanti delle posizioni per sostitu*ire i valori "None" con le posizioni
# long/short che rappresentano il mantenimento delle posizioni aparte in precedenza
df['Position'].fillna(method='ffill', inplace=True)

# Calcolo dei rendimenti giornalieri dei prezzi e moltiplicazione
# con la posizione per determinare i rendimenti della strategia
df['Market Return'] = np.log(df['Adj Close'] / df['Adj Close'].shift(1))
df['Strategy Return'] = df['Market Return'] * df['Position'].shift(1)

# Grafico dei rendimenti della strategia
df['Strategy Return'].cumsum().plot()
plt.show()
print("")


def bollinger_strat(df, window, std):
    rolling_mean = df['Settle'].rolling(window).mean()
    rolling_std = df['Settle'].rolling(window).std()

    df['Bollinger High'] = rolling_mean + (rolling_std * no_of_std)
    df['Bollinger Low'] = rolling_mean - (rolling_std * no_of_std)

    df['Short'] = None
    df['Long'] = None
    df['Position'] = None

    for row in range(len(df)):

        if (df['Settle'].iloc[row] > df['Bollinger High'].iloc[row]) and (
                df['Settle'].iloc[row - 1] < df['Bollinger High'].iloc[row - 1]):
            df['Position'].iloc[row] = -1

        if (df['Settle'].iloc[row] < df['Bollinger Low'].iloc[row]) and (
                df['Settle'].iloc[row - 1] > df['Bollinger Low'].iloc[row - 1]):
            df['Position'].iloc[row] = 1

    df['Position'].fillna(method='ffill', inplace=True)

    df['Market Return'] = np.log(df['Settle'] / df['Settle'].shift(1))
    df['Strategy Return'] = df['Market Return'] * df['Position'].shift(1)

    df['Strategy Return'].cumsum().plot()