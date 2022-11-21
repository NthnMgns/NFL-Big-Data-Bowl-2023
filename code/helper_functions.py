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

test = df.query("playId == '187' & frameId == '1'")
qb = test.query("officialPosition == 'QB'")
test = test.assign(dist_qb = distance_qb(qb.x.values,qb.y.values,test.x.values,test.y.values))       
test.dist_qb  


# ------------------------ #
#       Visualisation      #
# ------------------------ #
    
def plot_play(playid,frameid,data,title):
    """
    Tracer une frame d'un jeu.
    """
    dt = data.query("playId == '" + str(playid) + "' & frameId == '" + str(frameid) + "'")
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
    
    
df.playId.unique()
plot_play(137,1,df,"")

