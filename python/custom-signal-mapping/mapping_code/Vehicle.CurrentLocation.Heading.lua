local local_signals = {{
    name = "ID2D3UI_solarData.UI_solarAzimuthAngleCarRef",
    namespace = "ChassisBus"
}, {
    name = "ID2D3UI_solarData.UI_solarAzimuthAngle",
    namespace = "ChassisBus"
}}
local local_frequecy_hz = 0

-- Required, declare which input is needed to operate this program.
function input_signals()
    return local_signals
end

-- Provided parameters are used for populating metadata when listing signals.
function output_signals()
    return "Vehicle.CurrentLocation.Heading"
end

-- Required, declare what frequence you like to get "timer" invoked. 0 means no calls to "timer".
function timer_frequency_hz()
    return local_frequecy_hz
end

-- Invoked with the frequecy returned by "timer_frequency_hz".
-- @param system_timestamp_us: system time stamp 
function timer(system_timestamp_us)
    return return_value_or_bytes("your value")
end

-- Invoked when ANY signal declared in "local_signals" arrive
-- @param signals_timestamp_us: signal time stamp
-- @param system_timestamp_us
-- @param signals: array of signals containing all or a subset of signals declared in "local_signals". Make sure to nil check before use.
function signals(signals, namespace, signals_timestamp_us, system_timestamp_us)
    return return_value_or_bytes(math.fmod((360 + signals["ID2D3UI_solarData.UI_solarAzimuthAngle"] - signals["ID2D3UI_solarData.UI_solarAzimuthAngleCarRef"]), 360))
end

-- helper return function, make sure to use return_value_or_bytes or return_nothing.
function return_value_or_bytes(value_or_bytes)
    return value_or_bytes
end

-- helper return function, make sure to use return_value_or_bytes or return_nothing.
function return_nothing()
    return
end
