from __future__ import annotations

import argparse
import csv
import sys

import yaml


def generate_db(source_file: str, target_file: str, csv_recording_file: str):
    signal_names = set()
    targe_yaml_db = {}
    with open(source_file, 'r') as file:
        source_db_yaml = yaml.safe_load(file)

    with open(csv_recording_file, newline='') as csvfile:
        source_recording_csv = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in source_recording_csv:
            # Row is time, signal_name, value
            signal_names.add(row[1])

    # Sorting to make list of signal names in yaml better
    sorted(signal_names)

    # Create target yaml db file
    for name in signal_names:
        targe_yaml_db[name] = source_db_yaml[name]

    with open(target_file, 'w') as file:
        yaml.dump(targe_yaml_db, file)


def main():
    parser = argparse.ArgumentParser(description="Generate new signal database based on csv recording")

    parser.add_argument(
        "-s",
        "--source",
        help="Path to full yaml signal database",
        type=str,
        required=True
    )

    parser.add_argument(
        "-t",
        "--target",
        help="File name of the generated signal database",
        type=str,
        required=True
    )

    parser.add_argument(
        "-r",
        "--recording",
        help="CSV recording to take signals from",
        type=str,
        required=True
    )

    args = parser.parse_args()
    try:
        generate_db(args.source, args.target, args.recording)
    except FileNotFoundError as e:
        print(e)


if __name__ == "__main__":
    main()
