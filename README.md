 # Power Monitor (for Raspberry Pi)

This project will allow you to monitor your power situation in real time, including accurate consumption, generation, and net-production. The data are stored to a database and displayed in a Grafana dashboard for monitoring and reporting purposes.

This project is derived from and inspired by the resources located at https://learn.openenergymonitor.org and https://github.com/David00/rpi-power-monitor. 

---

## How do I install?

> The instructions below are just a quick start. For the full documentation, please see https://david00.github.io/rpi-power-monitor for the original documentation. Please note that this project is still a work in progress.

There are two ways to install.

### Clone the repository

```bash
git clone https://github.com/M4271/rpi-power-monitor rpi_power_monitor
```

Then, to run, for example:

```bash
cd rpi_power_monitor

python3 -m pip install .
python3 power_monitor.py terminal
```

### Install python package

```bash

python3 -m pip install git+https://github.com/M4271/rpi-power-monitor.git
```

---

## What does it do?

This code supports monitoring a Carlo Gavazzi EM112 utility meter. The individual readings are then used in calculations to provide real data on consumption and generation, including the following key metrics:

* Total home consumption
* Total solar PV generation
* Net home consumption
* Net home generation
* Total current, voltage, power, and power factor values
* Individual current transformer readings
* Harmonics inspection through a built in snapshot/plotting mechanism.

The code takes one sample per second. Each sample consists out of the real power, the current, the voltage and the power factor. The code can be extended to read additional values such as reactive, capacitive, and resisitve loads.

---

