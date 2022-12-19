# Simple ECU
`simple-ecu` folder contains `ecu.py`. With intention to give example and inspiration to further development. To get started and to get more details of the examples, continue reading.

Simple ecu simulates 2 ecu:s which are connected (using `LIN`/`CAN`/`udp`) (defaults to `upd`)

> If you use `CAN` devices you need to connect the connectors, creating you own simple network (remember to terminated the ends).

`Ecu_A`:
- Publishes `counter` signal on a timer.
- Synchronously reads `counter_times_2` and prints the results.

`Ecu_B`:
- Subscribes to `counter`
- Doubles the value and publishes `counter_times_2` 
> Ecu_B also showcases a syncronous read using a timer.

## Pre-requisites
> Have knowledge of the ip address to your RemotiveBroker installation, if you have the web-client running you can get the ip in the bottom left corner.

This sample will connect to a RemotiveBroker instance. Make sure you have on up and running either locally or via the cloud.

## Get started

From *this* location run:
```
pip install -r requirements.txt
```

> if you don't have python3 installed go [here](https://github.com/beamylabs/beamylabs-start/tree/master/examples/grpc/python#readme)

### Options

ecu.py can be started with options `-h` or `--ecu <address>`.

* `--url <address>` - Points to the ip of your RemotiveBroker installation, if this option is not used the scripts will use address `http://127.0.0.1:50051`. For example start the script by typing:
`python3 ecu.py --url http://192.168.0.xxx`

* `-h` - Help, shows available options for script, run `python3 ecu.py -h`

### Default instructions
1. Run shell (terminal, powershell, etc.).
2. From [this directory](.) run:

```sh
python ecu.py --url <address>
```

### Overview
A bunch of things are going on in this examples and it all starts in the main function `def run(argv):`. Lets break it down.

#### Setting up stubs and configuration
First we start of with setting up a connection to the RemotiveBroker (with the ip that was passed to the script) and then defining the gRPC stubs that will be used. In code it typically looks like this:

```python
intercept_channel = br.create_channel(url, x_api_key)

network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
br.check_license(system_stub)
```

#### Configuration
Simple ecu folder contains some examples of different configurations, available configurations to use are the following:

* [CAN](configuration_can).
* [LIN](configuration_lin).
* [UDP](configuration_udp).

The example scripts uploads and reloads configuration with the `system_stub` that was defined above. Some lines are commented and not in use, but you can easily uncomment a line to shift between configurations or feel free to use your own.
It will look similar to this:
```
br.upload_folder(system_stub, "configuration_udp")
# br.upload_folder(system_stub, "configuration_lin")
# br.upload_folder(system_stub, "configuration_can")
# br.upload_folder(system_stub, "configuration_canfd")
br.reload_configuration(system_stub)
```
> For _CAN_/_LIN_ to work you need seperate HW.

#### Threads
The last part of `ecu.py` is starting up threads, you can read the docs for threading [here](https://docs.python.org/3/library/threading.html). 
You will see a thread called `ecu_A_thread`, this thread defines the target-function `ecu_A` and will then start the thread. 
```python
ecu_A_thread = Thread(
  target=ecu_A,
  args=(network_stub,),
)
ecu_A_thread.start()
```
The function `ecu_A` will publish one or multiple signals which then can be caught and read by ecu_B. In this examples `ecu_A` also reads a value that's been published by ecu_B.

We also see a thread called `ecu_B_sub_thread` which shows how to subscribe to signals that has been published by ecu_A. The thread `ecu_read_on_timer` is a synchronous variant of this and also has the purpose to read.

`ecu_B_sub_thread` thread uses `subscribe` which then calls `act_on_signal` which will invoke provided function (here a lambda) once a subscrpition is triggered on any of the provided signals.

```python
for subs_counter in subscripton:
    fun(subs_counter.signal)
```

```python
# Starting subscription thread
    subscription = subscribe(
        br,
        ecu_b_client_id,
        network_stub,
        [
            signal_creator.signal("counter", "ecu_B"),
            # here you can add any signal from any namespace
            # signal_creator.signal("TestFr04", "ecu_B"),
        ],
        lambda signals: double_and_publish(
            network_stub,
            ecu_b_client_id,
            signal_creator.signal("counter", "ecu_B"),
            signals,
        ),
    )
```

Every time the `counter` signal arrives, the function will take the value from the incoming signal, double the value and publish it as another signal `counter_times_2` (which then can be read by ecu_A).

```python
def double_and_publish(network_stub, client_id, trigger, signals):
    for signal in signals:
        print(f"ecu_B, (subscribe) {signal.id.name} {get_value(signal)}")
        if signal.id == trigger:
            publish_signals(
                client_id,
                network_stub,
                [
                    signal_creator.signal_with_payload(
                        "counter_times_2", "ecu_B", ("integer", get_value(signal) * 2)
                    ),
                ],
            )
```

#### Support
If you have any further questions, please reach out!

