import pandas as pd

# Caricamento parole positive e negative
with open('pos_words.txt', 'r') as file1:
    poswords = file1.read().splitlines()
with open('neg_words.txt', 'r') as file2:
    negwords = file2.read().splitlines()

pospts = {word: (2.0 if word in poswords else 0.0) for word in poswords + negwords}
negpts = {word: (2.0 if word in negwords else 0.0) for word in poswords + negwords}

df_full = pd.read_excel("Cartel1.xlsx")

# Stopwords e negazioni
stopwords = {"un", "uno", "una", "il", "lo", "la", "i", "gli", "le", "e", "ma", "o", "di", "a", "da", "in", "con", "su",
             "per", "tra", "fra", "è", "sono", "era", "avere", "ho", "fare", "do","che"}
negazioni = {"non", "niente", "poco", "meno", "nulla"}

# DEFINIZIONE DI TUTTE LE VARIABILI DA AGGIUSTARE
MIN_PTS = 0.0
MAX_PTS = 15.0
ATTEMPTS = 50
CORREZZIONE_TRAINING = 0.1
NEUTRAL_THRESHOLD = 3.0
POSPTS_NUOVA_PAROLA_SE_TWEET_POSITIVO = 0.6
NEGPTS_NUOVA_PAROLA_SE_TWEET_POSITIVO = 0.2
POSPTS_NUOVA_PAROLA_SE_TWEET_NEGATIVO = 0.2
NEGPTS_NUOVA_PAROLA_SE_TWEET_NEGATIVO = 0.6
POSPTS_NUOVA_PAROLA_SE_TWEET_NEUTRO = 0.4
NEGPTS_NUOVA_PAROLA_SE_TWEET_NEUTRO = 0.4
MOLTIPLICATORE_ESCLAMAZIONI = 2

# creazione sample
df = df_full.sample(frac=0.9, random_state=42)
df_remaining_10 = df_full.loc[~df_full.index.isin(df.index)]

# training sul 90%

tot = 0
righe = df.shape[0]

for i, row in df.iterrows():
    fatto = False
    tweet = row[1]
    tentativi = 0

    while not fatto:
        if tentativi > ATTEMPTS:
            #print(tweet,", got", score, ", expected", row[-1])
            #if row[-1] != "neutral":
                #print(f"pos = {pos_score}, neg = {neg_score}, expected {row[-1]}")
            break

        pos_score = 0
        neg_score = 0
        nextisnegazione = False
        escl = MOLTIPLICATORE_ESCLAMAZIONI if '!' in tweet else 1

        for parola in tweet.lower().split():
            if parola in stopwords or parola[0] == '@' or parola[0] == '#' or parola[:4] == 'http':
                # parole inutili
                continue
            if parola in negazioni:
                nextisnegazione = True
                continue

            # Se la parola è nuova, aggiungila
            if parola not in pospts.keys() and parola not in negpts.keys():
                if row[-1] == "positive":
                    pospts[parola] = POSPTS_NUOVA_PAROLA_SE_TWEET_POSITIVO
                    negpts[parola] = NEGPTS_NUOVA_PAROLA_SE_TWEET_POSITIVO
                elif row[-1] == "negative":
                    pospts[parola] = POSPTS_NUOVA_PAROLA_SE_TWEET_NEGATIVO
                    negpts[parola] = NEGPTS_NUOVA_PAROLA_SE_TWEET_NEGATIVO
                else:
                    pospts[parola] = POSPTS_NUOVA_PAROLA_SE_TWEET_NEUTRO
                    negpts[parola] = NEGPTS_NUOVA_PAROLA_SE_TWEET_NEUTRO

            # Gestione del punteggio per le parole già note
            if nextisnegazione:
                neg_score += pospts[parola] * escl
                pos_score += negpts[parola] * escl
                nextisnegazione = False
            else:
                pos_score += pospts[parola] * escl
                neg_score += negpts[parola] * escl

        # Controllo del sentiment ottenuto
        #print(f"{pos_score - neg_score} e {row[-1]}")
        if abs(pos_score - neg_score) <= NEUTRAL_THRESHOLD:
            score = "neutral"
        elif pos_score > neg_score:
            score = "positive"
        else:
            score = "negative"

        # Trasformo il risultato e l'obiettivo in un valore numerico per confrontarli
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

        # Confronto
        if obiettivo == risultato:
            fatto = True
            tot += 1
            break
        else:
            for parola in tweet.lower().split():
                if parola not in stopwords and parola not in negazioni and parola[0] != '@' and parola[0] != '#' and parola[:4] != 'http':
                    if risultato < obiettivo:
                        # Tuning al rialzo
                        pospts[parola] = min(pospts[parola] + CORREZZIONE_TRAINING, MAX_PTS)
                        negpts[parola] = max(negpts[parola] - CORREZZIONE_TRAINING, MIN_PTS)
                    elif risultato > obiettivo:
                        # Tuning al ribasso
                        pospts[parola] = max(pospts[parola] - CORREZZIONE_TRAINING, MIN_PTS)
                        negpts[parola] = min(negpts[parola] + CORREZZIONE_TRAINING, MAX_PTS)

        tentativi += 1

'''nuoveparole = dict(sorted(nuoveparole.items(), key=lambda item: item[1], reverse=True))
print(nuoveparole)'''

# Calcolo dell'accuratezza
print("TRAINING")
accuracy = (tot / righe) * 100
print("Accuracy = {:.2f}%".format(accuracy), "su ", righe)

# test sul restante 10%
tot = 0
sbagliate_neutrali = 0
sbagliate_positive = 0
sbagliate_negative = 0
righe = df_remaining_10.shape[0]
for i,row in df_remaining_10.iterrows():
    tweet = row[1]
    pos_score = 0
    neg_score = 0
    nextisnegazione = False
    escl = MOLTIPLICATORE_ESCLAMAZIONI if '!' in tweet else 1

    for parola in tweet.lower().split():
        if parola in stopwords or parola[0] == '@' or parola[0] == '#' or parola[:4] == 'http':
            # parole inutili
            continue
        if parola in negazioni:
            nextisnegazione = True
            continue

        # Se la parola è nuova, boh, evitala
        if parola not in pospts.keys() and parola not in negpts.keys():
            continue

        # Gestione del punteggio per le parole già note
        if nextisnegazione:
            neg_score += pospts[parola] * escl
            pos_score += negpts[parola] * escl
            nextisnegazione = False
        else:
            pos_score += pospts[parola] * escl
            neg_score += negpts[parola] * escl

    # Controllo del sentiment ottenuto
    if abs(pos_score - neg_score) <= NEUTRAL_THRESHOLD:
        score = "neutral"
    elif pos_score > neg_score:
        score = "positive"
    else:
        score = "negative"
    if score == row[-1]:
        tot += 1

    if score != row[-1]:
        #print(f"pos = {pos_score}, neg = {neg_score}, expected {row[-1]}")
        if row[-1] == "neutral":
            sbagliate_neutrali +=1
        elif row[-1] == "positive":
            sbagliate_positive +=1
        else:
            sbagliate_negative +=1

print(f"neutrali = {(sbagliate_neutrali / (righe-tot)) * 100}%, positive = {(sbagliate_positive / (righe-tot)) * 100}%, negative = {(sbagliate_negative / (righe-tot)) * 100}%")

print("TESTING")
accuracy = (tot / righe) * 100
print("Accuracy = {:.2f}%".format(accuracy), "su ", righe)
