import argparse
import os
import pandas as pd
import numpy as np
import glob
import datetime

from app.configured_shot import simulate
from models import FullSimulationConfig, SimulationConfig


def mm_to_m(millimeters: float) -> float:
    return millimeters / 1000


def g_to_kg(g: float) -> float:
    return g / 1000


CONVERTING_MAP = {
    "BA": g_to_kg,
    "CE": mm_to_m,
    "PE": mm_to_m,
    "BP": mm_to_m,
}

RENAMING_MAP = {
    "BA": "ball_mass",
    "FA": "firing_angle",
    "RA": "release_angle",
    "CE": "cup_elevation",
    "PE": "pin_elevation",
    "BP": "bungee_position",
    "R": "x_ground",
    "Y": "y_ground",
    "Z": "z_ground",
    "MH": "max_height"
}

REVERSE_NAMING_MAP = {v: k for k, v in RENAMING_MAP.items()}

# Dict with amplitudes of deltas in percentages for maximum possible deviation
# Change / Comment before run
DELTAS = {
    "delta_g": 0.01,
    "delta_spring_constant": 0.05,
    "delta_moment_of_inertia": 0.05,
    "delta_cup_mass": 0.05,
    "delta_ball_mass": 0.05,

    "delta_axle_distance": 0.05,
    "delta_bungee_length_no_load": 0.05,
    "delta_height_offset": 0.05,

    "delta_pin_elevation": 0.05,
    "delta_bungee_position": 0.05,
    "delta_cup_elevation": 0.05,
    "delta_firing_angle": 0.05,
    "delta_release_angle": 0.05,

    # The only delta factor without core counterpart, and in degrees
    "lateral_deviation_angle": 0.05 * 30  # degrees
}

ALL_FACTORS = [
    'ball_mass',
    'firing_angle',
    'release_angle',
    'cup_elevation',
    'pin_elevation',
    'bungee_position'
]

