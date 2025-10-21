local local_signals = {{
    name = "ID257DIspeed.DI_vehicleSpeed",
    namespace = "VehicleBus"
}}

local local_frequecy_hz = 10
local state_of_charge = 0

-- Required, declare which input is needed to operate this program.
function input_signals()
    return local_signals
end

-- Provided parameters are used for populating metadata when listing signals.
function output_signals()
    return "Vehicle.Speed"
end

-- Required, declare what frequency you like to get "timer" invoked. 0 means no calls to "timer".
function timer_frequency_hz()
    return local_frequecy_hz
end

-- Invoked with the frequecy returned by "timer_frequency_hz".
-- @param system_timestamp_us: system time stamp
function timer(system_timestamp_us)
    return return_value_or_bytes(state_of_charge)
end

-- Invoked when ANY signal declared in "local_signals" arrive
-- @param signals_timestamp_us: signal time stamp
-- @param system_timestamp_us
-- @param signals: array of signals containing all or a subset of signals declared in "local_signals". Make sure to nil check before use.
function signals(signals, namespace, signals_timestamp_us, system_timestamp_us)
    state_of_charge = signals["ID257DIspeed.DI_vehicleSpeed"]
    return return_value_or_bytes(signals["ID257DIspeed.DI_vehicleSpeed"])
end

-- helper return function, make sure to use return_value_or_bytes or return_nothing.
function return_value_or_bytes(value_or_bytes)
    return value_or_bytes
end

-- helper return function, make sure to use return_value_or_bytes or return_nothing.
function return_nothing()
    return
end
