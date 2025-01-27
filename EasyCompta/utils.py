import pandas as pd
import os
def get_pcg():
    # Exemple étendu de données du PCG incluant les classes 6 et 7
    if os.path.exists("./pcg.xlsx"):
        pcgxls= pd.read_excel("./pcg.xlsx")
    else:
        pcgxls= pd.read_excel("/workspace/pcg.xlsx")

    pcgxls["CompteNum"]=pcgxls["CompteNum"].astype(str)
    pcgxls["CompteNum"]=pcgxls["CompteNum"].apply(add_zero_if_shorter)
    return pcgxls

def add_zero_if_shorter(row, char="0", threshold=2):
    if len(row) <= threshold:
        return row + char
    return row

# Fonction pour générer le bilan comptable
def generer_bilan(fec_data):
    # Actif
    actif_immobilise = fec_data[fec_data['CompteNum'].str.startswith('2')]['Debit'].sum()
    actif_circulant = fec_data[fec_data['CompteNum'].str.startswith('3')]['Debit'].sum()
    tresorerie_actif = fec_data[fec_data['CompteNum'].str.startswith(('50', '51'))]['Debit'].sum()

    total_actif = actif_immobilise + actif_circulant + tresorerie_actif

    # Passif
    capitaux_propres = fec_data[fec_data['CompteNum'].str.startswith('1')]['Credit'].sum()
    dettes = fec_data[fec_data['CompteNum'].str.startswith(('16', '40', '42', '43'))]['Credit'].sum()
    tresorerie_passif = fec_data[fec_data['CompteNum'].str.startswith(('50', '51'))]['Credit'].sum()

    total_passif = capitaux_propres + dettes + tresorerie_passif

    bilan = {
        "Actif Immobilisé": actif_immobilise,
        "Actif Circulant": actif_circulant,
        "Trésorerie (Actif)": tresorerie_actif,
        "Total Actif": total_actif,
        "Capitaux Propres": capitaux_propres,
        "Dettes": dettes,
        "Trésorerie (Passif)": tresorerie_passif,
        "Total Passif": total_passif
    }

    return bilan

def calculate_financials(fec_data):
    # Supprimer les lignes contenant des valeurs manquantes dans les colonnes pertinentes
    fec_data = fec_data.dropna(subset=['CompteNum', 'Debit', 'Credit'])
    fec_data.CompteNum = fec_data.CompteNum.astype(str)
    fec_data.Credit = fec_data.Credit.astype(str)
    fec_data.Debit = fec_data.Debit.astype(str)
    
    fec_data.Credit = fec_data.Credit.str.replace(",",".",regex=False).astype(float)
    fec_data.Debit = fec_data.Debit.str.replace(",",".",regex=False).astype(float)
    # Calculer les indicateurs financiers
    # Total des ventes (CA global)
    ca = fec_data[fec_data['CompteNum'].str.startswith('70')]['Credit'].sum()

    # Achats consommés (comptes 60)
    achats_consommés = fec_data[fec_data['CompteNum'].str.startswith('60')]['Debit'].sum()

    # Fournitures consommables (comptes 602)
    fournitures_consommables = fec_data[fec_data['CompteNum'].str.startswith('602')]['Debit'].sum()

    # Services extérieurs (comptes 61 et 62)
    services_exterieurs = fec_data[fec_data['CompteNum'].str.startswith(('61', '62'))]['Debit'].sum()

    # Valeur ajoutée
    valeur_ajoutee = ca - (achats_consommés + fournitures_consommables + services_exterieurs)

    # Aides (comptes 74)
    aides = fec_data[fec_data['CompteNum'].str.startswith('74')]['Credit'].sum()

    # Impôts et taxes (comptes 63)
    impots_taxes = fec_data[fec_data['CompteNum'].str.startswith('63')]['Debit'].sum()

    # Masse salariale (comptes 64)
    masse_salariale = fec_data[fec_data['CompteNum'].str.startswith('64')]['Debit'].sum()

    # Excédent Brut d'Exploitation (EBE)
    ebe = valeur_ajoutee - (masse_salariale + impots_taxes)

    # Résultat d'Exploitation (REX)
    rex = ebe + fec_data[fec_data['CompteNum'].str.startswith('75')]['Credit'].sum() \
              - fec_data[fec_data['CompteNum'].str.startswith('66')]['Debit'].sum()

    # Résultat Courant Avant Impôts (RCAI)
    rcai = rex - fec_data[fec_data['CompteNum'].str.startswith('68')]['Debit'].sum()

    # Résultat Net (RN)
    rn = rcai - fec_data[fec_data['CompteNum'].str.startswith('69')]['Debit'].sum()

    financials = {
        "CA global": ca,
        "Achats consommés": achats_consommés,
        "Marge": ca - achats_consommés,
        "Fournitures consommables": fournitures_consommables,
        "Services extérieurs": services_exterieurs,
        "Valeur ajoutée": valeur_ajoutee,
        "Aides": aides,
        "Impôts et taxes": impots_taxes,
        "Masse salariale": masse_salariale,
        "EBE": ebe,
        "Résultat d'Exploitation (REX)": rex,
        "Résultat Courant Avant Impôts": rcai,
        "Résultat Net": rn
    }

    return financials

def calculer_ratios(indicateurs):
    ratios = {
        "Taux de marge brute": (indicateurs["Marge"] / indicateurs["CA global"] * 100) if indicateurs["CA global"] > 0 else 0,
        "Taux de rentabilité nette": (indicateurs["Résultat Net"] / indicateurs["CA global"] * 100) if indicateurs["CA global"] > 0 else 0,
        "Taux de valeur ajoutée": (indicateurs["Valeur ajoutée"] / indicateurs["CA global"] * 100) if indicateurs["CA global"] > 0 else 0,
        "Poids des charges de personnel": (indicateurs["Masse salariale"] / indicateurs["Valeur ajoutée"] * 100) if indicateurs["Valeur ajoutée"] > 0 else 0,
    }
    return ratios