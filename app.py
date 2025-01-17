import streamlit as st
import pandas as pd
import plotly.express as px
import time
from EasyCompta.utils import *
import numpy as np
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
st.set_page_config(page_title="EasyCompta", layout="wide")



def filter_dataframe(container,df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = container.checkbox("Add filters")

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

    modification_container = container.container()

    with modification_container:
        to_filter_columns = container.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = container.columns((1, 20))
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
load_data = st.sidebar.container(border=True)

# Téléchargement du fichier FEC
uploaded_file = load_data.file_uploader("Télécharger un fichier FEC (.xlsx, .csv, .txt)", type=['xlsx', 'csv', 'txt'])

personal_pcg = load_data.checkbox("Voulez-vous ajouter votre propre PCG ?")

if personal_pcg:
    # Téléchargement du fichier FEC
    load_data.write("Merci de fournir un pcg au format CompteNum;Libellé")
    pcg_perso = load_data.file_uploader("Télécharger un fichier PCG (.xlsx, .csv, .txt)", type=['xlsx', 'csv', 'txt'])
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
    df['Mois'] = df['EcritureDate'].dt.strftime("%m")
    df["ANMOIS"] = df["Année"]+"-"+df["Mois"]
    df['EcritureDate'] =df['EcritureDate'].dt.strftime("%Y/%m/%d")
    df['PieceDate'] = pd.to_datetime(df['PieceDate'], format="%Y%m%d",errors="coerce").dt.strftime("%Y/%m/%d")
    df['DateLet'] = pd.to_datetime(df['DateLet'],format="%Y%m%d",errors="coerce").dt.strftime("%Y/%m/%d")
    df['ValidDate'] = pd.to_datetime(df['ValidDate'],format="%Y%m%d",errors="coerce").dt.strftime("%Y/%m/%d")
    df["CompteNum"]=df["CompteNum"].astype(str)
    df["PieceRef"] = df["PieceRef"].astype(str)

    st.sidebar.subheader("Filtrer par période")
    min_date = pd.to_datetime(df['EcritureDate']).min()
    max_date = pd.to_datetime(df['EcritureDate']).max()
    start_date = st.sidebar.date_input("Date de début", min_date)
    end_date = st.sidebar.date_input("Date de fin", max_date)
    df['EcritureDate'] = pd.to_datetime(df['EcritureDate'])


    progress_text = "Chargement des indicateurs en cours. Merci de patienter..."

    pcg_df.CompteNum = pcg_df.CompteNum.str.ljust(df.CompteNum.str.len().max(),'0')
    df.CompteNum = df.CompteNum.str.ljust(df.CompteNum.str.len().max(),'0')
    pcg_df = pcg_df.rename(columns={"Libellé":"Libellé PCG"})
    df = df.merge(pcg_df,how="left",on="CompteNum")
    container = st.container()
    details_expander = container.expander("Tableau FEC")

    ownfilterdf = filter_dataframe(details_expander,df)

    details_expander.dataframe(ownfilterdf)
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
    filtered_df = df[(df['EcritureDate'] >= pd.Timestamp(start_date)) & 
                                (df['EcritureDate'] <= pd.Timestamp(end_date))]
    filtered_dfn1= df[~((df['EcritureDate'] >= pd.Timestamp(start_date)) & 
                           (df['EcritureDate'] <= pd.Timestamp(end_date)))]

    financials=calculate_financials(filtered_df)

    if not filtered_dfn1.empty:
        financials1=calculate_financials(filtered_dfn1)

    
    my_bar.progress(20, text=progress_text)
    my_bar.empty()
    container_indicateurs = st.container(border=True)
    container_indicateurs.write("### Indicateurs financiers")

    container_indicateurs_c1,container_indicateurs_c2 = container_indicateurs.columns(2)
    container_indicateurs_1 = container_indicateurs_c1.container(border=True)
    col1,col2,col3 = container_indicateurs_1.columns(3)
    i = 0
    for key, value in financials.items():
        formatted_value = f"{value:,.2f}".replace(',', ' ')
        delta  = 0
        if not filtered_dfn1.empty:
            if not financials1[key] == 0.0:
                delta = round(value - financials1[key],2)
            if i%3==0:
                col1.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé aux périodes non séléctionnées")
            elif i%3==1:
                col2.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé aux périodes non séléctionnées")
            elif i%3==2:
                col3.metric(label="**"+key+"**", value=f"{formatted_value} €", delta=str(delta)+ " € -- comparé aux périodes non séléctionnées")
        else:
            if i%3==0:
                col1.metric(label="**"+key+"**", value=f"{formatted_value} €")
            elif i%3==1:
                col2.metric(label="**"+key+"**", value=f"{formatted_value} €")
            elif i%3==2:
                col3.metric(label="**"+key+"**", value=f"{formatted_value} €")
        i=i+1
    my_bar.progress(40, text=progress_text)
    ct = container_indicateurs_c2.container(border=True)
    col11,col21 = ct.columns(2)
    i = 0
    for key, value in calculer_ratios(financials).items():
        formatted_value = f"{value:,.2f}".replace(',', ' ')
        if i%2==0:
            col11.metric(label="**"+key+"**", value=f"{formatted_value} %")
        elif i%2==1:
            col21.metric(label="**"+key+"**", value=f"{formatted_value} %")
        i=i+1

    extra_info = st.container(border=True)
    Bilan_tab,Graph_tab = extra_info.tabs(["Bilan","Graphiques"])
    Bilan_tab.subheader("Bilan Comptable")
    bilan = generer_bilan(filtered_df)
    bilan_df = pd.DataFrame(list(bilan.items()), columns=["Poste", "Montant (€)"])
    Bilan_tab.data_editor(
    bilan_df,
    column_config={
        "Montant (€)": st.column_config.NumberColumn(
            "Montant (€)",
            help="Le prix en euro",
            step=1,
            format="%d €",
        )
    },
    hide_index=True,
)

    con = Graph_tab.container(border=True)
    con.write("### Rémunération dirigeant, Cotisations dirigeant, Rémunération personnel, Charges sociales et Masse salariale par ANMOIS")
    details = con.expander("Détails")
    # Pivot table
    test_df = filtered_df[filtered_df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["Année","Mois","CompteLib","Libellé PCG"]).agg({"Solde":"sum",}).reset_index()
    pivot = pd.pivot_table(test_df,values="Solde",index=["Année","Mois"],columns=["Libellé PCG"]).reset_index()
    pivot_temp =  pd.concat([pivot,pivot.groupby("Année").sum().reset_index().drop(columns=["Mois"])])
    pivot_temp["Mois"] = pivot_temp["Mois"].fillna(" Tous les mois")
    details.write("Classe de compte 641,645,644,646")
    details.write(pivot_temp.fillna(0.0).sort_values(["Année","Mois"],ascending=[True,True]).set_index(["Année","Mois"]))

    fig = px.bar(
        filtered_df[filtered_df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["Libellé PCG","ANMOIS"]).Solde.sum().reset_index(),
        x='ANMOIS',
        y='Solde',
        color='Libellé PCG',
        orientation='v',
        barmode='group',
        title="Solde par ANMOIS et par Libellé PCG pour les compte de classe 641,645,644,646",
        labels={'Solde': 'Solde (€)', 'ANMOIS': 'Année-Mois'}
    )

    con.plotly_chart(fig, use_container_width=True)
    # con.bar_chart(data=filtered_df[filtered_df["CompteNum"].str.contains("^641.*|^645.*|^644.*|^646.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),x="ANMOIS",y="Solde",color="CompteLib",stack=False)
    my_bar.progress(60, text=progress_text)


    cont = Graph_tab.container(border=True)
    cont.write("### Achats par ANMOIS")
    details1 = cont.expander("Détails")
    test1_df = filtered_df[filtered_df["CompteNum"].str.contains("^6.*")].groupby(["Année","Mois","CompteLib","Libellé PCG"]).agg({"Solde":"sum",}).reset_index()
    pivot1 = pd.pivot_table(test1_df,values="Solde",index=["Année","Mois"],columns=["Libellé PCG"]).reset_index()
    pivot1_temp = pd.concat([pivot1,pivot1.groupby("Année").sum().reset_index().drop(columns=["Mois"])])
    pivot1_temp["Mois"]= pivot1_temp["Mois"].fillna(" Tous les mois")
    details1.write("Classe de compte 6")
    details1.write(pivot1_temp.fillna(0.0).sort_values(["Année","Mois"],ascending=[True,True]).set_index(["Année","Mois"]))
    my_bar.progress(80, text=progress_text)
    fig1 = px.bar(
        filtered_df[filtered_df["CompteNum"].str.startswith("6")].groupby(["Libellé PCG","ANMOIS"]).Solde.sum().reset_index(),
        x='ANMOIS',
        y='Solde',
        color='Libellé PCG',
        orientation='v',
        barmode='group',
        title="Achats par ANMOIS et par Libellé PCG pour les compte de classe 6",
        labels={'Solde': 'Solde (€)', 'ANMOIS': 'Année-Mois'}
    )
    cont.plotly_chart(fig1, key="achats",use_container_width=True)


    # Création du graphique personnalisé
    cont.subheader("Paramètres du graphique")
    colonne_x = cont.selectbox("Sélectionnez la colonne pour l'axe X", df.columns)
    colonne_y = cont.selectbox("Sélectionnez la colonne pour l'axe Y", df.columns)
    couleur_colonne = cont.selectbox("Colonne pour la couleur (facultatif)", [None] + list(df.columns))
    type_graphique = cont.selectbox(
        "Sélectionnez le type de graphique",
        ["Barres", "Lignes", "Nuages de points", "Histogramme", "Boîte à moustaches (Boxplot)"]
    )

        # Options supplémentaires
    cont.subheader("Options supplémentaires")
    titre = cont.text_input("Titre du graphique", "Mon Graphique")
    largeur = cont.slider("Largeur du graphique", 400, 1200, 800)
    hauteur = cont.slider("Hauteur du graphique", 300, 800, 600)

    # Génération du graphique
    cont.subheader("Graphique Personnalisé")
    if colonne_x and colonne_y:
        if type_graphique == "Barres":
            fig = px.bar(
                df,
                x=colonne_x,
                y=colonne_y,
                color=couleur_colonne,
                title=titre,
                width=largeur,
                height=hauteur
            )
        elif type_graphique == "Lignes":
            fig = px.line(
                df,
                x=colonne_x,
                y=colonne_y,
                color=couleur_colonne,
                title=titre,
                width=largeur,
                height=hauteur
            )
        elif type_graphique == "Nuages de points":
            fig = px.scatter(
                df,
                x=colonne_x,
                y=colonne_y,
                color=couleur_colonne,
                title=titre,
                width=largeur,
                height=hauteur
            )
        elif type_graphique == "Histogramme":
            fig = px.histogram(
                df,
                x=colonne_x,
                color=couleur_colonne,
                title=titre,
                width=largeur,
                height=hauteur
            )
        elif type_graphique == "Boîte à moustaches (Boxplot)":
            fig = px.box(
                df,
                x=colonne_x,
                y=colonne_y,
                color=couleur_colonne,
                title=titre,
                width=largeur,
                height=hauteur
            )

        # Affichage du graphique
        cont.plotly_chart(fig, use_container_width=True)
    # cont.bar_chart(data=filtered_df[filtered_df["CompteNum"].str.contains("^6.*")].groupby(["CompteLib","ANMOIS"]).Solde.sum().reset_index(),x="ANMOIS",y="Solde",color="CompteLib",stack=False)
    my_bar.progress(100, text=progress_text)
    time.sleep(1)
    my_bar.empty()