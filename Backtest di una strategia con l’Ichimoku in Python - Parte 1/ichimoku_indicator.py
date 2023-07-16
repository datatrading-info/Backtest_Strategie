import pandas as pd
import yfinance as yf
import matplotlib as mpl
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as dates
import datetime
import matplotlib.pyplot as plt


start = '2017-01-01'
end = '2019-01-27'
d = yf.download("AAPL", start, end)
# converte le date in valori interi da usare per le
# funzioni dei grafici a candele di matplotlib
d['Dates'] = dates.date2num(d.index)

# Tenkan-sen (Conversion Line): (massimo di 9 periodi + minimo di 9 periodi) / 2
nine_period_high = d['High'].rolling(window= 9).max()
nine_period_low = d['Low'].rolling(window= 9).min()
d['tenkan_sen'] = (nine_period_high + nine_period_low) /2

# Kijun-sen (Base Line): (massimo di 26 periodi + minimo di 26 periodi) / 2
period26_high = d['High'].rolling(window=26).max()
period26_low = d['Low'].rolling(window=26).min()
d['kijun_sen'] = (period26_high + period26_low) / 2

# Senkou Span A (Leading Span A): (Conversion Line + Base Line) / 2
d['senkou_span_a'] = ((d['tenkan_sen'] + d['kijun_sen']) / 2).shift(26)

# Senkou Span B (Leading Span B): (massimo di 52 periodi + minimo di 52 periodi low) / 2
period52_high = d['High'].rolling(window=52).max()
period52_low = d['Low'].rolling(window=52).min()
d['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)

# Proiezione dei prezzi di chiusura indietro di 26 periodo
d['chikou_span'] = d['Close'].shift(-26)

# Crea un grafico dei risultati per verificare cosa abbiamo calcolato
d.drop(['Dates', 'Volume'], axis=1).plot(figsize=(15,8))
plt.show()

# Riordina i dati in modo che ogni riga contenga i valori di un giorno: 'Date','Open','High','Low','Close'.
# Il 'Date' non può essere un oggetto "datetime" in quanto la funzione non li accetterà. Ecco perché abbiamo
# convertito la nostra colonna "Data" in valori interi utilizzando la funzione "date2num".
quotes = [tuple(x) for x in d[['Dates','Open','High','Low','Close']].values]

# Grafico a candele insieme alle linee Ichimoku
fig, ax = plt.subplots(figsize=(15,8))
d[['tenkan_sen','kijun_sen','senkou_span_a','senkou_span_b','chikou_span']].plot(ax=ax, linewidth=0.5)
candlestick_ohlc(ax, quotes, width=1.0, colorup='g', colordown='r')
plt.show()

import plotly.graph_objs as go
from plotly.subplots import make_subplots

trace = go.Candlestick(x=d.index, open=d['Open'], high=d['High'], low=d['Low'], close=d['Close'])

fig = go.Figure()
fig = make_subplots(rows=1, cols=1)

# candlestick
fig.append_trace(trace, row=1, col=1)

fig.update_layout(title="Semplice Grafico a candele")
fig.show()


# Imposta i colori per le candere up e down
INCREASING_COLOR = '#00ff00'
DECREASING_COLOR = '#ff0000'
# Crea la lista che contiene i dizionari con i dati
# della prima serie di dati da visualizzare
data = [dict(type='candlestick',
    open=d.Open,
    high=d.High,
    low=d.Low,
    close=d.Close,
    x=d.index,
    yaxis='y2',
    name='AAPL',
    increasing=dict(line=dict(color=INCREASING_COLOR)),
    decreasing=dict(line=dict(color=DECREASING_COLOR)),
)]
# Crea un dizionario vuoto per contentere le impostazioni e il layout
layout = dict()
# Crea l'oggetto principale "Figure" che contiene i dati da visualizzare e le impostazioni
fig = dict(data=data, layout=layout)
# Assegna vari valori di impoestazioni - colore di sfondo, range di selezione, ecc
fig['layout']['plot_bgcolor'] = 'rgb(250, 250, 250)'
fig['layout']['xaxis'] = dict(rangeselector=dict(visible=True))
fig['layout']['yaxis'] = dict(domain=[0, 0.2], showticklabels=False)
fig['layout']['yaxis2'] = dict(domain=[0.2, 0.8])
fig['layout']['legend'] = dict(orientation='h', y=0.9, x=0.3, yanchor='bottom')
fig['layout']['margin'] = dict(t=40, b=40, r=40, l=40)

# Popola l'oggetto "rangeselector" con le impostazioni necessarie
rangeselector = dict(
    visible=True,
    x=0, y=0.9,
    bgcolor='rgba(150, 200, 250, 0.4)',
    font=dict(size=13),
    buttons=list([
        dict(count=1,
             label='reset',
             step='all'),
        dict(count=1,
             label='1yr',
             step='year',
             stepmode='backward'),
        dict(count=3,
             label='3 mo',
             step='month',
             stepmode='backward'),
        dict(count=1,
             label='1 mo',
             step='month',
             stepmode='backward'),
        dict(step='all')
    ]))

fig['layout']['xaxis']['rangeselector'] = rangeselector
# Aggiunge gli elementi Ichimoku nel grafico
fig['data'].append(dict(x=d['tenkan_sen'].index, y=d['tenkan_sen'], type='scatter', mode='lines',
                        line=dict(width=1),
                        marker=dict(color='#33BDFF'),
                        yaxis='y2', name='tenkan_sen'))
fig['data'].append(dict(x=d['kijun_sen'].index, y=d['kijun_sen'], type='scatter', mode='lines',
                        line=dict(width=1),
                        marker=dict(color='#F1F316'),
                        yaxis='y2', name='kijun_sen'))
fig['data'].append(dict(x=d['senkou_span_a'].index, y=d['senkou_span_a'], type='scatter', mode='lines',
                        line=dict(width=1),
                        marker=dict(color='#228B22'),
                        yaxis='y2', name='senkou_span_a'))
fig['data'].append(dict(x=d['senkou_span_b'].index, y=d['senkou_span_b'], type='scatter', mode='lines',
                        line=dict(width=1), fill='tonexty',
                        marker=dict(color='#e99653'),
                        yaxis='y2', name='senkou_span_b'))
fig['data'].append(dict(x=d['chikou_span'].index, y=d['chikou_span'], type='scatter', mode='lines',
                        line=dict(width=1),
                        marker=dict(color='#D105F5'),
                        yaxis='y2', name='chikou_span'))

# Imposta la lista dei colori per le candele
colors = []
for i in range(len(d.Close)):
    if i != 0:
        if d.Close[i] > d.Close[i - 1]:
            colors.append(INCREASING_COLOR)
        else:
            colors.append(DECREASING_COLOR)
    else:
        colors.append(DECREASING_COLOR)

grafico = go.Figure(fig)
grafico.show()

print("")
