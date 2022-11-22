import pandas as pd
import os
import glob
import numpy as np
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
    points = plot_df.loc[mask, ['x', 'y', 'team', 'officialPosition']]
    points = points.reset_index().drop(columns = ['index'])
    return points

def get_Dline_position(selected_tracking_df):
    """Récupère la position des joueurs de la D-line"""
    plot_df = selected_tracking_df.copy()
    mask = plot_df.pff_role.isin(['Pass Rush'])
    points = plot_df.loc[mask, ['x', 'y', 'team', 'officialPosition']]
    points = points.reset_index().drop(columns = ['index'])
    return points

def calculate_voronoi_zones(QB_zone, offensice_points, defensive_points):
    """
    Calcul le graph de Voronoi pour un ensemble de points donnés.
    Inspired by : https://github.com/rjtavares/football-crunching/blob/master/notebooks/using%20voronoi%20diagrams.ipynb
    """
    defensive_points.loc[:, 'isInQBzone'] = False
    for i in range(len(defensive_points)):
        point_x, point_y = defensive_points.iloc[i][['x', 'y']].values
        if Point(point_x, point_y).within(Polygon(QB_zone)):
            defensive_points.loc[i, 'isInQBzone'] = True
    players_points = pd.concat([offensice_points, defensive_points[defensive_points.isInQBzone]]).reset_index().drop(columns = ['index'])
    try :
        region_polys, region_pts = voronoi_regions_from_coords(players_points[["x", "y"]].values, Polygon(QB_zone))
    except : 
        region_polys, region_pts = dict(), dict()
        print("Le calcul du graph de voronoi a échoué")
    return region_polys, region_pts, players_points

def calculate_Oline_zones(points, line_of_scrimmage):
    """Calcule la zone confexe formée par l'ensemble de la D-line + QB"""
    y_max, y_min = 53.3, 0 #points.y.max(), points.y.min()
    x_QB = points[points.officialPosition == 'QB'].iloc[0].x - 1
    init_zone_points = np.array([[x_QB, y_max], [x_QB, y_min], [line_of_scrimmage, y_min], [line_of_scrimmage, y_max]]) #np.concatenate([points.loc[:, ["x", 'y']].values, [[x_QB, y_max], [x_QB, y_min]]])
    hull = ConvexHull(init_zone_points[:, :2])
    return init_zone_points[hull.vertices,:2]

def compute_orientation(data):
    copy = data.copy()
    copy = copy.assign(o_x = np.sin(copy.o*2*np.pi/360))
    copy = copy.assign(o_y = np.cos(copy.o*2*np.pi/360))
    return copy

def face2face(tracking_data, scouting_data):
    """
    run in a for loop to compute for each play at each frame
    """
    blocked_opponent = scouting_data[["nflId","pff_nflIdBlockedPlayer"]]
    #data_with_opp = pd.merge(tracking_data,blocked_opponent,how="outer",on="nflId")
    #print(data_with_opp)
    opp_orientation = pd.merge(tracking_data[["nflId","o_x","o_y"]],blocked_opponent,how="inner",left_on="nflId", right_on="pff_nflIdBlockedPlayer")
    opp_orientation = opp_orientation.rename(columns={"nflId_y" : "nflId"})
    #print(opp_orientation)
    data_with_opp_orientation = pd.merge(tracking_data, opp_orientation[["nflId","o_x","o_y","pff_nflIdBlockedPlayer"]],how="inner",on="nflId")
    data_with_opp_orientation = data_with_opp_orientation.rename(columns={"o_x_x" : "o_x_off", 
                                                                        "o_y_x" : "o_y_off",
                                                                        "o_x_y" : "o_x_def",
                                                                        "o_y_y" : "o_y_def",})

    data_with_opp_orientation["f2f"] = data_with_opp_orientation.o_x_off*data_with_opp_orientation.o_x_def < 0
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
    other = tracking_data.query(f"nflId != {nflId} & gameId == {gameId} & playId == {playId} & frameId == {frameId} & team != 'football'")
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
    Ajoute un booléen à tracking_data indiquant si la balle est dans les mains du QB (1) ou non (0).
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



