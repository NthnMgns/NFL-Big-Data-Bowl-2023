import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
from helper_functions import *
from feature import * 

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
    Outnumber().read(df_scouting),
    UnblockedPlayer().read(df_scouting),
    SurvivalData().read(df_detail_plays)
]

# ------------------------------------------------------ #
#                     ML process                         #
# ------------------------------------------------------ #
# Split data
ids_train = [1, 2, 3, 4, 5]
ids_test = [6, 7, 8]

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

model.check_assumptions(df_train)

print("Résumé")
print(model.summary)

# Test Score
print("Score (concordance) :")
print(model.score(df_test, 'concordance_index'))

# Extract Image
if True : 
    path = 'figures/'

    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='yardsToGo', values=[0,10,20,30], cmap='coolwarm')
    plt.savefig(path + 'yardsToGo.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='absoluteYardlineNumber', values=[10,30,60,100], cmap='coolwarm')
    plt.savefig(path + 'absoluteYardlineNumber.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='down', values=[0,1,2,3,4], cmap='coolwarm')
    plt.savefig(path + 'down.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='nbRusher', values=[2,5,7], cmap='coolwarm')
    plt.savefig(path + 'nbRusher.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='nbBlock', values=[5,6,7,8], cmap='coolwarm')
    plt.savefig(path + 'nbBlock.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='qbPosition', values=[0, 1], cmap='coolwarm')
    plt.savefig(path + 'qbPosition.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='weightDiffPack', values=[-200,0,500,1000,1200], cmap='coolwarm')
    plt.savefig(path + 'weightDiffPack.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='unblockedRusher', values=[-1,0,1,2,3], cmap='coolwarm')
    plt.savefig(path + 'unblockedRusher.png')
    plt.figure()
    model.plot_partial_effects_on_outcome(covariates='outnumber_O', values=[0,1,2,3], cmap='coolwarm')
    plt.savefig(path + 'outnumber_O.png')

# Merge with te
df_test.loc[:, "t_med"] = model.predict_percentile(df_test, p = 0.5) 
print((df_test.t_med.min(), df_test.t_med.max(),df_test.t_med.mean(),df_test.t_med.std()))
df_test = df_test.reset_index()

# Compute Won Time
df_test = df_test.merge(df_play, on = ['playId', 'gameId'])
df_test = df_test.merge(df_area_features, on = ['playId', 'gameId'])

df_test.loc[df_test.event == "pass", 'Won Time'] = df_test[df_test.event == "pass"].apply(lambda x: x.duration - x.t_med if x.t_med < x.duration else 0, axis = 1) / 10 #
df_test.loc[df_test.event != "pass", 'Won Time'] = df_test[df_test.event != "pass"].apply(lambda x: x.duration - x.t_med, axis = 1) / 10 #

df_test = df_test[["playId", "gameId", "duration", "t_med", 'Won Time','event']]
df_test.to_csv("xPL.csv")