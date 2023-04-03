import argparse
import math
import time
import re
from typing import Generator, Tuple, TypeAlias, Iterable, Optional

import remotivelabs.broker.sync as br


class SignalValue:
    def __init__(self, name: str, values: list[br.network_api_pb2.Signal]):
        self.index = 0
        self.name = name
        self.values = values

    def next(self):
        ret = self.values[self.index]
        self.index = (self.index + 1) % len(self.values)
        return ret


SchedulingTuple: TypeAlias = Tuple[float, str, list[SignalValue]]
E2eCounterStates: TypeAlias = dict[str, int]
OverrideValues: TypeAlias = dict[str, list[float]]


def genDefaultPublishValues(
    signal_creator, manual_sets, child_info
) -> Generator[SignalValue, None, None]:

    for ci in child_info:
        signalId = ci.id
        meta_data = signal_creator.get_meta(signalId.name, signalId.namespace.name)
        default_values = [meta_data.getStartValue(0.0)]
        if signalId.name in manual_sets:
            default_values = manual_sets[signalId.name]

        def _yield_values():
            for value in default_values:
                yield signal_creator.signal_with_payload(
                    signalId.name, signalId.namespace.name, ("double", value)
                )

        yield SignalValue(signalId.name, list(_yield_values()))


def selectRestBusFrames(
    signal_creator: br.SignalCreator,
    manual_sets: OverrideValues,
    frame_infos: Iterable[br.common_pb2.FrameInfo],
    match_frames: list[str],
    exclude: bool,
) -> Generator[SchedulingTuple, None, None]:

    for fi in frame_infos:
        si = fi.signalInfo

        matching = si.id.name in match_frames
        if exclude:
            matching = not matching

        if matching:
            frame_id = si.id
            meta_data = signal_creator.get_meta(frame_id.name, frame_id.namespace.name)
            cycle_time = meta_data.getCycleTime(0.0)
            publish_values = list(
                genDefaultPublishValues(signal_creator, manual_sets, fi.childInfo)
            )
            yield (cycle_time, frame_id.name, publish_values)


def selectE2eCounters(
    frame_infos: Iterable[br.common_pb2.FrameInfo],
) -> Generator[str, None, None]:
    def _yield_all_e2e():
        for frame in frame_infos:
            metaData = frame.signalInfo.metaData
            if metaData.e2e and metaData.e2e.signalCounter:
                yield metaData.e2e.signalCounter
            for group in metaData.groups:
                if group.e2e and group.e2e.signalCounter:
                    yield group.e2e.signalCounter

    for opt_e2e_counter in _yield_all_e2e():
        if opt_e2e_counter:
            yield opt_e2e_counter


def restBusSchedule(
    frameSelection: list[SchedulingTuple],
    e2eCounters: E2eCounterStates,
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    verbose: bool,
) -> None:

    # Use a monotonic timer for scheduling
    clock: float = time.monotonic()

    # Schedule is a sorted list with tuples made of:
    # - Next schedule trigger
    # - Cycle time
    # - Publishable RemoviteBroker values
    schedule: list[Tuple[float, float, list[br.network_api_pb2.Signal]]] = []

    # Put all signals from frame selection in scheduling array
    for cycle_time_ms, _, publish_values in frameSelection:
        cycle_time: float = cycle_time_ms * 0.001
        schedule.append((clock, cycle_time, publish_values))

    # Client ID of our problam to use in our publish operation
    clientId: br.common_pb2.ClientId = br.common_pb2.ClientId(id="MyRestbus")

    # Counter only used to print verbose information
    sentFramesCount: int = 0

    # Scheduling loop, run as long as there are cyclic frames to publish
    while len(schedule) > 0:
        # Check if sleep is necessary, sleep if so
        next_publish = schedule[0][0]
        clock = time.monotonic()

        if next_publish > clock:
            # For debugging, print what's going on in scheduler
            if verbose:
                ms: int = math.ceil((next_publish - clock) * 1000.0)
                print("Sent {} frames, sleeping for {} ms".format(sentFramesCount, ms))
                sentFramesCount = 0

            # Sleep scheduler until next scheduled event
            sleep_time: float = next_publish - clock
            time.sleep(sleep_time)

        # Look for frames ready to be sent according to schedule
        trigger_index = 0
        for i, sh in enumerate(schedule):
            next_trigger, _, _ = sh
            if next_trigger < clock:
                trigger_index = i + 1

        triggers = schedule[:trigger_index]  # Signals for publish
        schedule = schedule[trigger_index:]  # Singals not ready for publish

        if len(triggers) > 0:
            # Collect values to be published
            publish_combined: list[br.network_api_pb2.Signal] = []
            for next_sleep, cycle_time, signalValues in triggers:

                for signalValue in signalValues:
                    name = signalValue.name
                    if name in e2eCounters:
                        next = e2eCounters[name]
                        next += 1
                        if next > 14:
                            next = 0
                        # Update E2E counter
                        signalValue.values[0].integer = e2eCounters[name] = next

                publish_data = list(
                    map(lambda signalValue: signalValue.next(), signalValues)
                )
                publish_combined += publish_data
                sentFramesCount += 1
                if cycle_time > 0.0:
                    new_next_sleep: float = next_sleep + cycle_time
                    schedule.append((new_next_sleep, cycle_time, signalValues))

            # Publish values
            br.publish_signals(clientId, network_stub, publish_combined)

        # Sort schedule by upcoming publish time, first signals in array are upcoming in schedule
        schedule.sort(key=lambda s: s[0])

    # Exit if there are no cyclic signals
    print("No more schedules...")


