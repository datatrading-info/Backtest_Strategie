import math
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib as mpl

mpl.style.use('bmh')
import matplotlib.pylab as plt

import statsmodels.api as sm
from pykalman import KalmanFilter
import yahooquery

# Otteniamo il risultato dello screener di yahoo per il settore tecnologico per i primi 50 ticker
s = yahooquery.Screener()
data = s.get_screeners('information_technology_services', count=50)
# Inseriamo il risultato in un dataframe Pandas
df = pd.DataFrame(data['information_technology_services']['quotes'])
# Creiamo la lista dei ticker dal dataframe
stocks = df['symbol'].dropna().tolist()
# Creaiamo una lista vouta per memorizzare i prezzi storici dei ticker
df_list = []
# Creiamo una lista dei ticker per cui abbiamo ottenuto i dati storici
used_stocks = []
# Ciclo sulla lista dei ticker per scaricari i dati storici e memorizzarli in una lista
for stock in stocks:
    try:
        data = yahooquery.Ticker(stock).history(start='2010-01-01', end='2020-01-01')['close']
        data.reset_index(level=0, drop=True, inplace=True)
        data.name = stock
        df_list.append(data)
        used_stocks.append(stock)
    except:
        pass
# Concatena la lista dei dataframe individuali dei prezzi dei ticker in un unico dataframe
df = pd.concat(df_list, axis=1)
# Rimuoviamo tutti i ticker che non hanno abbastanza storico nel periodo considerato
df = df.dropna(axis=1)

df.plot(figsize=(20, 10))


# LA SOGLIA CRITICA PER IL TEST DI COINTEGRAZIONE E' STATO IMPOSTATO AL 5%
def find_cointegrated_pairs(dataframe, critial_level=0.05):
    n = dataframe.shape[1]  # lunghezza del dateframe
    pvalue_matrix = np.ones((n, n))  # inizializza la matrice dei risultati
    keys = dataframe.columns  # ottiene il nome delle colonne
    pairs = []  # inizializza la lista delle coppie di ticker
    for i in range(n):
        for j in range(i + 1, n):  # con j > i
            stock1 = dataframe[keys[i]]  # prezzi dello "stock1"
            stock2 = dataframe[keys[j]]  # prezzi dello "stock2"
            result = sm.tsa.stattools.coint(stock1, stock2)  # calcolo cointegrazione
            pvalue = result[1]  # memorizza il p-value
            pvalue_matrix[i, j] = pvalue
            if pvalue < critial_level:  # se il p-value è minore della soglia
                pairs.append((keys[i], keys[j], pvalue))  # memorizza la coppia di ticker con il p-value
    return pvalue_matrix, pairs


# Imposta lo split point per i "dati di addestramento" su cui eseguire il test di co-integrazione
# (i restanti dati verranno inviati alla funzione di backtest)
split = int(len(df) * .4)
# esegue la funzione di cointegrazionerun sul dataframe dei dati di addestramento
pvalue_matrix, pairs = find_cointegrated_pairs(df[:split])
# converte la matrice dei risultati in un dataframe
pvalue_matrix_df = pd.DataFrame(pvalue_matrix)
# usa Seaborn per il grafico della heatmap dei risultati
fig, ax = plt.subplots(figsize=(15, 10))
sns.heatmap(pvalue_matrix_df, xticklabels=df.columns.to_list(), yticklabels=df.columns.to_list(), ax=ax)

for pair in pairs:
    print("Stock {} and stock {} has a co-integration score of {}".format(pair[0], pair[1], round(pair[2], 4)))


def KalmanFilterAverage(x):
    # Construct a Kalman filter
    kf = KalmanFilter(transition_matrices=[1],
                      observation_matrices=[1],
                      initial_state_mean=0,
                      initial_state_covariance=1,
                      observation_covariance=1,
                      transition_covariance=.01)
    # Use the observed values of the price to get a rolling mean
    state_means, _ = kf.filter(x.values)
    state_means = pd.Series(state_means.flatten(), index=x.index)
    return state_means


# Regressione con filtro di Kalman
def KalmanFilterRegression(x, y):
    delta = 1e-3
    trans_cov = delta / (1 - delta) * np.eye(2)  # Oscillazione della random walk
    obs_mat = np.expand_dims(np.vstack([[x], [np.ones(len(x))]]).T, axis=1)
    kf = KalmanFilter(n_dim_obs=1, n_dim_state=2,  # y è a 1 dimensione, (alpha, beta) è a 2 dimensioni
                      initial_state_mean=[0, 0],
                      initial_state_covariance=np.ones((2, 2)),
                      transition_matrices=np.eye(2),
                      observation_matrices=obs_mat,
                      observation_covariance=2,
                      transition_covariance=trans_cov)
    # Usare l'osservazione y per ottenere le stime e gli errori per i parametri dello stato
    state_means, state_covs = kf.filter(y.values)
    return state_means


def half_life(spread):
    spread_lag = spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = int(round(-np.log(2) / res.params[1], 0))
    if halflife <= 0:
        halflife = 1
    return halflife

