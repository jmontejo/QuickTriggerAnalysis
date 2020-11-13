#!/usr/bin/env python
import os
import sys
from math import pi,sqrt,cos
from ctypes import *
import array
import struct 
import ROOT
import argparse

def ntupName( stri ) :
        strtopo = stri.replace("-","_")
        strtopo = strtopo.replace("[","_")
        strtopo = strtopo.replace("]","_")
        return strtopo

parser = argparse.ArgumentParser(description='skim (D)AODs!')

parser.add_argument('--l1rois', dest='save_l1rois', action='store_true',
                    default=False, help='store all L1 RoIs in the output')

parser.add_argument('--isData', dest='isData', action='store',
                    default=None, help='are you running on data or MC?')
                    
parser.add_argument('--inputFiles', dest='inputFiles', action='store',
                    default='', help='comma-separated list of input files (or a single file)')

args = parser.parse_args()
inputFiles = args.inputFiles
save_l1rois = args.save_l1rois
isData = args.isData

ROOT.gROOT.Macro( '$ROOTCOREDIR/scripts/load_packages.C' )

# Initialize the xAOD infrastructure: 
if(not ROOT.xAOD.Init().isSuccess()): print "Failed xAOD.Init()"

inputFiles = inputFiles.split(',')
print "inputFiles = ", inputFiles
fileName=inputFiles[0]
if len(fileName) == 0 :
    print "Please provide input"
    exit()


######### Read input tree

treeName = "CollectionTree" # default when making transient tree anyway

ch = ROOT.TChain(treeName)
for infile in inputFiles :
    ch.Add(infile)
    print infile

t = ROOT.xAOD.MakeTransientTree( ch )

######### Initialize TrigDecision
ROOT.gROOT.ProcessLine("#include \"TrigConfxAOD/xAODConfigTool.h\"")
ROOT.gROOT.ProcessLine("#include \"TrigDecisionTool/TrigDecisionTool.h\"")
ROOT.gROOT.ProcessLine("#include \"TrigConfInterfaces/ITrigConfigTool.h\"")
ROOT.gROOT.ProcessLine("#include \"AsgTools/AnaToolHandle.h\"")

ROOT.gROOT.ProcessLine(
   "asg::AnaToolHandle<TrigConf::ITrigConfigTool> configTool(\"TrigConf::xAODConfigTool\", nullptr);\
    asg::AnaToolHandle<Trig::TrigDecisionTool> trigDecTool(\"Trig::TrigDecisionTool\", nullptr);\
    ASG_MAKE_ANA_TOOL (configTool, TrigConf::xAODConfigTool).ignore();\
    configTool.initialize().ignore();\
    ASG_MAKE_ANA_TOOL (trigDecTool, Trig::TrigDecisionTool).ignore();\
    trigDecTool.setProperty(\"ConfigTool\",configTool).ignore();\
    trigDecTool.setProperty(\"TrigDecisionKey\",\"xTrigDecision\").ignore();\
    trigDecTool.initialize().ignore();")

ROOT.gROOT.ProcessLine("#include \"MuonAnalysisInterfaces/IMuonSelectionTool.h\"")
muonSelection = ROOT.CP.MuonSelectionTool("MuonSelection") 
muonSelection.setProperty("double")( "MaxEta", 2.7 )
muonSelection.setProperty("int")( "MuQuality", 	ROOT.xAOD.Muon.Quality.Medium)
if muonSelection.initialize().isSuccess():
  print ("Muon selection successfully initialized")


######## get list of all triggers ##########
t.GetEntry(0)
trigList = []
L1items = ROOT.trigDecTool.getChainGroup("L1_.*").getListOfTriggers()
for itrig in xrange(len(L1items)) :
    trig = L1items[itrig]
    #customize the list of L1 triggers you want saved to your ntuple here
    #this will save only L1 Muon decisions
    if "EMPTY" in trig  or "UNPAIRED" in trig: continue
    if "MU" not in trig: continue
    trigList.append(trig)

