import argparse


def parse(argv):
    parser = argparse.ArgumentParser(description="Provide address to RemotiveBroker")

    parser.add_argument(
        "-url",
        "--url",
        type=str,
        help="URL of the RemotiveBroker",
        required=True,
    )

    parser.add_argument(
        "-api-key",
        "--api-key",
        type=str,
        help="API key is required when accessing brokers running in the cloud",
        required=False,
        default=None
    )

    parser.add_argument(
        "-t",
        "--access-token",
        help="Personal or service-account access token",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "-signals",
        "--signals",
        required=False,
        help="Comma separated list of signal names to subscribe on",
        default="Speed",
        type=lambda s: [item for item in s.split(',')]
    )

    args = parser.parse_args()
    # run(args.url, args.api_key, args.signals)
    return args
