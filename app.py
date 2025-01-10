import streamlit as st
import pandas as pd
import plotly.express as px
import time
from EasyCompta.utils import get_pcg
import numpy as np
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
st.set_page_config(page_title="EasyCompta", layout="wide")


def calculate_financials(data):
    # Supprimer les lignes contenant des valeurs manquantes dans les colonnes pertinentes
    data = data.dropna(subset=['CompteNum', 'Debit', 'Credit'])
    data.CompteNum = data.CompteNum.astype(str)
    data.Credit = data.Credit.astype(str)
    data.Debit = data.Debit.astype(str)
    
    
    data.Credit = data.Credit.str.replace(",",".").astype(float)
    data.Debit = data.Debit.str.replace(",",".").astype(float)
    # Calculer les indicateurs financiers
    ca = data[data['CompteNum'].str.startswith('7')]['Credit'].sum() - data[data['CompteNum'].str.startswith('7')]['Debit'].sum()
    achats_consommés = data[data['CompteNum'].str.startswith(('6'))]['Debit'].sum() - data[data['CompteNum'].str.startswith(('6'))]['Credit'].sum()
    marge = ca - achats_consommés
    fournitures_consommables = data[data['CompteNum'].str.startswith('60')]['Debit'].sum() - data[data['CompteNum'].str.startswith('60')]['Credit'].sum()
    services_exterieurs = data[data['CompteNum'].str.startswith('611','612','613','614','615','616','617','618') | data['CompteNum'].str.startswith('62')]['Debit'].sum() - data[data['CompteNum'].str.startswith('61') | data['CompteNum'].str.startswith('62')]['Credit'].sum()
    valeur_ajoutee = marge - fournitures_consommables - services_exterieurs
    aides = data[data['CompteNum'].str.startswith('74')]['Credit'].sum() - data[data['CompteNum'].str.startswith('74')]['Debit'].sum()
    impots_taxes = data[data['CompteNum'].str.startswith('63')]['Debit'].sum() - data[data['CompteNum'].str.startswith('63')]['Credit'].sum()
    masse_salariale = data[data['CompteNum'].str.startswith('64')]['Debit'].sum() - data[data['CompteNum'].str.startswith('64')]['Credit'].sum()
    ebe = valeur_ajoutee + aides - impots_taxes - masse_salariale

    return {
        "CA global": ca,
        "Achats consommés": achats_consommés,
        "Marge": marge,
        "Fournitures consommables": fournitures_consommables,
        "Services extérieurs": services_exterieurs,
        "Valeur ajoutée": valeur_ajoutee,
        "Aides": aides,
        "Impôts et taxes": impots_taxes,
        "Masse salariale": masse_salariale,
        "EBE": ebe
    }

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

# Définir les colonnes du DataFrame
columns = ["JournalCode", "JournalLib", "EcritureNum", "EcritureDate", "CompteNum", "CompteLib", 
           "CompAuxNum", "CompAuxLib", "PieceRef", "PieceDate", "EcritureLib", "Debit", 
           "Credit", "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"]

# Titre du tableau de bord
pcg_df=pd.DataFrame(get_pcg())
load_data = st.container(border=True)

# Téléchargement du fichier FEC
uploaded_file = load_data.file_uploader("Télécharger un fichier FEC (.xlsx, .csv, .txt)", type=['xlsx', 'csv', 'txt'])

personal_pcg = st.checkbox("Voulez-vous ajouter votre propre PCG ?")

if personal_pcg:
    st.write("Merci de fournir un pcg au format CompteNum;Libellé")
    # Téléchargement du fichier FEC
    pcg_perso = load_data.file_uploader("Télécharger un fichier PCG (.xlsx, .csv, .txt) avec un séparateur ;", type=['xlsx', 'csv', 'txt'])
    # Détection du type de fichier et chargement dans un DataFrame
    if pcg_perso:
        if pcg_perso.name.endswith('.xlsx'):
            pcg_df = pd.read_excel(pcg_perso, names=["CompteNum","Libellé"])
        elif pcg_perso.name.endswith('.csv'):
            pcg_df = pd.read_csv(pcg_perso, sep=';', names=["CompteNum","Libellé"])
        elif pcg_perso.name.endswith('.txt'):
            pcg_df = pd.read_csv(pcg_perso, sep=';', names=["CompteNum","Libellé"])