HLTitems = ROOT.trigDecTool.getChainGroup("HLT_.*").getListOfTriggers()
for itrig in xrange(len(HLTitems)) :
    trig = HLTitems[itrig]
    if trig in trigList : continue
    #customize the HLT decisions you want saved to your ntuple here
    if "EMPTY" in trig : continue
    if "UNPAIRED" in trig : continue
    if "perf" in trig : continue
    if "split" in trig : continue
    if "boff" in trig : continue
    if "tau" in trig : continue
    if "BTAG" in trig : continue
    if "j15" in trig : continue
    if "j20" in trig : continue
    if "j30" in trig : continue
    if "j40" in trig : continue
    if "ivar" in trig : continue
    if "_lh" in trig : continue
    if "muvtx" in trig : continue
    if "iloose" in trig : continue
    if "mucombTag" in trig : continue
    if "cosmic" in trig : continue
    if "noComb" in trig : continue
    if "calib" in trig : continue
    #save the decisions of all HLT muon chains that aren't selected by the above identifiers
    if "mu" in trig or "nomucomb" in trig :   
        trigList.append(trig)
        continue

# You can also append specific triggers here, or only do this method if you know a priori
# exactly the decisions you want saved
trigList.append(
'HLT_e5_lhtight_nod0_e4_etcut'
)

counters = {}
for trig in trigList :
    counters[trig] = 0

passTrig = {}

fOut = ROOT.TFile("tmpTrig.root","RECREATE")
tOut = ROOT.TTree("trig","trig")

passTrig = {}
for trig in trigList :
    passTrig[trig] = array.array("i",(0 for i in range(0,1)))
    tOut.Branch(ntupName(str(trig)), passTrig[trig],ntupName(str(trig))+"/I")

eventNumber = array.array("l",(0 for i in range(0,1)))
tOut.Branch("eventNumber", eventNumber,"eventNumber/L")
eventWeight = array.array("f",(0 for i in range(0,1)))
if not isData: tOut.Branch("eventWeight", eventWeight,"eventWeight/F")
avgmu = array.array("f",(0 for i in range(0,1)))
tOut.Branch("averageMu", avgmu,"avgmu/F")


reference_trig_name = 'L1_MU20'
reference_trig =  array.array("i",(0 for i in range(0,1)))
if isData: tOut.Branch('reference_trig_'+reference_trig_name, reference_trig,'reference_trig_'+reference_trig_name+'/I')

offline_selection = array.array("i",(0 for i in range(0,1)))
tOut.Branch('pass_offline_selection', offline_selection,'pass_offline_selection/I')

l1muons = ROOT.vector('TLorentzVector')(10)
l1muonsn= array.array("i",(0 for i in range(0,1)))
if save_l1rois :
    tOut.Branch('l1muons_n',  l1muonsn, "l1muons_n/I"  )
    tOut.Branch('l1muons',  l1muons  )
    
l1ems = ROOT.vector('TLorentzVector')(10)
l1emsn= array.array("i",(0 for i in range(0,1)))
l1em_max_threshold = ROOT.vector('float')(10)
l1em_max_iso = ROOT.vector('int')(10)
if save_l1rois:
    tOut.Branch('l1ems_n',  l1emsn, "l1ems_n/I"  )
    tOut.Branch('l1ems',  l1ems  )
    tOut.Branch('l1ems_max_th',  l1em_max_threshold  )
    tOut.Branch('l1ems_max_iso',  l1em_max_iso  )
    
l1taus = ROOT.vector('TLorentzVector')(10)
l1tausn= array.array("i",(0 for i in range(0,1)))
l1tau_max_threshold = ROOT.vector('float')(10)
l1tau_max_iso = ROOT.vector('int')(10)
if save_l1rois:
    tOut.Branch('l1taus_n',  l1tausn, "l1taus_n/I"  )
    tOut.Branch('l1taus',  l1taus  )
    tOut.Branch('l1taus_max_th',  l1tau_max_threshold  )
    tOut.Branch('l1taus_max_iso',  l1tau_max_iso  )   

