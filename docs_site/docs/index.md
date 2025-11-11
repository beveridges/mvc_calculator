<h2 id="welcome-to-mvc-calculator">Welcome to MVC Calculator</h2>
<p>MVC Calculator follows <span class="citation"
data-cites="Konrad05">(Konrad, 2005)</span>.</p>
<p>MVC Calculator calculates the Maximum Voluntary Contraction (MVC)
based on the signal-processing guidelines in <span class="citation"
data-cites="Konrad05">(Konrad, 2005)</span>. The MVC Calculator provides
a visual workflow for burst identification, noise reduction, and
normalization.</p>
<h2 id="why-dont-we-just-use-a-script-for-this-calculation">Why don’t we
just use a script for this calculation?</h2>
<p>sEMG can be noisy. Depending on the testing protocol and recording
success, this noise can make its way into the measurement process. By
allowing the user to define the MVC bursts manually, MVC Calculator
provides a <strong>visual</strong> method of reducing noise. It also
provides a method for saving, loading, and modifying MVC datasets.</p>
<p>The system is written to follow the <em>“best of 3”</em> procedure
described in <span class="citation" data-cites="Konrad05">(Konrad,
2005)</span>.</p>
<h2 id="quick-start">Quick start</h2>
<p>The input files for MVC Calculator are <code>.mat</code> files
created by Qualisys. The system uses this data structure to extract data
from all sensors.</p>
<p>!!! note “Remember” Noraxon / Qualisys records all sensors by
default.<br />
It is the user’s responsibility to identify which sensors are relevant
for the MVC computation.</p>
<p>!!! tip “Configuration” To change the <strong>‘best of x’</strong>
rule (number of trials used), edit the variable <code>BEST_OF</code> in
<code>./config/defaults.py</code>.</p>
<hr />
<h2 id="measurement-protocol-suggestions">Measurement protocol
suggestions</h2>
<p>The system is written to follow the <em>‘best of 3’</em> procedure in
(Konrad, 2005).</p>
<hr />
<div id="refs" class="## Referencescsl-bib-body hanging-indent"
data-entry-spacing="0" data-line-spacing="2" role="list">
<div id="ref-Konrad05" class="csl-entry" role="listitem">
Konrad, P. (2005). The abc of emg. <em>A Practical Introduction to
Kinesiological Electromyography</em>, <em>1</em>.
</div>
</div>
