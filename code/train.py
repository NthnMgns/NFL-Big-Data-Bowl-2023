import pandas as pd 
import numpy as np
from helper_functions import *
from feature import * 

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.neural_network import MLPRegressor
from sklearn import svm


# ------------------------------------------------------ #
#                      Input Data                        #
# ------------------------------------------------------ #

# Dataframe
df_play = pd.read_csv("data/plays.csv")
df_area = pd.read_csv("data/area_features/Area_features.csv")
df_area_play = df_area.merge(df_play, how='left', on = ['gameId', 'playId'])
df_scouting = pd.read_csv("data/pffScoutingData.csv")
df_players = pd.read_csv("data/players.csv")
df_tracking = pd.read_csv("data/week1.csv")
#df_qbPosition = qb_position(df_players,df_tracking)

# TODO Simulation de données à supprimer
df_area["t_c"] = [np.random.random() for i in range(len(df_area))]

# ------------------------------------------------------ #
#                  Feature Choice                        #
# ------------------------------------------------------ #

list_feature = [
    GeneralDescriptionPlay().read(df_play),
    #CharacteristicTime().read(df_area),
    #CharacteristicArea().read(df_area),
    #CharacteristicSpeed().read(df_area),
    #EventTime().read(df_area),
    #EventArea().read(df_area),
    PocketLifeTime().read(df_area_play),
    #CriticalTime().read(df_area),
    NbRusher().read(df_scouting),
    NbBlock().read(df_scouting),
    #QBPosition().read(df_qbPosition)
    #WeightDiffMatchup().read(data)
]

# ------------------------------------------------------ #
#                     ML process                         #
# ------------------------------------------------------ #
# Split data
ids_train = [1, 2, 3, 4 ,5, 6]
ids_test = [7, 8]

gameIds_train = list()
gameIds_test = list()
for week in ids_train :
    gameIds_train += pd.read_csv(f"data/week{week}.csv").gameId.unique().tolist()
for week in ids_test :
    gameIds_test += pd.read_csv(f"data/week{week}.csv").gameId.unique().tolist()

# ETL for features
df_train = etl(gameIds_train, list_feature)
df_test = etl(gameIds_test, list_feature)

# Train
model = MLPRegressor()
X_train, y_train = df_train.drop(columns = ['PocketLife']), df_train.loc[:, 'PocketLife']
model.fit(X_train, y_train)

# Test
X_test, y_test = df_test.drop(columns = ['PocketLife']), df_test.loc[:, 'PocketLife']
y_pred = model.predict(X_test)
print(y_pred[:5])
print(df_test.head())
# Error Metric 
print(abs(y_pred - y_test).mean())
#print(model.coefs_[0])

df_test.loc[:, 'xPL'] = model.predict(X_test)
df_test.to_csv('xPL.csv')