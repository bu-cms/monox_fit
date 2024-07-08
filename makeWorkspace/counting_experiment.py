import ROOT as r
import sys
import array
import re
from HiggsAnalysis.CombinedLimit.ModelTools import *

MAXBINS = 100

def naming_convention(id, catid, convention="BU"):
    if convention == "BU":
        return "model_mu_cat_%s_bin_%d" % (catid, id)
    elif convention == "IC":
        m = re.match(".*(201\d).*", catid)
        if not m or len(m.groups()) > 1:
            raise RuntimeError("Cannot derive year from category ID: " + catid)
        year = m.groups()[0]
        return "MTR_%s_QCDZ_SR_bin%d" % (year, id+1)
    else:
        raise RuntimeError("Unknown naming convention: " + convention)


def getNormalizedHist(hist):
    thret = hist.Clone()
    nb = hist.GetNbinsX()
    for b in range(1, nb+1):
        sfactor = 1./hist.GetBinWidth(b)
        thret.SetBinContent(b, hist.GetBinContent(b)*sfactor)
        thret.SetBinError(b, hist.GetBinError(b)*sfactor)
        # thret.GetYaxis().SetTitle("Events")
        thret.GetYaxis().SetTitle("Events/GeV")
    return thret

class Bin:
    def __init__(self, category, catid, chid, id, var, datasetname, wspace, wspace_out, xmin, xmax, convention):
        self.category = category
        self.chid = chid  # This is the thing that links two bins from different controls togeher
        self.id = id
        self.catid = catid
        #self.type_id   = 10*MAXBINS*catid+MAXBINS*chid+id

        self.convention = convention

        if self.convention == "BU":
            self.binid = "cat_%s_ch_%s_bin_%d" % (catid, chid, id)
        elif self.convention == "IC":
            self.binid = "cat_%s_ch_%s_bin%d" % (catid, chid, id+1)

        self.wspace_out = wspace_out
        self.wspace_out._safe_import = SafeWorkspaceImporter(self.wspace_out)

        self.set_wspace(wspace)

        self.var = self.wspace_out.var(var.GetName())
        #self.dataset   = self.wspace.data(datasetname)

        self.rngename = "rnge_%s" % self.binid
        self.var.setRange(self.rngename, xmin, xmax)
        self.xmin = xmin
        self.xmax = xmax
        self.cen = (xmax+xmin)/2

        self.initY = 0
        self.initE = 0
        self.initE_precorr = 0
        self.initB = 0
        self.binerror = 0
        self.binerror_m = 0

        # self.dataset.sumEntries("%s>=%g && %s<%g "%(var.GetName(),xmin,var.GetName(),xmax))
        self.o = 1
        # r.RooRealVar("observed","Observed Events bin",1)
        self.obs = self.wspace_out.var("observed")

        # <-------------------------- Check this is cool
        self.argset = r.RooArgSet(wspace.var(self.var.GetName()))
        self.obsargset = r.RooArgSet(self.wspace_out.var(
            "observed"), self.wspace_out.cat("bin_number"))

        self.b = 0
        #self.constBkg = True

    def add_background(self, bkg):
        if "Purity" in bkg:
            tmp_pfunc = r.TF1("tmp_bkg_%s" % self.id, bkg.split(":")[-1])  # ?
            b = self.o*(1-tmp_pfunc.Eval(self.cen))
            #self.constBkg = False
        else:
            bkg_set = self.wspace.data(bkg)
            #if not self.wspace_out.data(bkg): self.wspace_out._import(bkg)
            b = bkg_set.sumEntries("%s>=%g && %s<%g " % (
                self.var.GetName(), self.xmin, self.var.GetName(), self.xmax))

        # Now model nuisances for background
        nuisances = self.cr.ret_bkg_nuisances()
        if len(nuisances) > 0:
            prod = 0
            print ("Is this really true? How many nuisance:", len(nuisances))

            if len(nuisances) > 1:
                nuis_args = r.RooArgList()
                for nuis in nuisances:
                    print ("Adding Background Nuisance ", nuis)
                    # Nuisance*Scale is the model
                    #form_args = r.RooArgList(self.wspace_out.var("nuis_%s"%nuis),self.wspace_out.function("sys_function_%s_%s"%(nuis,self.binid)))
                    print ("Trying to continue", self.wspace_out.function(
                        "sys_function_%s_%s" % (nuis, self.binid)).GetName())
                    print ("Does it have an attribute:", self.wspace_out.function(
                        "sys_function_%s_%s" % (nuis, self.binid)).getAttribute("temp"))
                    if (self.wspace_out.function("sys_function_%s_%s" % (nuis, self.binid)).getAttribute("temp")):
                        continue
                    form_args = r.RooArgList(self.wspace_out.function(
                        "sys_function_%s_%s" % (nuis, self.binid)))
                    delta_nuis = r.RooFormulaVar("delta_bkg_%s_%s" % (
                        self.binid, nuis), "Delta Change from %s" % nuis, "1+@0", form_args)
                    self.wspace_out._import(
                        delta_nuis, r.RooFit.RecycleConflictNodes())
                    nuis_args.add(self.wspace_out.function(
                        delta_nuis.GetName()))
                prod = r.RooProduct("prod_background_%s" %
                                    self.binid, "Nuisance Modifier", nuis_args)
            else:
                print ("Adding Background Nuisance ", nuisances[0])
                # if (self.wspace_out.function.getAttribute("temp")):
                ##  prod = r.RooFormulaVar("prod_background_%s"%self.binid,"Delta Change in Background from %s"%nuisances[0],"1",r.RooArgList())
                # else:
                prod = r.RooFormulaVar("prod_background_%s" % self.binid, "Delta Change in Background from %s" %
                                       nuisances[0], "1+@0", r.RooArgList(self.wspace_out.function("sys_function_%s_%s" % (nuisances[0], self.binid))))

            self.b = r.RooFormulaVar(
                "background_%s" % self.binid, "Number of expected background events in %s" % self.binid, "@0*%f" % b, r.RooArgList(prod))
        else:
            self.b = r.RooFormulaVar("background_%s" % self.binid, "Number of expected background events in %s" %
                                     self.binid, "@0", r.RooArgList(r.RooFit.RooConst(b)))
        self.wspace_out._import(self.b)
        self.b = self.wspace_out.function(self.b.GetName())

    def ret_initY(self):
        return self.initY

    def set_initY(self, mcdataset):

        print ("INIT Y: ", "%s>=%g && %s<%g" % (self.var.GetName(), self.xmin, self.var.GetName(
        ), self.xmax), self.rngename, self.wspace, self.wspace.data(mcdataset), mcdataset)
        self.initY = self.wspace.data(mcdataset).sumEntries("%s>=%g && %s<%g" % (
            self.var.GetName(), self.xmin, self.var.GetName(), self.xmax), self.rngename)

    def set_initE_precorr(self):
        return 0
        self.initE_precorr = self.wspace_out.var(naming_convention(
            self.id, self.catid, self.convention)).getVal()*self.wspace_out.var(self.sfactor.GetName()).getVal()

    def set_initE(self):
        return 0
        self.initE = self.ret_expected()
        self.initB = self.ret_background()
        self.set_initE_precorr()

    def set_label(self, cat):
        self.categoryname = cat.GetName()
        # self.wspace._import(cat,r.RooFit.RecycleConflictNodes())

    def set_wspace(self, w):
        self.wspace = w
        #self.wspace._import = getattr(self.wspace,"import") # workaround: import is a python keyword
        self.wspace._safe_import = SafeWorkspaceImporter(self.wspace)

    def set_sfactor(self, val):
        #print "Scale Factor for " ,self.binid,val
        if self.wspace_out.var("sfactor_%s" % self.binid):
            self.sfactor.setVal(val)
            self.wspace_out.var(self.sfactor.GetName()).setVal(val)
        else:
            self.sfactor = r.RooRealVar(
                "sfactor_%s" % self.binid, "Scale factor for bin %s" % self.binid, val, 0.00001, 10000)
            self.sfactor.removeRange()
            self.sfactor.setConstant()
            self.wspace_out._import(
                self.sfactor, r.RooFit.RecycleConflictNodes())

    def setup_expect_var(self, functionalForm=""):
        print (functionalForm)
        if not len(functionalForm):
            if not self.wspace_out.var(naming_convention(self.id, self.catid, self.convention)):
                self.model_mu = r.RooRealVar(
                    naming_convention(self.id, self.catid, self.convention),
                    "Model of N expected events in %d" % self.id,
                    self.initY,
                    0,
                    3*self.initY
                )
                self.model_mu.removeMax()
            else:
                self.model_mu = self.wspace_out.var(
                    naming_convention(self.id, self.catid, self.convention))
        else:
            print ("Setting up dependence!!")
            if self.convention == "BU":
                DEPENDANT = "%s_bin_%d" % (functionalForm, self.id)
            else:
                DEPENDANT = "%s_bin%d" % (functionalForm, self.id+1)

            self.model_mu = self.wspace_out.function("pmu_%s" % (DEPENDANT))

        arglist = r.RooArgList(
            (self.model_mu), self.wspace_out.var(self.sfactor.GetName()))

        # Multiply by each of the uncertainties in the control region, dont alter the Poisson pdf, we will add the constraint at the end. Actually we won't use this right now.
        nuisances = self.cr.ret_nuisances()
        if len(nuisances) > 0:
            prod = 0
            if len(nuisances) > 1:
                nuis_args = r.RooArgList()
                for nuis in nuisances:

                    if (self.wspace_out.function("sys_function_%s_%s" % (nuis, self.binid)).getAttribute("temp")):
                        continue

                    print ("Adding Nuisance ", nuis)
                    # Nuisance*Scale is the model
                    #form_args = r.RooArgList(self.wspace_out.var("nuis_%s"%nuis),self.wspace_out.function("sys_function_%s_%s"%(nuis,self.binid)))
                    form_args = r.RooArgList(self.wspace_out.function(
                        "sys_function_%s_%s" % (nuis, self.binid)))
                    delta_nuis = r.RooFormulaVar("delta_%s_%s" % (
                        self.binid, nuis), "Delta Change from %s" % nuis, "1+@0", form_args)
                    self.wspace_out._import(
                        delta_nuis, r.RooFit.RecycleConflictNodes())
                    nuis_args.add(self.wspace_out.function(
                        delta_nuis.GetName()))

                prod = r.RooProduct("prod_%s" % self.binid,
                                    "Nuisance Modifier", nuis_args)
            else:
                print ("Adding Nuisance ", nuisances[0])
                prod = r.RooFormulaVar("prod_%s" % self.binid, "Delta Change from %s" % nuisances[0], "1+@0", r.RooArgList(
                    self.wspace_out.function("sys_function_%s_%s" % (nuisances[0], self.binid))))
            arglist.add(prod)
            self.pure_mu = r.RooFormulaVar(
                "pmu_%s" % self.binid, "Number of expected (signal) events in %s" % self.binid, "(@0*@1)*@2", arglist)
        else:
            self.pure_mu = r.RooFormulaVar(
                "pmu_%s" % self.binid, "Number of expected (signal) events in %s" % self.binid, "(@0*@1)", arglist)
        # Finally we add in the background
        bkgArgList = r.RooArgList(self.pure_mu)
        #if self.constBkg: self.mu = r.RooFormulaVar("mu_%s"%self.binid,"Number of expected events in %s"%self.binid,"%f+@0"%self.b,bkgArgList)
        # else : self.mu = r.RooFormulaVar("mu_%s"%self.binid,"Number of expected events in %s"%self.binid,"@0/%f"%self.b,bkgArgList)
        self.mu = r.RooFormulaVar(
            "mu_%s" % self.binid, "Number of expected events in %s" % self.binid, "@0", bkgArgList)

        #self.mu = r.RooFormulaVar("mu_%s"%self.binid,"Number of expected events in %s"%self.binid,"@0/(@1*@2)",r.RooArgList(self.integral,self.sfactor,self.pdfFullInt))
        self.wspace_out._import(self.mu, r.RooFit.RecycleConflictNodes())
        self.wspace_out._import(self.obs, r.RooFit.RecycleConflictNodes())
        self.wspace_out.factory(
            "Poisson::pdf_%s(observed,mu_%s)" % (self.binid, self.binid))

    def add_to_dataset(self):
        return
        # create a dataset called observed
        # self.wspace_out.var("observed").setVal(self.o)
        # self.wspace_out.cat(self.categoryname).setIndex(self.type_id)
        lv = self.wspace_out.var("observed")
        lc = self.wspace_out.cat("bin_number")
        local_obsargset = r.RooArgSet(lv, lc)
        if not self.wspace_out.data("combinedData"):
            obsdata = r.RooDataSet(
                "combinedData", "Data in all Bins", local_obsargset)
            self.wspace_out._import(obsdata)
        obsdata = self.wspace_out.data("combinedData")
        obsdata.addFast(local_obsargset)

    def set_control_region(self, control):
        self.cr = control

    def ret_binid(self):
        return self.binid

    def ret_observed_dset(self):
        return self.wspace_out.data(dsname)

    def ret_observed(self):
        return self.o

    def ret_err(self):
        return self.binerror

    def add_err(self, e):
        self.binerror = (self.binerror**2+e**2)**0.5

    def add_model_err(self, e):
        self.binerror_m = (self.binerror_m**2+e**2)**0.5

    def ret_expected(self):
        return self.wspace_out.function(self.mu.GetName()).getVal()

    def ret_expected_err(self):
        return self.wspace_out.function(self.mu.GetName()).getError()

    def ret_model_err(self):
        return self.binerror_m

    def ret_background(self):
        # if self.constBkg: return self.b
        # else: return (1-self.b)*(self.ret_expected())
        return 0  # self.wspace_out.function(self.b.GetName()).getVal()

    def ret_correction(self):
        return (self.wspace_out.var(self.model_mu.GetName()).getVal())/self.initY

    def ret_correction_err(self):
        return self.ret_model_err()/self.initY

    def ret_model(self):
        return self.wspace_out.var(self.model_mu.GetName()).getVal()

    def Print(self):
        print ("Channel/Bin -> ", self.chid, self.binid, ", Var -> ", self.var.GetName(
        ), ", Range -> ", self.xmin, self.xmax, "MODEL MU (prefit/current state)= ", self.initY, "/", self.ret_model())
        print (" .... observed = ", self.o, ", expected = ", self.wspace_out.function(self.mu.GetName()).getVal(
        ), " (of which %f is background)" % self.ret_background(), ", scale factor = ", self.wspace_out.function(self.sfactor.GetName()).getVal())
        print (", Pre-corrections (nuisance at 0) expected (-bkg) ", self.initE_precorr)


