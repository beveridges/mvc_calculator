# Welcome to MVC Calculator

![Build](https://img.shields.io/badge/build-alpha--25.11--01-blueviolet?style=flat-square)
![Version](https://img.shields.io/badge/version-25.11--alpha.01.66-orange?style=flat-square)

## What is mvc_calculator ?

MVC Calculator provides a **visual workflow** for burst identification. 


## Why do we need manual MVC detection?
...because things go wromg during recording sessions. sEMG can be noisy. Depending on the testing protocol and recording success, noise often contaminates the measurement process.  
By allowing the user to manually define MVC bursts, the Calculator provides a **visual and reliable** way to reduce noise before analysis.

The system is written to follow the *“best of 3”* procedure described in (Konrad, 2005).

---

## Features

- Import `.mat` files recorded by Qualisys or Noraxon systems  
- Detect and visualize MVC bursts interactively  
- Export processed data to CSV, JSON, or OpenSim-compatible formats  
- Adjustable burst thresholds and auto-normalization  
- Built-in logging and data management features  

---



---

## Quick Start

1. Open **MVC Calculator** and load your `.mat` file from the recording system.  
2. Use the **Energy Detection** tool to locate candidate MVC bursts.  
3. Fine-tune burst regions using the graphical selector.  
4. Press **Save Results** to store computed MVC metrics.  

!!! tip
    You can change the “best of X” rule in the configuration file:  
    `./config/defaults.py` → variable `BEST_OF`.

!!! note
    Noraxon / Qualisys record all sensors by default.  
    It’s the user’s responsibility to identify which sensors are relevant for MVC computation.

---

## Measurement Protocol Suggestions

- Perform three maximum-effort trials for each muscle group.  
- Allow sufficient rest (≥ 30 seconds) between trials.  
- Ensure consistent electrode placement across sessions.  
- Use the same sampling frequency for all measurements.

---

## References

Konrad, P. (2005). *The ABC of EMG: A Practical Introduction to Kinesiological Electromyography.* Noraxon Inc.
