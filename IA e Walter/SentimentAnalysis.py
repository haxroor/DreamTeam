import pandas as pd
# manca una migliore implementazione dei punti extra delle nuove parole, magari capendo se sono positive o negative in
# base al contesto: aumenta o diminuisci il loro valore in base all'obiettivo e sommalo al punteggio corrispondente

# Caricamento parole positive e negative
with open('pos_words.txt', 'r') as file1:
    poswords = file1.read().splitlines()
with open('neg_words.txt', 'r') as file2:
    negwords = file2.read().splitlines()

pospts = {word: 2 for word in poswords}
negpts = {word: 2 for word in negwords}
nuoveparole = {}

df = pd.read_excel("Cartel1.xlsx")

# Stopwords e negazioni
stopwords = {"un", "uno", "una", "il", "lo", "la", "i", "gli", "le", "e", "ma", "o", "di", "a", "da", "in", "con", "su",
             "per", "tra", "fra", "è", "sono", "era", "avere", "ho", "fare", "do","che"}
negazioni = {"non", "niente", "poco", "meno", "nulla"}

# Definire limiti per evitare che i punteggi diventino troppo alti o bassi
MIN_PTS = 0.0  # 0,15 68%
MAX_PTS = 15.0  # 0.1,15 61%

# Definire una soglia per considerare sentiment neutro
NEUTRAL_THRESHOLD = 0.1

tot = 0
righe = df.shape[0]

for i, row in df.iterrows():
    fatto = False
    tweet = row[1]
    tentativi = 0

    while not fatto:
        if tentativi > 50:
            break

        pos_score = 0
        neg_score = 0
        ex_score = 0
        nextisnegazione = False
        escl = 2 if '!' in tweet else 1

        for parola in tweet.lower().split():
            if parola in stopwords or parola[0] == '@' or parola[0] == '#' or parola[:4] == 'http':
                continue
            if parola in negazioni:
                nextisnegazione = True
                continue

            # Se la parola è nuova, aggiungila a nuoveparole
            if parola not in pospts.keys() and parola not in negpts.keys() and parola not in nuoveparole.keys():
                nuoveparole[parola] = 0.5  # 0,5 0,15 68%

            # Gestione del punteggio per le parole già note
            if parola in pospts:
                if nextisnegazione:
                    neg_score += pospts[parola] * escl
                    nextisnegazione = False
                else:
                    pos_score += pospts[parola] * escl
            elif parola in negpts:
                if nextisnegazione:
                    pos_score += negpts[parola] * escl
                    nextisnegazione = False
                else:
                    neg_score += negpts[parola] * escl
            elif parola in nuoveparole:
                if nextisnegazione:
                    ex_score -= nuoveparole[parola] * escl
                    nextisnegazione = False
                else:
                    ex_score += nuoveparole[parola] * escl

        # Controllo del sentiment ottenuto
        total_pos_score = pos_score + ex_score
        total_neg_score = neg_score + ex_score

        if abs(total_pos_score - total_neg_score) <= NEUTRAL_THRESHOLD:
            score = "neutral"
        elif total_pos_score > total_neg_score:
            score = "positive"
        else:
            score = "negative"

        # Verifica dell'obiettivo e aggiustamento dei punteggi
        if row[-1] == "positive":
            obiettivo = 1
        elif row[-1] == "negative":
            obiettivo = -1
        else:
            obiettivo = 0

        if score == "positive":
            risultato = 1
        elif score == "negative":
            risultato = -1
        else:
            risultato = 0

        if obiettivo == risultato:
            fatto = True
            tot += 1
            break
        elif risultato < obiettivo:
            # Tuning al rialzo
            for parola in tweet.lower().split():
                if parola in pospts:
                    pospts[parola] = min(pospts[parola] + 0.1, MAX_PTS)
                elif parola in negpts:
                    negpts[parola] = max(negpts[parola] - 0.1, MIN_PTS)
                elif parola in nuoveparole:
                    nuoveparole[parola] = min(nuoveparole[parola] + 0.1, MAX_PTS)
        elif risultato > obiettivo:
            # Tuning al ribasso
            for parola in tweet.lower().split():
                if parola in pospts:
                    pospts[parola] = max(pospts[parola] - 0.1, MIN_PTS)
                elif parola in negpts:
                    negpts[parola] = min(negpts[parola] + 0.1, MAX_PTS)
                elif parola in nuoveparole:
                    nuoveparole[parola] = max(nuoveparole[parola] - 0.1, MIN_PTS)

        tentativi += 1

#nuoveparole = dict(sorted(nuoveparole.items(), key=lambda item: item[1], reverse=True))
#print(nuoveparole)

# Calcolo dell'accuratezza
print("Tot = ", tot)
accuracy = (tot / righe) * 100
print("Accuracy = {:.2f}%".format(accuracy), "su ", righe)