def backtest(df,s1, s2):
    #############################################################
    # INPUT:
    # DataFrame dei prezzi
    # s1: il simbolo del ticker 1
    # s2: il simbolo del ticker 2
    # x: la serie dei prezzi del ticker 1
    # y: la serie dei prezzi del ticker 2
    # OUTPUT:
    # df1['cum rets']: i rendimenti comulativi in un dataframe pandas
    # sharpe: Sharpe ratio
    # CAGR: Compound Annual Growth Rate
    x = df[s1]
    y = df[s2]
    # esecuzione della regressione (compreso il filtro di Kalman)
    # per trovare il hedge ratio e creare la serie degli spread
    df1 = pd.DataFrame({'y':y,'x':x})
    df1.index = pd.to_datetime(df1.index)
    state_means = KalmanFilterRegression(KalmanFilterAverage(x),KalmanFilterAverage(y))
    df1['hr'] = - state_means[:,0]
    df1['spread'] = df1.y + (df1.x * df1.hr)
    # calcolo half life
    halflife = half_life(df1['spread'])
    # calcolo dello z-score con la finestra del periodo pari a half life
    meanSpread = df1.spread.rolling(window=halflife).mean()
    stdSpread = df1.spread.rolling(window=halflife).std()
    df1['zScore'] = (df1.spread-meanSpread)/stdSpread
    ##############################################################
    # LOGICA DELLA STRATEGIA
    entryZscore = 2
    exitZscore = 0
    # impostazione dei setup long
    df1['long entry'] = ((df1.zScore < - entryZscore) & ( df1.zScore.shift(1) > - entryZscore))
    df1['long exit'] = ((df1.zScore > - exitZscore) & (df1.zScore.shift(1) < - exitZscore))
    df1['num units long'] = np.nan
    df1.loc[df1['long entry'], 'num units long'] = 1
    df1.loc[df1['long exit'], 'num units long'] = 0
    df1['num units long'].iat[0] = 0
    df1['num units long'] = df1['num units long'].fillna(method='pad')
    # impostazione dei setup short
    df1['short entry'] = ((df1.zScore > entryZscore) & ( df1.zScore.shift(1) < entryZscore))
    df1['short exit'] = ((df1.zScore < exitZscore) & (df1.zScore.shift(1) > exitZscore))
    df1.loc[df1['short entry'], 'num units short'] = -1
    df1.loc[df1['short exit'], 'num units short'] = 0
    df1['num units short'].iat[0] = 0
    df1['num units short'] = df1['num units short'].fillna(method='pad')
    df1['numUnits'] = df1['num units long'] + df1['num units short']
    df1['spread pct ch'] = (df1['spread'] - df1['spread'].shift(1)) / ((df1['x'] * abs(df1['hr'])) + df1['y'])
    df1['port rets'] = df1['spread pct ch'] * df1['numUnits'].shift(1)
    df1['cum rets'] = df1['port rets'].cumsum()
    df1['cum rets'] = df1['cum rets'] + 1
    ##############################################################
    sharpe = ((df1['port rets'].mean() / df1['port rets'].std()) * math.sqrt(252))
    if math.isnan(sharpe):
        sharpe = 0.0
    ##############################################################
    start_val = 1
    end_val = df1['cum rets'].iat[-1]
    start_date = df1.iloc[0].name
    end_date = df1.iloc[-1].name
    days = (end_date - start_date).days
    CAGR = round(((float(end_val) / float(start_val)) ** (252.0/days)) - 1,4)
    df1[s1+ " "+s2] = df1['cum rets']
    return df1[s1+" "+s2], sharpe, CAGR

results = []
for pair in pairs:
    rets, sharpe,  CAGR = backtest(df[split:], pair[0], pair[1])
    results.append(rets)
    print("The pair {} and {} produced a Sharpe Ratio of {} and a CAGR of {}".format(pair[0],pair[1],round(sharpe,2),round(CAGR,4)))
    rets.plot(figsize=(20,15),legend=True)


# Concatena le singole curve di equity in un solo dataframe
results_df = pd.concat(results,axis=1).dropna()
# Pesa equamente ogni equity dividendo per il numero di coppie nel dataframe
results_df /= len(results_df.columns)
# Somma le equity pesate per ottenere l'equity finale
final_res = results_df.sum(axis=1)
# Stampa il grafico della curva dell'equity finale
final_res.plot(figsize=(20,15))

# Calcola e stampa alcune statistiche dell'equity finale
sharpe = (final_res.pct_change().mean() / final_res.pct_change().std()) * (math.sqrt(252))
start_val = 1
end_val = final_res.iloc[-1]
start_date = final_res.index[0]
end_date = final_res.index[-1]
days = (end_date - start_date).days
CAGR = round(((float(end_val) / float(start_val)) ** (252.0/days)) - 1, 4)
print("Sharpe Ratio is {} and CAGR is {}".format(round(sharpe, 2), round(CAGR, 4)))

