from __future__ import annotations

import argparse
import math
import re
import time
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple

import google.protobuf.internal.containers  # type: ignore
import remotivelabs.broker.sync as br
from grpc import Channel
from typing_extensions import TypeAlias


class SignalValue:  # pylint: disable=R0903
    def __init__(self, name: str, values: list[br.network_api_pb2.Signal]) -> None:
        self.index = 0
        self.name = name
        self.values = values

    def next(self) -> br.network_api_pb2.Signal:
        ret = self.values[self.index]
        self.index = (self.index + 1) % len(self.values)
        return ret


SchedulingTuple: TypeAlias = Tuple[float, str, List[SignalValue]]
E2eCounterStates: TypeAlias = Dict[str, int]
OverrideValues: TypeAlias = Dict[str, List[float]]


def gen_default_publish_values(
    signal_creator: br.SignalCreator,
    manual_sets: OverrideValues,
    child_info: google.protobuf.internal.containers.RepeatedCompositeFieldContainer[Any],
) -> Generator[SignalValue, None, None]:
    for ci in child_info:
        signal_id = ci.id
        meta_data = signal_creator.get_meta(signal_id.name, signal_id.namespace.name)
        default_values = [meta_data.getStartValue(0.0)]
        if signal_id.name in manual_sets:
            default_values = manual_sets[signal_id.name]

        def _yield_values() -> Any:
            for value in default_values:  # pylint: disable=W0640
                yield signal_creator.signal_with_payload(signal_id.name, signal_id.namespace.name, ("double", value))  # pylint: disable=W0640

        yield SignalValue(signal_id.name, list(_yield_values()))


def select_rest_bus_frames(
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
            publish_values = list(gen_default_publish_values(signal_creator, manual_sets, fi.childInfo))
            yield (cycle_time, frame_id.name, publish_values)


def select_e2e_counters(
    frame_infos: Iterable[br.common_pb2.FrameInfo],
) -> Generator[str, None, None]:
    def _yield_all_e2e() -> Generator[str, None, None]:
        for frame in frame_infos:
            meta_data = frame.signalInfo.metaData
            if meta_data.e2e and meta_data.e2e.signalCounter:
                yield meta_data.e2e.signalCounter
            for group in meta_data.groups:
                if group.e2e and group.e2e.signalCounter:
                    yield group.e2e.signalCounter

    for opt_e2e_counter in _yield_all_e2e():
        if opt_e2e_counter:
            yield opt_e2e_counter


# pylint: disable=R0914,R1702
def rest_bus_schedule(
    frame_selection: list[SchedulingTuple],
    e2e_counters: E2eCounterStates,
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    verbose: bool,
) -> None:
    # Use a monotonic timer for scheduling
    clock: float = time.monotonic()

    # Schedule is a sorted list with tuples made of:
    # - Next schedule trigger
    # - Cycle time
    # - Publishable RemoviteBroker values
    schedule: list[Tuple[float, float, list[SignalValue]]] = []

    # Put all signals from frame selection in scheduling array
    for cycle_time_ms, _, publish_values in frame_selection:
        cycle_time: float = cycle_time_ms * 0.001
        schedule.append((clock, cycle_time, publish_values))

    # Client ID of our problam to use in our publish operation
    client_id: br.common_pb2.ClientId = br.common_pb2.ClientId(id="MyRestbus")

    # Counter only used to print verbose information
    sent_frames_count: int = 0

    # Scheduling loop, run as long as there are cyclic frames to publish
    while len(schedule) > 0:
        # Check if sleep is necessary, sleep if so
        next_publish = schedule[0][0]
        clock = time.monotonic()

        if next_publish > clock:
            # For debugging, print what's going on in scheduler
            if verbose:
                ms: int = math.ceil((next_publish - clock) * 1000.0)
                print(f"Sent {sent_frames_count} frames, sleeping for {ms} ms")
                sent_frames_count = 0

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
            for next_sleep, cycle_time, signal_values in triggers:
                for signal_value in signal_values:
                    name = signal_value.name
                    if name in e2e_counters:
                        next_value = e2e_counters[name]
                        next_value += 1
                        if next_value > 14:
                            next_value = 0
                        # Update E2E counter
                        signal_value.values[0].integer = e2e_counters[name] = next_value

                publish_data = list(map(lambda signal_value: signal_value.next(), signal_values))
                publish_combined += publish_data
                sent_frames_count += 1
                if cycle_time > 0.0:
                    new_next_sleep: float = next_sleep + cycle_time
                    schedule.append((new_next_sleep, cycle_time, signal_values))

            # Publish values
            br.publish_signals(client_id, network_stub, publish_combined)

        # Sort schedule by upcoming publish time, first signals in array are upcoming in schedule
        schedule.sort(key=lambda s: s[0])

    # Exit if there are no cyclic signals
    print("No more schedules...")


class RunInfo:
    # pylint: disable=R0903,R0913
    # Contains properties used for a restbus run, such as url and keys.

    def __init__(
        self, url: str, namespace_name: str, frames: list[str], x_api_key: Optional[str] = None, access_token: Optional[str] = None
    ) -> None:
        self.url: str = url
        self.namespace_name: str = namespace_name
        self.frames: list[str] = frames
        self.x_api_key: Optional[str] = x_api_key
        self.access_token: Optional[str] = access_token


def get_frame_selection(
    run_info: RunInfo, intercept_channel: Channel, configure: Optional[str], manual_sets: OverrideValues, exclude: bool
) -> Tuple[list[SchedulingTuple], E2eCounterStates]:
    """Get the frame selection and E2eCounterStates for a chosen run"""

    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)

    if configure:
        print(f"Configuring broker with {configure}")
        br.upload_folder(system_stub, configure)
        br.reload_configuration(system_stub)

    # Get all signals available on broker
    namespace = br.common_pb2.NameSpace(name=run_info.namespace_name)
    signals = system_stub.ListSignals(namespace)

    if len(run_info.frames) == 0:
        # Exit if no frames selected
        print(f"No frames specified, selecting all frames in namespace {run_info.namespace_name}")
        run_info.frames = []
        exclude = True

    # Generate a list of values ready for publish
    sc = br.SignalCreator(system_stub)

    e2e_counters: E2eCounterStates = dict([(signal_name, 0) for signal_name in select_e2e_counters(signals.frame)])  # pylint: disable=R1717
    frame_selection: list[SchedulingTuple] = list(select_rest_bus_frames(sc, manual_sets, signals.frame, run_info.frames, exclude))
    # Return both the frame selection and counters to use for running the restbus
    return frame_selection, e2e_counters


