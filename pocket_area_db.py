import pandas as pd 
import os 
import sys
from tqdm import tqdm
import time

sys.path.insert(0, os.getcwd() + '/code')
from viz import *
from helper_functions import * 

# ------------------------------------------------- #
#  Lecture des dataframes             

df_game = pd.read_csv("data/games.csv")
df_play = pd.read_csv("data/plays.csv")
df_players = pd.read_csv("data/players.csv")
df_pffScoutingData = pd.read_csv("data/pffScoutingData.csv")

# ------------------------------------------------- #
#  Numéro de la semaine 
week = 2
df_tracking = pd.read_csv(f"data/week{week}.csv")

# ------------------------------------------------- #
#  Process

# TODO delete play action 

gameIds = df_tracking.gameId.unique()
df_games = list()
for gameId in tqdm(gameIds) :
    # Boucle des matchs 
    playIds = df_play[df_play.gameId==gameId].playId.unique()
    playIds.sort()
    df_plays = list()
    for playId in tqdm(playIds):
        
        # Boucle sur les séquences de passe
        selected_play_df = df_play[(df_play.playId==playId)&(df_play.gameId==gameId)].copy()    
        tracking_players_df = pd.merge(df_tracking,df_players,how="left",on = "nflId")
        tracking_players_df = pd.merge(tracking_players_df,df_pffScoutingData,how="left",on = ["nflId","playId","gameId"])
        selected_tracking_df = tracking_players_df[(tracking_players_df.playId==playId)&(tracking_players_df.gameId==gameId)].copy()
        selected_tracking_df = beaten_by_defender(gameId, playId, df_pffScoutingData, selected_tracking_df, seuil = 0.5)

        # Liste des frames
        sorted_frame_list = selected_tracking_df.frameId.unique()
        sorted_frame_list.sort()
        # Lecture de données pertinentes
        line_of_scrimmage = selected_play_df.absoluteYardlineNumber.values[0]
        # playDescription = selected_play_df.playDescription.values[0]
        list_aire_t = list()
        
        for frameId in sorted_frame_list:
            # Boucle sur les frames
            selected_frame_df = selected_tracking_df[selected_tracking_df.frameId == frameId]
            offensive_points = get_Oline_position(selected_frame_df)
            defensive_points = get_Dline_position(selected_frame_df)
            QB_zone = calculate_Oline_zones(offensive_points, line_of_scrimmage)
            region_polys, region_pts, players_points = calculate_voronoi_zones(QB_zone, offensive_points, defensive_points)
            list_aire_t.append(pd.DataFrame([[frameId, pocketArea(region_polys, region_pts, players_points)]], columns = ['frameId', 'Area']))
        df_aire = pd.concat(list_aire_t)
        df_aire.loc[:, 'playId'] = playId
        df_plays.append(df_aire)

        #except : 
        #    print('Problème pour gameId, playId, frameId : ' + str((gameId, playId)))
        #    continue
    df_plays = pd.concat(df_plays)
    df_plays.loc[:, 'gameId'] = gameId
    df_games.append(df_plays)
    df_plays.to_csv(f'data/area/match/week{week}_{gameId}.csv')
    
df_games = pd.concat(df_games)
df_games.to_csv(f'data/area/week{week}.csv')