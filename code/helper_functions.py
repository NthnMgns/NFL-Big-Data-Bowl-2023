import pandas as pd
import os
import glob
import numpy as np
import math
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = "browser"

from scipy.spatial import Voronoi, ConvexHull
from shapely.geometry import Polygon, Point
from geovoronoi import voronoi_regions_from_coords

# ------------------------------------------------------ #
#                 Définition de la poche                 #
# ------------------------------------------------------ #

def get_Oline_position(selected_tracking_df):
    """Récupère la position des joueurs de la O-line"""
    plot_df = selected_tracking_df.copy()
    mask = plot_df.pff_role.isin(['Pass Block', 'Pass'])
    points = plot_df.loc[mask, ['x', 'y', 'team', 'officialPosition', 'beaten']]
    points = points.reset_index().drop(columns = ['index'])
    return points

def get_Dline_position(selected_tracking_df):
    """Récupère la position des joueurs de la D-line"""
    plot_df = selected_tracking_df.copy()
    mask = plot_df.pff_role.isin(['Pass Rush'])
    points = plot_df.loc[mask, ['x', 'y', 'team', 'officialPosition', 'beaten']]
    points = points.reset_index().drop(columns = ['index'])
    return points

def calculate_voronoi_zones(QB_zone, offensive_points, defensive_points):
    """
    Calcul le graph de Voronoi pour un ensemble de points donnés.
    Inspired by : https://github.com/rjtavares/football-crunching/blob/master/notebooks/using%20voronoi%20diagrams.ipynb
    """
    defensive_points.loc[:, 'isInQBzone'] = False
    for i in range(len(defensive_points)):
        point_x, point_y = defensive_points.iloc[i][['x', 'y']].values
        if Point(point_x, point_y).within(Polygon(QB_zone)):
            defensive_points.loc[i, 'isInQBzone'] = True
    # Prise en compte des joueurs qui ne sont pas battus
    players_points = pd.concat([offensive_points[~offensive_points.beaten], defensive_points[defensive_points.isInQBzone]]).reset_index().drop(columns = ['index'])
    try :
        region_polys, region_pts = voronoi_regions_from_coords(players_points[["x", "y"]].values, Polygon(QB_zone))
    except : 
        region_polys, region_pts = dict(), dict()
    return region_polys, region_pts, players_points

def calculate_Oline_zones(points, line_of_scrimmage):
    """Calcule la zone confexe formée par l'ensemble de la D-line + QB"""
    y_max, y_min = points.y.max(), points.y.min()
    x_QB = points[points.officialPosition == 'QB'].iloc[0].x 
    init_zone_points = np.concatenate([points.loc[:, ["x", 'y']].values, [[x_QB, y_max], [x_QB, y_min]]]) #np.array([[x_QB, y_max], [x_QB, y_min], [line_of_scrimmage, y_min], [line_of_scrimmage, y_max]])
    hull = ConvexHull(init_zone_points[:, :2])
    return init_zone_points[hull.vertices,:2]

def pocketArea(region_polys, region_pts, players_points):
    """Calcul pour 1 frame l'aire de la poche du QB"""
    team = players_points[players_points.officialPosition == 'QB'].iloc[0].team
    region_polys_ids = list()
    for i in region_pts.keys() :
        if players_points.iloc[region_pts[i]].iloc[0].team == team :
            region_polys_ids.append(i)
    team_area = 0
    for i in region_polys_ids:
        team_area += region_polys[i].area    
    return team_area

# ------------------------------------------------- #
#          Calcul Orientations et face à face       #
# ------------------------------------------------- #

def compute_orientation(data):
    copy = data.copy()
    copy = copy.assign(o_x = np.sin(copy.o*2*np.pi/360))
    copy = copy.assign(o_y = np.cos(copy.o*2*np.pi/360))
    return copy