class Channel:
    # This class holds a "channel" which is as dumb as saying it holds a dataset and scale factors
    def __init__(self, cname, wspace, wspace_out, catid, scalefactors, convention="BU"):
        self.catid = catid
        self.chid = cname
        self.scalefactors = scalefactors
        self.chname = "ControlRegion_%s" % self.chid
        self.backgroundname = ""
        self.wspace_out = wspace_out
        self.wspace_out._safe_import = SafeWorkspaceImporter(self.wspace_out)
        #self.wspace_out = getattr(self.wspace_out, "import")
        self.set_wspace(wspace)
        self.nuisances = []
        self.bkg_nuisances = []
        self.systematics = {}
        self.crname = cname
        self.nbins = scalefactors.GetNbinsX()
        self.convention = convention

    def ret_title(self):
        return self.crname

    def add_systematic_shape(self, sys, file):
        sys.exit("Nothing Will Happen with add_systematic, use add_nuisance")
        sfup = self.scalefactors.GetName()+"_%s_" % sys+"Up"
        sfdn = self.scalefactors.GetName()+"_%s_" % sys+"Down"
        print ("Looking for systematic shapes ... %s, %s" % (sfup, sfdn))
        try:
            print (file.Get(sfup).GetName())
            print (file.Get(sfdn).GetName())
        except AttributeError:
            print ("Missing one of ", sfup, sfdn, " in ", file.GetName())
            print ("Following is in directory ")
            file.Print()
            sys.exit()
        self.systematics[sys] = [file.Get(sfup), file.Get(sfdn)]

    def add_systematic_yield(self, syst, kappa):
        sys.exit("Nothing Will Happen with add_systematic, use add_nuisance")
        sfup = self.scalefactors.GetName()+"_%s_" % sys+"Up"
        sfdn = self.scalefactors.GetName()+"_%s_" % sys+"Down"
        sfup = self.scalefactors.Clone()
        sfup.SetName(self.scalefactors.GetName()+"_%s_" % syst+"Up")
        sfdn = self.scalefactors.Clone()
        sfdn.SetName(self.scalefactors.GetName()+"_%s_" % syst+"Down")
        # log-normal scalefactors
        sfup.Scale(1+kappa)
        sfdn.Scale(1./(1+kappa))
        self.systematics[syst] = [sfup, sfdn]

    def add_nuisance(self, name, size, bkg=False):
        #print "Error, Nuisance parameter model not supported fully for shape variations, dont use it!"
        if not(self.wspace_out.var("%s" % name)):
            #nuis = r.RooRealVar("nuis_%s"%name,"Nuisance - %s"%name,0,-3,3);
            nuis = r.RooRealVar("%s" % name, "Nuisance - %s" % name, 0, -3, 3)
            nuis.setAttribute("NuisanceParameter_EXTERNAL", True)
            if bkg:
                nuis.setAttribute("BACKGROUND_NUISANCE", True)
            self.wspace_out._import(nuis)
            cont = r.RooGaussian("const_%s" % name, "Constraint - %s" % name, self.wspace_out.var(
                nuis.GetName()), r.RooFit.RooConst(0), r.RooFit.RooConst(1))
            self.wspace_out._import(cont)

        # run through all of the bins in the control regions and create a function to interpolate
        for b in range(self.nbins):
            if self.convention == "BU":
                fname = "sys_function_%s_cat_%s_ch_%s_bin_%d" % (
                    name, self.catid, self.chid, b)
            else:
                fname = "sys_function_%s_cat_%s_ch_%s_bin%d" % (
                    name, self.catid, self.chid, b+1)
            func = r.RooFormulaVar(
                fname,
                "Systematic Varation",
                "@0*%f" % size, r.RooArgList(self.wspace_out.var("%s" % name))
            )
            if not self.wspace_out.function(func.GetName()):
                self.wspace_out._import(func)
        # else
        #  nuis = self.wspace_out.var("nuis_%s"%name)
        if bkg:
            self.bkg_nuisances.append(name)
        else:
            self.nuisances.append(name)

    def add_nuisance_shape(self, name, file, setv="", functype="quadratic"):
        if not(self.wspace_out.var("%s" % name)):
            nuis = r.RooRealVar("%s" % name, "Nuisance - %s" % name, 0, -3, 3)
            nuis.setAttribute("NuisanceParameter_EXTERNAL", True)
            self.wspace_out._import(nuis)
            nuis_IN = r.RooRealVar("nuis_IN_%s" % name,
                                   "Constraint Mean - %s" % name, 0, -10, 10)
            nuis_IN.setConstant()
            self.wspace_out._import(nuis_IN)

            cont = r.RooGaussian("const_%s" % name, "Constraint - %s" % name, self.wspace_out.var(
                nuis.GetName()), self.wspace_out.var(nuis_IN.GetName()), r.RooFit.RooConst(1))
            self.wspace_out._import(cont)

        sfup = self.scalefactors.GetName()+"_%s_" % name+"Up"
        sfdn = self.scalefactors.GetName()+"_%s_" % name+"Down"
        print ("Looking for systematic shapes ... %s,%s" % (sfup, sfdn))
        sysup, sysdn = file.Get(sfup), file.Get(sfdn)
        try:
            sysup.GetName()
            sysdn.GetName()
        except ReferenceError:
            print ("Missing one of ", sfup, sfdn, " in ", file.GetName())
            print ("Following is in directory ")
            file.ls()
            sys.exit()
        # Now we loop through each bin and construct a polynomial function per bin
        for b in range(self.nbins):
            # Name of the function depends on naming scheme
            if self.convention == "BU":
                fname = "sys_function_%s_cat_%s_ch_%s_bin_%d" % (
                    name, self.catid, self.chid, b)
            else:
                fname = "sys_function_%s_cat_%s_ch_%s_bin%d" % (
                    name, self.catid, self.chid, b+1)
            if functype=="quadratic":
                if self.scalefactors.GetBinContent(b+1) == 0:
                    nsf = 0
                    vu = 0
                    vd = 0
                else:
                    nsf = 1./(self.scalefactors.GetBinContent(b+1))
                    vu = 1./(sysup.GetBinContent(b+1)) - nsf

                    if sysdn.GetBinContent(b+1) == 0:
                        vd = 0
                    else:
                        # Note this should be <ve if down is lower, its not a bug
                        vd = 1./(sysdn.GetBinContent(b+1)) - nsf
                coeff_a = 0.5*(vu+vd)
                coeff_b = 0.5*(vu-vd)

                func = r.RooFormulaVar(
                    fname,
                    "Systematic Varation",
                    "(%f*@0*@0+%f*@0)/%f" % (coeff_a, coeff_b, nsf),
                    r.RooArgList(
                        self.wspace_out.var("%s" % name))
                )  # this is now relative deviation, SF-SF_0 = func => SF = SF_0*(1+func/SF_0)

                if (coeff_a==0 and coeff_b==0):
                    func.setAttribute("temp", True)
            elif functype=="lognorm":
                n0 = self.scalefactors.GetBinContent(b+1)
                if n0 == 0:
                    sigma = 0
                    direction = 1
                else:
                    sfmax = max(0, sysup.GetBinContent(b+1))
                    sfmin = max(0, sysdn.GetBinContent(b+1))
                    sigma = 0.5 * abs(sfmax-sfmin)

                    direction = 1 if sfmax > sfmin else -1
                
                
                func = r.RooFormulaVar(
                    fname,
                    "Systematic Variation",
                    "({N} * (1+{SIGMA}/{N})**({DIRECTION}*@0) - {N}) / {N}".format(N=n0, SIGMA=sigma,DIRECTION=direction),
                    r.RooArgList(self.wspace_out.var("%s" % name))
                )
                if sigma == 0:
                    func.setAttribute("temp", True)
            self.wspace_out.var("%s" % name).setVal(0)
            if not self.wspace_out.function(func.GetName()):
                self.wspace_out._import(func)
        if setv != "":
            if "SetTo" in setv:
                vv = float(setv.split("=")[1])
                self.wspace_out.var("nuis_IN_%s" % name).setVal(vv)
                self.wspace_out.var("%s" % name).setVal(vv)
            else:
                print ("DIRECTIVE %s IN SYSTEMATIC %s, NOT UNDERSTOOD!" % (
                    setv, name))
                sys.exit()
        self.nuisances.append(name)

    def set_wspace(self, w):
        self.wspace = w
        self.wspace._safe_import = SafeWorkspaceImporter(self.wspace)
        #self.wspace._import = getattr(self.wspace,"import") # workaround: import is a python keyword

    def ret_bkg_nuisances(self):
        return self.bkg_nuisances

    def ret_nuisances(self):
        return self.nuisances

    def ret_name(self):
        return self.chname

    def ret_chid(self):
        return self.chid

    def ret_sfactor(self, i, syst="", direction=1):
        if self.scalefactors.GetBinContent(i+1) == 0:
            return 0
        if syst and syst in self.systematics.keys():
            if direction > 0:
                index = 0
            else:
                index = 1
            return 1./(self.systematics[syst][index].GetBinContent(i+1))
        else:
            return 1./(self.scalefactors.GetBinContent(i+1))

    def ret_background(self):
        return self.backgroundname

    def has_background(self):
        return len(self.backgroundname)


