import pandas as pd
import sqlite3 as db
import requests

# creare una lista vuota per archiviare i dati prelevati dal web
frames = []
# creare una stringa di pagine web che inseriremo nel parser html
s = '''
http://www.etf.com/channels/bond-etfs
http://www.etf.com/channels/mlp-etfs
http://www.etf.com/channels/silver-etfs
http://www.etf.com/channels/china-etfs
http://www.etf.com/channels/muni-etfs
http://www.etf.com/channels/us-broad-market-bond-etfs
http://www.etf.com/channels/dividend-etfs
http://www.etf.com/channels/natural-gas-etfs
http://www.etf.com/channels/global-bond-etfs
http://www.etf.com/channels/oil-etfs
http://www.etf.com/channels/treasury-etfs
http://www.etf.com/channels/gold-etfs
http://www.etf.com/channels/reit-etfs
http://www.etf.com/channels/high-dividend-yield-etfs
http://www.etf.com/channels/japan-etfs
http://www.etf.com/channels/smart-beta-etfs
http://www.etf.com/etf-lists/alternatives-etfs
http://www.etf.com/etf-lists/asset-allocation-etfs
http://www.etf.com/etf-lists/currency-etfs
http://www.etf.com/etf-lists/fixed-income-etfs
http://www.etf.com/channels/alpha-seeking-etfs
http://www.etf.com/channels/basic-materials-etfs
http://www.etf.com/channels/consumer-cyclicals-etfs
http://www.etf.com/channels/consumer-non-cyclicals-etfs
http://www.etf.com/channels/energy-etfs
http://www.etf.com/channels/extended-market-etfs
http://www.etf.com/channels/financials-etfs
http://www.etf.com/channels/health-care-etfs
http://www.etf.com/channels/high-dividend-yield-etfs
http://www.etf.com/channels/industrials-etfs
http://www.etf.com/channels/real-estate-etfs
http://www.etf.com/channels/small-cap-etfs
http://www.etf.com/channels/technology-etfs
http://www.etf.com/channels/telecommunications-etfs
http://www.etf.com/channels/theme-etfs
http://www.etf.com/channels/total-market-etfs
http://www.etf.com/channels/utilities-etfs
http://www.etf.com/channels/asia-pacific-etfs
http://www.etf.com/channels/developed-markets-etfs
http://www.etf.com/channels/emerging-markets-etfs
http://www.etf.com/channels/europe-etfs
http://www.etf.com/channels/global-etfs
http://www.etf.com/channels/global-ex-us-etfs
http://www.etf.com/channels/latin-america-etfs
http://www.etf.com/channels/middle-east-and-africa-etfs
'''

# divide gli URL in una stringa e li inserisce nel parser html di pandas
# per creare un dataframe delle informazioni raccolte
for i in s.split():
    print("Scraping data from {}.".format(i))
    df = pd.read_html(requests.get(i,headers={'User-agent': 'Mozilla/5.0'}).text)
    # df contiene più DataFrame.
    # l'indice [5] è il DataFrame a cui siamo interessati per i dati raccolti hanno intestazioni
    # leggermente diverse su pagine Web diverse, quindi reimpostiamo le intestazioni di colonna
    # in modo che siano identiche per ogni DataFrame, questi nomi corrispondono anche alle
    # colonne che imposteremo nel nostro database SQLite
    df[5].columns = ['Fund Name','Ticker','Asset Class','Region','Geography','Category','Focus',
                      'Niche', 'Inverse','Leveraged','ETN','Underlying Index','Selection Criteria',
                      'Weighting Scheme','Active per SEC']
    frames.append(df[5])

# crea un dataframe "master" che concatena insieme tutti i DataFrame pertinenti (indice 5).
masterFrame = pd.concat(frames)

# crea una connessione al database SQLite precedentemente creato
# usa il percorso e il nome che corrisponde al database locale
cnx = db.connect('databases_etfs.db')
cur = cnx.cursor()

# rimuovere la tabella se esiste già e tutti i dati che contiene
cur.execute('DROP TABLE IF EXISTS etftable;')

# crea la tabella all'interno del database
sql = '''CREATE TABLE etftable ('Fund Name' TEXT, 'Ticker' TEXT, 'Asset Class' TEXT, 
                                'Region' TEXT, 'Geography' TEXT, 'Category' TEXT, 'Focus' TEXT,
                                'Niche' TEXT, 'Inverse' TEXT, 'Leveraged' TEXT, 'ETN' TEXT, 
                                'Underlying Index' TEXT, 'Selection Criteria' TEXT, 'Weighting Scheme' TEXT, 
                                'Active per SEC' TEXT)'''
cur.execute(sql)

# aggiunge i dati
masterFrame.to_sql(name='etftable', con=cnx, if_exists = 'append', index=False)
cnx.close()