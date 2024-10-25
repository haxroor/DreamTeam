import pandas as pd
import csv
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from pywin32_testutil import testmain

# DEFINIZIONE DI TUTTE LE VARIABILI DA AGGIUSTARE
MIN_PTS = 0.0
MAX_PTS = 20
ATTEMPTS = 3
CORREZZIONE_TRAINING = 0.5
NEUTRAL_THRESHOLD = 9
POSPTS_E_NEGPTS_INIZIALE = 5.0
POSPTS_NUOVA_PAROLA_SE_TWEET_POSITIVO = 5
NEGPTS_NUOVA_PAROLA_SE_TWEET_POSITIVO = 1
POSPTS_NUOVA_PAROLA_SE_TWEET_NEGATIVO = 1
NEGPTS_NUOVA_PAROLA_SE_TWEET_NEGATIVO = 5
POSPTS_NUOVA_PAROLA_SE_TWEET_NEUTRO = 3
NEGPTS_NUOVA_PAROLA_SE_TWEET_NEUTRO = 3
MOLTIPLICATORE_ESCLAMAZIONI = 2

# Caricamento parole positive e negative
with open('pos_words.txt', 'r') as file1:
    poswords = file1.read().splitlines()
with open('neg_words.txt', 'r') as file2:
    negwords = file2.read().splitlines()

pospts = {word: (POSPTS_E_NEGPTS_INIZIALE if word in poswords else 0.0) for word in poswords + negwords}
negpts = {word: (POSPTS_E_NEGPTS_INIZIALE if word in negwords else 0.0) for word in poswords + negwords}

df = pd.read_excel("Cartel1.xlsx")

# Stopwords e negazioni
stopwords = {"un", "uno", "una", "il", "lo", "la", "i", "gli", "le", "e", "ma", "o", "di", "a", "da", "in", "con", "su",
             "per", "tra", "fra", "è", "sono", "era", "avere", "ho", "fare", "do","che","mio","mia","tuo","tua","suo","sua",
             "loro","nostro","nostra","vostro","vostra","loro","questo","questa","quello","quella","cui","chi","cosa","come",
             "dove","quando","perché","perche"}
negazioni = {"non", "niente", "poco", "meno", "nulla"}

# training

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
#print("TRAINING")
accuracy = (tot / righe) * 100
#print("Accuracy = {:.2f}%".format(accuracy), "su ", righe)

#-----------------------------------------------------------------------------------------------------------------------
filename_w = 'consegna.csv'
with open(filename_w, mode='w', newline='') as file:
    writer = csv.writer(file)
    #writer.writerow(["ID","LABEL"])

    filename_r = 'test.csv'
    df_test = pd.read_csv(filename_r)
    for i, row in df_test.iterrows():
        tweet = row[1]
        pos_score = 0
        neg_score = 0
        nextisnegazione = False
        escl = MOLTIPLICATORE_ESCLAMAZIONI if '!' in tweet else 1
        for parola in tweet.lower().split():
            # controllo parole inutili
            if parola in stopwords or parola[0] == '@' or parola[0] == '#' or parola[:4] == 'http':
                continue

            #controllo parole sconosciute
            if parola not in pospts.keys() and parola not in negpts.keys():
                lista_parole_adiacenti_alla_sconosciuta = []
                temp_pos_score = 0
                temp_neg_score = 0
                # append adjacent words
                if tweet.lower().split().index(parola) > 2:
                    lista_parole_adiacenti_alla_sconosciuta.append(tweet.lower().split()[tweet.lower().split().index(parola) - 1])
                    lista_parole_adiacenti_alla_sconosciuta.append(tweet.lower().split()[tweet.lower().split().index(parola) - 2])
                if tweet.lower().split().index(parola) < len(tweet.lower().split()) - 2:
                    lista_parole_adiacenti_alla_sconosciuta.append(tweet.lower().split()[tweet.lower().split().index(parola) + 1])
                    lista_parole_adiacenti_alla_sconosciuta.append(tweet.lower().split()[tweet.lower().split().index(parola) + 2])
                for parola_sconosciuta in lista_parole_adiacenti_alla_sconosciuta:
                    if parola in stopwords or parola[0] == '@' or parola[0] == '#' or parola[:4] == 'http':
                        temp_pos_score += pospts[parola_sconosciuta]
                        temp_neg_score += negpts[parola_sconosciuta]
                pospts[parola] = temp_pos_score / 2
                negpts[parola] = temp_neg_score / 2

                pos_score += pospts[parola] * escl
                neg_score += negpts[parola] * escl

                continue

            if parola in negazioni:
                nextisnegazione = True
                continue

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

        writer.writerow([str(row[0]), score])

print(pospts['amore'])
print(negpts['amore'])
