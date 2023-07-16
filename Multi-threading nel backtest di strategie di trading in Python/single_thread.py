import numpy as np
import pandas as pd
import itertools
import time

# Funzione per calcolare lo Sharpe Ratio
def annualised_sharpe(returns, N=252):
    if returns.std() == 0:
        return 0
    return np.sqrt(N) * (returns.mean() / returns.std())

def ma_strat(data, short_ma, long_ma):
    # Calcolo dei valori delle SMA
    data['short_ma'] = np.round(data['Close'].rolling(window=short_ma).mean(),2)
    data['long_ma'] = np.round(data['Close'].rolling(window=long_ma).mean(),2)
    # Calcolo dello spread delle medie mobili
    data['short_ma-long_ma'] = data['short_ma'] - data['long_ma']
    # Imposta il numero di punti come soglia dello spread e
    # calcolo dello ''Stance' della strategia
    X = 5
    data['Stance'] = np.where(data['short_ma-long_ma'] > X, 1, 0)
    data['Stance'] = np.where(data['short_ma-long_ma'] < -X, -1, data['Stance'])
    data['Stance'].value_counts()
    # Calcolo dei rendimenti logaritmici giornalieri per i prezzi e per la strategia
    data['Market Returns'] = np.log(data['Close'] / data['Close'].shift(1))
    data['Strategy'] = data['Market Returns'] * data['Stance'].shift(1)
    # Calcolo della curva equity
    data['Strategy Equity'] = data['Strategy'].cumsum()
    # Calcolo dello Sharpe Ratio
    try:
        sharpe = annualised_sharpe(data['Strategy'])
    except:
        sharpe = 0
    return data['Strategy'].cumsum(), sharpe, data['Strategy'].mean(), data['Strategy'].std()


def monte_carlo_strat(data, inputs, iters):
    # Numero di giorni per ogni simulazione Monte Carlo
    days = 252

    # Backtest della strategia con i parametri della funzione
    # e memorizzazione dei risultati
    perf, sharpe, mu, sigma = ma_strat(data, inputs[0], inputs[1])

    # Crea 2 liste vuote per memorizzare i risultati delle simulazioni MC
    mc_results = []
    mc_results_final_val = []
    # Esegue il numero di simulazione MC e memorizza i risultati
    for j in range(iters):
        daily_returns = np.random.normal(mu, sigma, days) + 1
        price_list = [1]
        for x in daily_returns:
            price_list.append(price_list[-1] * x)

        # Memorizza la serie dei prezzi di ogni simulazione
        mc_results.append(price_list)
        # Memorizza solo il valore finale di ogni serie di prezzi
        mc_results_final_val.append(price_list[-1])
    return (inputs, perf, sharpe, mu, sigma, mc_results, mc_results_final_val)


if __name__ == '__main__':

    # Legge i dati dei prezzi
    data = pd.read_csv('F.csv', index_col='Date', dayfirst=True, parse_dates=True)

    # Genera la lista dei possibili valori per la media mobile breve
    short_mas = np.linspace(20, 50, 30, dtype=int)

    # Genera la lista dei possibili valori per la media mobile lunga
    long_mas = np.linspace(100, 200, 30, dtype=int)

    # Genera la lista di tuple che contengono tutte le possibile combinazioni
    # dei periodi delle medie mobili
    mas_combined = list(itertools.product(short_mas, long_mas))

    # Numero di simulazioni MC per l'ottimizzazione dei backtest
    iters = 2000

    # Crea una lista vuota
    results = []

    # tempo di inizio
    start_time = time.time()

    # iterazione attraverso la lista dei valori per le MA ed esegue la funzione
    for inputs in mas_combined:
        res = monte_carlo_strat(data, inputs, iters)
        results.append(res)

    # Stampa il numero di secondi impiegati dal processo
    print("MP--- %s seconds for single---" % (time.time() - start_time))