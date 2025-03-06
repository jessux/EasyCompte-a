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

def calculate_ca(fec_data):
    # Sélectionner les comptes de classe 70 (sauf 709)
    mask_70 = fec_data['CompteNum'].str.startswith('70') & ~fec_data['CompteNum'].str.startswith('709')
    
    # Calculer le CA brut (crédits - débits des comptes 70)
    ca_brut = fec_data[mask_70]['Credit'].sum() - fec_data[mask_70]['Debit'].sum()
    
    # Soustraire les remises, rabais et ristournes (comptes 709)
    rrr = fec_data[fec_data['CompteNum'].str.startswith('709')]['Credit'].sum()
    
    # Calculer le CA net
    ca_net = ca_brut - rrr
    
    return ca_net

def calculate_achats_consommes(fec_data):
    # Achats (comptes 60, sauf 603)
    achats = fec_data[fec_data['CompteNum'].str.startswith('60') & ~fec_data['CompteNum'].str.startswith('603')]['Debit'].sum()
    
    # Frais accessoires d'achat (comptes 607 et 608)
    frais_accessoires = fec_data[fec_data['CompteNum'].str.startswith(('607', '608'))]['Debit'].sum()
    
    # Variation des stocks (compte 603)
    variation_stocks = (
        fec_data[fec_data['CompteNum'].str.startswith('603')]['Debit'].sum() -
        fec_data[fec_data['CompteNum'].str.startswith('603')]['Credit'].sum()
    )
    
    # Remises, rabais, ristournes obtenus (compte 609)
    rrr = fec_data[fec_data['CompteNum'].str.startswith('609')]['Credit'].sum()
    
    # Calcul final des achats consommés
    achats_consommes = achats + frais_accessoires + variation_stocks - rrr
    
    return achats_consommes

def calculate_fournitures_consommables(fec_data):
    # Fournitures consommables (comptes 602)
    fournitures = fec_data[fec_data['CompteNum'].str.startswith('602')]['Debit'].sum()
    
    # Variation des stocks de fournitures (compte 603)
    variation_stocks_fournitures = (
        fec_data[fec_data['CompteNum'].str.startswith('603')]['Debit'].sum() -
        fec_data[fec_data['CompteNum'].str.startswith('603')]['Credit'].sum()
    )
    
    # Calcul final des fournitures consommables
    fournitures_consomables = fournitures + variation_stocks_fournitures
    
    return fournitures_consomables

def calculate_services_exterieurs(fec_data):
    # Services extérieurs (comptes 61 et 62)
    services_61 = fec_data[fec_data['CompteNum'].str.startswith('61')]['Debit'].sum()
    services_62 = fec_data[fec_data['CompteNum'].str.startswith('62')]['Debit'].sum()
    
    # Rabais, remises et ristournes obtenus (comptes 619 et 629)
    rrr_61 = fec_data[fec_data['CompteNum'].str.startswith('619')]['Credit'].sum()
    rrr_62 = fec_data[fec_data['CompteNum'].str.startswith('629')]['Credit'].sum()
    
    # Calcul final des services extérieurs
    services_exterieurs = services_61 + services_62 - rrr_61 - rrr_62
    
    return services_exterieurs

def calculate_valeur_ajoutee(fec_data):
    # Chiffre d'affaires (comptes 70)
    ca = fec_data[fec_data['CompteNum'].str.startswith('70')]['Credit'].sum()
    
    # Production stockée (compte 71)
    production_stockee = fec_data[fec_data['CompteNum'].str.startswith('71')]['Credit'].sum() - \
                         fec_data[fec_data['CompteNum'].str.startswith('71')]['Debit'].sum()
    
    # Production immobilisée (compte 72)
    production_immobilisee = fec_data[fec_data['CompteNum'].str.startswith('72')]['Credit'].sum()
    
    # Achats consommés (comptes 60 sauf 603)
    achats_consommes = fec_data[fec_data['CompteNum'].str.startswith('60') & 
                                ~fec_data['CompteNum'].str.startswith('603')]['Debit'].sum()
    
    # Variation des stocks (compte 603)
    variation_stocks = fec_data[fec_data['CompteNum'].str.startswith('603')]['Debit'].sum() - \
                       fec_data[fec_data['CompteNum'].str.startswith('603')]['Credit'].sum()
    
    # Services extérieurs (comptes 61 et 62)
    services_exterieurs = fec_data[fec_data['CompteNum'].str.startswith(('61', '62'))]['Debit'].sum()
    
    # Calcul de la valeur ajoutée
    valeur_ajoutee = (ca + production_stockee + production_immobilisee) - \
                     (achats_consommes + variation_stocks + services_exterieurs)
    
    return valeur_ajoutee

