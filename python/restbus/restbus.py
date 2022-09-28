import argparse
import math
import sys
import time

import remotivelabs.broker.sync as br

def publishScheduler():
    pass

def genDefaultPublishValues(signal_creator, child_info):
    for ci in child_info:
        # TODO Use default value
        signalId = ci.id
        meta_data = signal_creator.get_meta(signalId.name, signalId.namespace.name)
        default_value = meta_data.getStartValue(0.0)
        yield signal_creator.signal_with_payload(
                signalId.name, signalId.namespace.name, ("double", default_value)
                )

def selectRestBusFrames(signal_creator, frame_infos, match_frames, exclude):

    for fi in frame_infos:
        si = fi.signalInfo
        # TODO get cycle time

        matching = si.id.name in match_frames
        if exclude:
            matching = not matching

        if matching:
            frame_id = si.id
            meta_data = signal_creator.get_meta(frame_id.name, frame_id.namespace.name)
            cycle_time = meta_data.getCycleTime(0.0)
            publish_values = list(genDefaultPublishValues(signal_creator, fi.childInfo))
            yield (cycle_time, frame_id.name, publish_values)

def restBusSchedule(frameSelection, network_stub, verbose):
    clock = time.monotonic()
    schedule = []

    # Put everything in schedule
    for cycle_time_ms, _, publish_values in frameSelection:
        cycle_time = cycle_time_ms * 0.001
        schedule.append((clock, cycle_time, publish_values))

    clientId = br.common_pb2.ClientId(id="Restbus")

    now = time.monotonic()
    sentFramesCount = 0
    while len(schedule) > 0:
        next_publish = schedule[0][0]
        now = time.monotonic()
        if next_publish > now:
            if verbose:
                ms = math.ceil((next_publish - now) * 1000.0)
                print("Sent {} frames, sleeping for {} ms".format(sentFramesCount, ms))
                sentFramesCount = 0
            time.sleep(next_publish - now)

        trigger_index = 0
        for i, sh in enumerate(schedule):
            next_trigger, _, _ = sh
            if next_trigger < now:
                trigger_index = i+1
        triggers = schedule[:trigger_index]
        schedule = schedule[trigger_index:]

        if len(triggers) > 0:
            publish_combined = []
            for next_sleep, cycle_time, publish_data in triggers:
                publish_combined += publish_data
                sentFramesCount += 1
                if cycle_time > 0.0:
                    new_next_sleep = next_sleep + cycle_time
                    schedule.append((new_next_sleep, cycle_time, publish_data))
            br.publish_signals(clientId, network_stub, publish_combined)

        schedule.sort()
    print("No more schedules...")

def run(url, x_api_key, namespace_name, frames, exclude, verbose, reload_config):
    intercept_channel = br.create_channel(url, x_api_key)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)

    if reload_config:
        print('Reloading sample configuration')
        br.upload_folder(system_stub, "configuration_udp")
        # br.upload_folder(system_stub, "configuration_can")
        br.reload_configuration(system_stub)

    sc = br.SignalCreator(system_stub)
    namespace = br.common_pb2.NameSpace(name=namespace_name)
    signals = system_stub.ListSignals(namespace)

    if len(frames) == 0:
        print('No frames specified, selecting all frames in namespace {}'.format(namespace_name))
        frames = []
        exclude = True

    frameSelection = list(selectRestBusFrames(sc, signals.frame, frames, exclude))

    if len(frameSelection) > 0:
        print("Running restbus for {} frames on namespace {}".format(len(frameSelection), namespace_name))
        if verbose:

            for cycle_time, frame_id, publish_values in frameSelection:
                signals = ", ".join(map(lambda pair: pair.id.name, publish_values))
                if cycle_time > 0.0:
                    print('- Frame {} with cycle time {} ms.'.format(frame_id, cycle_time))
                else:
                    print('- Frame {} without cycle time.'.format(frame_id))
                for pair in publish_values:
                    print('  - Signal {}, default value: {}.'.format(pair.id.name, pair.double))

        try:
            restBusSchedule(frameSelection, network_stub, verbose)
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Closing scheduler.")
    else:
        print("No frames selected, exit...")

def main(argv):
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
        default="offline",
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
        default=[]
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
        default=False
    )

    parser.add_argument(
        "-reload",
        "--reload",
        help="Reload with example configuration",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    run(args.url, args.x_api_key, args.namespace, args.frame, args.exclude, args.verbose, args.reload)


if __name__ == "__main__":
    main(sys.argv[1:])