# TODO:
# [x] - create pydantic type for experiment with default values
# [x] - create module to convert to excel DB format
# [x] - add units handling
# - If the value is const, add a little jitter: 10^-6
# [x] - Make a unified structure for data concatenation from different experiments
# - Run identifier to be added to the output .xlsx file
# - Not to vary too much -> if finish with rect only then go to normal distribution
# - Start with absolute value of the stiffness before looking at jitter
if __name__ == "__main__":
    # Set up seed for random generator
    np.random.seed(43)

    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", help="provide file path to input file")

    default_input_dir = "../data/simulations/raw"
    default_output_dir = "../data/simulations/generated"

    # Get all the files in the input directory
    filenames = glob.glob("*.xlsx", root_dir=default_input_dir)
    experiments_count = 0

    # Stacking data from all designs in a df
    stacked_data_df = None

    # Amount of total generations
    generations = 4

    # Iterating over files
    for input_file_name in filenames:
        # Skip temporary excel files
        if "~$" in input_file_name:
            continue

        input_path = os.path.join(default_input_dir, input_file_name)

        input_df = pd.read_excel(input_path, header=0, converters=CONVERTING_MAP)
        input_df = input_df.rename(mapper=RENAMING_MAP, axis="columns")

        # Meta-data information df
        metadata_df = pd.read_excel(input_path, sheet_name="Meta-data")

        # Experiment identifier
        experiment_core_identifier = input_file_name.split('.')[0]

        # Deltas information df
        deltas_information_df = pd.read_excel(input_path, sheet_name="deltas_for_design")

        # Factors chosen in the design
        design_input_columns = list(input_df.columns)
        # List of all possible factors
        input_columns = ALL_FACTORS
        # Set of factors not chosen in the design
        const_input_columns = set(input_columns) - set(design_input_columns)
        for gen_idx in range(generations):

            experiment_identifier = experiment_core_identifier + f"-generation_{gen_idx}"

            # Insert file_name into meta-data df
            metadata_df['Experiment Identifier'] = experiment_identifier

            outputs_only = []
            io_only = []
            extended_ls = []

            output_columns = None
            for index, df_row in input_df.iterrows():
                fl_model = FullSimulationConfig(**df_row.to_dict())

                # Wear out (lower stiffness of) bungee rope
                fl_model.spring_constant = fl_model.spring_constant * 0.9**gen_idx
                print(experiments_count, "/", len(filenames))

                # Necessary data for simulation
                input_dict = {k: v for k, v in fl_model.model_dump().items() if 'delta' not in k}
                deltas_dict = deltas_information_df.loc[0].to_dict()

                # Data going to output files
                chosen_deltas = {}
                initial_inputs = input_dict.copy()
                initial_inputs['Experiment Identifier'] = metadata_df.loc[0, 'Experiment Identifier']

                for k_delta, v_delta in deltas_dict.items():
                    relative_delta = np.random.uniform(-1 * v_delta, v_delta)

                    chosen_deltas[f"{k_delta}_chosen"] = relative_delta

                    k_core = k_delta[6:]
                    if k_delta != "lateral_deviation_angle":
                        input_dict[k_core] = input_dict[k_core] + input_dict[k_core] * relative_delta
                    else:
                        input_dict[k_delta] = relative_delta

                # Adjust firing and release angles
                # due to difference of starting point and direction of angle calculation
                input_dict['release_angle'] = 180 - input_dict['release_angle']
                input_dict['firing_angle'] = 180 - input_dict['firing_angle']

                # Leave empty erroring experiments
                try:
                    output_simulation = simulate(input_dict)

                except ValueError as e:
                    output_simulation = {
                        "x_ground": "",
                        "y_ground": "",
                        "z_ground": "",
                        "max_height": ""
                    }

                # Set output columns names
                if output_columns is None:
                    output_columns = output_simulation.keys()

                output_simulation['Index'] = index

                io_data = {**output_simulation, **initial_inputs}
                extended_data = {**io_data, **chosen_deltas}

                outputs_only.append(output_simulation)
                io_only.append(io_data)
                extended_ls.append(extended_data)

            assert output_columns is not None, "Column names for the outputs were not inferred"

            # Output paths
            default_output_file_name = f"output-{experiment_identifier}.xlsx"
            default_output_path = os.path.join(default_output_dir, 'xlsx', default_output_file_name)

            csv_output_file_name = f"output-{experiment_identifier}.csv"
            csv_output_path = os.path.join(default_output_dir, 'csv', csv_output_file_name)

            metadata_output_file_name = f"output-{experiment_identifier}.csv"
            metadata_output_path = os.path.join(default_output_dir, 'metadata', metadata_output_file_name)

            # Writing down data
            output_df = pd.DataFrame(
                io_only,
                columns=[
                    *input_columns,
                    *output_columns,
                    'Experiment Identifier',
                ]
            )
            output_df.set_index('Index', inplace=True)
            output_df = output_df.rename(REVERSE_NAMING_MAP, axis='columns')
            output_df.to_excel(default_output_path)

            # Stacking data in all runs data file
            if stacked_data_df is None:
                stacked_data_df = output_df.copy()
            else:
                stacked_data_df = pd.concat([stacked_data_df, output_df], ignore_index=True)

            extended_df = pd.DataFrame(extended_ls)
            extended_df.set_index('Index', inplace=True)
            extended_df.to_csv(csv_output_path)

            metadata_df.to_csv(metadata_output_path)

            experiments_count += 1

        # Stacked data output path
        stacked_output_file_name = f"stacked-{datetime.date.today()}.csv"
        stacked_output_path = os.path.join(default_output_dir, 'stacked', stacked_output_file_name)
        stacked_excel_name = f"stacked-{datetime.date.today()}.xlsx"
        stacked_excel_path = os.path.join(default_output_dir, 'stacked', stacked_excel_name)

        # Writing down stacked data
        stacked_data_df = stacked_data_df.reset_index(drop=True)
        stacked_data_df.to_csv(stacked_output_path)
        stacked_data_df.to_excel(stacked_excel_path)

    print("===============================-Success!-===============================")
    print(f"Data has been generated for {experiments_count} experiments")
    print(f"Find respective generated files in the following directory: {os.path.abspath(default_output_dir)}")
    print("========================================================================")
