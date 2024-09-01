import argparse
import os
import pandas as pd
import datetime

from app.configured_shot import simulate

# TODO:
# - create pydantic type for experiment with default values
# - create module to convert to excel DB format
# - add units handling
if __name__ == "__main__":
    start_time = datetime.datetime.now()
    loaded_time = None
    executed_fully_time = None

    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", help="provide file path to input file")

    default_path = "../data/input.csv"
    output_path = "../data/output.csv"

    args = parser.parse_args()

    input_file_path = default_path
    if args.input_file is not None:
        input_file_path = args.input_file

    assert os.path.isfile(input_file_path), "Input file could not be located. Make sure to provide valid path, " \
                                            "or that it is located under /data/input.csv"

    input_df = pd.read_csv(input_file_path, header=0, index_col=0)

    loaded_time = datetime.datetime.now()

    delta_columns = [col for col in input_df.columns if 'delta' in col]
    core_columns = [col for col in input_df.columns if 'delta' not in col]

    output_ls = []
    for index, df_row in input_df.iterrows():
        input_dict = df_row[core_columns].to_dict()
        deltas_dict = df_row[delta_columns].to_dict()

        for k_delta, v_delta in deltas_dict.items():
            k_core = k_delta[6:]
            input_dict[k_core] = input_dict[k_core] + v_delta

        output_simulation = simulate(input_dict)
        output_simulation['Index'] = index
        output_ls.append(output_simulation)

    output_df = pd.DataFrame(output_ls)
    output_df.set_index('Index', inplace=True)

    output_df.to_csv(output_path)

    executed_fully_time = datetime.datetime.now()

    print(f"Time taken to load data: {loaded_time - start_time}")
    print(f"Time taken to process data: {executed_fully_time - loaded_time}")
    print(f"Time taken for the whole process: {executed_fully_time - start_time}")
