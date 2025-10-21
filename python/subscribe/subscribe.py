#!/usr/bin/env python

from __future__ import annotations

import argparse
from dataclasses import asdict
import asyncio
from remotivelabs.broker.client import BrokerClient
from remotivelabs.broker.auth import ApiKeyAuth, NoAuth


class ParseSignals(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        store = getattr(namespace, self.dest, None)
        if store is None:
            store = []

        temp: dict[str, list[str]] = {}

        for item in values:
            if ":" not in item:
                raise argparse.ArgumentError(
                    self, f"Invalid format: '{item}', expected namespace:signal"
                )
            ns, sig = item.split(":", 1)
            temp.setdefault(ns, []).append(sig)

        store.extend((ns, sigs) for ns, sigs in temp.items())

        setattr(namespace, self.dest, store)


async def main():
    parser = argparse.ArgumentParser(description="Provide address to RemotiveBroker")

    parser.add_argument(
        "-u",
        "--url",
        help="URL of the RemotiveBroker",
        type=str,
        required=False,
        default="http://127.0.0.1:50051",
    )

    parser.add_argument(
        "-x",
        "--x_api_key",
        help="API key is required when accessing brokers running in the cloud",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "-t",
        "--access_token",
        help="Personal or service-account access token",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "-s",
        "--signals",
        help="Signal to subscribe to",
        required=True,
        nargs="*",
        action=ParseSignals,
    )

    args = parser.parse_args()
    auth = ApiKeyAuth(args.x_api_key) if args.x_api_key is not None else NoAuth()
    async with BrokerClient(url=args.url, auth=auth) as client:
        async for signals in await client.subscribe(*args.signals):
            for signal in signals:
                print(asdict(signal))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