if uploaded_file:
    # Détection du type de fichier et chargement dans un DataFrame
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file, names=columns)
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, sep=';', names=columns)
    elif uploaded_file.name.endswith('.txt'):
        df = pd.read_csv(uploaded_file,  sep='\t', lineterminator='\r', names=columns, encoding='latin1',header=0)
    # Formattage des dates
    df['EcritureDate'] = pd.to_datetime(df['EcritureDate'], format="%Y%m%d",errors="coerce")
    df=df.dropna(subset = ['EcritureDate'])
    df['Année'] = df['EcritureDate'].dt.strftime("%Y")
    df['Mois'] = df['EcritureDate'].dt.month_name("Fr")
    df["ANMOIS"] = df["Année"]+"-"+df["Mois"]
    df['EcritureDate'] =df['EcritureDate'].dt.strftime("%Y/%m/%d")
    df['PieceDate'] = pd.to_datetime(df['PieceDate'], format="%Y%m%d",errors="coerce").dt.strftime("%Y/%m/%d")
    df['DateLet'] = pd.to_datetime(df['DateLet'],format="%Y%m%d",errors="coerce").dt.strftime("%Y/%m/%d")
    df['ValidDate'] = pd.to_datetime(df['ValidDate'],format="%Y%m%d",errors="coerce").dt.strftime("%Y/%m/%d")
    df["CompteNum"]=df["CompteNum"].astype(str)
    df["PieceRef"] = df["PieceRef"].astype(str)

    years_options = df.ANMOIS.unique()
    years_selection = st.segmented_control(
        "Séléction pour filtre : Années-mois", years_options, selection_mode="multi"
    )
    progress_text = "Chargement des indicateurs en cours. Merci de patienter..."

    pcg_df.CompteNum = pcg_df.CompteNum.str.ljust(df.CompteNum.str.len().max(),'0')
    df.CompteNum = df.CompteNum.str.ljust(df.CompteNum.str.len().max(),'0')

    df = df.merge(pcg_df,how="left",on="CompteNum")
    df = df.rename(columns={"Libellé":"Libellé PCG"})
    ownfilterdf = filter_dataframe(df)
    st.dataframe(ownfilterdf)
    my_bar = st.progress(0, text=progress_text)
    # Convertir les colonnes 'Debit' et 'Credit' en numérique
    df.Credit = df.Credit.astype(str)
    df.Debit = df.Debit.astype(str)
    
    df['Debit'] = df['Debit'].str.replace(',', '.').astype(float)
    df['Credit'] = df['Credit'].str.replace(',', '.').astype(float)

    # Ajouter une colonne avec le montant net (Credit - Debit)
    df['Solde'] = df['Debit'] - df['Credit']
    df['Solde'] = df['Solde'].astype(str).str.replace(',','.').astype(float)
    # Filtrage par année et mois

    # selected_months = load_data.selectbox("Sélectionner les mois", months)
    if years_selection:# and selected_months == "Tous les mois":
        filtered_df = df[df['ANMOIS'].isin(years_selection)]
        filtered_dfn1= df[~df['ANMOIS'].isin(years_selection)]
    else:
        filtered_df = df
        filtered_dfn1=None

    ca = filtered_df[filtered_df["CompteNum"].str.contains("^7.*")]["Solde"].sum()*-1
    achats_consommés = filtered_df[filtered_df['CompteNum'].str.contains('^603.*|^607.*')]["Solde"].sum()
    marge = ca - achats_consommés
    fournitures_consommables = filtered_df[filtered_df["CompteNum"].str.contains('^602.*|^606.*')]["Solde"].sum()
    services_exterieurs = filtered_df[filtered_df["CompteNum"].str.contains('^61.*|^62.*')]["Solde"].sum()
    valeur_ajoutee = marge - fournitures_consommables - services_exterieurs
    aides = filtered_df[filtered_df['CompteNum'].str.startswith('74')]["Solde"].sum()
    impots_taxes = filtered_df[filtered_df['CompteNum'].str.startswith('63')]["Solde"].sum()
    masse_salariale = filtered_df[filtered_df['CompteNum'].str.startswith('64')]["Solde"].sum()
    ebe = valeur_ajoutee + aides - impots_taxes - masse_salariale
    ammortissements_provisions = filtered_df[filtered_df["CompteNum"].str.contains("^681.*")]["Solde"].sum()
    transfert_charges = filtered_df[filtered_df["CompteNum"].str.contains("^791.*|^796.*|^797.*")]["Solde"].sum()
    autres_produits = filtered_df[filtered_df["CompteNum"].str.contains("^75.*")]["Solde"].sum()
    autres_charges = filtered_df[filtered_df["CompteNum"].str.contains("^65.*")]["Solde"].sum()
    rex = ebe - ammortissements_provisions +transfert_charges + autres_produits - autres_charges
    charges_financiere = filtered_df[filtered_df["CompteNum"].str.contains("^66.*|^686.*")]["Solde"].sum()
    produits_financiers = filtered_df[filtered_df["CompteNum"].str.contains("^76.*")]["Solde"].sum()
    rcai = rex - charges_financiere + produits_financiers
    charges_exceptionnels = filtered_df[filtered_df["CompteNum"].str.contains("^67.*")]["Solde"].sum()
    produits_exceptionnels = filtered_df[filtered_df["CompteNum"].str.contains("^77.*")]["Solde"].sum()
    participation_salaries = filtered_df[filtered_df["CompteNum"].str.contains("^69.*")]["Solde"].sum()
    impots_societe = filtered_df[filtered_df["CompteNum"].str.contains("^695.*")]["Solde"].sum()
    rn = rcai - charges_exceptionnels + produits_exceptionnels - participation_salaries - impots_societe
    financials = {
        "CA global": ca,
        "Achats consommés": achats_consommés,
        "Marge": marge,
        "Fournitures consommables": fournitures_consommables,
        "Services extérieurs": services_exterieurs,
        "Valeur ajoutée": valeur_ajoutee,
        "Aides": aides,
        "Impôts et taxes": impots_taxes,
        "Masse salariale": masse_salariale,
        "EBE": ebe,
        "Résultat d'Exploitation (REX)":rex,
        "Résultat Courant Avant Impôts":rcai,
        "Résultat Net":rn
    }

    if filtered_dfn1 is not None:
        ca1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^7.*")]["Solde"].sum()*-1
        achats_consommés1= filtered_dfn1[filtered_dfn1['CompteNum'].str.contains('^603.*|^607.*')]["Solde"].sum()
        marge1= ca1 - achats_consommés1
        fournitures_consommables1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains('^602.*|^606.*')]["Solde"].sum()
        services_exterieurs1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains('^61.*|^62.*')]["Solde"].sum()
        valeur_ajoutee1 = marge1 - fournitures_consommables1 - services_exterieurs1
        aides1 = filtered_dfn1[filtered_dfn1['CompteNum'].str.startswith('74')]["Solde"].sum()
        impots_taxes1 = filtered_dfn1[filtered_dfn1['CompteNum'].str.startswith('63')]["Solde"].sum()
        masse_salariale1 = filtered_dfn1[filtered_dfn1['CompteNum'].str.startswith('64')]["Solde"].sum()
        ebe1 = valeur_ajoutee1 + aides1 - impots_taxes1 - masse_salariale1

        ammortissements_provisions1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^681.*")]["Solde"].sum()
        transfert_charges1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^791.*|^796.*|^797.*")]["Solde"].sum()
        autres_produits1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^75.*")]["Solde"].sum()
        autres_charges1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^65.*")]["Solde"].sum()
        rex1 = ebe - ammortissements_provisions1 +transfert_charges1 + autres_produits1 - autres_charges1
        charges_financiere1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^66.*|^686.*")]["Solde"].sum()
        produits_financiers1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^76.*")]["Solde"].sum()
        rcai1 = rex1 - charges_financiere1 + produits_financiers1
        charges_exceptionnels1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^67.*")]["Solde"].sum()
        produits_exceptionnels1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^77.*")]["Solde"].sum()
        participation_salaries1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^69.*")]["Solde"].sum()
        impots_societe1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^695.*")]["Solde"].sum()
        rn1 = rcai1 - charges_exceptionnels1 + produits_exceptionnels1 - participation_salaries1 - impots_societe1

        financials1 = {
            "CA global": ca1,
            "Achats consommés": achats_consommés1,
            "Marge": marge1,
            "Fournitures consommables": fournitures_consommables1,
            "Services extérieurs": services_exterieurs1,
            "Valeur ajoutée": valeur_ajoutee1,
            "Aides": aides1,
            "Impôts et taxes": impots_taxes1,
            "Masse salariale": masse_salariale1,
            "EBE": ebe1,
            "Résultat d'Exploitation (REX)":rex1,
            "Résultat Courant Avant Impôts":rcai1,
            "Résultat Net":rn1
        }
    
    my_bar.progress(20, text=progress_text)
    my_bar.empty()
    
    c = st.container(border=True)
    c.write("### Indicateurs financiers")
    col1,col2,col3,col4 = c.columns(4)
    i = 0
    for key, value in financials.items():
        formatted_value = f"{value:,.2f}".replace(',', ' ')
        delta  = 0
        if filtered_dfn1 is not None:
            if not financials1[key] == 0.0:
                delta = round(value - financials1[key],2)
            if i%4==0:
                col1.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé aux périodes non séléctionnées")
            elif i%4==1:
                col2.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé aux périodes non séléctionnées")
            elif i%4==2:
                col3.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé aux périodes non séléctionnées")
            else:
                col4.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé aux périodes non séléctionnées")
        else:
            if i%4==0:
                col1.metric(label="**"+key+"**", value=f"{formatted_value} €")
            elif i%4==1:
                col2.metric(label="**"+key+"**", value=f"{formatted_value} €")
            elif i%4==2:
                col3.metric(label="**"+key+"**", value=f"{formatted_value} €")
            else:
                col4.metric(label="**"+key+"**", value=f"{formatted_value} €")
        i=i+1
    my_bar.progress(40, text=progress_text)

    #### Vision personnalisé ?###
    # con1 = st.container(border=True)
    # con1.write("### Personalisation de la visualisation")
    # select_options = df.columns
    # select_selection = con1.segmented_control(
    #     "Séléction pour filtre : Années-mois", select_options, selection_mode="multi"
    # )
    # detailsdatatable = con1.expander("Détails")
    # detailsdatatable.write(filtered_df[list(select_selection)])
    # con1.(data=filtered_df[list(select_selection)])


    con = st.container(border=True)
    con.write("### Rémunération dirigeant, Cotisations dirigeant, Rémunération personnel, Charges sociales et Masse salariale par ANMOIS")
    details = con.expander("Détails")
    # Pivot table
    test_df = filtered_df[filtered_df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["Année","Mois","CompteLib"]).agg({"Solde":"sum",}).reset_index()
    pivot = pd.pivot_table(test_df,values="Solde",index=["Année","Mois"],columns=["CompteLib"]).reset_index()
    pivot_temp =  pd.concat([pivot,pivot.groupby("Année").sum().reset_index().drop(columns=["Mois"])])
    pivot_temp["Mois"] = pivot_temp["Mois"].fillna(" Tous les mois")
    details.write("Classe de compte 641,645,644,646")
    details.write(pivot_temp.fillna(0.0).sort_values(["Année","Mois"],ascending=[True,True]).set_index(["Année","Mois"]))

    fig = px.bar(
        filtered_df[filtered_df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),
        x='ANMOIS',
        y='Solde',
        color='CompteLib',
        orientation='v',
        barmode='group',
        title="Solde par ANMOIS et par CompteLib pour les compte de classe 641,645,644,646",
        labels={'Solde': 'Solde (€)', 'ANMOIS': 'Année-Mois'}
    )

    con.plotly_chart(fig, use_container_width=True)
    # con.bar_chart(data=filtered_df[filtered_df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),x="ANMOIS",y="Solde",color="CompteLib",stack=False)
    my_bar.progress(60, text=progress_text)


    cont = st.container(border=True)
    cont.write("### Achats par ANMOIS")
    details1 = cont.expander("Détails")
    test1_df = filtered_df[filtered_df["CompteNum"].str.contains("^6.*")].groupby(["Année","Mois","CompteLib"]).agg({"Solde":"sum",}).reset_index()
    pivot1 = pd.pivot_table(test1_df,values="Solde",index=["Année","Mois"],columns=["CompteLib"]).reset_index()
    pivot1_temp = pd.concat([pivot1,pivot1.groupby("Année").sum().reset_index().drop(columns=["Mois"])])
    pivot1_temp["Mois"]= pivot1_temp["Mois"].fillna(" Tous les mois")
    details1.write("Classe de compte 6")
    details1.write(pivot1_temp.fillna(0.0).sort_values(["Année","Mois"],ascending=[True,True]).set_index(["Année","Mois"]))
    my_bar.progress(80, text=progress_text)
    fig1 = px.bar(
        filtered_df[filtered_df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),
        x='ANMOIS',
        y='Solde',
        color='CompteLib',
        orientation='v',
        barmode='group',
        title="Achats par ANMOIS et par CompteLib pour les compte de classe 6",
        labels={'Solde': 'Solde (€)', 'ANMOIS': 'Année-Mois'}
    )
    cont.plotly_chart(fig1, key="achats",use_container_width=True)
    # cont.bar_chart(data=filtered_df[filtered_df["CompteNum"].str.contains("^6.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),x="ANMOIS",y="Solde",color="CompteLib",stack=False)
    my_bar.progress(100, text=progress_text)
    time.sleep(1)
    my_bar.empty()