def face2face(tracking_data, scouting_data):
    #def face2face(gameId, playId, frameId, tracking_data, scouting_data):
    #tracking_data = tracking_data.query(f"gameId == {gameId} & playId == {playId} & frameId == {frameId}")
    #scouting_data = scouting_data.query(f"gameId == {gameId} & playId == {playId}")
    #tracking_data = tracking_data.query(f"frameId == {frameId}")
    """
    run in a for loop to compute for each play at each frame
    """
    blocked_opponent = scouting_data[["nflId","pff_nflIdBlockedPlayer"]]
    #data_with_opp = pd.merge(tracking_data,blocked_opponent,how="outer",on="nflId")
    #print(data_with_opp)
    opp_orientation = pd.merge(tracking_data[["nflId","o_x","o_y"]],blocked_opponent,how="inner",left_on="nflId", right_on="pff_nflIdBlockedPlayer")
    opp_orientation = opp_orientation.rename(columns={"nflId_y" : "nflId"})
    #print(opp_orientation)
    data_with_opp_orientation = pd.merge(tracking_data , opp_orientation[["nflId","o_x","o_y","pff_nflIdBlockedPlayer"]],how="inner",on="nflId")
    data_with_opp_orientation = data_with_opp_orientation.rename(columns={"o_x_x" : "o_x", 
                                                                        "o_y_x" : "o_y",
                                                                        "o_x_y" : "o_x_opp",
                                                                        "o_y_y" : "o_y_opp",})

    data_with_opp_orientation["isBeaten"] = data_with_opp_orientation.o_x*data_with_opp_orientation.o_x_opp > 0
    return data_with_opp_orientation

# ------------------------------------------------- #
#          Création de nouvelles variables          #
# ------------------------------------------------- #

def distance(x1,y1,x2,y2):
    """
    Calcul la distance entre deux points de coordonnées (x1,y1) et (x2,y2).
    """
    distance = np.sqrt((x1-x2)**2+(y1-y2)**2)
    return distance

def nearest_player(nflId, gameId, playId, frameId, tracking_data):
    """
    Retourne l'id du joueur le plus proche de nflId.
    """
    player = tracking_data.query(f"nflId == {nflId} & gameId == {gameId} & playId == {playId} & frameId == {frameId}")
    player_team = player.team.values[0]
    other = tracking_data.query(f"nflId != {nflId} & gameId == {gameId} & playId == {playId} & frameId == {frameId} & team != 'football' & team != '{player_team}'")
    dist = distance(player.x.values,player.y.values,other.x.values,other.y.values)
    return other.nflId.values[np.argmin(dist)]  

def compute_matchup(gameId, playId, scouting_data, tracking_data):
    """
    Identifie les matchups des joueurs offensifs identifiés comme bloqueurs.
    """
    tracking_data = tracking_data.query(f"gameId == {gameId} & playId == {playId}")
    tracking_data = tracking_data.assign(nearestPlayer = np.nan)
    n_frame = tracking_data.frameId.unique().shape[0]
    scouting_data = scouting_data.query(f"gameId == {gameId} & playId == {playId}")
    pass_block = scouting_data.query("pff_role == 'Pass Block'").nflId.values

    for frame in np.arange(n_frame)+1:
        data = tracking_data.query(f"frameId == {frame}").copy()
        for player in pass_block:
            data.loc[data["nflId"] == player,"nearestPlayer"] = nearest_player(player, gameId, playId, frame, data)
        tracking_data.loc[tracking_data["frameId"] == frame] = data    
    
    return tracking_data

def ball_qb_hands(gameId, playId, scouting_data, tracking_data, seuil = 1):
    """
    Ajoute une variable binaire (ballInQBHands) à tracking_data indiquant si la balle est dans les mains du QB (1) ou non (0).
    """
    qbId = scouting_data.query(f"gameId == {gameId} & playId == {playId} & pff_role == 'Pass'").nflId.values[0]
    qb = tracking_data.query(f"nflId == {qbId} & gameId == {gameId} & playId == {playId}")
    tracking_data = tracking_data.query(f"gameId == {gameId} & playId == {playId}")
    ball = tracking_data.query("team == 'football'")
    dist = distance(qb.x.values,qb.y.values,ball.x.values,ball.y.values)
    tracking_data = tracking_data.assign(ballInQBHands = np.nan)
    tracking_data.loc[tracking_data["nflId"] == qbId, "ballInQBHands"] = dist
    tracking_data.loc[tracking_data["ballInQBHands"] <= seuil, "ballInQBHands"] = 1
    tracking_data.loc[tracking_data["ballInQBHands"] > seuil, "ballInQBHands"] = 0
    return tracking_data

