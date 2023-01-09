import pandas as pd
import numpy as np
from helper_functions import *
from viz import *
pio.renderers.default = "browser"


# ------------------------------------------------------ #
#       Importations des données - Data Management       #
# ------------------------------------------------------ #

## Statistiques classiques ##
df_scouting = pd.read_csv("data/pffScoutingData.csv")
df_games = pd.read_csv("data/games.csv")
df_plays = pd.read_csv("data/plays.csv")
stat_off = get_stat(df_scouting, df_plays, "possessionTeam")
stat_def = get_stat(df_scouting, df_plays, "defensiveTeam")
df_scouting_test = data_by_week(df_scouting, df_games, [6,7,8])
stat_off_test = get_stat(df_scouting_test, df_plays, "possessionTeam")
# stat_off_test.to_csv("offense_stats_test.csv",index=False)
stat_def_test = get_stat(df_scouting_test, df_plays, "defensiveTeam")
# stat_def_test.to_csv("defense_stats_test.csv",index=False)

## Mean area ##
area_off_test = pd.read_csv("offense_mean_area.csv").rename(columns={"team":"possessionTeam"})
area_off = pd.read_csv("offense_mean_area_all.csv").rename(columns={"team":"possessionTeam"})
df_area_off = pd.merge(area_off,stat_off,how = "left", on = "possessionTeam")
area_def_test = pd.read_csv("defense_mean_area.csv").rename(columns={"team":"defensiveTeam"})
area_def = pd.read_csv("defense_mean_area_all.csv").rename(columns={"team":"defensiveTeam"})
df_area_def = pd.merge(area_def,stat_def,how = "left", on = "defensiveTeam")

## Success ##
xsp = pd.read_csv("xPL.csv")
xsp = pd.merge(xsp, df_plays, how = "left", on = ["gameId","playId"])
xsp = xsp.loc[:,["possessionTeam","defensiveTeam","xSuccessPocket"]]
xsp_off = xsp.groupby("possessionTeam").sum().reset_index()
xsp_off = pd.merge(xsp_off,stat_off_test,how = "left", on = "possessionTeam")
xsp_def = xsp.groupby("defensiveTeam").sum().reset_index()
xsp_def = pd.merge(xsp_def,stat_def_test,how = "left", on = "defensiveTeam")

## PCA ##
acp_offense = pd.read_csv("acp_offense.csv")


# ------------------------------------------------------ #
#                  Validation mean area                  #
# ------------------------------------------------------ #

## Offense ##
data = df_area_off.groupby("n_sack").mean()
np.corrcoef(data.index,data.meanArea) # -0.44
np.corrcoef(df_area_off.n_sack,df_area_off.meanArea) # -0.26
fig_2D_plot_team(df_area_off, "n_sack", "meanArea", "possessionTeam", x_legend = "Number of sack", y_legend = "Mean area", imagette_size = 1)

## Defense ##
data = df_area_def.groupby("n_sack").mean()
np.corrcoef(data.index,data.meanArea) # -0.38
np.corrcoef(df_area_def.n_sack,df_area_def.meanArea) # -0.25
fig_2D_plot_team(df_area_def, "n_sack", "meanArea", "defensiveTeam", imagette_size = 0.6)


# ------------------------------------------------------ #
#                Validation success pocket               #
# ------------------------------------------------------ #

## Offense ##
np.corrcoef(xsp_off.n_sack,xsp_off.xSuccessPocket) # -0.35
fig_2D_plot_team(xsp_off, "n_sack", "xSuccessPocket", "possessionTeam", imagette_size = 1.5)

## Defense ##
np.corrcoef(xsp_def.n_sack,xsp_def.xSuccessPocket) # -0.20
fig_2D_plot_team(xsp_def, "n_sack", "xSuccessPocket", "defensiveTeam", imagette_size = 1)


# ------------------------------------------------------ #
#                 Graphique area/success                 #
# ------------------------------------------------------ #

## Offense ##
data_off = pd.merge(xsp_off,area_off_test,how="left",on = "possessionTeam")
np.corrcoef(data_off.xSuccessPocket,data_off.meanArea) # -0.06
data_off.loc[:,"xSuccessPocket"] = data_off.loc[:,"xSuccessPocket"] - np.mean(data_off.loc[:,"xSuccessPocket"])
data_off.loc[:,"meanArea"] = data_off.loc[:,"meanArea"] - np.mean(data_off.loc[:,"meanArea"])
fig_2D_plot_team(data_off, "xSuccessPocket", "meanArea", "possessionTeam", x_legend = "PSOTE", y_legend = "Mean area", plot_title = "PSOTE and Mean area for O-line (computed on weeks 6, 7 and 8)", imagette_size = 1)

## Defense ##
data_def = pd.merge(xsp_def,area_def_test,how="left",on = "defensiveTeam")
np.corrcoef(data_def.xSuccessPocket,data_def.meanArea) # -0.16
data_def.loc[:,"xSuccessPocket"] = data_def.loc[:,"xSuccessPocket"] - np.mean(data_def.loc[:,"xSuccessPocket"])
data_def.loc[:,"meanArea"] = data_def.loc[:,"meanArea"] - np.mean(data_def.loc[:,"meanArea"])
fig_2D_plot_team(data_def, "xSuccessPocket", "meanArea", "defensiveTeam", imagette_size = 0.8)



# ------------------------------------------------------ #
#                 Validation area/success                #
# ------------------------------------------------------ #

## Offense ##
fig_2D_plot_team(acp_offense, "dim1", "dim2", "team", x_legend = "Dim 1", y_legend = "Dim 2", plot_title = "PCA on the number of sack, hurry and hit for O-line (weeks 6, 7 and 8)", imagette_size = 0.4)

