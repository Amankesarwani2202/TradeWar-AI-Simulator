import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.arima.model import ARIMA

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    from live_data import refresh_profiles
except Exception:
    refresh_profiles = None

COUNTRIES = ["China", "India", "Vietnam", "Bangladesh", "Thailand", "South Korea", "Taiwan", "Japan", "EU", "US"]
CATEGORIES = ["Electronics", "Textiles", "Semiconductors", "Machinery", "Chemicals", "Steel"]
YEARS = list(range(2015, 2025))
TRADE_ELASTICITY = {"Electronics": -0.8, "Semiconductors": -0.9, "Machinery": -0.7, "Chemicals": -0.5, "Textiles": -0.6, "Steel": -0.7}
ALTERNATIVE_SUPPLIERS = {
    "China": ["Vietnam", "India", "Thailand", "Bangladesh"], "US": ["EU", "Japan", "South Korea"],
    "Vietnam": ["China", "Thailand", "Bangladesh", "India"], "India": ["Vietnam", "Bangladesh", "Thailand"],
    "Bangladesh": ["Vietnam", "India", "Thailand"], "Thailand": ["Vietnam", "India", "Bangladesh"],
    "Japan": ["South Korea", "Taiwan"], "South Korea": ["Japan", "Taiwan"], "Taiwan": ["South Korea", "Japan"], "EU": ["US", "Japan"],
}
TRADE_FLOWS = [("China","US",500),("China","EU",400),("China","Japan",170),("China","South Korea",160),("China","India",100),("China","Vietnam",80),("Vietnam","US",110),("Vietnam","EU",50),("Vietnam","China",70),("Vietnam","Japan",25),("India","US",80),("India","EU",65),("India","China",20),("South Korea","China",150),("South Korea","US",80),("Taiwan","China",180),("Taiwan","US",100),("Japan","US",150),("Japan","China",160),("Japan","EU",80),("US","EU",350),("US","Japan",80),("US","China",150),("Bangladesh","EU",20),("Bangladesh","US",10),("Thailand","US",45),("Thailand","China",40),("Thailand","EU",30)]
CATEGORY_TRADE_WEIGHTS = {"Electronics": .30, "Semiconductors": .20, "Machinery": .18, "Chemicals": .12, "Textiles": .12, "Steel": .08}
CATEGORY_BILATERAL_MULTIPLIERS = {
    "Electronics": {("China","US"):3.5,("China","EU"):2.8,("China","Japan"):2.0,("China","South Korea"):1.8,("Vietnam","US"):4.5,("Vietnam","EU"):2.5,("Vietnam","Japan"):2.0,("South Korea","US"):2.8,("Taiwan","US"):3.0,("Taiwan","China"):2.5,("Japan","US"):2.2,("India","US"):1.8},
    "Textiles": {("Bangladesh","EU"):14.0,("Bangladesh","US"):12.0,("Vietnam","US"):7.0,("Vietnam","EU"):5.5,("India","EU"):4.5,("India","US"):4.0,("China","US"):2.0,("China","EU"):2.0,("Thailand","US"):2.5,("Thailand","EU"):2.0},
    "Semiconductors": {("Taiwan","US"):10.0,("Taiwan","China"):8.0,("South Korea","China"):6.0,("South Korea","US"):5.5,("Japan","US"):3.5,("China","US"):3.0,("China","South Korea"):2.5,("China","Japan"):2.0,("US","China"):2.0},
    "Machinery": {("EU","US"):4.5,("EU","Japan"):2.5,("EU","China"):3.0,("Japan","US"):4.0,("Japan","China"):3.5,("US","EU"):3.5,("US","Japan"):2.5,("China","US"):2.0,("South Korea","US"):2.0},
    "Chemicals": {("EU","US"):4.0,("EU","Japan"):2.5,("US","EU"):3.5,("Japan","US"):2.5,("China","India"):5.0,("China","US"):2.0,("India","US"):3.5,("India","EU"):3.0,("China","EU"):2.5},
    "Steel": {("China","EU"):3.5,("China","India"):4.5,("China","US"):3.0,("China","Japan"):2.5,("China","South Korea"):2.5,("South Korea","US"):4.0,("Japan","US"):3.5,("EU","US"):2.0,("Taiwan","US"):2.0},
}

