from openpyxl import load_workbook
import pandas as pd
import glob
import os


DB_PATH = "../data/db/db.xlsx"
TEMPLATE_PATH = "../data/db/doe_template.xlsx"
FILES_DIR = "../data/simulations/generated/xlsx"
METADATA_DIR = "../data/simulations/generated/metadata"

PREFIX = "Year_2024_Olzhas_BA"


def m_to_mm(meters: float) -> float:
    return meters * 1000


def kg_to_g(kg: float) -> float:
    return kg * 1000


CONVERTERS = {
    "BA": kg_to_g,
    "CE": m_to_mm,
    "PE": m_to_mm,
    "BP": m_to_mm,
    "R": m_to_mm,
    "Y": m_to_mm,
    "Z": m_to_mm,
    "MH": m_to_mm
}


RESPONSES = ["R", "Y", "Z", "MH"]


SYMBOL_TO_NAME = {
    "FA": "FiringAngle",
    "RA": "ReleaseAngle",
    "BA": "BallMass",
    "CE": "CupElevation",
    "PE": "PinElevation",
    "BP": "BungeePosition",
    "R": "Distance",
    "Y": "Height",
    "Z": "LateralDistance",
    "MH": "MaximumHeight"
}


SYMBOL_TO_UNITS = {
    "FA": "Grad",
    "RA": "Grad",
    "BA": "g",
    "CE": "mm",
    "PE": "mm",
    "BP": "mm",
    "R": "mm",
    "Y": "mm",
    "Z": "mm",
    "MH": "mm"
}


if __name__ == "__main__":
    # Get all file names in the generated data directory
    file_names = glob.glob("*.xlsx", root_dir=FILES_DIR)

    wb = load_workbook(TEMPLATE_PATH)

    design_row = 2
    design_factors_last_row = 2
    design_responses_last_row = 2

    dfd_last_row = 2
    drd_last_row = 2

    # Iterate over generated files
    for fn in file_names:
        # Skip excel temp files
        if "~$" in fn:
            continue

        df = pd.read_excel(os.path.join(FILES_DIR, fn), header=0, converters=CONVERTERS, index_col=0)

        metadata_file_name = fn.split(".")[0] + ".csv"
        metadata_df = pd.read_csv(os.path.join(METADATA_DIR, metadata_file_name), index_col=0)

        run_number = 1

        factors = [c for c in df.columns if c not in ["Experiment Identifier", *RESPONSES]]

        # ----- Design Info filling -----
        ws_info = wb["DesignInfo"]

        # Design name
        design_name = f"{PREFIX}_{''.join(fn.split('.')[0].split('_')[1:])}"
        ws_info[f"A{design_row}"] = design_name

        # Factors
        ws_info[f"B{design_row}"] = len(factors)

        # Response
        ws_info[f"C{design_row}"] = len(RESPONSES)

        # Runs
        ws_info[f"D{design_row}"] = len(df)

        # Inclusions
        ws_info[f"E{design_row}"] = 0

        # Constraints
        ws_info[f"F{design_row}"] = 2

        # ConstraintsFormula
        ws_info[f"G{design_row}"] = "(FA-RA) <= (15) or (CE-BP) < (35)" if metadata_df.loc[0, "Constraints"] else ""

        # DesignType
        ws_info[f"H{design_row}"] = metadata_df.loc[0, "Design"]

        # Candidates
        ws_info[f"I{design_row}"] = metadata_df.loc[0, "Candidates"]

        # RunOrder
        ws_info[f"J{design_row}"] = metadata_df.loc[0, "Run Order"]

        # InformationIndex
        ws_info[f"K{design_row}"] = 0

        # ModelType
        ws_info[f"L{design_row}"] = "User-defined"

        # ModelTerms
        ws_info[f"M{design_row}"] = metadata_df.loc[0, "Terms"]

        # Documentation - left empty

        # Link - left empty

        # ----- Design Factors filling -----
        ws_df = wb['DesignFactors']
        for factor in factors:
            # Design name
            ws_df[f"A{design_factors_last_row}"] = design_name

            # Factor full name
            ws_df[f"B{design_factors_last_row}"] = SYMBOL_TO_NAME[factor]

            # Factor symbol
            ws_df[f"C{design_factors_last_row}"] = factor

            # Min, Max, Level - filled in manually

            # Type
            ws_df[f"G{design_factors_last_row}"] = "Continuous"

            # Scale
            ws_df[f"H{design_factors_last_row}"] = "Orthogonal"

            # Units
            ws_df[f"I{design_factors_last_row}"] = "Orthogonal"

            # Ease
            ws_df[f"J{design_factors_last_row}"] = "Easy"

            # Increment - filled in manually

            design_factors_last_row += 1

        # Increment once more to make empty row
        design_factors_last_row += 1

        # ----- Design Response filling -----
        ws_r = wb['DesignResponses']
        for response in RESPONSES:
            # Design name
            ws_r[f"A{design_responses_last_row}"] = design_name

            # Response
            ws_r[f"B{design_responses_last_row}"] = SYMBOL_TO_NAME[response]

            # Symbol
            ws_r[f"C{design_responses_last_row}"] = response

            # Goal
            ws_r[f"D{design_responses_last_row}"] = "None"

            # Low, High, target - are left empty

            # Units
            ws_r[f"H{design_responses_last_row}"] = SYMBOL_TO_UNITS[response]

            # Measurement
            ws_r[f"I{design_responses_last_row}"] = 1

            # Analyze
            ws_r[f"J{design_responses_last_row}"] = "D"

            # Weight
            ws_r[f"K{design_responses_last_row}"] = 1

            design_responses_last_row += 1

        # ----- Design Factor Data and Design Response Data filling
        ws_dfd = wb['DesignFactorData']
        ws_drd = wb['DesignResponseData']

        for idx, row in df.iterrows():
            # Iterate over factors
            for factor_symbol in factors:
                ws_dfd[f"A{dfd_last_row}"] = design_name
                ws_dfd[f"B{dfd_last_row}"] = run_number
                ws_dfd[f"C{dfd_last_row}"] = factor_symbol
                ws_dfd[f"D{dfd_last_row}"] = df.loc[idx, factor_symbol]

                dfd_last_row += 1

            for response_symbol in RESPONSES:
                ws_drd[f"A{drd_last_row}"] = design_name
                ws_drd[f"B{drd_last_row}"] = run_number
                ws_drd[f"C{drd_last_row}"] = 1
                ws_drd[f"D{drd_last_row}"] = response_symbol
                ws_drd[f"E{drd_last_row}"] = df.loc[idx, response_symbol]

                drd_last_row += 1

            run_number += 1

        design_row += 1

    wb.save(DB_PATH)

    print("===============================-Success!-===============================")
    print("Data successfully was converted to DB.")
    print(f"Amount of converted designs: {design_row - 2}")
    print("========================================================================")
