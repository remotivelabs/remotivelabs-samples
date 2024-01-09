# Code snippets

Small runnable code snippets for inspiration

## Moving average

Calculates a moving average (ish) for a numeric signal and prints to console.

*NOTE - This is a code sample - not a sample of how to use moving average properly :-)*

Uses environment variables to configure.

* URL: Local or cloud url (default: http://localhost:50051)
* API_KEY: api-key or user/service-account token (default: None)
* SIGNAL_NAME: The numeric signal to subscribe to (default: Vehicle.Speed)
* NAMESPACE: The namespace to use for subscription (default: vss)
* WINDOW: Moving average window size in signal count (default: 1000)
* INTERVAL: Seconds between each avg calculation (default: 2)

### Prepare

Prepare a virtualenv (or similar is recommended) with dependencies.

```bash
cd remotivelabs-samples/python/snippets
virtualenv venv
source venv/bin/activate
./venv/bin/pip install -r requirements.txt
```

#### Run from cloud with default signals

1. Goto https://demo.remotivelabs.com or https://cloud.remotivelabs.com and play any recording
with transformation "configuration_vss".

2. Run script, replace with correct url and api-key
```bash
URL=https://my-cloud-broker.url \
API_KEY=the_api_key \
 ./mov_avg.py
```
3. Output should look something like this

```json lines
{'avg': 37.7, 'min': 14, 'max': 50, 'latest': 50, 'count': 1000}
{'avg': 41.24, 'min': 14, 'max': 50, 'latest': 48, 'count': 1000}
{'avg': 43.87, 'min': 23, 'max': 50, 'latest': 38, 'count': 1000}
{'avg': 43.93, 'min': 21, 'max': 50, 'latest': 21, 'count': 1000}
```