def calculate_aides(fec_data):
    # Aides et subventions d'exploitation (comptes 74)
    aides = fec_data[fec_data['CompteNum'].str.startswith('74')]['Credit'].sum()
    
    # Allocation d'activité partielle (compte 6414 ou 6491)
    allocation_activite_partielle = fec_data[fec_data['CompteNum'].isin(['6414', '6491'])]['Credit'].sum()
    
    # Autres transferts de charges liés aux aides (compte 791)
    transferts_charges = fec_data[fec_data['CompteNum'] == '791']['Credit'].sum()
    
    # Total des aides
    total_aides = aides + allocation_activite_partielle + transferts_charges
    
    return total_aides

def calculate_impots_taxes(fec_data):
    # Impôts, taxes et versements assimilés (comptes 63)
    impots_taxes = fec_data[fec_data['CompteNum'].str.startswith('63')]['Debit'].sum()
    
    # Impôt sur les sociétés (compte 695)
    impot_societes = fec_data[fec_data['CompteNum'].str.startswith('695')]['Debit'].sum()
    
    # Contribution sociale sur les bénéfices (compte 697)
    contribution_sociale = fec_data[fec_data['CompteNum'].str.startswith('697')]['Debit'].sum()
    
    # Total des impôts et taxes
    total_impots_taxes = impots_taxes + impot_societes + contribution_sociale
    
    return total_impots_taxes

def calculate_masse_salariale(fec_data):
    # Salaires bruts (compte 641)
    salaires_bruts = fec_data[fec_data['CompteNum'].str.startswith('641')]['Debit'].sum()
    
    # Primes et gratifications (compte 644)
    primes = fec_data[fec_data['CompteNum'].str.startswith('644')]['Debit'].sum()
    
    # Charges sociales (compte 645)
    charges_sociales = fec_data[fec_data['CompteNum'].str.startswith('645')]['Debit'].sum()
    
    # Autres charges de personnel (comptes 647 et 648)
    autres_charges = fec_data[fec_data['CompteNum'].str.startswith(('647', '648'))]['Debit'].sum()
    
    # Calcul de la masse salariale totale
    masse_salariale = salaires_bruts + primes + charges_sociales + autres_charges
    
    return masse_salariale


def calculate_ebe(fec_data):
    # Chiffre d'affaires (comptes 70)
    ca = fec_data[fec_data['CompteNum'].str.startswith('70')]['Credit'].sum()
    
    # Production stockée (compte 71)
    production_stockee = fec_data[fec_data['CompteNum'].str.startswith('71')]['Credit'].sum() - \
                         fec_data[fec_data['CompteNum'].str.startswith('71')]['Debit'].sum()
    
    # Production immobilisée (compte 72)
    production_immobilisee = fec_data[fec_data['CompteNum'].str.startswith('72')]['Credit'].sum()
    
    # Subventions d'exploitation (compte 74)
    subventions = fec_data[fec_data['CompteNum'].str.startswith('74')]['Credit'].sum()
    
    # Achats consommés (comptes 60 sauf 603)
    achats_consommes = fec_data[fec_data['CompteNum'].str.startswith('60') & 
                                ~fec_data['CompteNum'].str.startswith('603')]['Debit'].sum()
    
    # Variation des stocks (compte 603)
    variation_stocks = fec_data[fec_data['CompteNum'].str.startswith('603')]['Debit'].sum() - \
                       fec_data[fec_data['CompteNum'].str.startswith('603')]['Credit'].sum()
    
    # Services extérieurs (comptes 61 et 62)
    services_exterieurs = fec_data[fec_data['CompteNum'].str.startswith(('61', '62'))]['Debit'].sum()
    
    # Impôts et taxes (comptes 63)
    impots_taxes = fec_data[fec_data['CompteNum'].str.startswith('63')]['Debit'].sum()
    
    # Charges de personnel (comptes 64)
    charges_personnel = fec_data[fec_data['CompteNum'].str.startswith('64')]['Debit'].sum()
    
    # Calcul de l'EBE
    ebe = (ca + production_stockee + production_immobilisee + subventions) - \
          (achats_consommes + variation_stocks + services_exterieurs + impots_taxes + charges_personnel)
    
    return ebe

