from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import plotly.express as px
import plotly.io as pio
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Fonction pour charger les données à partir d'un fichier téléchargé
def load_data(filepath):
    try:
        data = pd.read_excel(filepath, engine='openpyxl')
        data['EcritureDate'] = pd.to_datetime(data['EcritureDate'], errors='coerce', format="%Y%m%d")
        data.CompteNum = data.CompteNum.astype(str)
        data.Credit = data.Credit.str.replace(",", ".").astype(float)
        data.Debit = data.Debit.str.replace(",", ".").astype(float)
    except Exception as e:
        flash(f"Erreur lors du chargement du fichier : {e}", 'danger')
        return None
    return data

# Fonction pour calculer les indicateurs financiers
def calculate_financials(data):
    ca = data[data['CompteNum'].str.startswith('70')]['Credit'].sum() - data[data['CompteNum'].str.startswith('70')]['Debit'].sum()
    achats_consommés = data[data['CompteNum'].str.startswith('60')]['Debit'].sum() - data[data['CompteNum'].str.startswith('60')]['Credit'].sum()
    services_exterieurs = data[data['CompteNum'].str.startswith('61') | data['CompteNum'].str.startswith('62')]['Debit'].sum() - data[data['CompteNum'].str.startswith('61') | data['CompteNum'].str.startswith('62')]['Credit'].sum()
    valeur_ajoutee = ca - achats_consommés - services_exterieurs
    aides = data[data['CompteNum'].str.startswith('74')]['Credit'].sum() - data[data['CompteNum'].str.startswith('74')]['Debit'].sum()
    impots_taxes = data[data['CompteNum'].str.startswith('63')]['Debit'].sum() - data[data['CompteNum'].str.startswith('63')]['Credit'].sum()
    masse_salariale = data[data['CompteNum'].str.startswith('64')]['Debit'].sum() - data[data['CompteNum'].str.startswith('64')]['Credit'].sum()
    ebe = valeur_ajoutee + aides - impots_taxes - masse_salariale

    return {
        "CA global": ca,
        "Achats consommés": achats_consommés,
        "Services extérieurs": services_exterieurs,
        "Valeur ajoutée": valeur_ajoutee,
        "Aides": aides,
        "Impôts et taxes": impots_taxes,
        "Masse salariale": masse_salariale,
        "EBE": ebe
    }

