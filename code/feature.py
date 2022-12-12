import pandas as pd 
from helper_functions import *
import copy


class Features():
    """
    Classe générique des features. Elle possède plusieurs méthodes communes à tous les features utilisés :
        - read : Lecture des données csv pour les convertir en dataframe
        - split : Permet de récupérer un objet Feature dont les données ne contiennent que celles nécessaire à l'entrainement ou au test.
    """
    def __init__(self):
        self.df_dataraw = pd.DataFrame()
        self.index = ['gameId', 'playId']
        self.needed_data = 'Description of needed data'
        self.is_strata = False

    def read(self, df_data):
        """Lecture des données csv pour les convertir en dataframe. Alimente l'attribut df_dataraw"""
        self.df_dataraw = df_data.copy()
        return self

    def transform(self):
        """Transforme les données brutes pour extraire l'information pertinente de la variable et la mettre en forme selon l'index"""
        return self.df_dataraw

    def split(self, gameIds):
        """Permet de récupérer un objet Feature dont les données ne contiennent que celles nécessaire à l'entrainement ou au test"""
        new_feature = copy.copy(self)
        new_feature.df_dataraw = self.df_dataraw[self.df_dataraw.gameId.isin(gameIds)]
        return new_feature

class GeneralDescriptionPlay(Features):
    """Variable qui reprend plusieurs descriptions de la séquence"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['yardsToGo']
        self.needed_data = "Play Data"

    def transform(self):
        df_transformed_data = self.df_dataraw[self.kept_columns].set_index(self.index)
        return df_transformed_data

class CharacteristicTime(Features):
    """Variable qui renvoie le temps critique de la séquence de jeu"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['tc']
        self.needed_data = "Area Data"

    def transform(self):
        df_transformed_data = self.df_dataraw[self.kept_columns].set_index(self.index)
        return df_transformed_data

class CharacteristicSpeed(Features):
    """Variable qui renvoie la vitesse de décroissance de l'aire de la poche de la séquence de jeu"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['Va']
        self.needed_data = "Area Data"

    def transform(self):
        df_transformed_data = self.df_dataraw.copy()
        df_transformed_data.loc[:, 'Va'] = (self.df_dataraw.Ac - self.df_dataraw.Ae) / (self.df_dataraw.tc - self.df_dataraw.te)
        df_transformed_data = df_transformed_data[self.kept_columns].set_index(self.index)
        return df_transformed_data

class CharacteristicArea(Features):
    """Variable qui renvoie la valeur de l'air au temps critique de la séquence de jeu"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['Ac']
        self.needed_data = "Area Data"
        #self.is_strata = ['Ac_strata']

    def transform(self):
        df_transformed_data = self.df_dataraw.copy()
        df_transformed_data.loc[:, 'Ac_strata'] = pd.cut(df_transformed_data['Ac'], np.arange(0, 200, 10))
        return df_transformed_data[self.kept_columns].set_index(self.index)

class EventTime(Features):
    """Variable qui renvoie la valeur de t event"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['te']
        self.needed_data = "Area Data"

    def transform(self):
        df_transformed_data = self.df_dataraw[self.kept_columns].set_index(self.index)
        return df_transformed_data

class EventArea(Features):
    """Variable qui renvoie la valeur de l'aire à t event"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['Ae']
        self.needed_data = "Area Data"

    def transform(self):
        df_transformed_data = self.df_dataraw[self.kept_columns].set_index(self.index)
        return df_transformed_data

