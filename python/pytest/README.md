# Pytest
Sample for using [remotiveBroker Python API](https://github.com/remotivelabs/remotivelabs-apis) in a [pytest](https://docs.pytest.org/) environment.

## Usage
As all python samples in this repository, the pip package [remotivelabs-broker](https://pypi.org/project/remotivelabs-broker/) is required. Install all requirements with [pip](https://pypi.org/):

    pip install -r requirements.txt

This will also install the latest version of the `pytest` package

In order to run these tests, you must have a _remotiveBroker_ server instance up and running.
The address of the server and optional API key must be set in the top of the test file `test_sample.py`:

```python
_SERVER_URL = 'http://127.0.0.1:50051'
_SERVER_APIKEY = 'offline'
```

Run all tests in this directory:

    pytest
