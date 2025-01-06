import pandas as pd
import os
def get_pcg():
    # Exemple étendu de données du PCG incluant les classes 6 et 7
    if os.path.exists(".\\uploads\\pcg.xlsx"):
        pcgxls= pd.read_excel(".\\uploads\\pcg.xlsx")
    else:
        pcgxls= pd.read_excel("/workspace/uploads/pcg.xlsx")

    pcgxls["CompteNum"]=pcgxls["CompteNum"].astype(str)
    pcgxls["CompteNum"]=pcgxls["CompteNum"].apply(add_zero_if_shorter)
    return pcgxls

def add_zero_if_shorter(row, char="0", threshold=2):
    if len(row) <= threshold:
        return row + char
    return row

