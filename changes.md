makeWorkspace/convert.py:
  - I cannot remember why I did this change:
  ```
  103c103
  <             if (not ("wjet" in x.model)) and (not ("ewk" in x.model)):
  ---
  >             if not ("wjet" in x.model):
  ```

makeWorkspace/make_ws.py:
   -  `key_valid = lambda x: (tag in x) and (not "jesTotal" in x)  # , keynames`, syntax difference from `python2`?
     `filter(key_valid, keynames)` is called later anyway
   - Not attempting to get signal theory variations for vbf (not present for `makeWorkspace/sys/signal_theory_unc.root`)
      - Applied in `Z_contraints_qcd_withphoton.py`
   - Not attempting to get photon id variations for vbf (not present for `makeWorkspace/sys/photon_id_unc.root`)
   - Not attempting to get mistag variations for vbf (not present for `makeWorkspace/sys/mistag_sf_variations.root`)

vbf/templates/vbf_template_debug.txt:
   - copied from vbf_template_pretty_withphotons.txt
   - removed 1 process: qcd
   - qcd removed from signal region, single muon, single electron
      - removed shape uncertainties for that process
   - different number of bins

makeWorkspace/counting_experiment.py: 
   - putting high limit on nuisance for model_mu_cat_vbf_2017_... 
      (instead of letting it vary up to "infinity", handled differently in older combine version)

General changes:
   - Only running with "2018" configuration (using 2018 systematics templates):
      - Not running on 2017 or the combined 2017+2018
      - not running configuration for IC
      - not running the "nophoton" configuration
      - process_vbf.sh vbf/scripts/diagnostic.sh vbf/scripts/impacts.sh vbf/scripts/limits.sh vbf/scripts/make_cards.sh
   - Syntax changes from python2
      - plotter/plot_datavalidation.py, plotter/plot_PreFitPostFit.py
   - Plotting tweaks
      - lumi, CoM, ...
      - plotter/plot_diffnuis.py plotter/plot_ratio.py vbf/scripts/make_plots.py

vbf/scripts/diagnostic.sh:
   - removed mask on SR (we are using pseudo-data in SR)
   - plotting all nuisances (even the ones which are unchanged w.r.t. pre-fit values.)

vbf/scripts/impacts.sh:
   - changed some options (mirroring impacts_condor script)
   - using asimov toys

vbf/scripts/limits.sh:
   - not running the "nophoton" configuration
   - saving toys

vbf/scripts/make_cards.sh
   - changed template to use