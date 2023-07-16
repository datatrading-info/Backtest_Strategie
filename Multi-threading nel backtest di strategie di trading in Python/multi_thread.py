import numpy as np
import pandas as pd
import itertools
from multiprocessing.pool import ThreadPool as Pool
import time

# Funzione per calcolare lo Sharpe Ratio
def annualised_sharpe(returns, N=252):
    if returns.std() == 0:
        return 0
    return np.sqrt(N) * (returns.mean() / returns.std())

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(itertools.islice(it, size)), ())

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

    # Ciclo attraverso un sottoinsieme della lista delle tuple
    for input_slice in inputs:
        # Backtest della strategia con i parametri della funzione
        # e memorizzazione dei risultati
        perf, sharpe, mu, sigma = ma_strat(data, input_slice[0], input_slice[1])

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


def parallel_monte_carlo(data, inputs, iters):
    pool = Pool(5)
    future_res = [pool.apply_async(monte_carlo_strat, args=(data, inputs[i], iters)) for i in range(len(inputs))]
    samples = [f.get() for f in future_res]

    return samples


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

    # Usa la funzione per dividere la lista delle tuple dei periodi di MA in gruppi di 180 tuple
    mas_combined_split = list(chunk(mas_combined, 180))

    # Numero di simulazioni MC per l'ottimizzazione dei backtest
    iters = 2000

    # Tempo di inizio
    start_time = time.time()

    # Chiamata alla funzione di multi-threaded
    results = parallel_monte_carlo(data, mas_combined_split, iters)

    # Stampa il numero di secondi impiegati dal processo
    print("MP--- %s seconds for para---" % (time.time() - start_time))
