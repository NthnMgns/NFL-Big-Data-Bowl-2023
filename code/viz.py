import plotly.graph_objects as go
from shapely.geometry import Polygon
import pandas as pd 
import numpy as np 
from helper_functions import *

# ------------------------------------------------------ #
#                   Variables fixes                      #
# ------------------------------------------------------ #

# Couleur des équipes
colors_teams = {
    'ARI':"#97233F", 
    'ATL':"#A71930", 
    'BAL':'#241773', 
    'BUF':"#00338D", 
    'CAR':"#0085CA", 
    'CHI':"#C83803", 
    'CIN':"#FB4F14", 
    'CLE':"#311D00", 
    'DAL':'#003594',
    'DEN':"#FB4F14", 
    'DET':"#0076B6", 
    'GB':"#203731", 
    'HOU':"#03202F", 
    'IND':"#002C5F", 
    'JAX':"#9F792C", 
    'KC':"#E31837", 
    'LA':"#003594", 
    'LAC':"#0080C6", 
    'LV':"#000000",
    'MIA':"#008E97", 
    'MIN':"#4F2683", 
    'NE':"#002244", 
    'NO':"#D3BC8D", 
    'NYG':"#0B2265", 
    'NYJ':"#125740", 
    'PHI':"#004C54", 
    'PIT':"#FFB612", 
    'SEA':"#69BE28", 
    'SF':"#AA0000",
    'TB':'#D50A0A', 
    'TEN':"#4B92DB", 
    'WAS':"#5A1414", 
    'football':'#CBB67C'
}