def run(
    run_info: RunInfo,
    exclude: bool,
    verbose: bool,
    configure: Optional[str],
    manual_sets: OverrideValues,
) -> None:
    # gRPC connection to RemotiveBroker
    intercept_channel = br.create_channel(run_info.url, run_info.x_api_key, run_info.access_token)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)

    e2e_counters: E2eCounterStates
    frame_selection: list[SchedulingTuple]
    frame_selection, e2e_counters = get_frame_selection(run_info, intercept_channel, configure, manual_sets, exclude)

    # Run restbus with chosen frames
    if len(frame_selection) > 0:
        print(f"Running restbus for {len(frame_selection)} frames on namespace {run_info.namespace_name}")
        if verbose:
            for cycle_time, frame_id, signal_values in frame_selection:
                if cycle_time > 0.0:
                    print(f"- Frame {frame_id} with cycle time {cycle_time} ms.")
                else:
                    print(f"- Frame {frame_id} without cycle time.")
                for signal_value in signal_values:
                    values_msg = ", ".join(map(lambda value: str(value.double), signal_value.values))
                    print(f"  - Signal {signal_value.name}, default value(s): {values_msg}.")

        try:
            # Run scheduler loop
            rest_bus_schedule(frame_selection, e2e_counters, network_stub, verbose)
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

    raise ValueError("Use pattern SIGNAL_NAME=VALUE")


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
        "-t",
        "--access_token",
        help="Personal or service-account access token",
        type=str,
        required=False,
        default=None,
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
        "-s", "--set", type=str, action="append", metavar="NAME=VALUE", default=[], help="Manually the value of a given signal"
    )

    args = parser.parse_args()
    manual_sets = dict(map(__override_argument_to_tuple, args.set))

    run_info = RunInfo(args.url, args.namespace, args.frame, args.x_api_key, args.access_token)
    run(run_info, args.exclude, args.verbose, args.configure, manual_sets)


if __name__ == "__main__":
    main()
