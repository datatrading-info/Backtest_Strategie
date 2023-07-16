import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.dates as dates
import plotly.graph_objs as go

start = '2010-01-01'
end = '2020-01-01'
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


# Imposta i colori per le candere up e down
INCREASING_COLOR = '#00ff00'
DECREASING_COLOR = '#ff0000'
# Crea la lista che contiene i dizionari con i dati
# della prima serie di dati da visualizzare
data1 = [dict(type='candlestick',
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
fig = dict(data=data1, layout=layout)
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

#############
# STRATEGY
############

d.dropna(inplace=True)
d['above_cloud'] = 0
d['above_cloud'] = np.where((d['Low'] > d['senkou_span_a'])  & (d['Low'] > d['senkou_span_b'] ), 1, d['above_cloud'])
d['above_cloud'] = np.where((d['High'] < d['senkou_span_a']) & (d['High'] < d['senkou_span_b']), -1, d['above_cloud'])
d['A_above_B'] = np.where((d['senkou_span_a'] > d['senkou_span_b']), 1, -1)

d['tenkan_kiju_cross'] = np.NaN
d['tenkan_kiju_cross'] = np.where((d['tenkan_sen'].shift(1) <= d['kijun_sen'].shift(1)) & (d['tenkan_sen'] > d['kijun_sen']), 1, d['tenkan_kiju_cross'])
d['tenkan_kiju_cross'] = np.where((d['tenkan_sen'].shift(1) >= d['kijun_sen'].shift(1)) & (d['tenkan_sen'] < d['kijun_sen']), -1, d['tenkan_kiju_cross'])

d['price_tenkan_cross'] = np.NaN
d['price_tenkan_cross'] = np.where((d['Open'].shift(1) <= d['tenkan_sen'].shift(1)) & (d['Open'] > d['tenkan_sen']), 1, d['price_tenkan_cross'])
d['price_tenkan_cross'] = np.where((d['Open'].shift(1) >= d['tenkan_sen'].shift(1)) & (d['Open'] < d['tenkan_sen']), -1, d['price_tenkan_cross'])

d['buy'] = np.NaN
d['buy'] = np.where((d['above_cloud'].shift(1) == 1) & (d['A_above_B'].shift(1) == 1) & ((d['tenkan_kiju_cross'].shift(1) == 1) | (d['price_tenkan_cross'].shift(1) == 1)), 1, d['buy'])
d['buy'] = np.where(d['tenkan_kiju_cross'].shift(1) == -1, 0, d['buy'])
d['buy'].ffill(inplace=True)

d['sell'] = np.NaN
d['sell'] = np.where((d['above_cloud'].shift(1) == -1) & (d['A_above_B'].shift(1) == -1) & ((d['tenkan_kiju_cross'].shift(1) == -1) | (d['price_tenkan_cross'].shift(1) == -1)), -1, d['sell'])
d['sell'] = np.where(d['tenkan_kiju_cross'].shift(1) == 1, 0, d['sell'])
d['sell'].ffill(inplace=True)

d['position'] = d['buy'] + d['sell']

d['stock_returns'] = np.log(d['Open']) - np.log(d['Open'].shift(1))
d['strategy_returns'] = d['stock_returns'] * d['position']
d[['stock_returns','strategy_returns']].cumsum().plot(figsize=(15,8))
plt.show()