COUNTRY_PROFILES = {
    "India":{"population_mn":1410,"urbanization_pct":36,"median_age":28,"gdp_growth":6.5,"inflation":4.8,"labor_force_mn":520,"primary_sector_pct":43,"secondary_sector_pct":25,"tertiary_sector_pct":28,"quaternary_sector_pct":4,"currency":"INR","currency_vs_usd":83.5,"stock_index":"NIFTY 50","stock_ticker":"^NSEI","market_cap_bn":4200,"age_distribution":{"0-14":26,"15-29":27,"30-44":22,"45-59":15,"60+":10}},
    "China":{"population_mn":1411,"urbanization_pct":64,"median_age":39,"gdp_growth":5.2,"inflation":2.3,"labor_force_mn":770,"primary_sector_pct":23,"secondary_sector_pct":39,"tertiary_sector_pct":33,"quaternary_sector_pct":5,"currency":"CNY","currency_vs_usd":7.24,"stock_index":"SSE Composite","stock_ticker":"000001.SS","market_cap_bn":9800,"age_distribution":{"0-14":17,"15-29":19,"30-44":22,"45-59":22,"60+":20}},
    "US":{"population_mn":335,"urbanization_pct":83,"median_age":38,"gdp_growth":2.5,"inflation":3.3,"labor_force_mn":165,"primary_sector_pct":1,"secondary_sector_pct":19,"tertiary_sector_pct":69,"quaternary_sector_pct":11,"currency":"USD","currency_vs_usd":1.0,"stock_index":"S&P 500","stock_ticker":"SPY","market_cap_bn":42000,"age_distribution":{"0-14":18,"15-29":20,"30-44":20,"45-59":19,"60+":23}},
    "EU":{"population_mn":447,"urbanization_pct":75,"median_age":43,"gdp_growth":1.4,"inflation":2.9,"labor_force_mn":230,"primary_sector_pct":4,"secondary_sector_pct":25,"tertiary_sector_pct":63,"quaternary_sector_pct":8,"currency":"EUR","currency_vs_usd":.92,"stock_index":"Euro Stoxx 50","stock_ticker":"^STOXX50E","market_cap_bn":11000,"age_distribution":{"0-14":15,"15-29":17,"30-44":21,"45-59":22,"60+":25}},
    "Vietnam":{"population_mn":99,"urbanization_pct":37,"median_age":32,"gdp_growth":7.0,"inflation":3.5,"labor_force_mn":56,"primary_sector_pct":38,"secondary_sector_pct":34,"tertiary_sector_pct":25,"quaternary_sector_pct":3,"currency":"VND","currency_vs_usd":24500,"stock_index":"VN-Index","stock_ticker":"^VNINDEX","market_cap_bn":260,"age_distribution":{"0-14":23,"15-29":26,"30-44":25,"45-59":17,"60+":9}},
    "Bangladesh":{"population_mn":170,"urbanization_pct":29,"median_age":28,"gdp_growth":6.0,"inflation":5.2,"labor_force_mn":67,"primary_sector_pct":42,"secondary_sector_pct":28,"tertiary_sector_pct":27,"quaternary_sector_pct":3,"currency":"BDT","currency_vs_usd":110,"stock_index":"DSEX","stock_ticker":"DSEX.BD","market_cap_bn":45,"age_distribution":{"0-14":28,"15-29":29,"30-44":22,"45-59":13,"60+":8}},
    "Japan":{"population_mn":123,"urbanization_pct":82,"median_age":49,"gdp_growth":1.9,"inflation":2.5,"labor_force_mn":75,"primary_sector_pct":2,"secondary_sector_pct":24,"tertiary_sector_pct":67,"quaternary_sector_pct":7,"currency":"JPY","currency_vs_usd":149,"stock_index":"Nikkei 225","stock_ticker":"^N225","market_cap_bn":6400,"age_distribution":{"0-14":12,"15-29":14,"30-44":19,"45-59":22,"60+":33}},
    "South Korea":{"population_mn":52,"urbanization_pct":82,"median_age":42,"gdp_growth":2.6,"inflation":2.9,"labor_force_mn":28,"primary_sector_pct":4,"secondary_sector_pct":32,"tertiary_sector_pct":57,"quaternary_sector_pct":7,"currency":"KRW","currency_vs_usd":1320,"stock_index":"KOSPI","stock_ticker":"^KS11","market_cap_bn":1600,"age_distribution":{"0-14":12,"15-29":16,"30-44":22,"45-59":24,"60+":26}},
    "Taiwan":{"population_mn":24,"urbanization_pct":81,"median_age":42,"gdp_growth":3.2,"inflation":2.4,"labor_force_mn":12,"primary_sector_pct":5,"secondary_sector_pct":36,"tertiary_sector_pct":53,"quaternary_sector_pct":6,"currency":"TWD","currency_vs_usd":31.8,"stock_index":"TAIEX","stock_ticker":"^TWII","market_cap_bn":1800,"age_distribution":{"0-14":13,"15-29":17,"30-44":22,"45-59":24,"60+":24}},
    "Thailand":{"population_mn":71,"urbanization_pct":52,"median_age":40,"gdp_growth":2.5,"inflation":3.8,"labor_force_mn":38,"primary_sector_pct":31,"secondary_sector_pct":35,"tertiary_sector_pct":30,"quaternary_sector_pct":4,"currency":"THB","currency_vs_usd":35.5,"stock_index":"SET Index","stock_ticker":"^SET.BK","market_cap_bn":500,"age_distribution":{"0-14":17,"15-29":19,"30-44":25,"45-59":23,"60+":16}},
}

