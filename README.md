# QuickTriggerAnalysis

Scripts to make ntuples for quick trigger studies

There are two files: one for release 21 and one for release 22 (master).

The selection and trigger lists saved by these scripts are only toy exampes - you should tailor the selection for your own purposes.

To run locally, first setup AnalysisBase (in the release corresponding to your AODs). If your code gets errors about `RootCore/Packages.h`, after setting up the release, run this:

```
export ROOT_INCLUDE_PATH=$ROOT_INCLUDE_PATH:$ROOTCOREBIN/RootCore/include/
```

which adds the problematic file to the include path.

Then, you can simply execute the file locally. For example:
```
./skimTrig_r21.py --inputFiles /eos/atlas/atlasdatadisk/rucio/data18_13TeV/68/68/AOD.19448522._000080.pool.root.1 --isData True --l1rois
```

aside: the input file listed above is an AOD from the latest 21.3 enhanced bias processing. These are alwyas stored on CERN-PROD_DATADISK so are available locally on lxplus/testbed. To access the file paths, you can run:

```
rucio list-file-replicas data18_13TeV.00360026.physics_EnhancedBias.merge.AOD.r11637_r11638_p3989_tid19448522_00 --rse CERN-PROD_DATADISK
```

There are three command-line options, you can use `./skim_r12.py --help` to see how they work:
```
--inputFiles : a comma-separated list of files you want to run on (a single file is ok too!)
--isData : set this to True or False depending on whether you're running on data or MC
--l1rois : if you include this flag, L1 RoIs will be saved to your output ntuple (muon, egamma, and tau).
```

To run on the grid, you can use the following command (after running `lsetup panda` and `voms-proxy-init -voms atlas`, and changing the outDS to someting with your username):

```
prun --useAthenaPackages --exec "python skimTrig_r21.py  --inputFiles %IN --isData True --l1rois | tee log.txt" \
     --inDS data18_13TeV.00360026.physics_EnhancedBias.merge.AOD.r11637_r11638_p3989_tid19448522_00   \
     --outDS user.hrussell.testEB_360026.r11637_v01  \
     --outputs tmpTrig.root --excludeFile=\*.o,\*.so,\*.a   --mergeOutput   
```

Note that if you change the name of the output file `tmpTrig.root` in the script: `fOut = ROOT.TFile("tmpTrig.root","RECREATE")`, you also need to change the name of the file in outputs (likely some regex also works, but I have not tried).