recomuons = ROOT.vector('TLorentzVector')(10)
tOut.Branch('recomuons',  recomuons  )

dimuon_mass = array.array('f',(0 for i in range(0,1)))
tOut.Branch('dimuon_mass',dimuon_mass,'dimuon_mass/F')

hltmuons = ROOT.vector('TLorentzVector')(10)
tOut.Branch('hltmuons',  hltmuons  )

################################################################

print( "Number of input events: %s" % t.GetEntries() )
for entry in xrange( t.GetEntries() ):
    if entry % 1000 == 0:
        print( "On event number: %s" % entry )
    t.GetEntry( entry )
    
    #first, get info for our reference trigger. Need to keep these events to calculate rates (data only!)
    reference_trig = 0
    if isData and ROOT.trigDecTool.isPassed(reference_trig_name): reference_trig = 1
    
    # Make our basic offline selection. in our dummy analysis, this is two 8 GeV medium
    # combined muons with 10 < m(mumu) < 75 GeV
    pts = []
    recomuons.clear()
    if hasattr(ch, "Muons") :
        for imu in xrange(len(t.Muons)) :
            mu = t.Muons[imu]
            
            if mu.pt() < 8. : continue
            if not mu.muonType() == ROOT.xAOD.Muon.Combined : continue

            # don't pass in mu because this function needs a pointer
            if not muonSelection.accept(t.Muons.at(imu)):
                continue

            reco = ROOT.TLorentzVector()
            reco.SetPtEtaPhiM( mu.pt(), mu.eta(), mu.phi(), 105.65)

            pts.append(reco)

        pts.sort( key=lambda x: x.Pt(), reverse=True)
        for x in pts :
            recomuons.push_back(x)
        
    offline_selection = 0    
    dimuon_mass = -1
    if len(recomuons) >= 2:
        dimuon_mass = (recomuons[0] + recomuons[1]).M() 
        offline_selection = int(dimuon_mass > 10000. and dimuon_mass < 75000.)
    
    keep_event = False
    if offline_selection:
        keep_event = True
    if reference_trig and isData:
        keep_event = True
    
	#only carry on if the event is useful!
    if not keep_event:
        continue

    eventNumber[0] = t.EventInfo.eventNumber()
    if not isData: eventWeight[0] = t.EventInfo.mcEventWeight()
    avgmu[0] = t.EventInfo.averageInteractionsPerCrossing()
    
    for trig in trigList :
        passTrig[trig][0] = 0
        if  ROOT.trigDecTool.isPassed( trig ) : passTrig[trig][0] = 1

    l1muons.clear()
    full_l1mus = []
    for imu in xrange(len(t.LVL1MuonRoIs)) :
        mu = t.LVL1MuonRoIs[imu]
        l1 = ROOT.TLorentzVector()
        l1.SetPtEtaPhiM( mu.thrValue(), mu.eta(), mu.phi(), 105.65) 
        full_l1mus.append([l1])

    full_l1mus.sort( key=lambda x: x[0].Pt(), reverse=True)
    for x in full_l1mus :
        l1muons.push_back(x[0])

    l1muonsn[0] = len(l1muons)


    l1ems.clear()
    l1em_max_iso.clear()
    l1em_max_threshold.clear()
    
    l1taus.clear()
    l1tau_max_iso.clear()
    l1tau_max_threshold.clear()
    
    full_l1ems = []
    full_l1taus = []
    for imu in xrange(len(t.LVL1EmTauRoIs)) :
        mu = t.LVL1EmTauRoIs[imu]
        if mu.roiType() == ROOT.xAOD.EmTauRoI_v2.EMRoIWord : 
            l1 = ROOT.TLorentzVector()
            l1.SetPtEtaPhiM( mu.eT(), mu.eta(), mu.phi(), .051)
            
            #if you wanted to play around with some of the L1 isolation variables:
            #but keep in mind these all change for run 3!
            
            #l1emroiWord= mu.roiWord()
            #l1emetScale = mu.etScale()  
            #l1emIsol = mu.isol()
            #l1emcore    = mu.core()    
            #l1em_emClus  = mu.emClus()  
            #l1em_tauClus = mu.tauClus() 
            #l1em_emIsol  = mu.emIsol()  
            #l1em_hadIsol = mu.hadIsol() 
            #l1em_hadCore = mu.hadCore() 
            
            l1em_thrValues = mu.thrValues()
            l1em_thrNames = mu.thrNames()
            isV = False; isVH = False; isVHI = False; isVHIM = False;
            max_th = 0; max_x = 0
            for tv,tm in zip(l1em_thrValues, l1em_thrNames):
                if "VHIM" in tm: isVHIM = True
                if "VHI" in tm: isVHI = True
                if "VH" in tm: isVH = True
                if "V" in tm: isV = True
                if tv > max_th: max_th = tv
            if isVHIM: max_x = 4
            elif isVHI: max_x = 3
            elif isVH: max_x = 2
            elif isV: max_x = 1
            else: max_x = 0
            full_l1ems.append([l1,max_th,max_x])
            
        elif mu.roiType() == ROOT.xAOD.EmTauRoI_v2.TauRoIWord : 
            l1 = ROOT.TLorentzVector()
            l1.SetPtEtaPhiM( mu.eT(), mu.eta(), mu.phi(), 1.777)
            l1tau_thrValues = mu.thrValues()
            l1tau_thrNames = mu.thrNames()
            isIL = False; isIM = False
            max_th = 0; max_x = 0
            for tv,tm in zip(l1tau_thrValues, l1tau_thrNames):
                if "IM" in tm: isIM = True
                if "IL" in tm: isIL = True
                if tv > max_th: max_th = tv
            
            if isIM: max_x = 2
            elif isIL: max_x = 1
            else: max_x = 0
            full_l1taus.append([l1,max_th,max_x])
            
    full_l1ems.sort( key=lambda x: x[0].Pt(), reverse=True)
    for x in full_l1ems :
        l1ems.push_back(x[0])
        l1em_max_threshold.push_back(x[1])
        l1em_max_iso.push_back(x[2])
    l1emsn[0] = len(l1ems)

    full_l1taus.sort( key=lambda x: x[0].Pt(), reverse=True)
    for x in full_l1taus :
        l1taus.push_back(x[0])
        l1tau_max_threshold.push_back(x[1])
        l1tau_max_iso.push_back(x[2])
    l1tausn[0] = len(l1taus)

    
    # get the HLT muon container and remove any overlapping muons
    if hasattr(ch, "HLT_xAOD__MuonContainer_MuonEFInfo") :
        for imu in xrange(len(ch.HLT_xAOD__MuonContainer_MuonEFInfo)):
            mu = ch.HLT_xAOD__MuonContainer_MuonEFInfo[imu]

            duplicate = False
            for jmu in xrange(len(pts)) :
                tmu = pts[jmu]
                #remove overlaps
                if mu.p4().DeltaR( tmu ) < 0.005:
                    duplicate =  True
                    break
            if not duplicate :
                mupt = mu.pt()
                hlt = ROOT.TLorentzVector()
                hlt.SetPtEtaPhiM( mupt, mu.eta(), mu.phi(), 105.65)
                pts.append(hlt)
    #print pts
    pts.sort( key=lambda x: x.Pt(), reverse=True)
    hltmuons.clear()
    for x in pts :
        hltmuons.push_back(x)

    
    tOut.Fill()

    
print "Write out trig ntuple ", fOut.GetName() , " with ", tOut.GetEntries(), " events"
fOut.Write()
fOut.Close()

ROOT.xAOD.ClearTransientTrees()

exit(0)
