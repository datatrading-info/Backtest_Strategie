import sqlite3 as db
import pandas as pd

# imposta il percorso del file del database a cui desideriamo connetterci
# questo è univoco e dipende dove si trova il database SQLite nel sistema locale
database = 'C:\Users\Datatrading\sqlite_databases\etfs.db'

# questa è l'istruzione SQL contenente le informazioni riguardo
# a quali ticker vogliamo estrarre dal database
# Ad esempio, ho scelto di estrarre tutti i ticker che hanno
# il loro "Focus" corrispondente a "Silver"
sql = 'SELECT Ticker FROM etftable WHERE Focus = "Silver";'

# crea una connessione al database
cnx = db.connect(database)
cur = cnx.cursor()

# eseque l'istruzione SQL e salva i risultati in una variabile chiamata "tickers"
tickers = pd.read_sql(sql, con=cnx)

# crea una lista vuota
symbList = []

# iterazione sul DataFrame e inserimento dei ticker nella lista
for i in range(len(tickers)):
    symbList.append(tickers.ix[i][0])


def get_symb_pairs(symbList):
    """
    symbList è una lista di simboli ETF
    Questa funzione ha una lista di simboli come paramentro
    e restituisce una lista di coppie univoche di simboli
    """

    symbPairs = []
    i = 0

    # scorre la lista e crea tutte le possibili combinazioni di coppie
    # di ticker e aggiunge le coppie alla lista "symbPairs"
    while i < len(symbList) - 1:
        j = i + 1
        while j < len(symbList):
            symbPairs.append([symbList[i], symbList[j]])
            j += 1
        i += 1

    # scorre la lista di coppie appena creato e rimuove
    # tutte le coppie composte da due ticker identici
    for i in symbPairs:
        if i[0] == i[1]:
            symbPairs.remove(i)

    # crea una nuova lista vuota per memorizzare solo coppie univoche
    symbPairs2 = []

    # scorre la lista originale e aggiunge alla nuova lista solo coppie univoche
    for i in symbPairs:
        if i not in symbPairs2:
            symbPairs2.append(i)
    return symbPairs2

symbPairs = get_symb_pairs(symbList)