def beaten_by_defender(gameId, playId, scouting_data, tracking_data, seuil = 0.5):   
    """
    Ajoute une variable binaire (beaten) à tracking_data indiquant si le joueur a été battu (1) ou non (0).
    """
    scouting_data = scouting_data.query(f"gameId == {gameId} & playId == {playId}")
    tracking_data = tracking_data.query(f"gameId == {gameId} & playId == {playId}")
    tracking_data = tracking_data.assign(beaten = False)
    n_frame = tracking_data.frameId.unique().shape[0]
    qbId = scouting_data.query("pff_role == 'Pass'").nflId.values[0]
    pass_block = scouting_data.query("pff_role == 'Pass Block'").nflId.values
    
    for frame in np.arange(n_frame)+1:
        data = tracking_data.query(f"frameId == {frame}").copy()
        qb = tracking_data.query(f"nflId == {qbId} & frameId == {frame}").copy()
        for player in pass_block:
            player_data = data.query(f"nflId == {player}")
            opponentId = scouting_data.query(f"nflId == {player}").pff_nflIdBlockedPlayer.values
            if not math.isnan(opponentId):
                opponent = tracking_data.query(f"nflId == {opponentId} & frameId == {frame}")
                dist_qb_def = distance(qb.x.values,qb.y.values,opponent.x.values,opponent.y.values)[0]
                dist_qb_off = distance(qb.x.values,qb.y.values,player_data.x.values,player_data.y.values)[0]
                diff = dist_qb_off - dist_qb_def
                if diff >= seuil:
                    data.loc[data["nflId"] == player,"beaten"] = True
                else: 
                    data.loc[data["nflId"] == player,"beaten"] = False
                tracking_data.loc[tracking_data["frameId"] == frame] = data
    return tracking_data

def scramble(gameId, playId, scouting_data, tracking_data, seuil = 1):
    """
    Ajoute une variable binaire (scramble) indiquant si le QB scramble (1) ou non (0).
    """
    scouting_data = scouting_data.query(f"gameId == {gameId} & playId == {playId}")
    tracking_data = tracking_data.query(f"gameId == {gameId} & playId == {playId}")
    tracking_data = tracking_data.assign(scramble = np.nan)
    n_frame = tracking_data.frameId.unique().shape[0]
    qbId = scouting_data.query("pff_role == 'Pass'").nflId.values[0]
    pass_block = scouting_data.query("pff_role == 'Pass Block'").nflId.values
    direction = tracking_data.query(f"nflId == {qbId}").playDirection.values[0]
    
    for frame in np.arange(n_frame)+1:
        data = tracking_data.query(f"frameId == {frame}").copy()
        qb_y = data.query(f"nflId == {qbId}").y.values[0]
        qb_x = data.query(f"nflId == {qbId}").x.values[0]
        oline_y = data.query(f"nflId in {pass_block.tolist()}").y.values.tolist()
        oline_x = data.query(f"nflId in {pass_block.tolist()}").x.values.tolist()
        max_y_oline = oline_y[np.argmax(oline_y)]
        min_y_oline = oline_y[np.argmin(oline_y)]
        x = [qb_x]
        x.extend(oline_x)
        if direction == "right":
            value = np.argmax(x)
        else: 
            value = np.argmin(x)
        
        if min_y_oline-qb_y > seuil or qb_y-max_y_oline > seuil or value == 0:
            data.loc[data["nflId"] == qbId,"scramble"] = 1
        else:
            data.loc[data["nflId"] == qbId,"scramble"] = 0
        tracking_data.loc[tracking_data["frameId"] == frame] = data
    return tracking_data