class PocketLifeTime(Features):
    """Variable qui renvoie le temps de vie de la poche"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['PocketLife']
        self.needed_data = "Area Data"

    def transform(self):
        Acrit = 11.2
        df_copy = self.df_dataraw.copy() 
        df_copy = df_copy[df_copy.pff_playAction == False]
        df_copy["PocketLife"] = (Acrit - df_copy.Ae)/(df_copy.Ac - df_copy.Ae) * (df_copy.tc - df_copy.te) + df_copy.te
        # A conserver ? 
        df_copy = df_copy[(df_copy.PocketLife > 0.0)&(df_copy.PocketLife < 100.0)]
        df_transformed_data = df_copy[self.kept_columns].set_index(self.index)
        return df_transformed_data

class NbRusher(Features):
    """Variable qui renvoie le nombre de rusher"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['nbRusher']
        self.needed_data = "Scouting Data"

    def transform(self):
        df_copy = self.df_dataraw.copy()
        df_copy = df_copy.query("pff_role == 'Pass Rush'").groupby(by=self.index).count().reset_index()
        df_copy = df_copy.rename(columns={"pff_role": "nbRusher"})
        df_transformed_data = df_copy[self.kept_columns].set_index(self.index)
        return df_transformed_data

class NbBlock(Features):
    """Variable qui renvoie le nombre de bloqueur"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['nbBlock']
        self.needed_data = "Scouting Data"

    def transform(self):
        df_copy = self.df_dataraw.copy()
        df_copy = df_copy.query("pff_role == 'Pass Block'").groupby(by=self.index).count().reset_index()
        df_copy = df_copy.rename(columns={"pff_role": "nbBlock"})
        df_transformed_data = df_copy[self.kept_columns].set_index(self.index)
        return df_transformed_data

class QBPosition(Features):
    """Variable qui renvoie si le QB est en shotgun ou non."""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ['qbPosition']
        self.needed_data = "Merged players and tracking data"

    def transform(self):
        df_copy = self.df_dataraw.copy()
        df_copy = df_copy.query("frameId == 1")
        qb = df_copy.loc[df_copy["officialPosition"]=="QB",["gameId","playId","x"]]
        football = df_copy.loc[df_copy["team"]=="football",["gameId","playId","x"]]
        data = pd.merge(qb,football,on=["gameId","playId"])
        data = data.assign(diff = np.abs(data.x_x - data.x_y))
        data = data.assign(qbPosition = 0)
        data.loc[data["diff"] > 2,"qbPosition"] = 1
        df_transformed_data = data[self.kept_columns].drop_duplicates(subset = ['playId', 'gameId'])     
        return df_transformed_data.set_index(self.index)  
    
class WeightDiffMatchup(Features):
    """Variable qui renvoie la différence de poids entre l'attaquant et le défenseur."""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ["matchup" + str(i) for i in np.arange(1,8)]
        self.needed_data = "Processed data with weight_diff function"

    def transform(self):
        df_transformed_data = self.df_dataraw[self.kept_columns].set_index(self.index)
        return df_transformed_data
    
class SurvivalData(Features):
    """Variable nécessaire à entrainer un model de survie : n_Durée et b_IsMort"""
    def __init__(self):
        super().__init__()
        self.kept_columns = self.index + ["duration", "death"]
        self.needed_data = "Merge Area_feature with play"

    def transform(self):
        df_transformed_data = self.df_dataraw.copy()
        # Enlève les playAction
        df_transformed_data = df_transformed_data[df_transformed_data.pff_playAction == 0]
        # Calcule la durée de vie de l'action 
        df_transformed_data.loc[:, 'duration'] = (df_transformed_data.te - df_transformed_data.tsnap)
        df_transformed_data = df_transformed_data[df_transformed_data.duration > 0]
        # La poche a survécu ? 
        df_transformed_data.loc[:, 'death'] = df_transformed_data.event.apply(lambda x : 0 if x == 'pass' else 1)
        return df_transformed_data[self.kept_columns].set_index(self.index)


# ------------------------------------------------- #
#                 Machine Learning                  #
# ------------------------------------------------- #

def etl(gameIds, list_feature):
    """Sélectionne et transforme les données pour former un dataframe unique"""
    df_features = list()
    strata_list = list()
    for feature in list_feature :
        feature_set = feature.split(gameIds)
        df_features.append(feature_set.transform())
        if feature.is_strata :
            strata_list += feature.is_strata
        #print(feature_set.transform().head())
    df_features = pd.concat(df_features, axis = 1)
    # Drop no data lt
    df_features = df_features.dropna(subset=['death', 'duration'])
    # Fill NA with 0
    df_features = df_features.fillna(0)
    return df_features, strata_list