import pandas as pd
import unicodedata
from io import StringIO

# === FONCTIONS DE NETTOYAGE ===
def remove_accents(text):
    if isinstance(text, str):
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text

# === CHARGEMENT ET NETTOYAGE DU FICHIER ===
def nettoyer_fichier_csv(fichier_csv):
    with open(fichier_csv, encoding='latin1') as f:
        lignes = f.readlines()

    # Identifier la ligne d'en-tête
    index_entete = next(i for i, ligne in enumerate(lignes) if "Nom de l" in ligne)

    # Extraire les lignes utiles
    lignes_utiles = lignes[index_entete:]
    texte_utiles = ''.join(lignes_utiles)

    # Charger dans un DataFrame
    df = pd.read_csv(StringIO(texte_utiles), sep=';')

    # Nettoyer les noms de colonnes
    df.columns = [
        remove_accents(col).strip().lower().replace(" ", "_") 
        for col in df.columns
    ]

    # Nettoyer les cellules
    df = df.applymap(remove_accents)

    # Supprimer les lignes vides
    df.dropna(how='all', inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df

# === UTILISATION ===
# Le fichier CSV doit être dans le même dossier que ce script
nom_fichier = "arret_bus_agde.csv"  # attention, sans accent ici
df_nettoye = nettoyer_fichier_csv(nom_fichier)

# Enregistrer le résultat dans un nouveau fichier
nom_fichier_sortie = "arret_agde_bus_nettoye.csv"
df_nettoye.to_csv(nom_fichier_sortie, index=False)

print(f"Fichier nettoyé enregistré sous : {nom_fichier_sortie}")
