import argparse
import os
import pandas as pd
import numpy as np

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
    "lateral_deviation_angle": 0.05 * 30    # degrees
}


# TODO:
# [x] - create pydantic type for experiment with default values
# - create module to convert to excel DB format
# [x] - add units handling
if __name__ == "__main__":
    # Set up seed for random generator
    np.random.seed(43)

    loaded_time = None
    executed_fully_time = None

    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", help="provide file path to input file")

    default_input_dir = "../data/simulations/raw"
    default_input_file_name = "test_1.xlsx"
    # Change before run ~~~~~~~^^^^^^^^^^^
    default_input_path = os.path.join(default_input_dir, default_input_file_name)

    default_output_dir = "../data/simulations/generated"
    default_output_file_name = f"output-{default_input_file_name}"
    default_output_path = os.path.join(default_output_dir, 'xlsx', default_output_file_name)
    csv_output_file_name = f"{default_output_file_name.split('.')[0]}.csv"
    csv_output_path = os.path.join(default_output_dir, 'csv', csv_output_file_name)

    args = parser.parse_args()

    input_file_path = default_input_path
    if args.input_file is not None:
        input_file_path = args.input_file

    assert os.path.isfile(input_file_path), "Input file could not be located. Make sure to provide valid path, " \
                                            "or that it is located under /data/input.csv"

    input_df = pd.read_excel(input_file_path, header=0, converters=CONVERTING_MAP)
    input_df = input_df.rename(mapper=RENAMING_MAP, axis="columns")

    input_columns = list(input_df.columns)

    outputs_only = []
    io_only = []
    extended_ls = []

    output_columns = None
    for index, df_row in input_df.iterrows():
        fl_model = FullSimulationConfig(**df_row.to_dict())

        input_dict = {k: v for k, v in fl_model.model_dump().items() if 'delta' not in k}
        deltas_dict = DELTAS

        chosen_deltas = {}
        initial_inputs = input_dict.copy()

        for k_delta, v_delta in deltas_dict.items():
            relative_delta = np.random.uniform(-1 * v_delta, v_delta)

            chosen_deltas[f"{k_delta}_chosen"] = relative_delta

            k_core = k_delta[6:]
            if k_delta != "lateral_deviation_angle":
                input_dict[k_core] = input_dict[k_core] + input_dict[k_core] * relative_delta
            else:
                input_dict[k_delta] = relative_delta

        # Adjust firing and release angles due to difference of starting point and direction of angle calculation
        input_dict['release_angle'] = 180 - input_dict['release_angle']
        input_dict['firing_angle'] = 180 - input_dict['firing_angle']

        output_simulation = simulate(input_dict)
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
    output_df = pd.DataFrame(io_only, columns=[*input_columns, *output_columns])
    output_df.set_index('Index', inplace=True)
    output_df = output_df.rename(REVERSE_NAMING_MAP, axis='columns')
    output_df.to_excel(default_output_path)

    extended_df = pd.DataFrame(extended_ls)
    extended_df.set_index('Index', inplace=True)
    extended_df.to_csv(csv_output_path)

    print("===============================-Success!-===============================")
    print(f"Data has been generated for an experiment with the following name: {default_input_file_name.split('.')[0]}")
    print(f"Find respective generated files in the following directory: {os.path.abspath(default_output_dir)}")
    print("========================================================================")