def compute_t_event(gameId, playId, plays, scouting_data, tracking_data):
    """
    Détermine t_event (frame où le QB lance, court, ou se fait sack) d'un jeu.
    """
    playresult = plays.query(f"gameId == {gameId} & playId == {playId}").passResult.values
    qbId = scouting_data.query(f"gameId == {gameId} & playId == {playId} & pff_role == 'Pass'").nflId.values[0]
    event = tracking_data.query(f"gameId == {gameId} & playId == {playId} & nflId == {qbId}").event.values.tolist()
    scramble_data = scramble(gameId, playId, scouting_data, tracking_data)
    frame_qb_run = scramble_data.query(f"nflId == {qbId}").scramble.values.tolist()
    if "ball_snap" in event:
        t_ball_snap = event.index("ball_snap")
    elif "autoevent_ballsnap" in event:
        t_ball_snap = event.index("autoevent_ballsnap")        
    else:
        t_ball_snap = 1
    if 1 in frame_qb_run:
        frame_qb_run = frame_qb_run.index(1) + 1
    else : 
        frame_qb_run = 1e6

    if playresult in ["C","I","IN"]:
        if "pass_forward" in event : 
            t_event = event.index("pass_forward")+1
        elif "autoevent_passforward" in event:
            t_event = event.index("autoevent_passforward")+1
        else:
            t_event = np.max(scramble_data.frameId)
        t_event = [frame_qb_run,t_event][np.argmin([frame_qb_run,t_event])]
        type_event = ["scramble","pass"][np.argmin([frame_qb_run,t_event])]
            
    elif playresult == "S":
        if "qb_sack" in event:
            t_event = event.index("qb_sack")+1
        elif "pass_forward" in event:
            t_event = event.index("pass_forward")+1
        else:
            t_event = np.max(scramble_data.frameId)
        t_event = [frame_qb_run,t_event][np.argmin([frame_qb_run,t_event])]
        type_event = ["scramble","sack"][np.argmin([frame_qb_run,t_event])]
    
    elif playresult == "R":
        if "run" in event:
            t_event = event.index("run")+1
        elif "pass_forward" in event:
            t_event = event.index("pass_forward")+1
        else:
            t_event = np.max(scramble_data.frameId)
        t_event = [frame_qb_run,t_event][np.argmin([frame_qb_run,t_event])]
        type_event = "scramble"
    return [type_event,t_event,t_ball_snap]

def weight_diff(gameId, playId, players_data, scouting_data):
    """
    Calcul la différence de poids entre l'attaquant et le défenseur.
    """
    scouting_data = scouting_data.query(f"gameId == {gameId} & playId == {playId}").loc[:,["nflId","pff_nflIdBlockedPlayer"]]
    scouting_data = scouting_data[~scouting_data["pff_nflIdBlockedPlayer"].isnull()]
    nflId = scouting_data.nflId.tolist()
    nflId.extend(scouting_data.pff_nflIdBlockedPlayer.unique().tolist())
    players_data = players_data.query(f"nflId in {nflId}").loc[:,["nflId","weight"]]
    scouting_data = scouting_data.assign(weight_off = pd.merge(players_data,scouting_data.nflId,on="nflId").weight.values)
    scouting_data = scouting_data.assign(weight_def = pd.merge(players_data.rename(columns={"nflId" : "pff_nflIdBlockedPlayer"}),scouting_data,on="pff_nflIdBlockedPlayer").weight.values)
    scouting_data = scouting_data.assign(weight_diff = scouting_data.weight_off-scouting_data.weight_def)
    return scouting_data

# ------------------------------------------------- #
#                 Machine Learning                  #
# ------------------------------------------------- #

def etl(gameIds, list_feature):
    """Sélectionne et transforme les données pour former un dataframe unique"""
    df_features = list()
    for feature in list_feature :
        feature_set = feature.split(gameIds)
        df_features.append(feature_set.transform())
    df_features = pd.concat(df_features, axis = 1)
    # Fill NA with 0
    df_features = df_features.fillna(0)
    return df_features