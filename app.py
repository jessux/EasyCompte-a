import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from EasyCompta.utils import get_pcg

# Définir les colonnes du DataFrame
columns = ["JournalCode", "JournalLib", "EcritureNum", "EcritureDate", "CompteNum", "CompteLib", 
           "CompAuxNum", "CompAuxLib", "PieceRef", "PieceDate", "EcritureLib", "Debit", 
           "Credit", "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"]

# Titre du tableau de bord
st.set_page_config(page_title="EasyCompta", layout="wide")
pcg_df=pd.DataFrame(get_pcg())
load_data = st.container(border=True)

# Téléchargement du fichier FEC
uploaded_file = load_data.file_uploader("Télécharger un fichier FEC (.xlsx, .csv, .txt)", type=['xlsx', 'csv', 'txt'])


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



if uploaded_file:
    # Détection du type de fichier et chargement dans un DataFrame
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file, names=columns)
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, sep=';', names=columns)
    elif uploaded_file.name.endswith('.txt'):
        df = pd.read_csv(uploaded_file, sep=';', names=columns)

    df = df.merge(pcg_df,how="left",on="CompteNum")

    
    df["CompteNum"]=df["CompteNum"].astype(str)
    # Convertir les colonnes 'Debit' et 'Credit' en numérique
    df['Debit'] = df['Debit'].str.replace(',', '.').astype(float)
    df['Credit'] = df['Credit'].str.replace(',', '.').astype(float)

    # Ajouter une colonne avec le montant net (Credit - Debit)
    df['Solde'] = df['Debit'] - df['Credit']
    df['Solde'] = df['Solde'].astype(str).str.replace(',','.').astype(float)
    # Filtrage par année et mois
    df['EcritureDate'] = pd.to_datetime(df['EcritureDate'], format='%Y%m%d')
    df['Année'] = df['EcritureDate'].dt.year
    df['Mois'] = df['EcritureDate'].dt.month

    years = df['Année'].unique()
    months = ["Tous les mois","1","2","3","4","5","6","7","8","9","10","11","12"]
    print(df[df['Année'] == 2023])
    selected_years = load_data.selectbox("Sélectionner les années", years)
    # selected_months = load_data.selectbox("Sélectionner les mois", months)
    if selected_years:# and selected_months == "Tous les mois":
        filtered_df = df[df['Année'] == selected_years]
        filtered_dfn1= df[df['Année'] == int(selected_years) -1]
    # elif selected_months != "Tous les mois" and not selected_years:
    #     filtered_df = df[df['Mois'] == selected_months]
    #     filtered_dfn1 = df[df['Mois'] ==  int(selected_months) -1]
    # else:
    #     filtered_df = df[(df['Année'] == selected_years) & (df['Mois'] == selected_months)]
    #     filtered_dfn1 = df[(df['Année']==int(selected_years)-1) & (df['Mois'] == int(selected_months)-1)]
    
    ca = filtered_df[filtered_df["CompteNum"].str.contains("^7.*")]["Solde"].sum()*-1
    ca1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains("^7.*")]["Solde"].sum()*-1
    
    achats_consommés = filtered_df[filtered_df['CompteNum'].str.contains('^603.*|^607.*')]["Solde"].sum()
    achats_consommés1= filtered_dfn1[filtered_dfn1['CompteNum'].str.contains('^603.*|^607.*')]["Solde"].sum()
    
    marge = ca - achats_consommés
    marge1= ca1 - achats_consommés1
    
    fournitures_consommables = filtered_df[filtered_df["CompteNum"].str.contains('^602.*|^606.*')]["Solde"].sum()
    fournitures_consommables1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains('^602.*|^606.*')]["Solde"].sum()
    
    services_exterieurs = filtered_df[filtered_df["CompteNum"].str.contains('^61.*|^62.*')]["Solde"].sum()
    services_exterieurs1 = filtered_dfn1[filtered_dfn1["CompteNum"].str.contains('^61.*|^62.*')]["Solde"].sum()
    
    valeur_ajoutee = marge - fournitures_consommables - services_exterieurs
    valeur_ajoutee1 = marge1 - fournitures_consommables1 - services_exterieurs1
    
    aides = filtered_df[filtered_df['CompteNum'].str.startswith('74')]["Solde"].sum()
    aides1 = filtered_dfn1[filtered_dfn1['CompteNum'].str.startswith('74')]["Solde"].sum()
    
    impots_taxes = filtered_df[filtered_df['CompteNum'].str.startswith('63')]["Solde"].sum()
    impots_taxes1 = filtered_dfn1[filtered_dfn1['CompteNum'].str.startswith('63')]["Solde"].sum()
    
    masse_salariale = filtered_df[filtered_df['CompteNum'].str.startswith('64')]["Solde"].sum()
    masse_salariale1 = filtered_dfn1[filtered_dfn1['CompteNum'].str.startswith('64')]["Solde"].sum()
    
    ebe = valeur_ajoutee + aides - impots_taxes - masse_salariale
    ebe1 = valeur_ajoutee1 + aides1 - impots_taxes1 - masse_salariale1
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
        "EBE": ebe
    }
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
        "EBE": ebe1
    }
    print(financials,financials1)
    c = st.container(border=True)
    c.write("### Indicateurs financiers")

    col1,col2,col3,col4 = c.columns(4)
    i = 0
    for key, value in financials.items():
        formatted_value = f"{value:,.2f}".replace(',', ' ')
        delta  = 0
        if not financials1[key] == 0.0:
            delta = round(value - financials1[key],2)
        if i%4==0:
            col1.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé à l'année : "+str(selected_years-1))
        elif i%4==1:
            col2.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé à l'année : "+str(selected_years-1))
        elif i%4==2:
            col3.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé à l'année : "+str(selected_years-1))
        else:
            col4.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé à l'année : "+str(selected_years-1))
        i=i+1
    # st.write(filtered_df.CompteNum.unique())
    df.loc[df["Mois"]<10,"Mois"]="0"+df["Mois"].astype(str)
    df["Mois"] = df["Mois"].astype(str)
    df["Année"] = df["Année"].astype(str)
    df["ANMOIS"]=df["Année"].astype(str)+"-"+df["Mois"].astype(str)
    con = st.container(border=True)
    con.write("### Rémunération dirigeant, Cotisations dirigeant, Rémunération personnel, Charges sociales et Masse salariale par ANMOIS")
    details = con.expander("Détails")
    # Pivot table
    test_df = df[df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["Année","Mois","CompteLib"]).agg({"Solde":sum,}).reset_index()
    pivot = pd.pivot_table(test_df,values="Solde",index=["Année","Mois"],columns=["CompteLib"]).reset_index()
    details.write(pd.concat([pivot,pivot.groupby("Année").apply("sum").reset_index().drop(columns=["Mois"])]).fillna(" Tous les mois").sort_values(["Année","Mois"],ascending=[True,True]).set_index(["Année","Mois"]))
    con.bar_chart(data=df[df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),x="ANMOIS",y="Solde",color="CompteLib",stack=False)
    
    cont = st.container(border=True)
    cont.write("### Achats par ANMOIS")
    details1 = cont.expander("Détails")
    test1_df = df[df["CompteNum"].str.contains("^6.*")].groupby(["Année","Mois","CompteLib"]).agg({"Solde":sum,}).reset_index()
    pivot1 = pd.pivot_table(test1_df,values="Solde",index=["Année","Mois"],columns=["CompteLib"]).reset_index()
    details1.write(pd.concat([pivot1,pivot1.groupby("Année").apply("sum").reset_index().drop(columns=["Mois"])]).fillna(" Tous les mois").sort_values(["Année","Mois"],ascending=[True,True]).set_index(["Année","Mois"]))
    cont.bar_chart(data=df[df["CompteNum"].str.contains("^6.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),x="ANMOIS",y="Solde",color="CompteLib",stack=False)