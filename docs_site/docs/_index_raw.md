# Welcome to MVC Calculator

<div class="badge-row">
  <img src="https://img.shields.io/badge/build-alpha--25.11--01-blueviolet?style=flat-square" alt="Build badge">
  <img src="https://img.shields.io/badge/version-25.11--alpha.01.61-orange?style=flat-square" alt="Version badge">
</div>

<p class="intro-spacing"></p>

MVC Calculator follows (Konrad, 2005).


MVC Calculator calculates the Maximum Voluntary Contraction (MVC) based on the signal-processing guidelines in [@Konrad05].  The MVC Calculator provides a visual workflow for burst identification, noise reduction, and normalization.

## Why don't we just use a script for this calculation?

sEMG can be noisy.  Depending on the testing protocol and recording success,
this noise can make its way into the measurement process.  By allowing the user
to define the MVC bursts manually, MVC Calculator provides a **visual**
method of reducing noise.  It also provides a method for saving, loading,
and modifying MVC datasets.

The system is written to follow the *“best of 3”* procedure described in
[@Konrad05].

## Quick start

The input files for MVC Calculator are `.mat` files created by Qualisys.
The system uses this data structure to extract data from all sensors.

!!! note "Remember"
    Noraxon / Qualisys records all sensors by default.  
    It is the user’s responsibility to identify which sensors are relevant
    for the MVC computation.

!!! tip "Configuration"
    To change the **‘best of x’** rule (number of trials used),
    edit the variable `BEST_OF` in `./config/defaults.py`.

---

## Measurement protocol suggestions

The system is written to follow the *‘best of 3’* procedure in (Konrad, 2005).

---



