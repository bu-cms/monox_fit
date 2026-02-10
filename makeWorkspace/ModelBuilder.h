#ifndef MODELBUILDER
#define MODELBUILDER

#include "diagonalize.h"
//#include "include/kinematic_reweights.h"
#include "TDirectory.h" 
#include "TFile.h" 
#include "TEventList.h" 
#include "TH2F.h"
#include "RooAbsReal.h"
#include "RooDataHist.h"
#include "RooHistPdf.h"
#include "RooEffProd.h"
#include "RooProdPdf.h"
#include "RooLandau.h"
#include "RooGaussian.h"
#include "RooLognormal.h"
#include "RooBernstein.h"
#include "RooFormulaVar.h"
#include <cstring>

using namespace std;

class ModelBuilder {
  public:

  ModelBuilder( int id, std::string catn ){
  	sel_i=id;
	catname = catn;
	wspace = new RooWorkspace(Form("wspace_%s",catname.c_str())); 
  };
  ~ModelBuilder(){
   v_samples.clear();
   save_hists.clear();
   save_datas.clear();   
   additional_vars.clear();
   extracuts.clear();
  };
  void add_cut(std::string, std::string);

  void addvariable(std::string v, int nb, double mn, double mx){
      TH1F *var_hist = new TH1F(Form("base_%s",v.c_str()),Form("Base Hist %s",v.c_str()),nb,mn,mx);
      additional_vars.insert(std::pair<std::string,TH1F*>(v,var_hist));
  }

  void setvariable(std::string v, double l, double u){
      varstring = v;
      RooRealVar var(varstring.c_str(),varstring.c_str(),l,u);
      var.setMin(l); var.setMax(u+100000);
      wspace->import(var);
      min = l;
      max = u;
      
  };

  void setweight(std::string w){
    RooRealVar weight(w.c_str(),w.c_str(),-1000000,100000);
    weight.removeRange();
    wspace->import(weight);
    weightname = w;
  };
  void addSample(std::string name, std::string region, std::string process, bool is_mc, bool is_signal, bool saveDataset=true);
  void save();
  bool has_process(ControlRegion &cr,std::string proc);
  void run_corrections(std::string correction_name,std::string region);
  int  process_type(ControlRegion &cr,std::string proc);
  void apply_corrections(std::string, std::string, std::string, bool run_corrections=false );

  std::string cutstring ;
  std::string varstring;
  std::string weightname;
  std::string catname;
  
  TH1F *lTmp;
  TFile *fIn;
  TDirectory *fOut;
  int _pdfmodel;

  private:
  const char * doubleexp(RooWorkspace *ws,RooRealVar &x,std::string ext);
  const char * singleexp(RooWorkspace *ws,RooRealVar &x,std::string ext);
  const char * powerlaw(RooWorkspace *ws,RooRealVar &x,std::string ext);
  const char * turnon(RooWorkspace *ws,RooRealVar &x,std::string ext);
  void saveHist(TH1F*);

  int sel_i;
  double min,max;
  RooWorkspace *wspace;
  std::map<std::string, ControlRegion> v_samples;
  std::map<std::string, TH1F*> save_hists;
  std::map<std::string, RooDataSet*> save_datas;

  std::map<std::string,TH1F*> additional_vars;
  std::map<std::string,std::string> extracuts;
};
#endif