def calculate_rex(fec_data):
    # Calcul de l'EBE (en utilisant la fonction précédente)
    ebe = calculate_ebe(fec_data)
    
    # Autres produits de gestion courante (compte 75)
    autres_produits = fec_data[fec_data['CompteNum'].str.startswith('75')]['Credit'].sum()
    
    # Transferts de charges d'exploitation (compte 791)
    transferts_charges = fec_data[fec_data['CompteNum'].str.startswith('791')]['Credit'].sum()
    
    # Reprises sur amortissements, dépréciations et provisions d'exploitation (compte 781)
    reprises = fec_data[fec_data['CompteNum'].str.startswith('781')]['Credit'].sum()
    
    # Autres charges de gestion courante (compte 65)
    autres_charges = fec_data[fec_data['CompteNum'].str.startswith('65')]['Debit'].sum()
    
    # Dotations aux amortissements, dépréciations et provisions d'exploitation (compte 681)
    dotations = fec_data[fec_data['CompteNum'].str.startswith('681')]['Debit'].sum()
    
    # Calcul du REX
    rex = ebe + autres_produits + transferts_charges + reprises - autres_charges - dotations
    
    return rex

def calculate_rcai(fec_data):
    # Calcul du REX (en utilisant la fonction précédente)
    rex = calculate_rex(fec_data)
    
    # Produits financiers (comptes 76)
    produits_financiers = fec_data[fec_data['CompteNum'].str.startswith('76')]['Credit'].sum()
    
    # Charges financières (comptes 66)
    charges_financieres = fec_data[fec_data['CompteNum'].str.startswith('66')]['Debit'].sum()
    
    # Calcul du résultat financier
    resultat_financier = produits_financiers - charges_financieres
    
    # Calcul du RCAI
    rcai = rex + resultat_financier
    
    return rcai


def calculate_rn(fec_data):
    # Calcul du RCAI (en utilisant la fonction précédente)
    rcai = calculate_rcai(fec_data)
    
    # Produits exceptionnels (comptes 77)
    produits_exceptionnels = fec_data[fec_data['CompteNum'].str.startswith('77')]['Credit'].sum()
    
    # Charges exceptionnelles (comptes 67)
    charges_exceptionnelles = fec_data[fec_data['CompteNum'].str.startswith('67')]['Debit'].sum()
    
    # Participation des salariés (compte 691)
    participation = fec_data[fec_data['CompteNum'].str.startswith('691')]['Debit'].sum()
    
    # Impôt sur les bénéfices (compte 695)
    impot_benefices = fec_data[fec_data['CompteNum'].str.startswith('695')]['Debit'].sum()
    
    # Calcul du résultat exceptionnel
    resultat_exceptionnel = produits_exceptionnels - charges_exceptionnelles
    
    # Calcul du RN
    rn = rcai + resultat_exceptionnel - participation - impot_benefices
    
    return rn


def calculate_financials(fec_data):
    # Prétraitement des données
    fec_data = fec_data.dropna(subset=['CompteNum', 'Debit', 'Credit'])
    fec_data['CompteNum'] = fec_data['CompteNum'].astype(str)
    fec_data['Credit'] = fec_data['Credit'].astype(str)
    fec_data['Debit'] = fec_data['Debit'].astype(str)
    fec_data['Credit'] = fec_data['Credit'].str.replace(",",".").astype(float)
    fec_data['Debit'] = fec_data['Debit'].str.replace(",",".").astype(float)

    # Calcul des indicateurs financiers
    financials = {
        "CA global": calculate_ca(fec_data),
        "Achats consommés": calculate_achats_consommes(fec_data),
        "Fournitures consommables": calculate_fournitures_consommables(fec_data),
        "Services extérieurs": calculate_services_exterieurs(fec_data),
        "Valeur ajoutée": calculate_valeur_ajoutee(fec_data),
        "Aides": calculate_aides(fec_data),
        "Impôts et taxes": calculate_impots_taxes(fec_data),
        "Masse salariale": calculate_masse_salariale(fec_data),
        "EBE": calculate_ebe(fec_data),
        "Résultat d'Exploitation (REX)": calculate_rex(fec_data),
        "Résultat Courant Avant Impôts": calculate_rcai(fec_data),
        "Résultat Net": calculate_rn(fec_data)
    }

    # Calcul de la marge
    financials["Marge"] = financials["CA global"] - financials["Achats consommés"]

    return financials


def calculer_ratios(indicateurs):
    ratios = {
        "Taux de marge brute": (indicateurs["Marge"] / indicateurs["CA global"] * 100) if indicateurs["CA global"] > 0 else 0,
        "Taux de rentabilité nette": (indicateurs["Résultat Net"] / indicateurs["CA global"] * 100) if indicateurs["CA global"] > 0 else 0,
        "Taux de valeur ajoutée": (indicateurs["Valeur ajoutée"] / indicateurs["CA global"] * 100) if indicateurs["CA global"] > 0 else 0,
        "Poids des charges de personnel": (indicateurs["Masse salariale"] / indicateurs["Valeur ajoutée"] * 100) if indicateurs["Valeur ajoutée"] > 0 else 0,
    }
    return ratios
