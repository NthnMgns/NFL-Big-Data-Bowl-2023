import pandas as pd 
import numpy as np
from helper_functions import *
from feature import * 

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.neural_network import MLPRegressor
from sklearn import svm

from lifelines import CoxPHFitter, WeibullAFTFitter

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
df_qbPosition = pd.merge(df_tracking,df_players,how="left",on="nflId")
df_weight = weight_diff(df_players,df_scouting)
df_weight_pack = weight_diff_pack(df_players,df_scouting)

df_area_features = pd.read_csv(f"data/area_features/Area_features.csv").drop(columns=['Unnamed: 0'])
df_detail_plays = pd.merge(df_area_features,df_play,how="left",on = ["playId","gameId"])

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
    #PocketLifeTime().read(df_area_play),
    #CriticalTime().read(df_area),
    NbRusher().read(df_scouting),
    NbBlock().read(df_scouting),
    QBPosition().read(df_qbPosition),
    #WeightDiffMatchup().read(df_weight),
    WeightDiffPack().read(df_weight_pack),
    SurvivalData().read(df_detail_plays)
]

# ------------------------------------------------------ #
#                     ML process                         #
# ------------------------------------------------------ #
# Split data
ids_train = [1, 2, 3, 4]
ids_test = [5, 6, 7, 8]

gameIds_train = list()
gameIds_test = list()
for week in ids_train :
    gameIds_train += pd.read_csv(f"data/week{week}.csv").gameId.unique().tolist()
for week in ids_test :
    gameIds_test += pd.read_csv(f"data/week{week}.csv").gameId.unique().tolist()

# ETL for features
df_train, strata_list = etl(gameIds_train, list_feature)
df_test, _ = etl(gameIds_test, list_feature)

print(df_train.head())
# Train
model = CoxPHFitter() #WeibullAFTFitter #CoxPHFitter
model.fit(df_train, duration_col='duration', event_col='death', show_progress = True)

#model.check_assumptions(df_train)

#print("Résumé")
#print(model.summary)

# Test
print("Score (concordance) :")
print(model.score(df_test, 'concordance_index'))

# Merge with te
df_test.loc[:, "t_med"] = model.predict_median(df_test) 
print((df_test.t_med.min(), df_test.t_med.max(),df_test.t_med.mean(),df_test.t_med.std()))
df_test = df_test.reset_index()[["playId", "gameId", "duration", "t_med"]]
df_test.to_csv("xPL.csv")