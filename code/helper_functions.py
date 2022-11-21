import pandas as pd
import os
import glob
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = "browser"

from scipy.spatial import Voronoi, ConvexHull
from shapely.geometry import Polygon

# ------------------------------------------------------ #
#                 Définition de la poche                 #
# ------------------------------------------------------ #

def get_player_position(selected_tracking_df, frameId):
    """Récupère la position des joueurs sur le terrain pour une frame donnée (selected_tracking_df, frame)"""
    points = list()
    for team in selected_tracking_df.team.unique():
        plot_df = selected_tracking_df[(selected_tracking_df.team==team)&(selected_tracking_df.frameId==frameId)].copy()
        if team != "football":
            mask = plot_df.pff_role.isin(['Pass Block', 'Pass'])
            #mask = plot_df.index
            points.append(plot_df.loc[mask, ['x', 'y', 'team', 'officialPosition']])
    points = pd.concat(points).reset_index().drop(columns = ['index'])
    return points

def calculate_voronoi_zones(points):
    """
    Calcul le graph de Voronoi pour un ensemble de points donnés.
    Inspired by : https://github.com/rjtavares/football-crunching/blob/master/notebooks/using%20voronoi%20diagrams.ipynb
    """
    vor = Voronoi(points.loc[:, ["x", 'y']].values)
    point_region = list(vor.point_region[:-4])
    # A investir
    for i in list(point_region):
        if not i in points.index.tolist() :
            point_region.remove(i)
    points.loc[point_region, 'region'] = [i for i in range(len(point_region))]
    voronoi_zone_points = list()
    for index, region in enumerate(vor.regions):
        if not -1 in region:
            if len(region)>0:
                pl = points[points['region']==index]
                team = pl.iloc[0].team if not pl.empty else None
                polygon = Polygon([vor.vertices[i] for i in region])
                x, y = polygon.exterior.xy
                voronoi_zone_points.append([list(x), list(y), team])
    return voronoi_zone_points 

def calculate_Oline_zones(points):
    hull = ConvexHull(points.loc[:, ["x", 'y']].values)
    np_points = points.loc[:, ["x", 'y', 'team']].values
    return np_points[hull.vertices,0], np_points[hull.vertices,1], np_points[hull.vertices,2]

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






