import pandas as pd
import os
import glob
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = "browser"


# ------------------------------------------------------ #
#       Importations des données - Data Management       #
# ------------------------------------------------------ #

path = os.path.join(os.getcwd(),"data")
csv_files = glob.glob(os.path.join(path, "*.csv"))

for f in csv_files:
    name = os.path.basename(f).replace(".csv", "")    
    globals()[f"df_{name}"] = pd.read_csv(f)
    
    print("Path: ", f)
    print("Filename: ", f.split("\\")[-1])

df = pd.merge(df_games,df_plays,how="inner",on="gameId")
df = pd.merge(df,df_week1,how="inner",on=["gameId","playId"])
df = pd.merge(df,df_players,how="left",on="nflId")



def distance_qb(x_qb,y_qb,x,y):
    dist = np.sqrt((x_qb-x)**2+(y_qb-y)**2)
    return dist

test = df.query("playId == 187 & frameId == 1")
qb = test.query("officialPosition == 'QB'")
test = test.assign(dist_qb = distance_qb(qb.x.values,qb.y.values,test.x.values,test.y.values))       
test.dist_qb  


draft_scouting = df_pffScoutingData.query(f"playId == 187 & gameId == {np.unique(test.gameId)}")

# ------------------------ #
#       Visualisation      #
# ------------------------ #
    
def plot_play(playid,frameid,data,title):
    """
    Tracer une frame d'un jeu.
    """
    dt = data.query(f"playId == {playid} & frameId == {frameid}")
    fig = go.Figure(layout_yaxis_range=[0,53.3],
                    layout_xaxis_range=[0,120])
    colors = {dt.team.unique()[0]:"blue", dt.team.unique()[1]:"red", dt.team.unique()[2]:"black"}
    for team in dt.team.unique():
        plot_data = dt[(dt.team==team)]
        fig.add_trace(go.Scatter(x=plot_data["x"],y=plot_data["y"],mode="markers",marker_color=colors[team],name=team))
    
    fig.update_layout(title=f"Week {dt.week.unique()[0]} : {dt.team.unique()[0]} VS {dt.team.unique()[1]} - Play {playid} frame {frameid}",
                    legend_title="Team",
                    plot_bgcolor="green")
    fig.show()

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
    #print(data_with_opp_orientation)

#df.playId.unique()
#plot_play(137,1,df,"")





