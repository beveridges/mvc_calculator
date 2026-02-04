# Welcome to MVC Calculator

![Build](https://img.shields.io/badge/build-26.01--alpha.01-blueviolet?style=flat-square)
![Version](https://img.shields.io/badge/version-26.01--alpha.01.02-orange?style=flat-square)

## What is MVC Calculator?

MVC Calculator is software that provides a **visual** method of
idenitfying bursts in sEMG signals.

## Why do we need to manually identify MVC bursts?

You would think that a process like burst identification could be
pefromed automatically. However, during the first drum study we ended up
with files that were so irregular, they couldn’t be processed
automatically. Examples of such irregularities include files with more
bursts than required (due to false starts or miscounting), multiple
files for the same participant, and noise. By allowing the user to
manually define MVC bursts, the MVC Calculator provides a method that is
**reliable, repeatable, and valid**.

!!! summary
    For all intents and purposes using MVC Calculator is one-and-done process. MATLAB .mat files go in, and an XML file with the MVC values comes out. This will probably be the case 90% of the time. The other 10% can be a pain. MVC Calculator makes dealing with this 10% much more painless.

## How MVC calculator fits into the workflow.




## Installation

There are currently two builds for Windows and one for Linux. These can
be found at <https://downloads.moviolabs.com/MVC_Calculator/releases/>.

The Windows portable version doesn’t require installtion, but can be
slower on startup. The installable version (.msi) is faster because it
does most of the time consuming heavy lifting only once during
installation.

!!! note
    During the alpha phase of development MVC Calculator will run
    with a temporary terminal in the background. This is designed as a
    troubleshooting tool and should mimic what is shown in the [console](#console).
    of MVC Calculator.

------------------------------------------------------------------------

## Features

- MATLAB<sup>&#174;</sup> `.mat` file importer  
- Detect and visualize MVC bursts interactively  
- Export processed MVC results data to XML  
- Import XML
- Adjustable burst thresholds detection function  
- Built-in logging and data management

------------------------------------------------------------------------
# Overview of the MVC Calculation and implementation 

The following asteps outline the entire process on implemeneting MVC single normalisation

------------------------------------------------------------------------

## Quick Start

Four (or six, depending on the sensor configuration) , .mat files are
loaded into the software

1.  Open **MVC Calculator** and load your `.mat` file from the recording
    system recorded by QualisysAB<sup>&#174;</sup> or Noraxon<sup>&#174;</sup> systems.  
2.  Use the **Energy Detection** tool to locate candidate MVC bursts.  
3.  Fine-tune burst regions using the graphical selector.  
4.  Press **Save Results** to store computed MVC metrics.

!!! measurementprotocol "Measurement Protocol"
    By default, MVC Calculator assumes two things:

    1. We are following the *“best of 3”* procedure (Konrad, 2005).
    2. The sEMG sampling frequency is 1500Hz.

    These settings can be modified by [changing the defaults](#changing-the-defaults)


------------------------------------------------------------------------

## Measurement Protocol Suggestions

- Perform three maximum-effort trials for each muscle group.  
- Allow sufficient rest (≥ 30 seconds) between trials.  
- Ensure consistent electrode placement across sessions.  
- Use the same sampling frequency for all measurements.

------------------------------------------------------------------------

<a id="console"></a>

## The Interface

The interface for MVC Calculator is very simple. It comprises:

1. Menu bar
2. Plotting area
3. Console
4. Main UI controls

<figure class="screenshot">
  <img
    src="../img/screenshots/full_ui.png"
    data-full="../img/screenshots/full_ui.png"
    width="700"
    alt="MVC Calculator UI"
    class="lightbox-trigger"
  />
  <figcaption aria-hidden="true">MVC Calculator UI</figcaption>
</figure>




## Quick Start 

What follows are thea series of videos demonstrating the primary functions of MVC Calculator


### Scenario 1:  Performing the MVC Calculation
Making an MVC Calculation is very straight forward, it involves:

1.  Importing MATLAB<sup>&#174;</sup> files
2.  Selecting bursts in the sEMG signal
3.  Performing the calculation
4.  Exportiong the saved data



The following video will demonstrate this process.

<figure class="screenshot">
  <img
    src="../img/screenshots/video_placeholder.png"
    data-full="../img/screenshots/video_placeholder.png"
    width="700"
    alt="Video Placeholder"
    class="lightbox-trigger"
  />
  <figcaption aria-hidden="true">MVC Calculator – Video Walkthrough (coming soon)</figcaption>
</figure>

### Scenario 2:  Performing a batch MVC Calculation
The majority of the time you will be processing multiple files (In our case four or six sensors).  The following video demonstrates this process.  The selection of single sEMG bursts is exactly the same as above except there are multiple tabs so multiple selections shoudl be made.  Note that the tabs that have not had an active selection will show a red dot when the batchg MVV calculation 

<figure class="screenshot">
  <img
    src="../img/screenshots/video_placeholder.png"
    data-full="../img/screenshots/video_placeholder.png"
    width="700"
    alt="Video Placeholder"
    class="lightbox-trigger"
  />
  <figcaption aria-hidden="true">MVC Calculator – Video Walkthrough (coming soon)</figcaption>
</figure>

### Scenario 3: Importing an XML file
XML is the format the system uses to save MVC calculations
<figure class="screenshot">
  <img
    src="../img/screenshots/video_placeholder.png"
    data-full="../img/screenshots/video_placeholder.png"
    width="700"
    alt="Video Placeholder"
    class="lightbox-trigger"
  />
  <figcaption aria-hidden="true">MVC Calculator – Video Walkthrough (coming soon)</figcaption>
</figure>



## Changing the Defaults

You can change the defaults mentioned above by modifying the relative
path `./config/defaults.py`. Just open the file in any text editor and
modify the two numbers corresponding to `BEST_OF` and
`DEFAULT_SEMG_FREQUENCY`.

!!! tip
    You can change the “best of X” rule in the configuration file:
    `./config/defaults.py` → variable `BEST_OF`.

!!! note
    Noraxon<sup>&#174;</sup> / QualisysAB<sup>&#174;</sup> record all sensors by default.
    It’s the user’s responsibility to identify which sensors are relevant
    for MVC computation.

## References

Konrad, P. (2005). *The ABC of EMG: A Practical Introduction to
Kinesiological Electromyography.* Noraxon<sup>&#174;</sup> Inc.