@st.cache_data(show_spinner=False)
def generate_trade_data():
    records=[]; base_exports={"China":2500,"India":450,"Vietnam":280,"Bangladesh":45,"Thailand":250,"South Korea":600,"Taiwan":380,"Japan":700,"EU":2200,"US":1600}
    for year in YEARS:
        for exporter in COUNTRIES:
            for category in CATEGORIES:
                base=base_exports[exporter]; growth=1.04**(year-2015); shock=1.0
                if year>=2018 and exporter in ["China","US"] and category in ["Electronics","Semiconductors"]: shock=.82
                elif year>=2018 and exporter in ["Vietnam","India"] and category in ["Electronics","Textiles"]: shock=1.15
                covid=.88 if year==2020 else 1.0
                records.append({"year":year,"country":exporter,"category":category,"export_value_bn_usd":round(base*CATEGORY_TRADE_WEIGHTS[category]*growth*shock*covid*np.random.uniform(.93,1.07),2),"tariff_rate_pct":round(np.random.uniform(2,8),2)})
    return pd.DataFrame(records)

@st.cache_data(show_spinner=False)
def build_trade_network():
    g=nx.DiGraph(); g.add_nodes_from(COUNTRIES)
    for exporter, importer, value in TRADE_FLOWS: g.add_edge(exporter,importer,weight=value,label=f"${value}B")
    pagerank=nx.pagerank(g,weight="weight"); indeg=nx.in_degree_centrality(g); outdeg=nx.out_degree_centrality(g); between=nx.betweenness_centrality(g,weight="weight")
    metrics=pd.DataFrame({"country":COUNTRIES,"pagerank":[round(pagerank.get(c,0),4) for c in COUNTRIES],"import_dependency":[round(indeg.get(c,0),4) for c in COUNTRIES],"export_reach":[round(outdeg.get(c,0),4) for c in COUNTRIES],"bridge_score":[round(between.get(c,0),4) for c in COUNTRIES]}).sort_values("pagerank",ascending=False)
    vulnerability={n:round((sum(g[u][n]["weight"] for u in g.predecessors(n))/1000)*.5+between.get(n,0)*100*.3+pagerank.get(n,0)*10*.2,3) for n in g.nodes()}
    return g,metrics,dict(sorted(vulnerability.items(),key=lambda x:-x[1]))

def build_scenario_trade_network(base_graph,country,category,tariff_change_pct,target_partner):
    g=nx.DiGraph(); g.add_nodes_from(base_graph.nodes()); alternatives=ALTERNATIVE_SUPPLIERS.get(country,[]); elasticity=abs(TRADE_ELASTICITY.get(category,-.7)); magnitude=min(.40,.10+elasticity*.12)
    if tariff_change_pct>0: exporter_mult=1-magnitude; alt_at_target_mult=1+magnitude*.70; ripple_mult=.98
    elif tariff_change_pct<0: exporter_mult=1+magnitude*.50; alt_at_target_mult=1-magnitude*.30; ripple_mult=1.01
    else: exporter_mult=alt_at_target_mult=ripple_mult=1.0
    for exporter,importer,base_value in TRADE_FLOWS:
        weight=base_value*CATEGORY_TRADE_WEIGHTS.get(category,.15)*CATEGORY_BILATERAL_MULTIPLIERS.get(category,{}).get((exporter,importer),1.0)
        if exporter==country and importer==target_partner: weight*=exporter_mult
        elif exporter in alternatives and importer==target_partner: weight*=alt_at_target_mult
        else: weight*=ripple_mult
        g.add_edge(exporter,importer,weight=max(1.0,round(weight,2)))
    pagerank=nx.pagerank(g,weight="weight"); indeg=nx.in_degree_centrality(g); outdeg=nx.out_degree_centrality(g); between=nx.betweenness_centrality(g,weight="weight")
    metrics=pd.DataFrame({"country":COUNTRIES,"pagerank":[round(pagerank.get(c,0),4) for c in COUNTRIES],"import_dependency":[round(indeg.get(c,0),4) for c in COUNTRIES],"export_reach":[round(outdeg.get(c,0),4) for c in COUNTRIES],"bridge_score":[round(between.get(c,0),4) for c in COUNTRIES]}).sort_values("pagerank",ascending=False)
    vulnerability={n:round((sum(g[u][n]["weight"] for u in g.predecessors(n))/1000)*.5+between.get(n,0)*100*.3+pagerank.get(n,0)*10*.2,3) for n in g.nodes()}
    return g,metrics,dict(sorted(vulnerability.items(),key=lambda x:-x[1]))

