import pandas as pd 
import numpy as np
from helper_functions import *
from feature import * 

from sklearn.gaussian_process import GaussianProcessRegressor

# ------------------------------------------------------ #
#                      Input Data                        #
# ------------------------------------------------------ #

# Dataframe
df_play = pd.read_csv("data/plays.csv")
df_area = pd.read_csv("data/plays.csv")
df_scouting = pd.read_csv("data/pffScoutingData.csv")
df_players = pd.read_csv("data/players.csv")
df_tracking = pd.read_csv("data/week1.csv")

# TODO Simulation de données à supprimer
df_area["t_c"] = [np.random.random() for i in range(len(df_area))]

# ------------------------------------------------------ #
#                  Feature Choice                        #
# ------------------------------------------------------ #

list_feature = [
    GeneralDescriptionPlay().read(df_play),
    CharacteristicTime().read(df_area)
    CharacteristicArea().read(df_area)
    EventTime().read(df_area)
    EventArea().read(df_area),
    PocketLifeTime().read(df_area),
    # CriticalTime().read(df_area),
    NbRusher().read(df_scouting),
    NbBlock().read(df_scouting)#,
    # QBPosition().read(data)
    # WeightDiffMatchup().read(data)
]

# ------------------------------------------------------ #
#                     ML process                         #
# ------------------------------------------------------ #
# Split data
gameIds_train = pd.read_csv("data/week1.csv").gameId.unique()
gameIds_test = pd.read_csv("data/week2.csv").gameId.unique()

# ETL for features
df_train = etl(gameIds_train, list_feature)
df_test = etl(gameIds_test, list_feature)
print(df_train.head())

# Train
model = GaussianProcessRegressor()
X_train, y_train = df_train.drop(columns = ['t_c']), df_train.loc[:, 't_c']
model.fit(X_train, y_train)

# Test
X_test, y_test = df_test.drop(columns = ['t_c']), df_test.loc[:, 't_c']
y_pred = model.predict(X_test)
print(y_pred)

# Error Metric 
print(abs(y_pred - y_test).mean())