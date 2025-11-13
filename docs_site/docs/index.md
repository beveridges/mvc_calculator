# Welcome to MVC Calculator

![Build](https://img.shields.io/badge/build-alpha--25.11--01-blueviolet?style=flat-square)
![Version](https://img.shields.io/badge/version-25.11--alpha.01.70-orange?style=flat-square)

## What is MVC Calculator?

MVC Calculator provides a **visual** method of idenitfying bursts in
sEMG signals.

## Why do we need manually identify MVC bursts?

You would think that a process like burst identification could be
pefromed very easily automagically. However, during the first drum study
we ended up with files that had more than 3 bursts (due to miscounting
or false starts), multiple files for the same participant, and other
assorted problems. By allowing the user to manually define MVC bursts,
the MVC Calculator provides a method that is **reliable, repeatable, and
valid**. For all intents and purposes using MVC Calculator is
one-and-done process. MATLAB .mat files go in, and an XML file with the
MVC values go out. This will probably be the case 90% of the time. The
other 10% can be a pain. MVC Calculator makes dealing with the 10% WAY
easier.

Let’s dive into a Quick Start. The Quick Start has the following
assumptions:

- We are following the *“best of 3”* procedure (Konrad, 2005).
- The sEMG sampling frequency is 1500Hz.

------------------------------------------------------------------------

## Features

- Import `.mat` files recorded by Qualisys or Noraxon systems  
- Detect and visualize MVC bursts interactively  
- Export processed data to CSV, JSON, or OpenSim-compatible formats  
- Adjustable burst thresholds and auto-normalization  
- Built-in logging and data management features

------------------------------------------------------------------------

------------------------------------------------------------------------

## Quick Start

Four (or six, depending on the sensor configuration) , .mat files are
loaded into the software

1.  Open **MVC Calculator** and load your `.mat` file from the recording
    system.  
2.  Use the **Energy Detection** tool to locate candidate MVC bursts.  
3.  Fine-tune burst regions using the graphical selector.  
4.  Press **Save Results** to store computed MVC metrics.

!!! tip You can change the “best of X” rule in the configuration file:  
`./config/defaults.py` → variable `BEST_OF`.

!!! note Noraxon / Qualisys record all sensors by default.  
It’s the user’s responsibility to identify which sensors are relevant
for MVC computation.

------------------------------------------------------------------------

## Measurement Protocol Suggestions

- Perform three maximum-effort trials for each muscle group.  
- Allow sufficient rest (≥ 30 seconds) between trials.  
- Ensure consistent electrode placement across sessions.  
- Use the same sampling frequency for all measurements.

------------------------------------------------------------------------

## References

Konrad, P. (2005). *The ABC of EMG: A Practical Introduction to
Kinesiological Electromyography.* Noraxon Inc.