def forecast_series(series,steps=3):
    if len(series)<5:return np.array([series[-1]]*steps)
    try:return ARIMA(series,order=(1,1,1)).fit().forecast(steps=steps)
    except Exception:
        x=np.arange(len(series)); c=np.polyfit(x,series,1); return np.array([c[1]+c[0]*(len(series)+i) for i in range(steps)])

def build_country_scenario(df,country,category,tariff_change_pct,target_partner,projection_horizon=3):
    elasticity=TRADE_ELASTICITY.get(category,-.7)
    base_export=float(df[(df.country==country)&(df.category==category)&(df.year==2024)].export_value_bn_usd.sum())
    # Smooth response: no hard floor on beneficiaries. A 30% tariff cut/increase still produces
    # a meaningful relative change rather than eliminating a country from the candidate set.
    raw_change=elasticity*tariff_change_pct
    trade_change_pct=float(np.clip(raw_change,-55.0,55.0))
    horizon_effect=1+(projection_horizon-1)*.08
    new_export=max(0.0,base_export*(1+(trade_change_pct/100)*horizon_effect)); delta=new_export-base_export
    alternatives=ALTERNATIVE_SUPPLIERS.get(country,[]); impact_rows=[]
    for other_country in COUNTRIES:
        baseline=float(df[(df.country==other_country)&(df.category==category)&(df.year==2024)].export_value_bn_usd.sum())
        if other_country==country: pct=trade_change_pct*horizon_effect
        elif other_country in alternatives: pct=-.40*trade_change_pct*horizon_effect
        elif other_country==target_partner: pct=.12*abs(trade_change_pct)*horizon_effect if tariff_change_pct>0 else -.05*abs(trade_change_pct)*horizon_effect
        else: pct=.04*trade_change_pct*horizon_effect
        predicted=baseline*(1+pct/100)
        impact_rows.append({"country":other_country,"baseline_export_bn":round(baseline,2),"predicted_export_bn":round(predicted,2),"change_pct":round(pct,2),"change_bn":round(predicted-baseline,2)})
    impact_df=pd.DataFrame(impact_rows).sort_values("change_bn",ascending=False)

    # Beneficiary scoring is proportional to diverted trade, supplier scale and trade intensity.
    # This avoids the old absolute $0.5B cutoff, which caused small tariff reductions such as
    # -30% to incorrectly return no beneficiaries for some scenarios.
    beneficiary_scores={}
    diversion_pool=abs(delta)*min(0.90,0.35+abs(tariff_change_pct)/100*0.45)
    if tariff_change_pct>0:
        for rank,alt in enumerate(alternatives):
            baseline=float(df[(df.country==alt)&(df.category==category)&(df.year==2024)].export_value_bn_usd.sum())
            share=(1/(rank+1))/sum(1/(i+1) for i in range(len(alternatives)))
            capacity=min(1.0,0.35+baseline/max(base_export,1)*0.65)
            beneficiary_scores[alt]=round(diversion_pool*share*capacity,3)
        beneficiary_type="diversion"
    elif tariff_change_pct<0:
        # Lower tariff benefits the exporter first, then the importer through cheaper goods.
        exporter_gain=abs(delta)*0.60
        importer_gain=abs(delta)*0.20
        beneficiary_scores[country]=round(exporter_gain,3)
        if target_partner!=country: beneficiary_scores[target_partner]=round(importer_gain,3)
        # Existing alternative suppliers also benefit indirectly from a larger market.
        for rank,alt in enumerate(alternatives[:2]):
            baseline=float(df[(df.country==alt)&(df.category==category)&(df.year==2024)].export_value_bn_usd.sum())
            beneficiary_scores[alt]=round(abs(delta)*0.08/(rank+1)*min(1.0,baseline/max(base_export,1)),3)
        beneficiary_type="gain"
    else:
        beneficiary_type="none"
    likely_beneficiaries=[k for k,v in sorted(beneficiary_scores.items(),key=lambda x:x[1],reverse=True) if v>0.001][:3]
    return {"country":country,"category":category,"target_partner":target_partner,"baseline_export_bn":round(base_export,2),"predicted_export_bn":round(new_export,2),"trade_change_pct":round(trade_change_pct,2),"trade_delta_bn":round(delta,2),"risk_score":round(min(100,abs(trade_change_pct)*1.6+12),1),"trade_diversion":beneficiary_scores,"likely_beneficiaries":likely_beneficiaries,"beneficiary_type":beneficiary_type,"impact_df":impact_df,"projection_horizon":projection_horizon}