# ------------------------------------------------------ #
#               Fonctions d'affichage                    #
# ------------------------------------------------------ #
def animate_play(tracking_df, play_df,players,pffScoutingData, gameId,playId, displayZone = False):
    """
    Création du lecteur vidéo pour nos visualisations. 
    Reprise du code : https://www.kaggle.com/code/huntingdata11/animated-and-interactive-nfl-plays-in-plotly/notebook
    """
    selected_play_df = play_df[(play_df.playId==playId)&(play_df.gameId==gameId)].copy()
    
    tracking_players_df = pd.merge(tracking_df,players,how="left",on = "nflId")
    tracking_players_df = pd.merge(tracking_players_df,pffScoutingData,how="left",on = ["nflId","playId","gameId"])
    selected_tracking_df = tracking_players_df[(tracking_players_df.playId==playId)&(tracking_players_df.gameId==gameId)].copy()

    sorted_frame_list = selected_tracking_df.frameId.unique()
    sorted_frame_list.sort()

    # get play General information 
    line_of_scrimmage = selected_play_df.absoluteYardlineNumber.values[0]
    first_down_marker = line_of_scrimmage + selected_play_df.yardsToGo.values[0]
    down = selected_play_df.down.values[0]
    quarter = selected_play_df.quarter.values[0]
    gameClock = selected_play_df.gameClock.values[0]
    playDescription = selected_play_df.playDescription.values[0]
    # Handle case where we have a really long Play Description and want to split it into two lines
    if len(playDescription.split(" "))>15 and len(playDescription)>115:
        playDescription = " ".join(playDescription.split(" ")[0:16]) + "<br>" + " ".join(playDescription.split(" ")[16:])

    # initialize plotly start and stop buttons for animation
    updatemenus_dict = [
        {
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 100, "redraw": False},
                                "fromcurrent": True, "transition": {"duration": 0}}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                      "mode": "immediate",
                                      "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }
    ]
    # initialize plotly slider to show frame position in animation
    sliders_dict = {
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {
            "font": {"size": 20},
            "prefix": "Frame:",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": []
    }

    frames = []
    for frameId in sorted_frame_list:
        data, slider_step = display_1_frame(frameId, line_of_scrimmage, first_down_marker, selected_tracking_df, displayZone)
        sliders_dict["steps"].append(slider_step)
        frames.append(go.Frame(data=data, name=str(frameId)))

    scale=9
    layout = go.Layout(
        autosize=False,
        width=120*scale,
        height=60*scale,
        xaxis=dict(range=[0, 120], autorange=False, tickmode='array',tickvals=np.arange(10, 111, 5).tolist(),showticklabels=False),
        yaxis=dict(range=[0, 53.3], autorange=False,showgrid=False,showticklabels=False),

        plot_bgcolor='#00B140',
        # Create title and add play description at the bottom of the chart for better visual appeal
        title=f"GameId: {gameId}, PlayId: {playId}<br>{gameClock} {quarter}Q", #+"<br>"*19+f"{playDescription}",
        updatemenus=updatemenus_dict,
        sliders = [sliders_dict]
    )

    fig = go.Figure(
        data=frames[0]["data"],
        layout= layout,
        frames=frames[1:]
    )
    # Create First Down Markers 
    for y_val in [0,53]:
        fig.add_annotation(
                x=first_down_marker,
                y=y_val,
                text=str(down),
                showarrow=False,
                font=dict(
                    family="Courier New, monospace",
                    size=16,
                    color="black"
                    ),
                align="center",
                bordercolor="black",
                borderwidth=2,
                borderpad=4,
                bgcolor="#ff7f0e",
                opacity=1
                )
    return fig

def create_field(data, line_of_scrimmage = None, first_down_marker = None):
    """Création du terrain et des lignes"""
    # Add Numbers to Field 
    data.append(
        go.Scatter(
            x=np.arange(20,110,10), 
            y=[5]*len(np.arange(20,110,10)),
            mode='text',
            text=list(map(str,list(np.arange(20, 61, 10)-10)+list(np.arange(40, 9, -10)))),
            textfont_size = 30,
            textfont_family = "Courier New, monospace",
            textfont_color = "#ffffff",
            showlegend=False,
            hoverinfo='none'
        )
    )
    data.append(
        go.Scatter(
            x=np.arange(20,110,10), 
            y=[53.5-5]*len(np.arange(20,110,10)),
            mode='text',
            text=list(map(str,list(np.arange(20, 61, 10)-10)+list(np.arange(40, 9, -10)))),
            textfont_size = 30,
            textfont_family = "Courier New, monospace",
            textfont_color = "#ffffff",
            showlegend=False,
            hoverinfo='none'
        )
    )
    # Add line of scrimage 
    data.append(
        go.Scatter(
            x=[line_of_scrimmage,line_of_scrimmage], 
            y=[0,53.5],
            line_dash='dash',
            line_color='blue',
            showlegend=False,
            hoverinfo='none'
        )
    )
    # Add First down line 
    data.append(
        go.Scatter(
            x=[first_down_marker,first_down_marker], 
            y=[0,53.5],
            line_dash='dash',
            line_color='yellow',
            showlegend=False,
            hoverinfo='none'
        )
    )
    return data

def add_players_viz(data, selected_tracking_df, frameId):
    """Ajoute les joueurs sur la viz du terrain"""
    # Plot Players
    for team in selected_tracking_df.team.unique():
        plot_df = selected_tracking_df[(selected_tracking_df.team==team)&(selected_tracking_df.frameId==frameId)].copy()
        if team != "football":
            hover_text_array=[]
            for nflId in plot_df.nflId:
                selected_player_df = plot_df[plot_df.nflId==nflId]
                hover_text_array.append("nflId:{}<br>displayName:{}<br>Position:{}<br>Role:{}".format(selected_player_df["nflId"].values[0],
                                                                                    selected_player_df["displayName"].values[0],
                                                                                    selected_player_df["pff_positionLinedUp"].values[0],
                                                                                    selected_player_df["pff_role"].values[0]))
            data.append(go.Scatter(x=plot_df["x"], y=plot_df["y"],mode = 'markers', marker_line_width=2, marker_size=10, marker_color=colors_teams[team],name=team,hovertext=hover_text_array,hoverinfo="text"))
        else:
            data.append(go.Scatter(x=plot_df["x"], y=plot_df["y"],mode = 'markers', marker_line_width=2, marker_size=10, marker_color=colors_teams[team],name=team,hoverinfo='none'))
    return data

def add_zone(data, voronoi_points):
    """Colorie les zones de voronoi de chaque joueur"""
    x, y, team = voronoi_points
    data.append(go.Scatter(
            x=x, 
            y=y, 
            mode='lines',
            fill="toself", 
            opacity=0.5,
            fillcolor = colors_teams[team[0]]
            )
        )
    return data

def display_1_frame(frameId, line_of_scrimmage = None, first_down_marker = None, 
            selected_tracking_df = pd.DataFrame(),
            displayZone = False) :
    """Créer l'ensemble des visualisations nécessaires à une frame"""
    data = []
    data = create_field(data, line_of_scrimmage, first_down_marker)
    if displayZone :
        points = get_player_position(selected_tracking_df, frameId)
        #voronoi_points = calculate_voronoi_zones(points)
        D_lines_points = calculate_Oline_zones(points)
        data = add_zone(data, D_lines_points)
    data = add_players_viz(data, selected_tracking_df, frameId)
    # add frame to slider
    slider_step = {"args": [
        [frameId],
        {"frame": {"duration": 100, "redraw": False},
            "mode": "immediate",
            "transition": {"duration": 0}}
    ],
        "label": str(frameId),
        "method": "animate"}

    # TODO 
    # Pour ajouter d'autres visualisation à une figure 
    # Exemple
    if False : 
        data.append(go.Scatter())
    return data, slider_step