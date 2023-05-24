import numpy as np


def calculate_contingency(fcst, obs):
    cont = np.zeros_like(obs)
    cont[(fcst > 0) & (obs > 0)] = 4  # hit
    cont[(fcst > 0) & (obs == 0)] = 3  # false alarm
    cont[(fcst == 0) & (obs > 0)] = 2  # miss
    cont[(fcst == 0) & (obs == 0)] = 1  # correct negative
    return cont


def calculate_cont_dry(fcst, obs):
    cont = np.zeros_like(obs)
    cont[((fcst >= 0.1) & (fcst < 5)) & ((obs >= 0.1) & (obs < 5))] = 4  # hit
    cont[((fcst >= 0.1) & (fcst < 5)) & (obs >= 5)] = 3  # false alarm
    cont[(fcst >= 5) & ((obs >= 0.1) & (obs < 5))] = 2  # miss
    cont[(fcst >= 5) & (obs >= 5)] = 1  # correct negative
    cont[(fcst == 0) | (obs == 0)] = np.nan  # no rain case
    return cont


def calculate_cont_low(fcst, obs):
    cont = np.zeros_like(obs)
    cont[((fcst >= 5) & (fcst < 20)) & ((obs >= 5) & (obs < 20))] = 4  # hit
    cont[
        ((fcst >= 5) & (fcst < 20)) & ((obs >= 20) | ((obs >= 0.1) & (obs < 5)))
    ] = 3  # false alarm
    cont[
        ((fcst >= 20) | ((fcst >= 0.1) & (fcst < 5))) & ((obs >= 5) & (obs < 20))
    ] = 2  # miss
    cont[
        ((fcst >= 20) | ((fcst >= 0.1) & (fcst < 5)))
        & ((obs >= 20) | ((obs >= 0.1) & (obs < 5)))
    ] = 1  # correct negative
    cont[(fcst == 0) | (obs == 0)] = np.nan  # no rain case
    return cont


def calculate_cont_moderate(fcst, obs):
    cont = np.zeros_like(obs)
    cont[((fcst >= 20) & (fcst < 35)) & ((obs >= 20) & (obs < 35))] = 4  # hit
    cont[
        ((fcst >= 20) & (fcst < 35)) & ((obs >= 35) | ((obs >= 0.1) & (obs < 20)))
    ] = 3  # false alarm
    cont[
        ((fcst >= 35) | ((fcst >= 0.1) & (fcst < 20))) & ((obs >= 20) & (obs < 35))
    ] = 2  # miss
    cont[
        ((fcst >= 35) | ((fcst >= 0.1) & (fcst < 20)))
        & ((obs >= 35) | ((obs >= 0.1) & (obs < 20)))
    ] = 1  # correct negative
    cont[(fcst == 0) | (obs == 0)] = np.nan  # no rain case
    return cont


def calculate_cont_heavy(fcst, obs):
    cont = np.zeros_like(obs)
    cont[((fcst >= 35) & (fcst < 50)) & ((obs >= 35) & (obs < 50))] = 4  # hit
    cont[
        ((fcst >= 35) & (fcst < 50)) & ((obs >= 50) | ((obs >= 0.1) & (obs < 35)))
    ] = 3  # false alarm
    cont[
        ((fcst >= 50) | ((fcst >= 0.1) & (fcst < 35))) & ((obs >= 35) & (obs < 50))
    ] = 2  # miss
    cont[
        ((fcst >= 50) | ((fcst >= 0.1) & (fcst < 35)))
        & ((obs >= 50) | ((obs >= 0.1) & (obs < 35)))
    ] = 1  # correct negative
    cont[(fcst == 0) | (obs == 0)] = np.nan  # no rain case
    return cont


def calculate_cont_extreme(fcst, obs):
    cont = np.zeros_like(obs)
    cont[(fcst >= 50) & (obs >= 50)] = 4  # hit
    cont[(fcst >= 50) & ((obs >= 0.1) & (obs < 50))] = 3  # false alarm
    cont[((fcst >= 0.1) & (fcst < 50)) & (obs >= 50)] = 2  # miss
    cont[
        ((fcst >= 0.1) & (fcst < 50)) & ((obs >= 0.1) & (obs < 50))
    ] = 1  # correct negative
    cont[(fcst == 0) | (obs == 0)] = np.nan  # no rain case
    return cont


def cont_table(cont):
    hit = (cont == 4).sum()
    f_alarm = (cont == 3).sum()
    miss = (cont == 2).sum()
    c_neg = (cont == 1).sum()

    fcst_yes = hit + f_alarm
    fcst_no = miss + c_neg
    obs_yes = hit + miss
    obs_no = f_alarm + c_neg
    totalobs = obs_yes + obs_no
    totalfcst = fcst_yes + fcst_no

    # Forecast metrics
    pod = (hit / (hit + miss)) * 100
    far = (f_alarm / (hit + f_alarm)) * 100
    sr = (hit / (hit + f_alarm)) * 100

    # Format to whole number
    pod = f"{pod:0.2f} %"
    far = f"{far:0.2f} %"
    sr = f"{sr:0.2f} %"

    # Prepare contingency table
    data = [
        [int(f"{hit}"), int(f"{f_alarm}"), int(f"{fcst_yes}")],
        [int(f"{miss}"), int(f"{c_neg}"), int(f"{fcst_no}")],
        [int(f"{obs_yes}"), int(f"{obs_no}"), int(f"{totalobs}")],
    ]

    return (pod, far, sr, data)
