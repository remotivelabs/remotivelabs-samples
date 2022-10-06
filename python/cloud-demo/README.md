# Cloud Demo

**Important! This is not a standalone sample** 

This sample is designed to run against our cloud demo environment with the drivecycle that is uploaded there.
You can find this at https://cloud-demo.beamylabs.com, you need to start a broker and play a recording in order
to run this sample.

Once you finish the cloud demo setup with broker + recording you will get the python start command to run
this sample against your broker.

## Run sample

The output command from our cloud-demo will look something like this.

Python 3 is required

```
pip3 install -r requirements.txt 
python3 cloud-demo.py \
  --url <url_from_cloud> \
  --api-key <api_key_from_cloud> \
  --signals Speed,SteeringWheel_Position,Accelerator_PedalPosition
```

This sample simply prints the speed but you can easily subscribe to more signals by digging into the code




## Support
If you have any further questions, please reach out!

