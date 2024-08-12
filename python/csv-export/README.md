# Export
This sample will subscribe to a given signal and print any published values to this signal.

## Usage

As all python samples in this repository, the pip package [remotivelabs-broker](https://pypi.org/project/remotivelabs-broker/) is required. Install all requirements with [pip](https://pypi.org/):

    pip install -r requirements.txt

Subscribe to a signal by running.

    python export.py --url http://192.168.4.1:50051  --namespace vss --file signals.csv
    
In cloud with cli

    python export.py --url $broker_url --access-token $(remotive cloud auth print-access-token) --namespace vss --file signals.csv


In cloud with api-key (deprecated)

    python export.py --url $broker_url --x-api-key $API_KEY  --namespace vss --file signals.csv


Generate minimal signal database based on signals in csv

    python generate-sigdb.py -s vss_rel_4.2.yaml -t vss_rel_4.2_min.yaml -r signals.csv