# Fonction pour calculer le compte de résultat (P&L) agrégé
def calculate_pnl(data):
    pcg_data = {
        'CompteNum': [
            '60260000', '60370000', '60611000', '60613000', '60630000', '60640000', '60700500', '60702000', '61220000', '61320000',
            '61321000', '61350000', '61351000', '61352000', '61352100', '61353000', '61400000', '61500000', '61510000', '61560000',
            '61600000', '61611000', '61810000', '62220000', '62260000', '62270000', '62280000', '62310000', '62370000', '62500000',
            '62540000', '62600000', '62620000', '62700000', '62710000', '62800000', '63120000', '63300000', '63310000', '63500000',
            '63511000', '63520000', '63720000', '63780000', '64110000', '64120000', '64140000', '64410000', '64420000', '64430000',
            '64431000', '64500000', '64520000', '64600000', '64601000', '64603000', '64604000', '64630000', '64640000', '64650000',
            '64750000', '64955100', '64960000', '65100000', '65800000', '66100000', '66150000', '67100000', '68111000', '68112000',
            '68710000', '69500000', '70700000', '70700001', '70705000', '70705001', '70710000', '70710001', '74000000', '75800000',
            '76301000', '76302000', '76303000', '76800000', '77100000', '79100000', '79100100', '79120000'
        ],
        'CompteLib': [
            'Emballages', 'Variation stocks marchandises', 'Electricité', 'Carburants', 'Fournitures entretien et petits équipements',
            'Fournitures administratives', 'Achats marchandises 5,5 %', 'Achats marchandises 20%', 'Leasing scooter melvyn celu ya',
            'Location immobilière', 'Location box 3011', 'Location locam alarme', 'Location monétique plus', 'Location logiciel epack',
            'Location logiciel skello', 'Location divers', 'Charges locatives et copro', 'Entretien et réparations', 'Entretien immeuble',
            'Maintenance', 'Primes d\'assurance', 'Assurance sur emprunt', 'Documentation générale', 'Commissions sur ventes', 'Honoraires',
            'Frais d\'actes', 'Honoraires divers', 'Frais publicité/promotion', 'Cadeaux salariés', 'Déplacements, missions, récept',
            'Frais de déplacements', 'Frais postaux et télécom.', 'Téléphone', 'Services bancaires et assimilé', 'Frais tickets restaurant',
            'Autres services externes divers', 'Taxe apprentissage', 'Formation continue', 'Cfp gérant', 'Taxe TLPE enseigne', 'Cfe/cvae',
            'Taxes sur le chiffre d\'affaire', 'Csg ded gérant', 'Taxes diverses', 'Salaires appointements', 'Congés payés',
            'Indemnités avantages divers', 'Salaire melvyn celu', 'Salaire luis candelas', 'Rémunération gérance', 'Av en nature nourriture gérant.',
            'Charges sociales', 'Cs sur congés payés', 'Rsi pedro luis candelas', 'Rsi melvyn celu', 'Cotisations personnelles gérant',
            'Cotisations prévoyance gérant', 'Prévoyance pedro luis candelas', 'Prévoyance melvyn celu', 'Frais de santé madelin p l candelas',
            'Médecine du travail, pharmacie', 'Avantage en nature salariés', 'Avantage en nature gérant', 'Redevances /concessions, brève',
            'Charges de gestion courante', 'Charges d\'intérêts', 'Décompte intérêts cc', 'Charges exceptionnelles /opération gestion',
            'Dot/amort. immob. incorporelles', 'Dot/amort. immob. corporelles', 'Dotations aux amortissements exceptionnels des immobilisations',
            'Impôt société', 'Ventes à 10%', 'Ventes de marchandises 10% Deliveroo Uber To Good', 'Ventes à 5.5%', 'Ventes à 5,5% Deliveroo Uber To Good',
            'Ventes à 20%', 'Ventes à 20% Deliveroo Uber To Good', 'Subventions d\'exploitation', 'Produits divers de gestion courante',
            'Abandon comptes ctct dfc industrie', 'Abandon ctct lc corporate', 'Abandon ctct 2k corporate', 'Autres produits financiers',
            'Produits exceptionnels /opérations gestion', 'Avantages en nature', 'Av en nature repas gérant', 'Financement formation'
        ]
    }

    # Créer le DataFrame pour le PCG
    pcg_df = pd.DataFrame(pcg_data)
    print(data.shape)
    data = data.merge(pcg_df, how="left", on="CompteNum")
    print(data.shape)
    pnl=data[data['CompteNum'].str.startswith(('6', '7'))]
    pnl["n1"]=pnl['CompteNum'].str[:1]
    pnl["n2"]=pnl['CompteNum'].str[:2]
    pnl["Solde"]=pnl["Debit"]-pnl['Credit']
    pnln1=pnl.groupby("n1").Solde.sum(numeric_only=True).reset_index()
    pnln2=pnl.groupby(["n1","n2","CompteLib_y"]).Solde.sum(numeric_only=True).reset_index()
    print(pnln1,pnln2)
    return pnln1, pnln2

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Aucun fichier sélectionné', 'danger')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            data = load_data(filepath)
            if data is not None:
                return redirect(url_for('results', filename=filename))
    return render_template('index.html')

@app.route('/results/<filename>', methods=['GET'])
def results(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    data = load_data(filepath)
    if data is None:
        return redirect(url_for('index'))

    data['Year'] = data['EcritureDate'].dt.year
    data['Month'] = data['EcritureDate'].dt.month

    selected_year = request.args.get('year', type=int, default=None)
    selected_month = request.args.get('month', type=int, default=None)

    if selected_year:
        if selected_month:
            filtered_data = data[(data['Year'] == selected_year) & (data['Month'] == selected_month)]
        else:
            filtered_data = data[data['Year'] == selected_year]
    else:
        filtered_data = data

    financials = calculate_financials(filtered_data)
    class_6_7_agg, class_2_digits_agg = calculate_pnl(filtered_data)

    fig = px.bar(
        x=list(financials.keys()),
        y=list(financials.values()),
        labels={'x': 'Indicateurs financiers', 'y': 'Montant (€)'},
        title='Indicateurs Financiers'
    )

    graph_html = pio.to_html(fig, full_html=False)

    years = data['Year'].dropna().unique().tolist()
    months = data['Month'].dropna().unique().tolist()

    return render_template(
        'results.html',
        financials=financials,
        class_6_7_agg=class_6_7_agg,
        class_2_digits_agg=class_2_digits_agg,
        graph_html=graph_html,
        years=years,
        months=months,
        selected_year=selected_year,
        selected_month=selected_month
    )

if __name__ == '__main__':
    app.run(debug=False)