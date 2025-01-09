import streamlit as st
import pandas as pd
import plotly.express as px
import time
from EasyCompta.utils import get_pcg
st.set_page_config(page_title="EasyCompta", layout="wide")


# Définir les colonnes du DataFrame
columns = ["JournalCode", "JournalLib", "EcritureNum", "EcritureDate", "CompteNum", "CompteLib", 
           "CompAuxNum", "CompAuxLib", "PieceRef", "PieceDate", "EcritureLib", "Debit", 
           "Credit", "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"]

# Titre du tableau de bord
pcg_df=pd.DataFrame(get_pcg())
load_data = st.container(border=True)

# Téléchargement du fichier FEC
uploaded_file = load_data.file_uploader("Télécharger un fichier FEC (.xlsx, .csv, .txt) avec un séparateur ;", type=['xlsx', 'csv', 'txt'])

personal_pcg = st.checkbox("Voulez-vous ajouter votre propre PCG ?")

if personal_pcg:
    st.write("Merci de fournir un pcg au format CompteNum;Libellé")
    # Téléchargement du fichier FEC
    pcg_perso = load_data.file_uploader("Télécharger un fichier PCG (.xlsx, .csv, .txt) avec un séparateur ;", type=['xlsx', 'csv', 'txt'])
    # Détection du type de fichier et chargement dans un DataFrame
    if pcg_perso:
        if pcg_perso.name.endswith('.xlsx'):
            pcg_df = pd.read_excel(uploaded_file, names=["CompteNum","Libellé"])
        elif pcg_perso.name.endswith('.csv'):
            pcg_df = pd.read_csv(uploaded_file, sep=';', names=["CompteNum","Libellé"])
        elif pcg_perso.name.endswith('.txt'):
            pcg_df = pd.read_csv(uploaded_file, sep=';', names=["CompteNum","Libellé"])

    print(pcg_df)

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

    df['EcritureDate'] = pd.to_datetime(df['EcritureDate'], format='%Y%m%d')
    df['Année'] = df['EcritureDate'].dt.year
    df['Mois'] = df['EcritureDate'].dt.month
    df.loc[df["Mois"]<10,"Mois"]="0"+df["Mois"].astype(str)
    df["Mois"] = df["Mois"].astype(str)
    df["Année"] = df["Année"].astype(str)
    df["ANMOIS"]=df["Année"].astype(str)+"-"+df["Mois"].astype(str)

    years_options = df.ANMOIS.unique()
    years_selection = st.segmented_control(
        "Séléction pour filtre : Années-mois", years_options, selection_mode="multi"
    )
    progress_text = "Chargement des indicateurs en cours. Merci de patienter..."

    df = df.merge(pcg_df,how="left",on="CompteNum")

    my_bar = st.progress(0, text=progress_text)
    df["CompteNum"]=df["CompteNum"].astype(str)
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