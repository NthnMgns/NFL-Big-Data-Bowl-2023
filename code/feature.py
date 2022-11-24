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
        self.kept_columns = self.index + ['down', 'yardsToGo', 'absoluteYardlineNumber', 'defendersInBox']
        self.needed_data = "Play Data"

    def transform(self):
        df_transformed_data = self.df_dataraw[self.kept_columns].set_index(self.index)
        return df_transformed_data

class CharacteristicTime(Features):
    """Variable qui renvoie le temps critique de la séquence de jeu"""
    def __init__(self):
        super().__init__()

    def transform(self):
        df_transformed_data = self.df_dataraw[self.index + ["tc"]].set_index(self.index)
        return df_transformed_data

class CharacteristicArea(Features):
    """Variable qui renvoie la valeur de l'air au temps critique de la séquence de jeu"""
    def __init__(self):
        super().__init__()

    def transform(self):
        df_transformed_data = self.df_dataraw[self.index + ["Ac"]].set_index(self.index)
        return df_transformed_data

class EventTime(Features):
    """Variable qui renvoie la valeur de t event"""
    def __init__(self):
        super().__init__()

    def transform(self):
        df_transformed_data = self.df_dataraw[self.index + ["te"]].set_index(self.index)
        return df_transformed_data

class EventArea(Features):
    """Variable qui renvoie la valeur de l'aire à t event"""
    def __init__(self):
        super().__init__()

    def transform(self):
        df_transformed_data = self.df_dataraw[self.index + ["Ae"]].set_index(self.index)
        return df_transformed_data

class PocketLifeTime(Features):
    """Variable qui renvoie le temps de vie de la poche"""
    def __init__(self):
        super().__init__()

    def transform(self):
        Acrit = 10
        df_copy = copy.copy(self) # Self est un objet Feature pas un dataframe ;) 
        df_copy["lt"] = (Acrit - df_copy.Ae)/(df_copy.Ac - df_copy.Ae) * (df_copy.tc - df_copy.te) +df_copy.te
        df_transformed_data = df_copy[df_copy.index + ["lt"]].set_index(df_copy.index)
        return df_transformed_data

class NbRusher(Features):
    """Variable qui renvoie le nombre de rusher"""
    def __init__(self):
        super().__init__()

    def transform(self):
        df_copy = copy.copy(self)
        df_copy = df_copy.query("pff_role == 'Pass Rush'").groupby(by=df_copy.index).count()
        df_copy = df_copy.rename(columns={"pff_role": "nbRusher"})
        df_transformed_data = df_copy[df_copy.index + ["nbRusher"]].set_index(df_copy.index)
        return df_transformed_data

    
class NbBlock(Features):
    """Variable qui renvoie le nombre de bloqueur"""
    def __init__(self):
        super().__init__()

    def transform(self):
        df_copy = copy.copy(self)
        df_copy = df_copy.query("pff_role == 'Pass Block'").groupby(by=df_copy.index).count()
        df_copy = df_copy.rename(columns={"pff_role": "nbBlock"})
        df_transformed_data = df_copy[df_copy.index + ["nbBlock"]].set_index(df_copy.index)
        return df_transformed_data

class QBPosition(Features):
    """
    Variable qui renvoie si le QB est en shotgun ou non.
    Nécessite les données de tracking et de scouting.
    """
    def __init__(self):
        super().__init__()

    def transform(self):
        df_transformed_data = self.df_dataraw[self.index + ["qbPosition"]].set_index(self.index)
        return df_transformed_data
    
class WeightDiffMatchup(Features):
    """
    Variable qui renvoie la différence de poids entre l'attaquant et le défenseur.
    Nécessite les données sur les joueurs et de scouting.
    """
    def __init__(self):
        super().__init__()

    def transform(self):
        df_transformed_data = self.df_dataraw[self.index + ["weigth_diff"]].set_index(self.index)
        return df_transformed_data
    
