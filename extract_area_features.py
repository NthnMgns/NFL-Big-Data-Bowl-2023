import pandas as pd 
import matplotlib.pyplot as plt 
import os 
import sys
from tqdm import tqdm
sys.path.insert(0, os.getcwd() + '/code')
from viz import *
from helper_functions import * 
from multiprocessing import Pool

df_game = pd.read_csv("data/games.csv")
df_tracking = pd.read_csv("data/week1.csv")
df_tracking = compute_orientation(df_tracking)
df_play = pd.read_csv("data/plays.csv")
df_players = pd.read_csv("data/players.csv")
df_pffScoutingData = pd.read_csv("data/pffScoutingData.csv")

#play_list = list()
#game_list = list()
#event_list = list()
#te_list = list()
#Ae_list = list() 
#tc_list = list()
#Ac_list = list()

def features_one_play(playId) : 
    gameId = df_area[df_area.playId == playId].gameId.unique()[0]
    #print(f'{playId} - {gameId}')
    selected_area_df = df_area[(df_area.playId==playId)&(df_area.gameId==gameId)].copy() 
    selected_play_df = df_play[(df_play.playId==playId)&(df_play.gameId==gameId)].copy()  
    tracking_players_df = pd.merge(df_tracking,df_players,how="left",on = "nflId")
    tracking_players_df = pd.merge(tracking_players_df,df_pffScoutingData,how="left",on = ["nflId","playId","gameId"])
    selected_tracking_df = tracking_players_df[(tracking_players_df.playId==playId)&(tracking_players_df.gameId==gameId)].copy()
    selected_tracking_df = beaten_by_defender(gameId, playId , df_pffScoutingData, selected_tracking_df, seuil = 0.5)
    try :
        selected_tracking_df = scramble(gameId, playId, df_pffScoutingData, selected_tracking_df, seuil = 0.5)
        event, te = compute_t_event(gameId, playId, selected_play_df, df_pffScoutingData, selected_tracking_df)
        Ae = selected_area_df[selected_area_df.frameId == te].Area.iloc[0]
        Ac = np.max(selected_area_df.Area)
        tc = selected_area_df[selected_area_df.Area == Ac].frameId.iloc[0]
        one_play =  pd.DataFrame([[playId, gameId, event, te, Ae, tc, Ac]], 
                                columns = ['playId', 'gameId', 'event', 'te', 'Ae', 'tc', 'Ac'])
        one_play.to_csv(f'data/area_features/plays/play{playId}_game{gameId}.csv')
        return one_play
    except : 
            print('Problème pour gameId, playId : ' + str((gameId, playId)))
    #play_list.append(playId)
    #game_list.append(gameId)
    #event_list.append(event)
    #te_list.append(te)
    #Ae_list.append(Ae)
    #tc_list.append(tc)
    #Ac_list.append(Ac)

Area_features = list()
for week in tqdm(range(1,9)):
    df_tracking = pd.read_csv(f"data/week{week}.csv")
    #df_tracking = compute_orientation(df_tracking)
    df_area = pd.read_csv(f"data/area/week{week}.csv")
    playIds = df_area.playId.unique()
    #print(len(playIds))
#
    #for i in playIds:
    #    Area_features += [features_one_play(i)]
    with Pool() as mp_pool:
        week_features = mp_pool.map(features_one_play, playIds)
        Area_features += week_features
    print(week_features)
    pd.concat(week_features).to_csv(f'data/area_features/week{week}.csv')
Area_features = pd.concat(Area_features)
print(Area_features)
Area_features.to_csv('data/area_features/Area_features.csv')

