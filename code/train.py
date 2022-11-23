import pandas as pd 
import numpy as np
from helper_functions import *
from feature import * 

from sklearn.gaussian_process import GaussianProcessRegressor

# ------------------------------------------------------ #
#                      Input Data                        #
# ------------------------------------------------------ #

# Dataframe
df_play = pd.read_csv("data/plays.csv")
df_area = pd.read_csv("data/plays.csv")

# TODO Simulation de données à supprimer
df_area["t_c"] = [np.random.random() for i in range(len(df_area))]

# ------------------------------------------------------ #
#                  Feature Choice                        #
# ------------------------------------------------------ #

list_feature = [
    GeneralDescriptionPlay().read(df_play),
    CriticalTime().read(df_area),
]

# ------------------------------------------------------ #
#                     ML process                         #
# ------------------------------------------------------ #
# Split data
gameIds_train = pd.read_csv("data/week1.csv").gameId.unique()
gameIds_test = pd.read_csv("data/week2.csv").gameId.unique()

# ETL for features
df_train = etl(gameIds_train, list_feature)
df_test = etl(gameIds_test, list_feature)
print(df_train.head())

# Train
model = GaussianProcessRegressor()
X_train, y_train = df_train.drop(columns = ['t_c']), df_train.loc[:, 't_c']
model.fit(X_train, y_train)

# Test
X_test, y_test = df_test.drop(columns = ['t_c']), df_test.loc[:, 't_c']
y_pred = model.predict(X_test)
print(y_pred)

# Error Metric 
print(abs(y_pred - y_test).mean())