class Category:
    # This class holds a "category" which contains a bunch of channels
    # It needs to hold a combined_pdf object, a combined_dataset object and
    # the target dataset for this channel
    def __init__(self, corrname, catid, cname 		# name for the parametric variation templates
                 , _fin 		# TDirectory
                 , _fout 		# and output file
                 , _wspace 		# RooWorkspace (in)
                 , _wspace_out 	# RooWorkspace (out)
                 , _bins  		# just get the bins
                 , _varname	    	# name of the variale
                 , _target_datasetname  # only for initial fit values
                 , _control_regions 	# CRs constructed
                 , diag		# a diagonalizer object
                 , convention="BU"  # Naming convention to use: either BU or IC
                 ):
        self.GNAME = corrname
        self.cname = cname
        self.category = catid
        self.catid = catid+'_'+corrname
        # A crappy way to store canvases to be saved in the end
        self.canvases = {}
        self.histograms = []
        self.model_hist = 0
        self._fin = _fin
        self._fout = _fout

        self._wspace = _wspace
        self._wspace_out = _wspace_out

        self._wspace_out._safe_import = SafeWorkspaceImporter(self._wspace_out)
        self._wspace._safe_import = SafeWorkspaceImporter(self._wspace)

        #self.diag = diag
        self.additional_vars = {}
        self.additional_targets = []

        self.channels = []
        self.all_hists = []
        self.cr_prefit_hists = []
        # Setup a bunch of the attributes for this category
        self._var = _wspace.var(_varname)
        self._varname = _varname
        self._bins = _bins[:]
        self._control_regions = _control_regions
        #self._data_mc  = _wspace.data(_target_datasetname)
        self._target_datasetname = _target_datasetname
        self.sample = self._wspace_out.cat("bin_number")
        self._obsvar = self._wspace_out.var("observed")
        #self._obsdata = self._wspace_out.data("combinedData")
        if self._wspace_out.var(self._var.GetName()):
            a = 1

        else:
            self._wspace_out._import(
                self._var, r.RooFit.RecycleConflictNodes())
        self._var = self._wspace_out.var(self._var.GetName())
        self.isSecondDependant = False
        # for j,cr in enumerate(self._control_regions):
        # for i,bl in enumerate(self._bins):
        #  if i >= len(self._bins)-1 : continue
        #  self.sample.defineType("cat_%s_ch_%s_bin_%d"%(self.catid,j,i),10*MAXBINS*catid+MAXBINS*j+i)
        #  self.sample.setIndex(10*MAXBINS*catid+MAXBINS*j+i)

        self.convention = convention

    def setDependant(self, BASE, CONTROL):
        self.isSecondDependant = True
        self.BASE = BASE
        self.CONTROL = CONTROL

    def addTarget(self, vn, CR, correct=True):
        self.additional_targets.append([vn, CR, correct])

    def addVar(self, vnam, n, xmin, xmax):
        self.additional_vars[vnam] = [n, xmin, xmax]

    def fillExpectedHist(self, cr, expected_hist):
        bc = 0
        for i, ch in enumerate(self.channels):
            if ch.chid == cr.chid:
                bc += 1
                expected_hist.SetBinContent(bc, ch.ret_expected())
                expected_hist.SetBinError(bc, ch.ret_err())

    def fillExpectedCorr(self, cr, expected_hist, regen=False):
        bc = 0
        for i, ch in enumerate(self.channels):
            if ch.chid == cr.chid:
                bc += 1
                prefitValue = ch.initE_precorr if regen else ch.initE - ch.initB
                expected_hist.SetBinContent(
                    bc, (ch.ret_expected()-ch.ret_background())/(prefitValue))
                expected_hist.SetBinError(bc, ch.ret_err()/(ch.initE-ch.initB))

    def fillObservedHist(self, cr, observed_hist):
        bc = 0
        for i, ch in enumerate(self.channels):
            if ch.chid == cr.chid:
                bc += 1
                observed_hist.SetBinContent(bc, ch.ret_observed())
                observed_hist.SetBinError(bc, (ch.ret_observed())**0.5)

    def fillBackgroundHist(self, cr, background_hist):
        bc = 0
        for i, ch in enumerate(self.channels):
            if ch.chid == cr.chid:
                bc += 1
                background_hist.SetBinContent(bc, ch.ret_background())

    def fillModelHist(self, model_hist):
        for i, ch in enumerate(self.channels):
            if i >= len(self._bins)-1:
                break
            model_hist.SetBinContent(i+1, ch.ret_model())

    def makeWeightHists(self, cr_i=-1, regen=False):
        hist = r.TH1F("control_Region_weights", "Expected Post-fit/Pre-fit",
                      len(self._bins)-1, array.array('d', self._bins))
        if cr_i == -1:
            for i, ch in enumerate(self.channels):
                if i >= len(self._bins)-1:
                    break
                hist.SetBinContent(i+1, ch.ret_correction())
                hist.SetBinError(i+1, ch.ret_correction_err())
        elif cr_i == -2:  # no correction
            for i, ch in enumerate(self.channels):
                if i >= len(self._bins)-1:
                    break
                hist.SetBinContent(i+1, 1)
                hist.SetBinError(i+1, 0)
        else:
            self.fillExpectedCorr(self._control_regions[cr_i], hist, regen)

        return hist.Clone()

    def init_channels(self):
        #print "self._wspace_out.Print(V)", self._wspace_out.Print("V")
        # r.RooCategory("bin_number","bin_number")
        sample = self._wspace_out.cat("bin_number")
        #print "zeynep sample", sample, self._wspace_out.cat("bin_number")

        # for j,cr in enumerate(self._control_regions):
        for j, cr in enumerate(self._control_regions):
            for i, bl in enumerate(self._bins):
                if i >= len(self._bins)-1:
                    continue
                xmin, xmax = bl, self._bins[i+1]
                if i == len(self._bins)-2:
                    xmax = 999999.
                ch = Bin(
                    self.category,
                    self.catid,
                    cr.chid,
                    i,
                    self._var,
                    "",
                    self._wspace,
                    self._wspace_out,
                    xmin,
                    xmax,
                    convention=self.convention)
                ch.set_control_region(cr)
                if cr.has_background():
                    ch.add_background(cr.ret_background())
                ch.set_label(sample)  # should import the sample category label
                ch.set_initY(self._target_datasetname)
                ch.set_sfactor(cr.ret_sfactor(i))
                # This has to the the last thing
                # Note, we can have an expected value which is itself a RooFormulaVar

                if self.isSecondDependant:
                    ch.setup_expect_var("cat_%s_%s_ch_%s" % (
                        self.category, self.BASE, self.CONTROL))
                else:
                    ch.setup_expect_var()

                # initialise expected  (but this will be somewhat a "post" state), i.e after fiddling with the nuisance parameters.
                ch.set_initE()
                ch.add_to_dataset()
                self.channels.append(ch)
        # fit is buggered so need to scale by 1.1

        for j, cr in enumerate(self._control_regions):
            # save the prefit histos
            cr_pre_hist = r.TH1F("control_region_%s" % cr.ret_name(
            ), "Expected %s control region" % cr.ret_name(), len(self._bins)-1, array.array('d', self._bins))
            self.fillExpectedHist(cr, cr_pre_hist)
            cr_pre_hist.SetLineWidth(2)
            cr_pre_hist.SetLineColor(r.kRed)
            self.all_hists.append(cr_pre_hist.Clone())
            self.cr_prefit_hists.append(cr_pre_hist.Clone())

        for i, bl in enumerate(self.channels):
            if i >= len(self._bins)-1:
                break
            model_mu = self._wspace_out.var(
                naming_convention(bl.id, bl.catid, self.convention))
            # self._wspace_out.var(model_mu.GetName()).setVal(1.2*model_mu.getVal())

    def ret_control_regions(self):
        return self._control_regions

    def ret_channels(self):
        return self.channels

    def generate_systematic_templates(self, diag, npars):
        if self.model_hist == 0:
            sys.exit("Error in generate_systematic_templates: cannot generate template variations before nominal model is created, first run Category.save_model() !!!! ")

        # First store nominal values in control regions (to make error bands)
        nominals = []
        for j, cr in enumerate(self._control_regions):
            nominal_values = []
            for i, ch in enumerate(self.channels):
                if ch.chid != cr.chid:
                    continue
                nominal_values.append(ch.ret_expected())
            nominals.append(nominal_values)

        # The parameters have changed so re-generate the templates
        # We also re-calculate the expectations in each CR to update the errors for the plotting
        leg_var = r.TLegend(0.56, 0.1, 0.89, 0.91)
        leg_var.SetFillColor(0)
        leg_var.SetTextFont(42)

        # We will make a plot along the way
        canvr = r.TCanvas("canv_variations_ratio")
        canv = r.TCanvas("canv_variations")
        model_hist_spectrum = getNormalizedHist(self.model_hist)
        model_hist_spectrum.SetTitle("")
        model_hist_spectrum.GetXaxis().SetTitle("E_{T}^{miss} (GeV)")
        model_hist_spectrum.Draw()
        self.all_hists.append(model_hist_spectrum)

        sys_c = 0
        systrats = []

        for par in range(npars):
            hist_up = r.TH1F("%s_combined_model_par_%d_Up" % (self.GNAME, par), "combined_model par %d Up 1 sigma - %s " %
                             (par, self.cname), len(self._bins)-1, array.array('d', self._bins))
            hist_dn = r.TH1F("%s_combined_model_par_%d_Down" % (self.GNAME, par), "combined_model par %d Down 1 sigma - %s" %
                             (par, self.cname), len(self._bins)-1, array.array('d', self._bins))

            diag.setEigenset(par, 1)  # up variation
            # fillModelHist(hist_up,channels)
            histW = self.makeWeightHists()
            diag.generateWeightedTemplate(
                hist_up, histW, self._varname, self._varname, self._wspace.data(self._target_datasetname))

            # Also want to calculate for each control region an error per bin associated, its very easy to do, but only do it for "Up" variation and the error will symmetrize itself
            for j, cr in enumerate(self._control_regions):
                chi = 0
                for i, ch in enumerate(self.channels):
                    if ch.chid != cr.chid:
                        continue
                    derr = abs(ch.ret_expected()-nominals[j][chi])
                    ch.add_err(derr)
                    chi += 1

            # also add in signalregion the errors
            for i, ch in enumerate(self.channels):
                derr = abs(hist_up.GetBinContent(i+1) -
                           self.model_hist.GetBinContent(i+1))
                ch.add_model_err(derr)
                if i > len(self._bins)-1:
                    break

            diag.setEigenset(par, -1)  # up variation
            # fillModelHist(hist_dn,channels)
            histW = self.makeWeightHists()
            diag.generateWeightedTemplate(
                hist_dn, histW, self._varname, self._varname, self._wspace.data(self._target_datasetname))

            # Reset parameter values
            diag.resetPars()

            # make the plots
            canv.cd()
            hist_up.SetLineWidth(2)
            hist_dn.SetLineWidth(2)
            if sys_c+2 == 10:
                sys_c += 1
            hist_up.SetLineColor(sys_c+2)
            hist_dn.SetLineColor(sys_c+2)
            hist_dn.SetLineStyle(2)

            # _fout.WriteTObject(hist_up)
            # _fout.WriteTObject(hist_dn)
            self.histograms.append(hist_up.Clone())
            self.histograms.append(hist_dn.Clone())

            hist_up = getNormalizedHist(hist_up)
            hist_dn = getNormalizedHist(hist_dn)
            self.all_hists.append(hist_up)
            self.all_hists.append(hist_dn)

            hist_up.Draw("samehist")
            hist_dn.Draw("samehist")

            flat = self.model_hist.Clone()
            hist_up_cl = hist_up.Clone()
            hist_up_cl.SetName(hist_up_cl.GetName()+"_ratio")
            hist_dn_cl = hist_dn.Clone()
            hist_dn_cl.SetName(hist_dn_cl.GetName()+"_ratio")
            hist_up_cl.Divide(model_hist_spectrum)
            hist_dn_cl.Divide(model_hist_spectrum)
            flat.Divide(self.model_hist)

            # ratio plot
            canvr.cd()
            flat.SetTitle("")
            flat.GetXaxis().SetTitle("E_{T}^{miss} (GeV)")
            # flat.GetYaxis().SetRangeUser(0.85,1.2)
            if par == 0:
                flat.Draw("hist")
            self.all_hists.append(flat)
            self.all_hists.append(hist_up_cl)
            self.all_hists.append(hist_dn_cl)
            systrats.append(hist_up_cl.Clone())
            systrats.append(hist_dn_cl.Clone())
            # hist_up_cl.Draw('histsame')
            # hist_dn_cl.Draw('histsame')
            leg_var.AddEntry(hist_up_cl, "Parameter %d" % par, "L")
            sys_c += 1

        # find maximum
        maxdiff = 0
        for syst in systrats:
            max_local = max([syst.GetBinContent(b+1)
                             for b in range(syst.GetNbinsX())])
            #print max_local, maxdiff, syst.GetName()
            if max_local > maxdiff:
                maxdiff = max_local
        print ("MaxDiff = ", maxdiff)
        maxdiff -= 1
        canvr.cd()
        dHist = r.TH1F(
            "dummy", ";E_{T}^{miss};Variation/Nominal", 1, self._bins[0], self._bins[-1])
        dHist.SetBinContent(1, 1)
        dHist.SetMaximum(1+1.1*maxdiff)
        dHist.SetMinimum(1-1.1*maxdiff)
        dHist.Draw("AXIS")
        for isy, syst in enumerate(systrats):
            syst.Draw("histsame")

        canv.cd()
        leg_var.Draw()
        canvr.cd()
        leg_var.Draw()
        self._fout.WriteTObject(canv)
        self._fout.WriteTObject(canvr)

    def save_model(self, diag):
        # Need to make ratio
        self.model_hist = r.TH1F("%s_combined_model" % (
            self.cname), "combined_model - %s" % (self.cname), len(self._bins)-1, array.array('d', self._bins))
        # fillModelHist(model_hist,channels)

        histW = self.makeWeightHists()
        diag.generateWeightedTemplate(
            self.model_hist, histW, self._varname, self._varname, self._wspace.data(self._target_datasetname))
        self.model_hist.SetLineWidth(2)
        self.model_hist.SetLineColor(1)

        #_fout = r.TFile("combined_model.root","RECREATE")
        # _fout.WriteTObject(self.model_hist)
        self.model_hist.SetName("%s_combined_model" % self.GNAME)
        histW.SetName("%s_correction_weights_%s" % (self.GNAME, self.cname))
        histW.SetLineWidth(2)
        histW.SetLineColor(4)
        self.histograms.append(histW)

    def save_all_models_internal(self, diag):

        # First we make errors for the nominal model histogram
        error_hist_F = r.TH1F("%s_combined_model_ERRORS" % (
            self.cname), "combined_model - %s" % (self.cname), len(self._bins)-1, array.array('d', self._bins))
        histW = self.makeWeightHists()
        histW_U = self.makeWeightHists()
        for b in range(histW_U.GetNbinsX()):
            # now its ~the default correction +1 sigma
            histW_U.SetBinContent(
                b+1, histW_U.GetBinContent(b+1)+histW_U.GetBinError(b+1))
        diag.generateWeightedTemplate(
            error_hist_F, histW_U, self._varname, self._varname, self._wspace.data(self._target_datasetname))
        for b in range(error_hist_F.GetNbinsX()):
            sterr = error_hist_F.GetBinError(b+1)
            self.model_hist.SetBinError(
                b+1, (sterr**2+(abs(error_hist_F.GetBinContent(b+1)-self.model_hist.GetBinContent(b+1)))**2)**0.5)

        # First, I think we want to pull in all of the "pre-fit" targets and make
        # them as the denominator, not necessary for the signal region

        for tg_v in self.additional_targets:
            tg = tg_v[0]
            cr_i = tg_v[1]
            histW = self.makeWeightHists(cr_i, True)
            histW_U = self.makeWeightHists(cr_i, True)
            histW.SetName("%s_%s_combined_model_WEIGHTS_CR_FORTARGET" %
                          (self.GNAME, tg))
            self.histograms.append(histW.Clone())
            for b in range(histW_U.GetNbinsX()):
                # now its ~the default correction +1 sigma
                histW_U.SetBinContent(
                    b+1, histW_U.GetBinContent(b+1)+histW_U.GetBinError(b+1))
            model_tg = r.TH1F("%s_%s_combined_model" % (self.GNAME, tg), "combined_model - %s" %
                              (self.cname), len(self._bins)-1, array.array('d', self._bins))
            diag.generateWeightedTemplate(
                model_tg, histW, self._varname, self._varname, self._wspace.data(tg))
            model_tg_errs = r.TH1F("%s_%s_combined_model_ERRORS" % (
                self.GNAME, tg), "combined_model - %s" % (self.cname), len(self._bins)-1, array.array('d', self._bins))
            diag.generateWeightedTemplate(
                model_tg_errs, histW_U, self._varname, self._varname, self._wspace.data(tg))
            # Errors are set as
            for b in range(model_tg_errs.GetNbinsX()):
                # add statisticsl part
                sterr = model_tg.GetBinError(b+1)
                model_tg.SetBinError(
                    b+1, (sterr**2+(abs(model_tg_errs.GetBinContent(b+1)-model_tg.GetBinContent(b+1)))**2)**0.5)
            self.histograms.append(model_tg.Clone())

        # Also make a weighted version of each other variable
        for varx in self.additional_vars.keys():
            histW = self.makeWeightHists()
            histW_U = self.makeWeightHists()
            for b in range(histW_U.GetNbinsX()):
                # now its ~the default correction +1 sigma
                histW_U.SetBinContent(
                    b+1, histW_U.GetBinContent(b+1)+histW_U.GetBinError(b+1))
            nb = self.additional_vars[varx][0]
            min = self.additional_vars[varx][1]
            max = self.additional_vars[varx][2]
            model_hist_vx = r.TH1F("%s_combined_model%s" % (
                self.GNAME, varx), "combined_model - %s" % (self.cname), nb, min, max)
            model_hist_vx_errs = r.TH1F("%s_combined_model%s_ERRORS" % (
                self.GNAME, varx), "combined_model - %s" % (self.cname), nb, min, max)
            diag.generateWeightedTemplate(
                model_hist_vx, histW, self._varname, varx, self._wspace.data(self._target_datasetname))
            diag.generateWeightedTemplate(
                model_hist_vx_errs, histW_U, self._varname, varx, self._wspace.data(self._target_datasetname))
            for b in range(model_hist_vx_errs.GetNbinsX()):
                sterr = model_hist_vx.GetBinError(b+1)
                model_hist_vx.SetBinError(
                    b+1, (sterr**2+(abs(model_hist_vx_errs.GetBinContent(b+1)-model_hist_vx.GetBinContent(b+1)))**2)**0.5)
            self.histograms.append(model_hist_vx.Clone())

            for tg_v in self.additional_targets:
                tg = tg_v[0]
                cr_i = tg_v[1]
                histW = self.makeWeightHists(cr_i, True)
                histW_U = self.makeWeightHists(cr_i, True)
                for b in range(histW_U.GetNbinsX()):
                    # now its ~the default correction +1 sigma
                    histW_U.SetBinContent(
                        b+1, histW_U.GetBinContent(b+1)+histW_U.GetBinError(b+1))
                model_hist_vx_tg = r.TH1F("%s_%s_combined_model%s" % (
                    self.GNAME, tg, varx), "combined_model - %s" % (self.cname), nb, min, max)
                model_hist_vx_tg_errs = r.TH1F("%s_%s_combined_model_ERRORS%s" % (
                    self.GNAME, tg, varx), "combined_model - %s" % (self.cname), nb, min, max)
                diag.generateWeightedTemplate(
                    model_hist_vx_tg, histW, self._varname, varx, self._wspace.data(tg))
                diag.generateWeightedTemplate(
                    model_hist_vx_tg_errs, histW_U, self._varname, varx, self._wspace.data(tg))
                for b in range(model_hist_vx_tg_errs.GetNbinsX()):
                    sterr = model_hist_vx_tg.GetBinError(b+1)
                    model_hist_vx_tg.SetBinError(
                        b+1, (sterr**2+(abs(model_hist_vx_tg_errs.GetBinContent(b+1)-model_hist_vx_tg.GetBinContent(b+1)))**2)**0.5)
                self.histograms.append(model_hist_vx_tg.Clone())

    def make_post_fit_plots(self):
        c = r.TCanvas("%sregion_mc_fit_before_after" %
                      self._target_datasetname)
        hist_original = r.TH1F("%s_OriginalZvv" % (self.cname), "", len(
            self._bins)-1, array.array('d', self._bins))
        hist_post = r.TH1F("%s_NewZvv" % (self.cname), "", len(
            self._bins)-1, array.array('d', self._bins))
        for i, ch in enumerate(self.channels):
            if i >= len(self._bins)-1:
                break
            hist_original.SetBinContent(i+1, ch.ret_initY())
            hist_post.SetBinContent(i+1, ch.ret_model())
        hist_original.GetXaxis().SetTitle("fake MET (GeV)")
        hist_original.GetXaxis().SetTitle("Events/GeV")
        hist_original.SetLineWidth(2)
        hist_post.SetLineWidth(2)
        hist_original.SetLineColor(2)
        hist_post.SetLineColor(4)
        hist_original = getNormalizedHist(hist_original)
        hist_post = getNormalizedHist(hist_post)
        hist_original.Draw("hist")
        hist_post.Draw("histsame")
        self._fout.WriteTObject(c)

        lat = r.TLatex()
        lat.SetNDC()
        lat.SetTextSize(0.04)
        lat.SetTextFont(42)

        # now build post fit plots in each control region with some indication of systematic variations from fit?
        for j, cr in enumerate(self._control_regions):
            c = r.TCanvas("c_%s" % cr.ret_name(), "", 800, 800)
            cr_hist = r.TH1F("%s_control_region_%s" % (self.cname, cr.ret_name(
            )), "Expected %s control region" % cr.ret_name(), len(self._bins)-1, array.array('d', self._bins))
            da_hist = r.TH1F("%s_data_control_region_%s" % (self.cname, cr.ret_name(
            )), "data %s control region" % cr.ret_name(), len(self._bins)-1, array.array('d', self._bins))
            mc_hist = r.TH1F("%s_mc_control_region_%s" % (self.cname, cr.ret_name(
            )), "Background %s control region" % cr.ret_name(), len(self._bins)-1, array.array('d', self._bins))
            self.fillObservedHist(cr, da_hist)
            self.fillBackgroundHist(cr, mc_hist)
            self.fillExpectedHist(cr, cr_hist)
            da_hist.SetTitle("")
            cr_hist.SetFillColor(r.kBlue-10)
            mc_hist.SetFillColor(r.kGray)

            cr_hist = getNormalizedHist(cr_hist)
            da_hist = getNormalizedHist(da_hist)
            mc_hist = getNormalizedHist(mc_hist)
            pre_hist = getNormalizedHist(self.cr_prefit_hists[j])

            cr_hist.SetLineColor(r.kBlue)
            cr_hist.SetLineWidth(2)
            mc_hist.SetLineColor(1)
            mc_hist.SetLineWidth(2)
            da_hist.SetMarkerColor(1)
            da_hist.SetLineColor(1)
            da_hist.SetLineWidth(2)
            da_hist.SetMarkerStyle(20)
            self.histograms.append(da_hist)
            self.histograms.append(cr_hist)
            self.histograms.append(mc_hist)
            self.histograms.append(pre_hist)

            c.cd()
            pad1 = r.TPad("p1", "p1", 0, 0.28, 1, 1)
            pad1.SetBottomMargin(0.01)
            pad1.SetCanvas(c)
            pad1.Draw()
            pad1.cd()
            tlg = r.TLegend(0.54, 0.53, 0.89, 0.89)
            tlg.SetFillColor(0)
            tlg.SetTextFont(42)
            tlg.AddEntry(da_hist, "Data - %s" % cr.ret_title(), "PEL")
            tlg.AddEntry(cr_hist, "Expected (post-fit)", "FL")
            tlg.AddEntry(mc_hist, "Backgrounds Component", "F")
            tlg.AddEntry(pre_hist, "Expected (pre-fit)", "L")
            da_hist.GetYaxis().SetTitle("Events/GeV")
            da_hist.GetXaxis().SetTitle("fake MET (GeV)")
            da_hist.Draw("Pe")
            cr_hist.Draw("sameE2")
            cr_line = cr_hist.Clone()
            cr_line.SetFillColor(0)
            self.all_hists.append(cr_line)
            pre_hist.Draw("samehist")
            cr_line.Draw("histsame")
            mc_hist.Draw("samehist")
            da_hist.Draw("Pesame")
            tlg.Draw()
            lat.DrawLatex(0.1, 0.92, "#bf{CMS} #it{Preliminary}")
            pad1.SetLogy()
            pad1.RedrawAxis()

            # Ratio plot
            c.cd()
            pad2 = r.TPad("p2", "p2", 0, 0.068, 1, 0.285)
            pad2.SetTopMargin(0.04)
            pad2.SetCanvas(c)
            pad2.Draw()
            pad2.cd()
            # Need to make sure cr hist has no errors for when we divide
            cr_hist_noerr = cr_hist.Clone()
            cr_hist_noerr.SetName(cr_hist.GetName()+"noerr")
            for b in range(cr_hist_noerr.GetNbinsX()):
                cr_hist_noerr.SetBinError(b+1, 0)
            pre_hist_noerr = pre_hist.Clone()
            pre_hist_noerr.SetName(pre_hist.GetName()+"noerr")
            for b in range(pre_hist_noerr.GetNbinsX()):
                pre_hist_noerr.SetBinError(b+1, 0)

            ratio = da_hist.Clone()
            ratio_pre = da_hist.Clone()
            ratio.GetYaxis().SetRangeUser(0.21, 1.79)
            ratio.Divide(cr_hist_noerr)
            ratio_pre.Divide(pre_hist_noerr)
            ratio.GetYaxis().SetTitle("Data/Bkg")
            ratio.GetYaxis().SetNdivisions(5)
            ratio.GetYaxis().SetLabelSize(0.1)
            ratio.GetYaxis().SetTitleSize(0.12)
            ratio.GetXaxis().SetTitleSize(0.085)
            ratio.GetXaxis().SetLabelSize(0.12)
            self.all_hists.append(ratio)
            self.all_hists.append(ratio_pre)
            ratio.GetXaxis().SetTitle("")
            ratio.SetLineColor(cr_hist.GetLineColor())
            ratio.SetMarkerColor(cr_hist.GetLineColor())
            ratio.Draw()
            ratio_pre.SetLineColor(pre_hist.GetLineColor())
            ratio_pre.SetMarkerColor(pre_hist.GetLineColor())
            ratio_pre.SetLineWidth(2)
            eline = ratio.Clone()
            eline.SetName("OneWithError_%s" % ratio.GetName())
            self.all_hists.append(eline)
            for b in range(ratio.GetNbinsX()):
                eline.SetBinContent(b+1, 1)
                if cr_hist.GetBinContent(b+1) > 0:
                    eline.SetBinError(
                        b+1, cr_hist.GetBinError(b+1)/cr_hist.GetBinContent(b+1))
            eline.SetFillColor(r.kBlue-10)
            eline.SetLineColor(r.kBlue-10)
            eline.SetMarkerSize(0)
            eline.Draw("sameE2")
            line = r.TLine(da_hist.GetXaxis().GetXmin(), 1,
                           da_hist.GetXaxis().GetXmax(), 1)
            line.SetLineColor(1)
            line.SetLineStyle(2)
            line.SetLineWidth(2)
            line.Draw()
            ratio.Draw("same")
            ratio_pre.Draw("pelsame")
            ratio.Draw("samepel")
            self.all_hists.append(line)
            pad2.RedrawAxis()
            self._fout.WriteTObject(c)

    def save(self):
        # for canv in self.canvases.keys():
        #  self._fout.WriteTObject(self.canvases[canv])
        # finally THE model
        self._fout.WriteTObject(self.model_hist)
        print ("Saving hitograms")
        for hist in self.histograms:
            print ("Saving - ", hist.GetName())
            self._fout.WriteTObject(hist)