def run(
    url: str,
    x_api_key: str,
    namespace_name: str,
    frames: list[str],
    exclude: bool,
    verbose: bool,
    configure: Optional[str],
    manual_sets: OverrideValues,
) -> None:

    # gRPC connection to RemotiveBroker
    intercept_channel = br.create_channel(url, x_api_key)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)

    if configure:
        print("Configuring broker with {}".format(configure))
        br.upload_folder(system_stub, configure)
        br.reload_configuration(system_stub)

    # Get all signals available on broker
    namespace = br.common_pb2.NameSpace(name=namespace_name)
    signals = system_stub.ListSignals(namespace)

    if len(frames) == 0:
        # Exit if no frames selected
        print(
            "No frames specified, selecting all frames in namespace {}".format(
                namespace_name
            )
        )
        frames = []
        exclude = True

    # Generate a list of values ready for publish
    sc = br.SignalCreator(system_stub)
    frameSelection: list[SchedulingTuple] = list(
        selectRestBusFrames(sc, manual_sets, signals.frame, frames, exclude)
    )
    e2eCounters: E2eCounterStates = dict(
        [(signal_name, 0) for signal_name in selectE2eCounters(signals.frame)]
    )

    if len(frameSelection) > 0:
        print(
            "Running restbus for {} frames on namespace {}".format(
                len(frameSelection), namespace_name
            )
        )
        if verbose:

            for cycle_time, frame_id, signalValues in frameSelection:
                if cycle_time > 0.0:
                    print(
                        "- Frame {} with cycle time {} ms.".format(frame_id, cycle_time)
                    )
                else:
                    print("- Frame {} without cycle time.".format(frame_id))
                for signalValue in signalValues:
                    valuesMsg = ", ".join(
                        map(
                            lambda value: str(value.double),
                            signalValue.values
                        )
                    )
                    print(
                        "  - Signal {}, default value(s): {}.".format(
                            signalValue.name, valuesMsg
                        )
                    )

        try:
            # Run scheduler loop
            restBusSchedule(frameSelection, e2eCounters, network_stub, verbose)
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Closing scheduler.")
    else:
        print("No frames selected, exit...")


__REGEXP_OVERRIDE_ARG = re.compile(r"(\w+)=(.+)")


def __override_argument_to_tuple(argument: str) -> Tuple[str, list[float]]:
    res = __REGEXP_OVERRIDE_ARG.match(argument)
    if res:
        name = res.group(1)
        values = list(map(float, res.group(2).split(",")))
        return (name, values)
    else:
        raise Exception("Use pattern SIGNAL_NAME=VALUE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Provide address to Beambroker")

    parser.add_argument(
        "-url",
        "--url",
        help="URL of the RemotiveBroker",
        type=str,
        required=False,
        default="http://127.0.0.1:50051",
    )

    parser.add_argument(
        "-x_api_key",
        "--x_api_key",
        help="API key is required when accessing brokers running in the cloud",
        type=str,
        required=False,
    )

    parser.add_argument(
        "-namespace",
        "--namespace",
        help="Namespace to select frames on",
        type=str,
        required=True,
    )

    parser.add_argument(
        "-frame",
        "--frame",
        help="Frame name to echo. If not specified all frames in namespace will be used",
        type=str,
        required=False,
        action="append",
        default=[],
    )

    parser.add_argument(
        "-exclude",
        "--exclude",
        help="Exclude selection of frames",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-v",
        "-verbose",
        "--verbose",
        help="Print verbose information",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-c",
        "--configure",
        type=str,
        required=False,
        metavar="DIRECTORY",
        help="Upload and use configuration",
    )

    parser.add_argument(
        "-s",
        "--set",
        type=str,
        action="append",
        metavar="NAME=VALUE",
        default=[],
        help="Manually the value of a given signal"
    )

    args = parser.parse_args()
    manual_sets = dict(map(__override_argument_to_tuple, args.set))

    run(
        args.url,
        args.x_api_key,
        args.namespace,
        args.frame,
        args.exclude,
        args.verbose,
        args.configure,
        manual_sets,
    )


if __name__ == "__main__":
    main()
